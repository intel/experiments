from kubernetes import config
from pkg_resources import get_distribution, DistributionNotFound


# prep version information
try:
    # TODO: revert to canonical import from __name__ once distribution matches
    # import name. See: https://github.com/IntelAI/experiments/issues/22
    # __version__ = get_distribution(__name__).version
    __version__ = get_distribution("experiments").version
except DistributionNotFound:
    print("unable to determine Experiments version info")

# ensure we can connect to a running cluster
try:
    config.load_incluster_config()
except Exception:
    config.load_kube_config()
