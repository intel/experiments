#!/usr/bin/env python3
from lib.exp import Client
import json
import os
from kubernetes import client as k8sclient


ns = os.getenv("EXPERIMENT_NAMESPACE", "demo")

test_namespace = k8sclient.V1Namespace()
test_namespace.metadata = k8sclient.V1ObjectMeta(name=ns)

v1_api = k8sclient.CoreV1Api()
try:
    v1_api.create_namespace(test_namespace)
except k8sclient.rest.ApiException as e:
    if json.loads(e.body)['reason'] == "AlreadyExists":
        pass
    else:
        raise e

c = Client(namespace=test_namespace.metadata.name)
c.create_crds()
