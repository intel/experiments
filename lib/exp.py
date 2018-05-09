from kubernetes import client
from collections import namedtuple
import copy
import json
import os
import uuid
import yaml


API = 'ml.intel.com'
API_VERSION = 'v1'
EXPERIMENT = "experiment"
EXPERIMENTS = "experiments"
RESULT = "result"
RESULTS = "results"


def deserialize_object(serialized_bytes, class_name):
    # Necessary to get access to request body deserialization methods.
    api_client = client.ApiClient()
    Response = namedtuple('Response', ['data'])
    body = Response(serialized_bytes)
    return api_client.deserialize(body, class_name)


# Simple Experiments API wrapper for kube client
class Client(object):
    def __init__(self, namespace='default'):
        self.namespace = namespace
        self.k8s = client.CustomObjectsApi()
        self.batch = client.BatchV1Api()

    # Type Definitions

    def create_crds(self):
        # API Extensions V1 beta1 API client.
        crd_api = client.ApiextensionsV1beta1Api()

        crd_dir = os.path.join(os.path.dirname(__file__), '../resources/crds')
        crd_paths = [os.path.abspath(os.path.join(crd_dir, name))
                     for name in os.listdir(crd_dir)]

        for path in crd_paths:
            with open(path) as crd_file:
                crd_json = json.dumps(
                    yaml.load(crd_file.read()), sort_keys=True, indent=2)
                crd = deserialize_object(
                    crd_json, 'V1beta1CustomResourceDefinition')
                try:
                    crd_api.create_custom_resource_definition(crd)
                except Exception:
                    pass

    # Experiments

    def current_experiment(self):
        exp_name = os.getenv('EXPERIMENT_NAME')
        if not exp_name:
            raise Exception('Environment variable EXPERIMENT_NAME not set')
        return self.get_experiment(exp_name)

    def list_experiments(self):
        response = self.k8s.list_namespaced_custom_object(
                API,
                API_VERSION,
                self.namespace,
                EXPERIMENTS)
        return [Experiment.from_body(item) for item in response['items']]

    def get_experiment(self, name):
        response = self.k8s.get_namespaced_custom_object(
                API,
                API_VERSION,
                self.namespace,
                EXPERIMENTS,
                name)
        return Experiment.from_body(response)

    def create_experiment(self, exp):
        response = self.k8s.create_namespaced_custom_object(
                API,
                API_VERSION,
                self.namespace,
                EXPERIMENTS,
                body=exp.to_body())
        return Experiment.from_body(response)

    def update_experiment(self, exp):
        response = self.k8s.replace_namespaced_custom_object(
                API,
                API_VERSION,
                self.namespace,
                EXPERIMENTS,
                exp.name,
                exp.to_body())
        return Experiment.from_body(response)

    def delete_experiment(self, name):
        return self.k8s.delete_namespaced_custom_object(
                API,
                API_VERSION,
                self.namespace,
                EXPERIMENTS,
                name,
                client.models.V1DeleteOptions())

    # Experiment Results

    def list_results(self):
        response = self.k8s.list_namespaced_custom_object(
                API,
                API_VERSION,
                self.namespace,
                RESULTS)
        return [Result.from_body(item) for item in response['items']]

    def get_result(self, name):
        response = self.k8s.get_namespaced_custom_object(
                API,
                API_VERSION,
                self.namespace,
                RESULTS,
                name)
        return Result.from_body(response)

    def create_result(self, result):
        response = self.k8s.create_namespaced_custom_object(
                API,
                API_VERSION,
                self.namespace,
                RESULTS,
                body=result.to_body())
        return Result.from_body(response)

    def update_result(self, result):
        response = self.k8s.replace_namespaced_custom_object(
                API,
                API_VERSION,
                self.namespace,
                RESULTS,
                result.name,
                result.to_body())
        return Result.from_body(response)

    def delete_result(self, name):
        return self.k8s.delete_namespaced_custom_object(
                API,
                API_VERSION,
                self.namespace,
                RESULTS,
                name,
                client.models.V1DeleteOptions())

    def list_jobs(self, experiment):
        return self.batch.list_namespaced_job(
            self.namespace,
            label_selector='experiment_uid={}'.format(experiment.uid())
        ).items

    def create_job(self, experiment, parameters):
        short_uuid = str(uuid.uuid4())[:8]
        metadata = {
            'name': "{}-{}".format(experiment.name, short_uuid),
            'labels': {
                'experiment_uid': experiment.uid(),
                'experiment_name': experiment.name
            },
            'annotations': {
                'job_parameters': json.dumps(parameters)
            },
            'ownerReferences': [
                {
                    'apiVersion': '{}/{}'.format(API, API_VERSION),
                    'controller': True,
                    'kind': EXPERIMENT.title(),
                    'name': experiment.name,
                    'uid': experiment.uid(),
                    'blockOwnerDeletion': True
                }
            ]
        }
        job_name = metadata['name']

        template = copy.deepcopy(experiment.job_template)

        containers = None
        if 'template' in template and \
           'spec' in template['template'] and \
           'containers' in template['template']['spec']:

            containers = template['template']['spec']['containers']

        if not containers:
            raise Exception(
                "Container templates are not available in experiment job")

        experiment_environment_metadata = [
            {'name': 'JOB_NAME', 'value': job_name},
            {'name': 'EXPERIMENT_NAMESPACE', 'value': self.namespace},
            {'name': 'EXPERIMENT_NAME', 'value': experiment.name},
            {'name': 'EXPERIMENT_UID', 'value': experiment.uid()}
        ]

        # Provide parameters in environment variables, encoded like:
        # PARAMETER_X_FLOAT = "3.14"
        for parameter in parameters:
            value = parameters[parameter]
            value_kind = str(type(value).__name__)
            key = "PARAMETER_{}_{}".format(parameter, value_kind).upper()

            # To avoid python'ist boolean values.
            # Encode them as either 'true' or 'false'
            if value_kind == "bool":
                value = str(value).lower()

            experiment_environment_metadata.append(
                    {'name': key, 'value': str(value)})

        for container in containers:
            if not container.get('env'):
                container['env'] = []

            container['env'].extend(experiment_environment_metadata)

        job = client.models.V1Job(
            api_version='batch/v1',
            kind='Job',
            metadata=metadata,
            spec=deserialize_object(json.dumps(template), 'V1JobSpec'))

        return self.batch.create_namespaced_job(
            self.namespace,
            body=job
        )


class Experiment(object):
    def __init__(self,
                 name,
                 job_template,
                 parameters=None,
                 status=None,
                 meta=None):
        if not parameters:
            parameters = {}
        if not status:
            status = {}
        if not meta:
            meta = {}
        self.name = name
        self.job_template = job_template
        self.parameters = parameters
        self.status = status
        self.meta = meta
        self.meta['name'] = self.name

    def uid(self):
        return self.meta.get('uid')

    def to_body(self):
        return {
            'apiVersion': "{}/{}".format(API, API_VERSION),
            'kind': EXPERIMENT.title(),
            'metadata': self.meta,
            'spec': {
                'jobSpec': self.job_template,
                'parameters': self.parameters
            },
            'status': self.status
        }

    def result(self, job):
        status = {}
        if 'job_parameters' in job.metadata.annotations:
            status['job_parameters'] = json.loads(
                job.metadata.annotations['job_parameters'])

        return Result(
            job.metadata.name,
            self.name,
            self.uid(),
            status=status
        )

    @staticmethod
    def from_body(body):
        return Experiment(body['metadata']['name'],
                          body.get('spec', {}).get('jobSpec'),
                          body.get('spec', {}).get('parameters'),
                          meta=body['metadata'],
                          status=body.get('status', {}))


class Result(object):
    def __init__(self, name, exp_name, exp_uid, status=None, meta=None):
        if not status:
            status = {}
        if not meta:
            meta = {}

        self.name = name
        self.meta = meta
        self.status = status
        self.meta['name'] = self.name
        self.meta['ownerReferences'] = [
            {
                'apiVersion': '{}/{}'.format(API, API_VERSION),
                'controller': True,
                'kind': EXPERIMENT.title(),
                'name': exp_name,
                'uid': exp_uid,
                'blockOwnerDeletion': True
            }
        ]
        labels = self.meta.get('labels', {})
        labels['experiment'] = exp_name
        self.meta['labels'] = labels

    def values(self):
        return self.status.get('values', {})

    def job_parameters(self):
        return self.status.get('job_parameters', {})

    # extends `.status.values` with the supplied map
    def record_values(self, new_values):
        old_values = self.status.get('values', {})
        self.status['values'] = old_values
        old_values.update(new_values)

    def to_body(self):
        return {
            'apiVersion': "{}/{}".format(API, API_VERSION),
            'kind': RESULT.title(),
            'metadata': self.meta,
            'status': self.status
        }

    @staticmethod
    def from_body(body):
        return Result(body['metadata']['name'],
                      body['metadata']['ownerReferences'][0]['name'],
                      body['metadata']['ownerReferences'][0]['uid'],
                      meta=body['metadata'],
                      status=body.get('status', {}))
