from fabric.api import sudo


def err(msg):
    raise AttributeError(msg)

def cmd(*cmd):
    """Execute an arbitrary command on the server. Example ``bin/fab run:"uname -a"``."""
    sudo(' '.join(cmd))
