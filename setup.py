#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from setuptools import setup

DESCRIPTION = 'Python binding for openDAQ hardware'
LONG_DESCRIPTION = """
`OpenDAQ <http://www.open-daq.com/>`_ is an open source acquisition \
instrument which provides several physical interaction capabilities \
such as analog inputs and outputs, digital inputs and outputs, \
timers and counters.
"""


requires = ['pyserial', 'numpy', 'terminaltables']
if sys.version_info[0] == 2:
    requires.append('enum34')


setup(
    name='opendaq',
    version='0.3.0',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author='Ingen10 Ingenieria SL',
    author_email='ingen10@ingen10.com',
    url='http://github.com/opendaq/python-opendaq',
    packages=['opendaq'],
    package_dir={'opendaq': 'opendaq'},
    include_package_data=True,
    install_requires=requires,
    license='LGPL',
    zip_safe=False,
    test_suite='tests',
    platforms=['any'],
    entry_points={
        'console_scripts': ['opendaq-utils = opendaq.utils:main']
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
