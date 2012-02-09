Changelog
=========

2.2.2 (2012-02-09)
------------------

- Use ``--force`` when purging old Duplicity backups so it also purges
  old incomplete backups.
  [zupo]

- Instructions on how to setup iOS or OS X to connect to IPsec server.
  [zupo]


2.2.1 (2012-01-25)
------------------

- Fixed GitHub's URLs to point to github.com/niteoweb.
  [zupo]


2.2 (2012-01-25)
----------------

- Fabric step for installing `IPsec`.
  [zupo]

- Use sudo when configuring rkhunter.
  [zupo]

- Moved config files in ``docs`` to ``docs/etc/`` folder so they don't mix with
  Sphinx files.
  [zupo]


2.1.3 (2011-12-23)
------------------

- Run `bootstrap` and `buildout` with ``prod_user``, not with `root`.
  [zupo]


2.1.2 (2011-12-23)
------------------

- Use ``prod_user`` from ``opts`` and not from ``env``.
  [zupo]


2.1.1 (2011-12-23)
------------------

- Minor runtime fix for ``supervisorctl`` command.
  [zupo]

- Moved ``cmd`` coomand to ``__init__.py`` so it's available both in
  ``server.py`` and ``project.py``.
  [zupo]

- Update RKHunter's files properties DB every time you run apt-get install,
  this prevents warnings every time a new version of some package is installed.
  [zupo]


2.1 (2011-11-15)
----------------

- Lots of minor bugfixes.
  [zupo]

- You can now specify python version that is used for bootstraping buildout.
  [zupo]

- Added `gitk` to list of libraries to install.
  [zupo]

- Added buildout.cfg to test how sphinx docs are generated.
  [zupo]

- Enabled choosing filename for 'production' buildout configuration.
  [zupo]

- The configure_egg_cache() command is now  more resilient to multiple runs.
  [zupo]

- Added instructions and examples on how to use niteoweb.fabfile for setting up
  a new server for running Plone projects.
  [zupo]

- Added commands for installing and configuring a server that will run Plone
  projects.
  [zupo]

- Added Sphinx documentation.
  [zupo]

2.0.2 (2011-11-13)
------------------

- You can now specify python version that is used for bootstraping buildout.
  [zupo]


2.0.1 (2011-11-13)
------------------

- HISTORY.txt missing from release.
  [zupo]


2.0 (2011-11-13)
----------------

- Use niteoweb.fabfile.err instead of _verify_opts.
  [zupo]

- Breaks backwards compatibility with commands in project.py
  [zupo]


0.1.2 (2011-10-21)
------------------

- Added many new commands for setting up servers.
  [zupo]


0.1.1 (2011-08-28)
------------------

- Packaging fixes.
  [zupo]


0.1 (2011-08-28)
----------------

- Initial release.
  [zupo]

