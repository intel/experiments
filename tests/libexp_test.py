import logging
import json
from . import test_namespace
from lib.exp import Client, Experiment


def log(msg):
    logging.getLogger('test').info(msg)


def test_client_list_experiments():
    c = Client(test_namespace.metadata.name)
    result = c.list_experiments()
    assert isinstance(result, list)


def test_client_list_results():
    c = Client(test_namespace.metadata.name)
    result = c.list_results()
    assert isinstance(result, list)


# TODO(CD): run tests in some namespace and destroy it when complete
def test_ux_flow():
    c = Client(test_namespace.metadata.name)

    # Create a new experiment
    jobSpec = {
        'template': {
            'spec': {
                'containers': [
                    {
                        'name': 'train',
                        'image': 'tensorflow',
                        'command': ['train.py']
                    }
                ],
                'restartPolicy': 'Never'
            }
        },
        'backoffLimit': 4
    }
    exp = c.create_experiment(Experiment('test', jobSpec))

    assert exp.name == 'test'

    # Create a job for the test experiment
    #
    #   This happens in the parameter search implementation.
    #   This project can provide some default algorithms, or the experiment
    #   author could emit parameter space samples however they like.
    #
    #   This project will provide a controller to materialize experiment
    #   runs into parameterized jobs.
    params = {'x': 3.14, 'y': 5.0, 'z': False}
    c.create_job(exp, params)

    jobs = c.list_jobs(exp)

    assert len(jobs) == 1
    assert jobs[0].metadata.annotations['experiment-job-parameters'] == \
        json.dumps(params)

    params = {'x': 3.14, 'y': 7.5, 'z': False}
    job2 = c.create_job(exp, params)

    jobs = c.list_jobs(exp)

    assert len(jobs) == 2

    result = c.create_result(exp.result(job2))
    result.record_values({'fitness': 0.86})
    result = c.update_result(result)

    assert result.values()['fitness'] == 0.86
    assert result.parameters() == params
