from lib.exp import Client
import uuid
from kubernetes import client as k8sclient


test_namespace = k8sclient.V1Namespace()
test_namespace.metadata = k8sclient.V1ObjectMeta(name='ns'+str(uuid.uuid4()))


def setup():
    v1_api = k8sclient.CoreV1Api()
    v1_api.create_namespace(test_namespace)

    c = Client(namespace=test_namespace.metadata.name)
    c.create_crds()


def teardown():
    v1_api = k8sclient.CoreV1Api()

    v1_api.delete_namespace(
        name=test_namespace.metadata.name,
        body=k8sclient.models.V1DeleteOptions())
