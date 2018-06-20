import logging
import json
from . import test_namespace
from lib.exp import Client, Experiment


def log(msg):
    logging.getLogger('test').info(msg)


def test_client_list_experiments():
    c = Client(logging.getLogger('test'), test_namespace.metadata.name)
    result = c.list_experiments()
    assert isinstance(result, list)


def test_client_list_results():
    c = Client(logging.getLogger('test'), test_namespace.metadata.name)
    result = c.list_results()
    assert isinstance(result, list)


# TODO(CD): run tests in some namespace and destroy it when complete
def test_ux_flow():
    c = Client(logging.getLogger('test'), test_namespace.metadata.name)

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

    verify_exp = c.get_experiment('test')
    assert verify_exp.__dict__ == exp.__dict__

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
    assert jobs[0].metadata.annotations['job_parameters'] == \
        json.dumps(params)

    verify_job = c.get_job(jobs[0].metadata.name)
    assert verify_job.metadata.__dict__ == jobs[0].metadata.__dict__

    params = {'x': 3.14, 'y': 7.5, 'z': False}
    job2 = c.create_job(exp, params)

    jobs = c.list_jobs(exp)

    assert len(jobs) == 2

    result = c.create_result(exp.result(job2))

    verify_result = c.get_result(result.name)
    assert verify_result.__dict__ == result.__dict__

    result.record_values({'fitness': 0.86})
    result = c.update_result(result)

    assert result.values()['fitness'] == 0.86
    assert result.job_parameters() == params
