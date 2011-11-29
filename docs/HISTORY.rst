Changelog
=========

2.1 (unreleased)
----------------

- Fixed upload_zodb, upload_blobs and upload_data methods - data was uploaded
  even if you selected 'no' when asked if you want to proceed.
  [jcerjak]

- Created an utils module that contains methods for running the fabric commands 
  with resume support.
  [jcerjak]

- Lots of minor bugfixes.
  [zupo, jcerjak]

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

