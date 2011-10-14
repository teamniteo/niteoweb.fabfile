from fabric.api import env
from fabric.api import run
from fabric.api import sudo
from fabric.contrib.console import confirm
from fabric.contrib.files import append
from fabric.contrib.files import exists
from fabric.contrib.files import sed
from fabric.contrib.files import uncomment
from fabric.contrib.files import upload_template
from fabric.operations import prompt
from fabric.contrib.files import comment
from niteoweb.fabfile import err

import os

def normalize_rackspace():
    """docstring for normalize_rackspace"""
    comment('/etc/sudoers', 'Defaults    requiretty')

def create_admin_accounts(admins=None, default_password=None):
    """Create admin accounts, so admins can access the server."""
    opts = dict(
        admins=admins or env.get('admins') or ['zupo', 'kunta', 'brodul'],
        default_password=default_password or env.get('default_password') or 'secret',
    )

    for admin in opts["admins"]:
        create_admin_account(admin, default_password=default_password)

    if not env.get('confirm'):
        confirm("Users %(admins)s were successfully created. Notify"
                "them that they must login and change their default password "
                "(%(default_password)s) with the ``passwd`` command. Proceed?" % opts)


def create_admin_account(admin, default_password=None):
    """Create an account for an admin to use to access the server."""
    opts = dict(
        admin=admin,
        default_password=default_password or env.get('default_password') or 'secret',
    )

    # create user
    sudo('egrep %(admin)s /etc/passwd || adduser %(admin)s --disabled-password --gecos ""' % opts)

    # add public key for SSH access
    if not exists('/home/%(admin)s/.ssh' % opts):
        sudo('mkdir /home/%(admin)s/.ssh' % opts)

    opts['pub'] = prompt("Paste admin's public key: ")
    sudo("echo '%(pub)s' > /home/%(admin)s/.ssh/authorized_keys" % opts)

    # allow this user in sshd_config
    append("/etc/ssh/sshd_config",'AllowUsers %(admin)s@*' % opts, use_sudo=True)

    # allow sudo for maintenance user by adding it to 'sudo' group
    sudo('gpasswd -a %(admin)s sudo' % opts)

    # set default password for initial login
    sudo('echo "%(admin)s:%(default_password)s" | chpasswd' % opts)


def install_ufw(rules=None):
    """Install and configure Uncomplicated Firewall."""
    sudo('apt-get -yq install ufw')
    configure_ufw(rules)


def configure_ufw(rules=None):
    """Configure Uncomplicated Firewall."""
    # reset rules so we start from scratch
    sudo('ufw --force reset')

    rules = rules or env.rules or err("env.rules must be set"),
    for rule in rules:
        sudo(rule)

    # re-enable firewall and print rules
    sudo('ufw --force enable')
    sudo('ufw status verbose')


def disable_root_login():
    """Disable `root` login for even more security. Access to `root` account
    is now possible by first connecting with your dedicated maintenance
    account and then running ``sudo su -``."""
    sudo('passwd --lock root')


def set_hostname(server_ip=None, hostname=None):
    """Set server's hostname."""
    opts = dict(
        server_ip=server_ip,
        hostname=hostname,
    )

    sudo('echo "\n%(server_ip)s %(hostname)s" >> /etc/hosts' % opts)
    sudo('echo "%(hostname)s" > /etc/hostname' % opts)
    sudo('hostname %(hostname)s' % opts)


def set_system_time(timezone=None):
    """Set timezone and install ``ntp`` to keep time accurate."""

    opts = dict(
        timezone=timezone or env.get('timezone') or '/usr/share/zoneinfo/Etc/UTC',
    )

    # set timezone
    sudo('cp %(timezone)s /etc/localtime' % opts)

    # install NTP
    sudo('apt-get -yq install ntp')


def install_system_libs(additional_libs=None):
    """Install a bunch of stuff we need for normal operation such as
    ``gcc``, ``rsync``, ``vim``, ``libpng``, etc."""

    opts = dict(
        additional_libs=additional_libs or env.get('additional_libs') or '',
    )

    sudo('apt-get -yq install '

             # tools
             'lynx '
             'curl '
             'rsync '
             'telnet '
             'build-essential '
             'python-software-properties '  # to get add-apt-repositories command

             # imaging, fonts, compression, encryption, etc.
             'libjpeg-dev '
             'libjpeg62-dev '
             'libfreetype6-dev '
             'zlib1g-dev '
             'libreadline5-dev '
             'zlib1g-dev '
             'libbz2-dev '
             'libssl-dev '
             'libjpeg62-dev '
             '%(additional_libs)s' % opts
             )


def install_unattended_upgrades(email=None):
    """Configure Ubuntu to automatically install security updates."""
    opts = dict(
        email=email or env.get('email') or 'maintenance@niteoweb.com',
    )

    sudo('apt-get -yq install unattended-upgrades')
    sed('/etc/apt/apt.conf.d/50unattended-upgrades',
        '//Unattended-Upgrade::Mail "root@localhost";',
        'Unattended-Upgrade::Mail "%(email)s";' % opts, use_sudo=True)


def raid_monitoring(email=None):
    """Configure monitoring of our RAID-1 field. If anything goes wrong,
    send an email!"""
    opts = dict(
        email=email or env.get('email') or 'maintenance@niteoweb.com',
    )

    # enable email notifications from mdadm raid monitor
    append('/etc/mdadm/mdadm.conf', 'MAILADDR %(email)s' % opts, use_sudo=True)

    # enable email notification for SMART disk monitoring
    sudo('apt-get -yq install smartmontools')
    uncomment('/etc/default/smartmontools', '#start_smartd=yes', use_sudo=True)


def install_nginx(nginx_conf=None):
    """Install and configure Nginx webserver."""

    sudo('add-apt-repository ppa:nginx/stable')
    sudo('apt-get update')
    sudo('apt-get -yq install nginx')

    configure_nginx()


def configure_nginx(nginx_conf=None):
    """Upload Nginx configuration and restart Nginx so this configuration takes
    effect."""
    opts = dict(
        nginx_conf=nginx_conf or env.get('nginx_conf') or '%s/etc/nginx.conf' % os.getcwd(),
    )

    upload_template(opts['nginx_conf'], '/etc/nginx/nginx.conf', use_sudo=True)
    sudo('service nginx restart')


def install_sendmail(email=None):
    """Prepare a localhost SMTP server for sending out system notifications
    to admins."""
    opts = dict(
        email=email or env.get('email') or 'maintenance@niteoweb.com',
    )

    # install sendmail
    sudo('apt-get -yq install sendmail')

    # all email should be sent to maintenance@niteoweb.com
    append('/etc/aliases', 'root:           %(email)s' % opts, use_sudo=True)


def install_bacula_client(bacula_client_conf=None):
    """Install and configure Bacula backup client, which listens for
    instructions from Bacula master and backups critical data
    when told to do so."""

    # Official repos only have version 5.0.1, we need 5.0.3
    run('wget http://launchpad.net/~mario-sitz/+archive/ppa/+build/1910399/+files/bacula-common_5.0.3-0ubuntu1%7Eppa1%7Elucid_amd64.deb -O bacula-common.deb')
    run('wget http://launchpad.net/~mario-sitz/+archive/ppa/+build/1910399/+files/bacula-fd_5.0.3-0ubuntu1%7Eppa1%7Elucid_amd64.deb -O bacula-fd.deb')
    sudo('dpkg -i bacula-common.deb bacula-fd.deb')
    run('rm -f bacula-common.deb bacula-fd.deb')

    # this folder is needed
    if not exists('/var/spool/bacula'):
        sudo('mkdir /var/spool/bacula')

    configure_bacula_client(bacula_client_conf)


def configure_bacula_client(bacula_client_conf=None):
    """Upload configuration for Bacula File Deamon (client)
    and restart it."""
    opts = dict(
        bacula_client_conf=bacula_client_conf or env.get('bacula_client_conf') or '%s/etc/bacula-fd.conf' % os.getcwd(),
    )

    upload_template(opts['bacula_client_conf'], '/etc/bacula/bacula-fd.conf', use_sudo=True)
    sudo('service bacula-fd restart')


def add_to_bacula_master(shortname=None, bacula_conf=None, bacula_host_string=None):
    """Add this server's configuration to Bacula master"""
    opts = dict(
        shortname=shortname or env.get('shortname'),
        bacula_conf=bacula_conf or env.get('bacula_conf') or '%s/etc/bacula-master.conf' % os.getcwd(),
        bacula_host_string=bacula_host_string or env.get('bacula_host_string') or 'bacula.niteoweb.com:22',
    )
    _verify_opts(opts, ['shortname', ])

    with settings(host_string=opts['bacula_host_string']):

        # upload project-specific configuration
        upload_template(opts['bacula_conf'], '/etc/bacula/clients/%(shortname)s.conf' % opts, use_sudo=True)

        # reload bacula master configuration
        sudo("/etc/init.d/bacula-dir restart")


def configure_hetzner_backup(duplicityfilelist=None, duplicitysh=None):
    """Hetzner gives us 100GB of backup storage. Let's use it with
    Duplicity to backup the whole disk."""
    opts = dict(
        duplicityfilelist=duplicityfilelist or env.get('duplicityfilelist') or '%s/etc/duplicityfilelist.conf' % os.getcwd(),
        duplicitysh=duplicitysh or env.get('duplicitysh') or '%s/etc/duplicity.sh' % os.getcwd(),
    )

    # install duplicity and dependencies
    sudo('apt-get -yq install duplicity ncftp')

    # what to exclude
    upload_template(opts['duplicityfilelist'], '/etc/duplicityfilelist.conf', use_sudo=True)

    # script for running Duplicity
    upload_template(opts['duplicitysh'], '/usr/sbin/duplicity.sh', use_sudo=True)
    sudo('chmod +x /usr/sbin/duplicity.sh')

    # cronjob
    sudo("echo '0 8 * * * root /usr/sbin/duplicity.sh' > /etc/cron.d/duplicity ")

    if not env.get('confirm'):
        confirm("You need to manually run a full backup first time. Noted?")


def install_rkhunter(email=None):
    """Install and configure RootKit Hunter."""
    opts = dict(
        email=email or env.get('email') or 'maintenance@niteoweb.com',
    )

    # install RKHunter
    sudo('apt-get -yq install rkhunter')

    # send emails on warnings
    uncomment('/etc/rkhunter.conf', '#MAIL-ON-WARNING=me@mydomain   root@mydomain', use_sudo=True)
    sed('/etc/rkhunter.conf', 'me@mydomain   root@mydomain', opts['email'], use_sudo=True)

    # ignore some Ubuntu specific files
    uncomment('/etc/rkhunter.conf', '#ALLOWHIDDENDIR=\/dev\/.udev', use_sudo=True)
    uncomment('/etc/rkhunter.conf', '#ALLOWHIDDENDIR=\/dev\/.static', use_sudo=True)
    uncomment('/etc/rkhunter.conf', '#ALLOWHIDDENDIR=\/dev\/.initramfs', use_sudo=True)


def generate_selfsigned_ssl(hostname=None):
    """Generate self-signed SSL certificates and provide them to Nginx."""
    opts = dict(
        hostname=hostname or env.get('hostname') or 'STAR.niteoweb.com',
    )

    if not exists('mkdir /etc/nginx/certs'):
        sudo('mkdir /etc/nginx/certs')

    sudo('openssl genrsa -des3 -out server.key 2048')
    sudo('openssl req -new -key server.key -out server.csr')
    sudo('cp server.key server.key.password')
    sudo('openssl rsa -in server.key.password -out server.key')
    sudo('openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt')
    sudo('cp server.crt /etc/nginx/certs/%(hostname)s.crt' % opts)
    sudo('cp server.key /etc/nginx/certs/%(hostname)s.key' % opts)


def install_php():
    """Install FastCGI interface for running PHP scripts via Nginx."""

    # add aditional repositories so we can install php5-fpm
    sudo('add-apt-repository ppa:brianmercer/php')
    sudo('apt-get update')

    # install php-fpm, php process manager
    sudo('apt-get -yq install php5-fpm php5-curl php5-mysql php5-gd')

    # the command above also pulls in apache, which we cannot remove -> make id not start at bootup
    sudo('update-rc.d -f apache2 remove')

    # security harden PHP5
    sed('/etc/php5/cgi/php.ini', ';cgi\.fix_pathinfo=1', 'cgi\.fix_pathinfo=0', use_sudo=True)
    sed('/etc/php5/cgi/php.ini', '; allow_call_time_pass_reference', 'allow_call_time_pass_reference = Off', use_sudo=True)
    sed('/etc/php5/cgi/php.ini', '; display_errors', 'display_errors = Off', use_sudo=True)
    sed('/etc/php5/cgi/php.ini', '; html_errors', 'html_errors = Off', use_sudo=True)
    sed('/etc/php5/cgi/php.ini', '; magic_quotes_gpc', 'magic_quotes_gpc = Off', use_sudo=True)
    sed('/etc/php5/cgi/php.ini', '; log_errors', 'log_errors = On', use_sudo=True)

    # restart for changes to apply
    sudo('/etc/init.d/php5-fpm restart')


def install_mysql(default_password=None):
    """Install MySQL database server."""
    opts = dict(
        default_password=default_password or env.get('default_password') or 'secret'
    )

    # first set root password in advance so we don't get the package
    # configuration dialog
    sudo('echo "mysql-server-5.0 mysql-server/root_password password %(default_password)s" | debconf-set-selections' % opts)
    sudo('echo "mysql-server-5.0 mysql-server/root_password_again password %(default_password)s" | debconf-set-selections' % opts)

    # install MySQL along with php drivers for it
    sudo('sudo apt-get -yq install mysql-server mysql-client')

    if not env.get('confirm'):
        confirm("You will now start with interactive MySQL secure installation."
                " Current root password is '%(default_password)s'. Change it "
                "and save the new one to your password managere. Then answer "
                "with default answers to all other questions. Ready?" % opts)
    sudo('/usr/bin/mysql_secure_installation')

    # restart mysql and php-fastcgi
    sudo('service mysql restart')
    sudo('/etc/init.d/php-fastcgi restart')

    # configure daily dumps of all databases
    sudo('mkdir /var/backups/mysql')
    password = prompt('Please enter your mysql root password so I can configure daily backups:')
    sudo("echo '0 7 * * * mysqldump -u root -p%s --all-databases | gzip > /var/backups/mysql/mysqldump_$(date +%%Y-%%m-%%d).sql.gz' > /etc/cron.d/mysqldump" % password)
