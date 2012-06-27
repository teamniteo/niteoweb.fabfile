============
IPsec server
============

This is how to setup an IPsec server in your office so you can remotely
access your internal LAN when you are on the road and also have all
traffic encrypted when sitting in a cafe and using a public network.

Prerequisities
--------------

You router needs to forward ports 500 and 4500 to your IPsec server.


Sample fabfile
--------------

Below is a ``fabfile.py.in`` buildout template that uses commands from `Server`
group to set up an IPsec server (based on Ubuntu 10.04).

.. sourcecode:: python

    import os
    from fabric.api import env
    from fabric.api import settings
    from fabric.api import sudo

    from niteoweb.fabfile.server import *

    env.path = os.getcwd()
    env.hosts = ['${ips:server}']
    env.server_ip = '${ips:server}'
    env.shortname = '${config:shortname}'
    env.hostname = '${config:hostname}'
    env.temp_root_pass = '${pass:temp_root}'

    env.email = 'maintenance@company.com'
    env.admins = ['bob', 'jane', ]

    def deploy():
        """The highest-level meta-command for deploying Plone to the server.
        Use this command only on a fresh and clean server."""

        with settings(user='root', password=env.temp_root_pass):
            create_admin_accounts(default_password='secret123')

        # security
        harden_sshd()
        disable_root_login()

        # bootstrap server
        set_hostname()
        set_system_time()
        install_unattended_upgrades()
        install_sendmail()
        install_rkhunter()

        # install software stack
        install_ipsec()


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
        fabfile
        fabric
        racoon.conf
        psk.txt

    [config]
    # Project shortname
    shortname = ipsec

    # Main domain on which this project runs on
    hostname = ipsec.company.com

    # Various IPs needed for deployment
    [ips]
    server = ?.?.?.?

    [pass]
    # Temporary root password assigned to us by hosting provider
    temp_root = some_password_here
    ipsec = strong_password_here

    # Prepare Fabric
    [fabric]
    recipe = zc.recipe.egg
    eggs =
        Fabric
        niteoweb.fabfile

    [fabfile]
    recipe = collective.recipe.template
    input = ${buildout:directory}/etc/fabfile.py.in
    output = ${buildout:directory}/fabfile.py

    # Generate config files from templates in ./etc
    [racoon.conf]
    recipe = collective.recipe.template
    input = ${buildout:directory}/etc/racoon.conf.in
    output = ${buildout:directory}/etc/racoon.conf

    [psk.txt]
    recipe = collective.recipe.template
    input = ${buildout:directory}/etc/psk.txt.in
    output = ${buildout:directory}/etc/psk.txt

Config files
------------

Samples of config files that you need to put inside ``etc/`` directory in your
buildout:

 * :download:`racoon.conf.in <etc/racoon.conf.in>`.
 * :download:`psk.txt.in <etc/psk.txt.in>`.


Client configuration
--------------------

Configuring a client to use this IPsec server is fairly easy. For iOS,
go to Settings -> Network -> VPN and add a new IPsec VPN with the following
settings:

 * Description: whatever
 * Server: Public IP of your router behind which the IPsec server sits
 * Account: a Linux user on the machine that is in the ``sudo`` group
 * Group name: ``sudo`` (it's specified in ``racoon.conf``)
 * Secret: secret set for group ``sudo`` in ``psk.txt``
