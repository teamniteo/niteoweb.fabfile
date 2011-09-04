# for legacy reasongs -> code was moved from __init__.py
# to project.py -> we import it here so these methods are
# still accessible for example by ``from niteoweb.fabfile configure_nginx``
from niteoweb.fabfile.project import configure_nginx
from niteoweb.fabfile.project import upload_configuration
from niteoweb.fabfile.project import enable_configuration
from niteoweb.fabfile.project import download_code
from niteoweb.fabfile.project import prepare_buildout
from niteoweb.fabfile.project import run_buildout
from niteoweb.fabfile.project import upload_data
from niteoweb.fabfile.project import upload_zodb
from niteoweb.fabfile.project import upload_blobs
from niteoweb.fabfile.project import start_supervisord
from niteoweb.fabfile.project import supervisorctl
from niteoweb.fabfile.project import download_data
from niteoweb.fabfile.project import upload_sphinx
