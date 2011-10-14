# for legacy reasongs -> code was moved from __init__.py
# to project.py -> we import it here so these methods are
# still accessible for example by ``from niteoweb.fabfile configure_nginx``
from niteoweb.fabfile.project import *


def err(msg):
    raise(msg)
