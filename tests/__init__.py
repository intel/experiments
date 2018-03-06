from lib.exp import Client


def setup():
    c = Client()
    c.create_crds()
