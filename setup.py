#!/usr/bin/env python

from setuptools import setup, Command

DESCRIPTION = 'Python binding for openDAQ hardware'
LONG_DESCRIPTION = """
`OpenDAQ <http://www.open-daq.com/>`_ is an open source acquisition instrument \
which provides several physical interaction capabilities such as analog \
inputs and outputs, digital inputs and outputs, timers and counters.
"""

class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        import sys,subprocess
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)


setup(
    name='opendaq',
    version='0.1',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author='Juan Menendez',
    author_email='juanmb@ingen10.com',
    url='http://github.com/opendaq/python-opendaq',
    license='LGPL',
    platforms=['any'],
    install_requires=['pyserial'],
    cmdclass = {'test': PyTest},
    packages=['opendaq'],
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
