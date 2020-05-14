Grow
=======

Designed for looking after plants, Grow monitors moisture levels and runs simple pumps to water plants. Learn more -
https://shop.pimoroni.com/products/grow

|Build Status| |Coverage Status| |PyPi Package| |Python Versions|

Installing
==========

The one-line installer enables the correct interfaces, 

One-line (Installs from GitHub)
-------------------------------

::

    curl -sSL https://get.pimoroni.com/grow | bash

**Note** report issues with one-line installer here:
https://github.com/pimoroni/get

Or... Install and configure dependencies from GitHub:
-----------------------------------------------------

-  ``git clone https://github.com/pimoroni/grow-python``
-  ``cd grow-python``
-  ``sudo ./install.sh``

**Note** Raspbian Lite users may first need to install git:
``sudo apt install git``

Or... Install from PyPi and configure manually:
-----------------------------------------------

-  Run ``sudo pip install grow``

**Note** this wont perform any of the required configuration changes on
your Pi, you may additionally need to:

-  Enable i2c: ``raspi-config nonint do_i2c 0``
-  Enable SPI: ``raspi-config nonint do_spi 0``

And install additional dependencies:

::

    sudo apt install python-numpy python-smbus python-pil python-setuptools

Help & Support
--------------

-  GPIO Pinout - https://pinout.xyz/pinout/grow
-  Support forums - http://forums.pimoroni.com/c/support
-  Discord - https://discord.gg/hr93ByC

.. |Build Status| image:: https://travis-ci.com/pimoroni/grow-python.svg?branch=master
   :target: https://travis-ci.com/pimoroni/grow-python
.. |Coverage Status| image:: https://coveralls.io/repos/github/pimoroni/grow-python/badge.svg?branch=master
   :target: https://coveralls.io/github/pimoroni/grow-python?branch=master
.. |PyPi Package| image:: https://img.shields.io/pypi/v/growhat.svg
   :target: https://pypi.python.org/pypi/growhat
.. |Python Versions| image:: https://img.shields.io/pypi/pyversions/growhat.svg
   :target: https://pypi.python.org/pypi/growhat

0.0.1
-----

* Initial Release
