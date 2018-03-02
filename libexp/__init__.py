from kubernetes import config


def initialize():
    try:
        config.load_incluster_config()

    except Exception:
        config.load_kube_config()


initialize()
