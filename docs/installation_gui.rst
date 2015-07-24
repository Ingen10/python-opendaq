Installation of openDAQ-gui
====================================

opendaq-gui depends on the following packages: 

- opendaq (can be found in our root repository)

- setuptools

- wxPython

- numpy

- matplotlib 

- dateutil

- pyparsing

In order to install opendaq-gui just run:

`$ python setup.py install`

The installer *setup.py* will try to install the package opendaq-gui and, if required, the packages *opendaq*, *wxPython*, *numpy* and *matplotlib*. If, after doing this, the demos are not working, then you should install on your own the packages listed above.

In Windows, you will need to include the route "C:\Python27\Scripts" into the system "Path" variable, if it does not already exist (System->Advanced Settings).
