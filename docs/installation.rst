Installation
============.

You will need Administrator rights (superuser) to install opendaq.py.

Run the command line in Administrator mode (Windows) or run sudo before the following commands in Linux.

You also need to have Python 2.7 installed to run setup installation::

    $ python setup.py install

If you have pip, at the command line::

    $ pip install opendaq

Or, if you have virtualenvwrapper installed::

    $ mkvirtualenv opendaq
    $ pip install opendaq


Development
===========

If you want to collaborate with this project, you must also install some
development tools. They are listed in the file ``requirements-dev.txt``::

    $ pip install -r requirements-dev.txt

Then you can install the package in `development` mode::

    $ python setup.py develop
