# -*- coding: utf-8 -*-
"""Installer for this package."""

from setuptools import setup
#from setuptools import find_packages

import os


# shamlessly stolen from Hexagon IT guys
def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

version = '0.1'

setup(name='niteoweb.fabfile',
      version=version,
      description="A bunch of Fabric commands we use all the time.",
      long_description=read('docs', 'README.rst'),
      classifiers=[
        "Framework :: Fabric",
        "Programming Language :: Python",
        ],
      keywords='Fabric Python',
      author='NiteoWeb Ltd.',
      author_email='info@niteoweb.com',
      url='http://www.niteoweb.com',
      license='BSD',
#      packages=find_packages('src', exclude=['ez_setup']),
#      namespace_packages=['niteoweb'],
#      package_dir={'': 'src'},
#      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # list project dependencies
          'Fabric',
          'setuptools',
      ],
      )
