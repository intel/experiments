#!/usr/bin/env python3
from lib.exp import Client
import uuid
from kubernetes import client as k8sclient


test_namespace = k8sclient.V1Namespace()
test_namespace.metadata = k8sclient.V1ObjectMeta(name='demo')

v1_api = k8sclient.CoreV1Api()
v1_api.create_namespace(test_namespace)

c = Client(namespace=test_namespace.metadata.name)
c.create_crds()
