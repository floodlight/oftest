#!/usr/bin/env python
'''Setuptools params'''

from setuptools import setup, find_packages

modname = distname = 'oftest'

setup(
    name='oftest',
    version='0.0.1',
    description='An OpenFlow Testing Framework',
    author='Dan Talayco/Tatsuya Yabe',
    author_email='dtalayco@stanford.edu',
    packages=find_packages(),
    long_description="""\
OpenFlow test framework package.
      """,
      classifiers=[
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Programming Language :: Python",
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "Topic :: Internet",
      ],
      keywords='networking protocol Internet OpenFlow validation',
      license='unspecified',
      install_requires=[
        'setuptools',
        'doxypy',
        'pylint'
      ])
