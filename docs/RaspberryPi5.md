# Raspberry Pi 5 & Zero 1 W

Raspberry Pi 5 & Zero 1 W with GrowHAT mini

*Uses Astral `uv` for python package management*
**This will BUILD a newer version of numpy**

## Apt Package Configuration
```
apt-get install python3-pip swig liblgpio-dev libjpeg-dev cmake dh-autoreconf ninja-build re2c patchelf libfreetype6-dev
apt-get remove gpiod python3-rpi.gpio python3-rpi-lgpio python3-numpy python3-gpiozero python3-pigpio
```

### Editing `/boot/firmware/config.txt

```
# Enable I2C
dtparam=i2c=on
# Enable SPI
dtparam=spi=on
# Set SPI0 CS0 to pin(GPIO) 26 (unused)
# Set SPI0 CS1 to pin(GPIO) 7 for chip select used by HAT
dtoverlay=spi0-2cs,cs0_pin=26,cs1_pin=7
```

### Setup environment
```
# Install Astral UV
# https://docs.astral.sh/uv/getting-started/installation/

curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync environment to uv.lock file
uv sync --frozen --verbose

# Walk away, this will take a while depending on your hardware.
```

### Run examples
```
uv run --directory examples/advanced moisture.py
uv run --directory examples/advanced lcd-demo.py
uv run --directory examples monitor.py
```
