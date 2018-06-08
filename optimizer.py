#!/usr/bin/env python3


"""optimizer.

Usage:
  optimizer.py --namespace=<ns> --experiment-name=<exp> [--verbose]

Options:
  -h --help           Show this screen.
  --version           Show version.
  --namespace=<ns>    Experiment namespace [default: default].
  --experiment=<exp>  Experiment name.
  --verbose           Enable verbose log output.
"""
from docopt import docopt
import itertools
import json
from lib.exp import Client
import logging


VERBOSE = False
LOG = None


def main():
    global LOG
    # Parse arguments
    args = docopt(__doc__, version='optimizer 0.1.0')

    # Set up logging
    LOG = logging.getLogger('optimizer')
    logging.basicConfig(level=logging.INFO)
    if args['--verbose']:
        logging.basicConfig(level=logging.DEBUG)
    LOG.debug('arguments:\n{}'.format(args))

    namespace = args['--namespace']
    experiment_name = args['--experiment-name']
    client = Client(namespace)
    do_grid_search(client, client.get_experiment(experiment_name))


def do_grid_search(client, exp):
    jobs = build_grid_jobs(client, exp)


def build_grid_jobs(client, exp):
    for point in grid(exp.parameters):
        LOG.info('creating job for point:\n{}'.format(json.dumps(
            point, sort_keys=True, indent=2)))
        job = client.create_job(exp, point)
        LOG.info('created job: {}'.format(job.metadata.name))


# `parameters` is a map that looks like this:
#
# {
#   "x": [1, 1, 2, 3, 5, 8, 13],
#   "y": [true, false],
#   "z": ["foo", "bar"]
# }
#
# This function returns a list of maps of parameter names to parameter
# values.
def grid(parameters):
    # Returns a list of (name, value) 2-tuples representing this parameter.
    def expand(name, values):
        return [(name, value) for value in values]

    expanded_parameters = [expand(item[0], item[1]) for item in
                           parameters.items()]

    results = []
    for point in itertools.product(*expanded_parameters):
        LOG.debug('processing point: {}'.format(point))
        result = {}
        for named_value in point:
            (name, value) = named_value
            result[name] = value
        results.append(result)
    return results


if __name__ == '__main__':
    main()
