from cuisine import dir_ensure
from cuisine import mode_sudo
from fabric.api import cd
from fabric.api import env
from fabric.api import get
from fabric.api import local
from fabric.api import settings
from fabric.api import sudo
from fabric.contrib.console import confirm
from fabric.contrib.files import append
from fabric.contrib.files import exists
from fabric.contrib.files import upload_template
from fabric.contrib.project import rsync_project
from niteoweb.fabfile import cmd
from niteoweb.fabfile import err

import os


def create_project_user(prod_user=None):
    """Add a user for a single project so the entire project can run under this
    user."""

    opts = dict(
        prod_user=prod_user or env.prod_user or err("env.prod_user must be set"),
    )

    # create user
    sudo('egrep %(prod_user)s /etc/passwd || adduser %(prod_user)s --disabled-password --gecos ""' % opts)

    # add user to `projects` group
    sudo('gpasswd -a %(prod_user)s projects' % opts)

    # make use of buildout default.cfg
    sudo('mkdir /home/%(prod_user)s/.buildout' % opts)
    sudo('ln -s /etc/buildout/default.cfg /home/%(prod_user)s/.buildout/default.cfg' % opts)
    sudo('chown -R %(prod_user)s:%(prod_user)s /home/%(prod_user)s/.buildout' % opts)


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


def add_files_to_backup(host_shortname=None, bacula_ip=None, bacula_fileset=None):
    """Append a list of project files to backup to this host's fileset."""
    opts = dict(
        host_shortname=host_shortname or env.host_shortname or err("env.host_shortname must be set"),
        bacula_ip=bacula_ip or env.get('bacula_ip') or err("env.bacula_ip must be set"),
        bacula_fileset=bacula_fileset or env.get('bacula_fileset') or '%s/etc/bacula-fileset.txt' % os.getcwd(),
    )

    with settings(host_string=opts['bacula_ip']):
        append(
            '/etc/bacula/clients/%(host_shortname)s-fileset.txt' % env,
            open(opts['bacula_fileset']).read(),
            use_sudo=True
        )

        # reload bacula master configuration
        sudo("service bacula-director restart")


def download_code(shortname=None, prod_user=None, svn_command=None, svn_params=None, svn_url=None, svn_repo=None, svn_dir=None):
    """Pull project code from code repository."""
    opts = dict(
        shortname=shortname or env.get('shortname'),
        prod_user=prod_user or env.get('prod_user'),
    )

    more_opts = dict(
        svn_command=svn_command or env.get('svn_command') or 'export',
        svn_params=svn_params or env.get('svn_params') or '--force --no-auth-cache',
        svn_url=svn_url or env.get('svn_url') or 'https://niteoweb.repositoryhosting.com/svn',
        svn_repo=svn_repo or env.get('svn_repo') or 'niteoweb_%(shortname)s' % opts,
        svn_dir=svn_dir or env.get('svn_dir') or 'niteoweb.%(shortname)s/trunk' % opts,
    )
    opts.update(more_opts)

    with cd('/home/%(prod_user)s' % opts):
        sudo(
            'svn %(svn_command)s %(svn_params)s %(svn_url)s/%(svn_repo)s/%(svn_dir)s ./' % opts,
            user=opts['prod_user']
        )


def prepare_buildout(prod_user=None, python_version=None, production_cfg=None):
    """Prepare zc.buildout environment so we can use
    ``bin/buildout -c production.cfg`` to build a production environment.
    """
    opts = dict(
        prod_user=prod_user or env.get('prod_user'),
        python_version=python_version or env.get('python_version') or '2.6',
        production_cfg=production_cfg or env.get('production_cfg') or 'production.cfg',
    )

    with cd('/home/%(prod_user)s' % opts):
        sudo(
            'virtualenv -p python%(python_version)s --no-site-packages ./' % opts,
            user=opts['prod_user']
        )
        sudo('bin/python bootstrap.py -c %(production_cfg)s' % opts, user=opts['prod_user'])


def run_buildout(prod_user=None, production_cfg=None):
    """Run ``bin/buildout -c production.cfg`` in production user's home folder
    on the production server.
    """
    opts = dict(
        prod_user=prod_user or env.get('prod_user'),
        production_cfg=production_cfg or env.get('production_cfg') or 'production.cfg',
    )

    with cd('/home/%(prod_user)s' % opts):
        sudo('bin/buildout -c %(production_cfg)s' % opts, user=opts['prod_user'])

    # allow everyone in group `projects` to use what you have just put inside
    # the egg cache
    sudo('chown -R root:projects /etc/buildout/{eggs,downloads,extends}')
    sudo('chmod -R 775 /etc/buildout/{eggs,downloads,extends}')


def upload_data(prod_user=None, path=None, zodb_files=None, blob_folders=None):
    """Upload Zope's data to the server."""
    upload_zodb(prod_user, path, zodb_files)
    upload_blobs(prod_user, path, blob_folders)


def upload_zodb(prod_user=None, path=None, zodb_files=None):
    """Upload ZODB part of Zope's data to the server."""
    opts = dict(
        prod_user=prod_user or env.get('prod_user'),
        path=path or env.get('path') or os.getcwd(),
    )
    zodb_files = zodb_files or env.get('zodb_files') or ['Data.fs']
    confirmed = env.get('confirm') or confirm("This will destroy the current" \
        " zodb file(s) on the server. Are you sure you want to continue?")

    if not confirmed:
        return

    with cd('/home/%(prod_user)s/var/filestorage' % opts):
        for filename in zodb_files:
            opts['filename'] = filename

            # backup current database
            if exists(filename):
                # remove the previous backup
                sudo('rm -rf %(filename)s.bak' % opts)

                # create a backup
                sudo('mv %(filename)s %(filename)s.bak' % opts)

            # remove temporary zodb file(s) from previous uploads
            if exists('/tmp/%(filename)s' % opts):
                sudo('rm -rf /tmp/%(filename)s' % opts)

            # upload zodb file(s)to server and set production user as the owner
            upload_template(
                filename='%(path)s/var/filestorage/%(filename)s' % opts,
                destination=filename,
                use_sudo=True
            )
            sudo('chown -R %(prod_user)s:%(prod_user)s %(filename)s' % opts)
            if exists('/home/%(prod_user)s/var/filestorage/%(filename)s.bak' % opts):
                sudo('chown -R %(prod_user)s:%(prod_user)s %(filename)s.bak' % opts)


def upload_blobs(prod_user=None, path=None, blob_folders=None):
    """Upload BLOB part of Zope's data to the server."""
    opts = dict(
        prod_user=prod_user or env.get('prod_user'),
        path=path or env.get('path') or os.getcwd(),
    )
    blob_folders = blob_folders or env.get('blob_folders') or ['blobstorage']
    confirmed = env.get('confirm') or confirm("This will destroy all current" \
        " BLOB files on the server. Are you sure you want to continue?")

    if not confirmed:
        return

    with cd('/home/%(prod_user)s/var' % opts):
        for folder in blob_folders:
            opts['folder'] = folder

            # backup current BLOBs
            if exists(folder):
                # remove the previous backup
                sudo('rm -rf %(folder)s.bak' % opts)

                # create a backup
                sudo('mv %(folder)s %(folder)s.bak' % opts)

            # remove temporary BLOBs from previous uploads
            if exists('/tmp/%(folder)s' % opts):
                sudo('rm -rf /tmp/%(folder)s' % opts)

            # upload BLOBs to the server and move them to their place
            rsync_project('/tmp', local_dir='%(path)s/var/%(folder)s' % opts)
            sudo('mv /tmp/%(folder)s ./' % opts)
            sudo('chown -R %(prod_user)s:%(prod_user)s %(folder)s' % opts)
            sudo('chmod -R 700 %(folder)s' % opts)


def start_supervisord(prod_user=None):
    """Start `supervisord` process monitor which in turn starts Zope and
    optionally others (Varnish, HAProxy, etc.)."""
    opts = dict(
        prod_user=prod_user or env.get('prod_user'),
    )

    with cd('/home/%(prod_user)s' % opts):
        sudo('bin/supervisord', user=opts['prod_user'])


def supervisorctl(*cmd):
    """Runs an arbitrary supervisorctl command."""
    opts = dict(
        prod_user=env.get('prod_user'),
    )
    with cd('/home/%(prod_user)s' % opts):
        sudo('bin/supervisorctl ' + ' '.join(cmd), user=env.prod_user)


def download_data():
    """Download Zope's Data.fs and blobstorage from the server."""

    confirmed = env.get('confirm') or confirm("This will destroy all current" \
        " Zope data on your local machine. Are you sure you want to continue?")

    if not confirmed:
        return

    with cd('/home/%(prod_user)s/var' % env):

        ### Downlaod Data.fs ###
        # backup current Data.fs
        if os.path.exists('%(path)s/var/filestorage/Data.fs' % env):
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


def upload_sphinx(hq_ip=None, sphinx_dir=None, path=None):
    """Uploads HTML files generated by Sphinx."""

    opts = dict(
        hq_ip=hq_ip or env.get('hq_ip') or err("env.hq_ip must be set"),
        sphinx_dir=sphinx_dir or env.get('sphinx_dir') or 'niteoweb.%(shortname)s' % env,
        path=path or env.get('path') or err('env.path must be set'),
    )

    with settings(host_string='%(hq_ip)s:22' % opts):
        with settings(host=opts['hq_ip']):  # additional needed for rsync_project

            # backup existing docs
            if exists('/var/www/sphinx/%(sphinx_dir)s' % opts):
                sudo('mv /var/www/sphinx/%(sphinx_dir)s /var/www/sphinx/%(sphinx_dir)s.bak' % opts)

            # upload new docs
            rsync_project(
                local_dir='%(path)s/docs/html/' % opts,
                remote_dir='/tmp/%(sphinx_dir)s' % opts,
            )

            # move them into place
            sudo('mv /tmp/%(sphinx_dir)s /var/www/sphinx/%(sphinx_dir)s' % env)
