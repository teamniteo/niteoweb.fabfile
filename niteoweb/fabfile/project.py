from fabric.api import cd
from fabric.api import env
from fabric.api import get
from fabric.api import local
from fabric.api import settings
from fabric.api import sudo
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from fabric.contrib.files import upload_template
from fabric.contrib.project import rsync_project
from niteoweb.fabfile import err

import os


def configure_nginx(shortname=None):
    """Upload Nginx configuration for this site to /etc/nginx/sites-available
    and enable it so it gets included in the main nginx.conf.
    """
    upload_nginx_config(shortname)
    enable_nginx_config(shortname)


def upload_nginx_config(shortname=None, nginx_conf=None):
    """Upload Nginx configuration to /etc/nginx/sites-available."""
    opts = dict(
        shortname=shortname or env.get('shortname'),
        nginx_conf=nginx_conf or env.get('nginx_conf') or '%s/etc/nginx.conf' % os.getcwd(),
    )

    upload_template(
        opts['nginx_conf'],
        '/etc/nginx/sites-available/%(shortname)s.conf' % env,
        use_sudo=True
    )


def enable_nginx_config(shortname=None):
    """Make a link from sites-available/ to sites-enabled/ and reload Nginx."""
    opts = dict(
        shortname=shortname or env.get('shortname'),
    )

    sudo('ln -fs /etc/nginx/sites-available/%(shortname)s.conf '
         '/etc/nginx/sites-enabled/%(shortname)s.conf' % opts)
    sudo('service nginx reload')


def download_code(shortname=None, prod_user=None, svn_params=None, svn_url=None, svn_repo=None, svn_dir=None):
    """Pull project code from code repository."""
    opts = dict(
        shortname=shortname or env.get('shortname'),
        prod_user=prod_user or env.get('prod_user'),
    )

    more_opts = dict(
        svn_params=svn_params or env.get('svn_params') or '--force --no-auth-cache',
        svn_url=svn_url or env.get('svn_url') or 'https://niteoweb.repositoryhosting.com/svn',
        svn_repo=svn_repo or env.get('svn_repo') or 'niteoweb_%(shortname)s' % opts,
        svn_dir=svn_dir or env.get('svn_dir') or 'niteoweb.%(shortname)s/trunk' % opts,
    )
    opts.update(more_opts)

    with cd('/home/%(prod_user)s' % opts):
        sudo(
            'svn export %(svn_params)s %(svn_url)s/%(svn_repo)s/%(svn_dir)s ./' % opts,
            user=opts['prod_user']
        )


def prepare_buildout(prod_user=None):
    """Prepare zc.buildout environment so we can use
    ``bin/buildout -c production.cfg`` to build a production environment.
    """
    opts = dict(
        prod_user=prod_user or env.get('prod_user'),
    )

    with cd('/home/%(prod_user)s' % env):
        sudo(
            'virtualenv -p python2.6 --no-site-packages ./',
            user=env.prod_user
        )
        sudo('bin/python bootstrap.py -c production.cfg', user=env.prod_user)


def run_buildout(prod_user=None):
    """Run ``bin/buildout -c production.cfg`` in production user's home folder
    on the production server.
    """
    opts = dict(
        prod_user=prod_user or env.get('prod_user'),
    )

    with cd('/home/%(prod_user)s' % env):
        sudo('bin/buildout -c production.cfg', user=env.prod_user)

    # allow everyone in group `projects` to use what you have just put inside
    # the egg cache
    sudo('chown -R root:projects /etc/buildout/{eggs,downloads,extends}')
    sudo('chmod -R 775 /etc/buildout/{eggs,downloads,extends}')


def upload_data(prod_user=None):
    """Upload Zope's data to the server."""

    if not env.get('confirm'):
        confirm("This will destroy all current Zope data on the server. " \
        "Are you sure you want to continue?")

    upload_zodb(prod_user)
    upload_blobs(prod_user)


def upload_zodb(prod_user=None, path=None):
    """Upload ZODB part of Zope's data to the server."""
    opts = dict(
        prod_user=prod_user or env.get('prod_user'),
        path=path or env.get('path') or os.getcwd()
    )

    # _verify_env(['prod_user', 'path', ])

    if not env.get('confirm'):
        confirm("This will destroy the current Data.fs file on the server. " \
        "Are you sure you want to continue?")

    with cd('/home/%(prod_user)s/var/filestorage' % opts):

        # remove temporary BLOBs from previous uploads
        if exists('/tmp/Data.fs'):
            sudo('rm -rf /tmp/Data.fs')

        # upload Data.fs to server and set production user as it's owner
        upload_template(
            filename='%(path)s/var/filestorage/Data.fs' % opts,
            destination='Data.fs',
            use_sudo=True
        )
        sudo('chown -R %(prod_user)s:%(prod_user)s Data.fs' % opts)


def upload_blobs(prod_user=None, path=None):
    """Upload BLOB part of Zope's data to the server."""
    opts = dict(
        prod_user=prod_user or env.get('prod_user'),
        path=path or env.get('path') or os.getcwd()
    )

    if not env.get('confirm'):
        confirm("This will destroy all current BLOB files on the server. " \
        "Are you sure you want to continue?")

    with cd('/home/%(prod_user)s/var' % opts):

        # backup current BLOBs
        if exists('blobstorage'):
            sudo('mv blobstorage blobstorage.bak')

        # remove temporary BLOBs from previous uploads
        if exists('/tmp/blobstorage'):
            sudo('rm -rf /tmp/blobstorage')

        # upload BLOBs to the server and move them to their place
        rsync_project('/tmp', local_dir='%(path)s/var/blobstorage' % opts)
        sudo('mv /tmp/blobstorage ./')
        sudo('chown -R %(prod_user)s:%(prod_user)s blobstorage' % opts)
        sudo('chmod -R 700 blobstorage')


def start_supervisord(prod_user=None):
    """Start `supervisord` process monitor which in turn starts Zope and
    optionally others (Varnish, HAProxy, etc.)."""
    opts = dict(
        prod_user=prod_user or env.get('prod_user'),
    )

    with cd('/home/%(prod_user)s' % env):
        sudo('bin/supervisord', user=env.prod_user)


def supervisorctl(*cmd):
    """Runs an arbitrary supervisorctl command."""
    with cd('/home/%(prod_user)s' % env):
        sudo('bin/supervisorctl ' + ' '.join(cmd), user=env.prod_user)


def download_data():
    """Download Zope's Data.fs from the server."""

    if not env.get('confirm'):
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
