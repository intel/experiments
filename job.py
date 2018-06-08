#!/usr/bin/env python3
from lib.exp import Client
import json
import kubernetes
import os
import random
import sys
import time


def main():
    ns = os.getenv('EXPERIMENT_NAMESPACE')
    job_name = os.getenv('JOB_NAME')
    if not ns or not job_name:
        raise Exception('Missing EXPERIMENT_NAMESPACE or JOB_NAME')

    c = Client(ns)
    exp = c.current_experiment()

    print('Starting job {} for experiment {}'.format(job_name, exp.name))

    try:
        result = c.create_result(exp.result(c.get_job(job_name)))
    except kubernetes.client.rest.ApiException as e:
        body = json.loads(e.body)
        if body['reason'] != 'AlreadyExists':
            raise e
        result = c.get_result(job_name)

    # result.record_values({'environment': os.environ})
	# result = c.update_result(result)

    for i in range(0, 201, 10):
        values = {
            'step-{}'.format(i): {
                'loss': random.random(),
                'accuracy': random.random()
            }
        }
        print('publishing results: {}'.format(
            json.dumps(values, sort_keys=True)))
        result.record_values(values)
        time.sleep(1)
        result = c.update_result(result)


if __name__ == '__main__':
    main()
