from fabric.api import sudo
from fabric.contrib.files import sed
from fabric.contrib.files import uncomment


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
