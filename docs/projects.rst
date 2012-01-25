===============
Projects server
===============

A Projects server is a server that runs your Plone projects. This is a
prerequisite to have before you can run any commands from the `Project` group
of commands.

Sample fabfile
--------------

Below is a ``fabfile.py.in`` buildout template that uses commands from `Server`
group to set up a Projects server (based on Ubuntu 10.04).

.. sourcecode:: python

    import os
    from fabric.api import env
    from niteoweb.fabfile.server import *

    env.path = os.getcwd()
    env.hosts = ['${ips:server}']
    env.hostname = '${config:hostname}'
    env.shortname = '${config:shortname}'
    env.temp_root_pass = '${pass:temp_root}'
    env.server_ip = '${ips:server}'
    env.hq_ip = '${ips:hq}'
    env.bacula_ip = '${ips:bacula}'
    env.office1_ip = '${ips:office1}'
    env.office2_ip = '${ips:office2}'

    env.email = 'maintenance@company.com'
    env.admins = ['bob', 'jane', ]

    env.rules = [
        # allow SSH access from our offices
        'ufw allow from %(office1_ip)s to any port ssh' % env,
        'ufw allow from %(office2_ip)s to any port ssh' % env,

        # allow access to Bacula File Deamon from our backup server
        'ufw allow from %(bacula_ip)s to any port bacula-fd' % env,

        # allow access to Munin from HQ server
        'ufw allow from %(hq_ip)s to any port munin' % env,

        # allow HTTP from everywhere
        ufw allow http
        ufw allow https
    ]

    def deploy():
        """The highest-level meta-command for deploying Projects
        server. Use this command only on a vanilla Ubuntu 10.04 server."""

        with settings(user='root', password=env.temp_root_pass):
            create_admin_accounts(default_password='secret123')

        create_projects_group()

        # security
        harden_sshd()
        install_ufw()
        disable_root_login()

        # bootstrap server
        set_hostname()
        set_system_time()
        install_unattended_upgrades()
        raid_monitoring()
        install_rkhunter()

        # install software stack
        install_system_libs()
        install_nginx()
        install_sendmail()

        # install python
        install_python_26()
        install_python_24()
        configure_egg_cache()

        # monitoring, backup, etc.
        install_munin_node()
        install_bacula_client()
        configure_hetzner_backup()


Sample buildout.cfg
-------------------

This ``fabfile.py`` template has a dependency on the `niteoweb.fabfile` package
and also expects to find certain buildout values and config files in certain
directories. Here's a sample ``buildout.cfg`` that you can use to prepare an
environment for using this ``fabfile.py.in``. Save the ``fabfile.py.in`` in
``etc/`` directory in your buildout.

::

    [buildout]
    unzip = true
    newest = false
    extensions = buildout.dumppickedversions
    prefer-final = true

    parts =
        fabric
        fabfile
        bacula-fd-conf
        bacula-master-conf
        duplicity-sh

    # Configuration constants
    [config]
    # domain on which this server runs
    hostname = zulu.company.com

    # server's name
    shortname = zulu

    # Ports of services running on this server
    # (besides Nginx running on port 80 and 443)
    [ports]
    ssh = 22
    munin = 4949
    bacula = 9102

    # Various IPs needed for deployment
    [ips]
    server = ?.?.?.?
    hq = ?.?.?.?
    bacula = ?.?.?.?
    office1 = ?.?.?.?
    office2 = ?.?.?.?

    # Passwords
    [pass]
    bacula = strong_password_here
    duplicity = strong_password_here
    hetzner_ftp_user = whatever_hetzner_gives_you
    hetzner_ftp_pass = whatever_hetzner_gives_you
    temp_root = root_password_that_hetzner_gives_you_for_a_new_server
    # temp_root password is changed and disabled later on in deployment

    # Prepare Fabric
    [fabfile]
    recipe = collective.recipe.template
    input = ${buildout:directory}/etc/fabfile.py.in
    output = ${buildout:directory}/fabfile.py

    [fabric]
    recipe = zc.recipe.egg
    eggs =
        Fabric
        niteoweb.fabfile

    # Generate config files from templates in ./etc
    [bacula-fd-conf]
    recipe = collective.recipe.template
    input = ${buildout:directory}/etc/bacula-fd.conf.in
    output = ${buildout:directory}/etc/bacula-fd.conf

    [bacula-master-conf]
    recipe = collective.recipe.template
    input = ${buildout:directory}/etc/bacula-master.conf.in
    output = ${buildout:directory}/etc/bacula-master.conf

    [duplicity-sh]
    recipe = collective.recipe.template
    input = ${buildout:directory}/etc/duplicity.sh.in
    output = ${buildout:directory}/etc/duplicity.sh

Config files
------------

Samples of config files that you need to put inside ``etc/`` directory in your
buildout:

 * :download:`bacula-fd.conf.in <etc/bacula-fd.conf.in>`.
 * :download:`bacula-master.conf.in <etc/bacula-master.conf.in>`.
 * :download:`duplicity.sh.in <etc/duplicity.sh.in>`.
 * :download:`duplicityfilelist.conf <etc/duplicityfilelist.conf>`.
 * :download:`nginx.conf <etc/nginx.conf>`.