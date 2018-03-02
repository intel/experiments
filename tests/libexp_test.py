import logging
from ..libexp import libexp


def log(msg):
    logging.getLogger('test').info(msg)


def test_client_list_experiments():
    c = libexp.Client()
    result = c.list_experiments()
    assert isinstance(result, list)


def test_client_list_runs():
    c = libexp.Client()
    result = c.list_runs()
    assert isinstance(result, list)


# TODO(CD): run tests in some namespace and destroy it when complete
def test_ux_flow():
    c = libexp.Client()

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
    exp = c.create_experiment(libexp.Experiment('test', jobSpec))

    assert exp.name == 'test'

    # Create a run for the test experiment
    params = {'x': 3.14, 'y': 5.0, 'z': False}
    run = c.create_run(libexp.Run('test-1', params, exp.name, exp.uid()))

    assert run.name == 'test-1'

    # Publish results for the test run
    run.record_results({'fitness': 0.86})
    run = c.update_run(run)

    assert run.results()['fitness'] == 0.86
