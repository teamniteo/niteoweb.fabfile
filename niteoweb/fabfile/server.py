from fabric.api import env
from fabric.api import sudo
from fabric.contrib.files import append
from fabric.contrib.files import sed
from fabric.contrib.files import uncomment
from fabric.operations import prompt


def install_rkhunter():
    """Install and configure RootKit Hunter."""

    # install RKHunter
    sudo('apt-get -yq install rkhunter')

    # send emails on warnings
    uncomment('/etc/rkhunter.conf', '#MAIL-ON-WARNING=me@mydomain   root@mydomain', use_sudo=True)
    sed('/etc/rkhunter.conf', 'me@mydomain   root@mydomain', 'maintenance@niteoweb.com', use_sudo=True)

    # ignore some Ubuntu specific files
    uncomment('/etc/rkhunter.conf', '#ALLOWHIDDENDIR=\/dev\/.udev', use_sudo=True)
    uncomment('/etc/rkhunter.conf', '#ALLOWHIDDENDIR=\/dev\/.static', use_sudo=True)
    uncomment('/etc/rkhunter.conf', '#ALLOWHIDDENDIR=\/dev\/.initramfs', use_sudo=True)


def create_maintenance_user(admin):
    """Create an account for an admin to use to access the server."""
    env.admin = admin

    # create user
    sudo('egrep %(admin)s /etc/passwd || adduser %(admin)s --disabled-password --gecos ""' % env)

    # add public key for SSH access
    sudo('mkdir /home/%(admin)s/.ssh' % env)
    env.pub = prompt("Paste admin's public key: ")
    sudo("echo '%(pub)s' > /home/%(admin)s/.ssh/authorized_keys" % env)

    # allow this user in sshd_config
    append('AllowUsers %(admin)s@*', use_sudo=True)

    # allow sudo for maintenance user by adding it to 'sudo' group
    sudo('gpasswd -a %(admin)s sudo' % env)

    # set default password for initial login
    sudo('echo "%(admin)s:geslo123" | chpasswd' % env)
