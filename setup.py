#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

DESCRIPTION = 'Python binding for openDAQ hardware'
LONG_DESCRIPTION = """
`OpenDAQ <http://www.open-daq.com/>`_ is an open source acquisition \
instrument which provides several physical interaction capabilities \
such as analog inputs and outputs, digital inputs and outputs, \
timers and counters.
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()


setup(
    name='opendaq',
    version='0.1.0',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author='Juan Menendez',
    author_email='juanmb@ingen10.com',
    url='http://github.com/opendaq/python-opendaq',
    packages=['opendaq'],
    package_dir={'opendaq': 'opendaq'},
    include_package_data=True,
    install_requires=['pyserial'],
    license='LGPL',
    zip_safe=False,
    test_suite='tests',
    platforms=['any'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Scientific/Engineering'
        ' :: Libraries :: Python Modules',
    ],
)
