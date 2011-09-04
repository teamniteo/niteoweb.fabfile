from fabric.api import cd
from fabric.api import get
from fabric.api import local
from fabric.api import settings
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project

from fabric.api import sudo
from fabric.api import env
from fabric.contrib.files import upload_template


import os


def _verify_env(params):
    for param in params:
        if not env.get(param):
            raise AttributeError('env.%s is missing' % param)


def configure_nginx():
    """Upload Nginx configuration for this site to /etc/nginx/sites-available
    and enable it so it gets included in the main nginx.conf.
    """

    upload_configuration()
    enable_configuration()


def upload_configuration():
    """Upload Nginx configuration to /etc/nginx/sites-available."""
    _verify_env(['path', 'shortname'])

    upload_template(
        '%(path)s/etc/nginx.conf' % env,
        '/etc/nginx/sites-available/%(shortname)s.conf' % env,
        use_sudo=True
    )


def enable_configuration():
    """Make a soft link from sites-available/ to sites-enabled/ and reload
    Nginx.
    """
    _verify_env(['shortname', ])

    sudo('ln -fs /etc/nginx/sites-available/%(shortname)s.conf '
         '/etc/nginx/sites-enabled/%(shortname)s.conf' % env)
    sudo('service nginx reload')


def download_code():
    """Pull project code from code repository."""
    _verify_env(['prod_user', 'shortname', ])

    env.svn_params = '--force --no-auth-cache'
    env.svn_url = 'https://niteoweb.repositoryhosting.com/svn'
    env.svn_repo = 'niteoweb_%(shortname)s' % env
    env.svn_dir = 'niteoweb.%(shortname)s/trunk' % env

    with cd('/home/%(prod_user)s' % env):
        sudo(
            'svn export %(svn_params)s %(svn_url)s/%(svn_repo)s/%(svn_dir)s ./' % env,
            user=env.prod_user
        )


def prepare_buildout():
    """Prepare zc.buildout environment so we can use
    ``bin/buildout -c production.cfg`` to build a production environment.
    """
    _verify_env(['prod_user', ])

    with cd('/home/%(prod_user)s' % env):
        sudo(
            'virtualenv -p python2.6 --no-site-packages ./',
            user=env.prod_user
        )
        sudo('bin/python bootstrap.py -c production.cfg', user=env.prod_user)


def run_buildout():
    """Run ``bin/buildout -c production.cfg`` in production user's home folder
    on the production server.
    """
    _verify_env(['prod_user', ])

    with cd('/home/%(prod_user)s' % env):
        sudo('bin/buildout -c production.cfg', user=env.prod_user)

    # allow everyone in group `projects` to use what you have just put put
    # inside the egg-cache
    sudo('chown -R root:projects /etc/buildout/{eggs,downloads,extends}')
    sudo('chmod -R 775 /etc/buildout/{eggs,downloads,extends}')


def upload_data():
    """Upload Zope's data to the server."""

    confirm("This will destroy all current Zope data on the server. " \
    "Are you sure you want to continue?")
    env.confirm = True

    upload_zodb()
    upload_blobs()


def upload_zodb():
    """Upload ZODB part of Zope's data to the server."""
    _verify_env(['prod_user', 'path', ])

    if not env.confirm:
        confirm("This will destroy the current Data.fs file on the server. " \
        "Are you sure you want to continue?")

    with cd('/home/%(prod_user)s/var/filestorage' % env):

        # remove temporary BLOBs from previous uploads
        if exists('/tmp/Data.fs'):
            sudo('rm -rf /tmp/Data.fs')

        # upload Data.fs to server and set production user as it's owner
        upload_template(
            filename='%(path)s/var/filestorage/Data.fs' % env,
            destination='Data.fs',
            use_sudo=True
        )
        sudo('chown -R %(prod_user)s:%(prod_user)s Data.fs' % env)


def upload_blobs():
    """Upload BLOB part of Zope's data to the server."""
    _verify_env(['prod_user', 'path', ])

    if not env.confirm:
        confirm("This will destroy all current BLOB files on the server. " \
        "Are you sure you want to continue?")

    with cd('/home/%(prod_user)s/var' % env):

        # backup current BLOBs
        if exists('blobstorage'):
            sudo('mv blobstorage blobstorage.bak')

        # remove temporary BLOBs from previous uploads
        if exists('/tmp/blobstorage'):
            sudo('rm -rf /tmp/blobstorage')

        # upload BLOBs to the server and move them to their place
        rsync_project('/tmp', local_dir='%(path)s/var/blobstorage' % env)
        sudo('mv /tmp/blobstorage ./')
        sudo('chown -R %(prod_user)s:%(prod_user)s blobstorage' % env)
        sudo('chmod -R 700 blobstorage')


def start_supervisord():
    """Start `supervisord` process monitor which in turn starts Zope and
    optionally others (Varnish, HAProxy, etc.)."""
    _verify_env(['prod_user', ])

    with cd('/home/%(prod_user)s' % env):
        sudo('bin/supervisord', user=env.prod_user)


def supervisorctl(*cmd):
    """Runs an arbitrary supervisorctl command."""
    import pdb; pdb.set_trace( )
    with cd('/home/%(prod_user)s' % env):
        sudo('bin/supervisorctl ' + ' '.join(cmd), user=env.prod_user)


def download_data():
    """Download Zope's Data.fs from the server."""

    confirm("This will destroy all current Zope data on your local machine. " \
            "Are you sure you want to continue?")

    with cd('/home/%(prod_user)s/var' % env):

        ### Downlaod Data.fs ###
        # backup current Data.fs
        if os.path.exists('filestorage/Data.fs'):
            local('mv %(path)s/var/filestorage/Data.fs %(path)s/var/filestorage/Data.fs.bak' % env)

        # remove temporary Data.fs file from previous downloads
        if exists('/tmp/Data.fs', use_sudo=True):
            sudo('rm -rf /tmp/Data.fs')

        # downlaod Data.fs from server
        sudo('rsync -a filestorage/Data.fs /tmp/Data.fs')
        get('/tmp/Data.fs', '%(path)s/var/filestorage/Data.fs' % env)

        ### Download Blobs ###
        # backup current Blobs
        if os.path.exists('%(path)s/var/blobstorage' % env):
            local('mv %(path)s/var/blobstorage %(path)s/var/blobstorage_bak' % env)

        # remove temporary Blobs from previous downloads
        if exists('/tmp/blobstorage', use_sudo=True):
            sudo('rm -rf /tmp/blobstorage')

        # download Blobs from server -> use maintenance user for transfer
        sudo('rsync -a blobstorage /tmp/')
        sudo('chown -R %(user)s /tmp/blobstorage' % env)
        local('rsync -az %(user)s@%(server)s:/tmp/blobstorage %(path)s/var/' % env)


def upload_sphinx():
    """Uploads HTML files generated by Sphinx."""
    with settings(host_string='%(hq)s:22' % env):
        with settings(host=env.hq):  # additional needed for rsync_project

            # backup existing docs
            if exists('/var/www/sphinx/niteoweb.%(shortname)s' % env):
                sudo('mv /var/www/sphinx/niteoweb.%(shortname)s /var/www/sphinx/niteoweb.%(shortname)s.bak' % env)

            # upload new docs
            rsync_project(
                local_dir='%(path)s/docs/html/' % env,
                remote_dir='/tmp/niteoweb.%(shortname)s' % env,
            )

            # move them into place
            sudo('mv /tmp/niteoweb.%(shortname)s /var/www/sphinx/niteoweb.%(shortname)s' % env)
