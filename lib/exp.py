import kubernetes
from kubernetes import client
from collections import namedtuple
import json
import logging
import os
import subprocess
import yaml


API = 'ml.intel.com'
API_VERSION = 'v1'
EXPERIMENT = "experiment"
EXPERIMENTS = "experiments"
RESULT = "result"
RESULTS = "results"


# Simple Experiments API wrapper for kube client
class Client(object):
    def __init__(self, namespace='default'):
        self.namespace = namespace
        self.k8s = client.CustomObjectsApi()

    # Type Definitions

    def create_crds(self):
        # Necessary to get access to request body deserialization methods.
        api_client = client.ApiClient()

        # API Extensions V1 beta1 API client.
        crd_api = client.ApiextensionsV1beta1Api()

        crd_dir = os.path.join(os.path.dirname(__file__), '../resources/crds')
        crd_paths = [os.path.abspath(os.path.join(crd_dir, name))
                for name in os.listdir(crd_dir)]
        Response = namedtuple('Response', ['data'])
        for path in crd_paths:
            with open(path) as crd_file:
                crd_json = json.dumps(yaml.load(crd_file.read()), sort_keys=True, indent=2)
                print('Deserializing CRD:\n{}'.format(crd_json))
                crd_body = Response(crd_json)
                crd = api_client.deserialize(crd_body, 'V1beta1CustomResourceDefinition')
                print('Deserialized CRD:\n{}'.format(crd))
                try:
                    crd_api.create_custom_resource_definition(crd)
                except Exception:
                    pass

    # Experiments

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


class Experiment(object):
    def __init__(self, name, job_template, status=None, meta=None):
        if not status:
            status = {}
        if not meta:
            meta = {}
        self.name = name
        self.job_template = job_template
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
                'jobSpec': self.job_template
            },
            'status': self.status
        }

    def result(self, job_name):
        return Result(
            job_name,
            self.name,
            self.uid()
        )

    @staticmethod
    def from_body(body):
        return Experiment(body['metadata']['name'],
                          body.get('spec', {}).get('jobSpec'),
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
                'uid': exp_uid
            }
        ]
        labels = self.meta.get('labels', {})
        labels['experiment'] = exp_name
        self.meta['labels'] = labels

    def values(self):
        return self.status.get('values', {})

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
