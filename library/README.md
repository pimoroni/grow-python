# Grow HAT Mini

Designed as a tiny valet for your plants, Grow HAT mini will monitor the soil moiture for up to 3 plants, water them with tiny pumps, and show you their health on its small but informative screen. Learn more - https://shop.pimoroni.com/products/grow

[![Build Status](https://travis-ci.com/pimoroni/enviroplus-python.svg?branch=master)](https://travis-ci.com/pimoroni/grow-python)
[![Coverage Status](https://coveralls.io/repos/github/pimoroni/grow-python/badge.svg?branch=master)](https://coveralls.io/github/pimoroni/grow-python?branch=master)
[![PyPi Package](https://img.shields.io/pypi/v/enviroplus.svg)](https://pypi.python.org/pypi/growhat)
[![Python Versions](https://img.shields.io/pypi/pyversions/enviroplus.svg)](https://pypi.python.org/pypi/growhat)

# Installing

You're best using the "One-line" install method.

## One-line (Installs from GitHub)

```
curl -sSL https://get.pimoroni.com/grow | bash
```

**Note** report issues with one-line installer here: https://github.com/pimoroni/get

## Or... Install and configure dependencies from GitHub:

* `git clone https://github.com/pimoroni/grow-python`
* `cd grow-python`
* `sudo ./install.sh`

**Note** Raspbian Lite users may first need to install git: `sudo apt install git`

## Or... Install from PyPi and configure manually:

* Install dependencies:

```
sudo apt install python3-setuptools python3-pip python3-yaml python3-smbus python3-pil python3-spidev python3-rpi.gpio
```

* Run `sudo pip3 install growhat`

**Note** this wont perform any of the required configuration changes on your Pi, you may additionally need to:

* Enable i2c: `sudo raspi-config nonint do_i2c 0`
* Enable SPI: `sudo raspi-config nonint do_spi 0`
* Add the following to `/boot/config.txt`: `dtoverlay=spi0-cs,cs0_pin=14`

## Monitoring

You should read the following to get up and running with our monitoring script:

* [Using and configuring monitor.py](examples/README.md)
* [Setting up monitor.py as a service](service/README.md)

## Help & Support

* GPIO Pinout - https://pinout.xyz/pinout/grow_hat_mini
* Support forums - http://forums.pimoroni.com/c/support
* Discord - https://discord.gg/hr93ByC

# Changelog

0.0.1
-----

* Initial Release
