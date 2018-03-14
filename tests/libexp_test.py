import logging
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

    # Create a run for the test experiment
    #
    #   This happens in the parameter search implementation.
    #   This project can provide some default algorithms, or the experiment
    #   author could emit parameter space samples however they like.
    #
    #   This project will provide a controller to materialize experiment
    #   runs into parameterized jobs.
    # params = {'x': 3.14, 'y': 5.0, 'z': False}
    # run = c.create_run(Run('test-1', params, exp.name, exp.uid()))

    # assert run.name == 'test-1'

    # Publish results for the test run
    #
    #   This happens from the job container itself.
    #   The controller will pass sufficient info via environment variables
    #   so that it's easy to fetch the current run and update it.

    job_name = 'test'  # TODO: get this from env
    result = c.create_result(exp.result(job_name))
    result.record_values({'fitness': 0.86})
    result = c.update_result(result)

    assert result.values()['fitness'] == 0.86
