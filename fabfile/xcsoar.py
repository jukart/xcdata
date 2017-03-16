import json

from fabric.api import task

from setup import settings


@task
def list():
    """List available setups
    """
    result = settings.keys()
    print json.dumps(result)


@task
def build(setup):
    """Build a setup
    """
    pass
