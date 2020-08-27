# Grow <!-- omit in toc -->

- [Getting Started](#getting-started)
  - [Requirements](#requirements)
    - [Python 3 & pip](#python-3--pip)
    - [Enabling i2c and spi](#enabling-i2c-and-spi)
  - [Installing the library](#installing-the-library)
- [Reference](#reference)
  - [Moisture](#moisture)
    - [Calibrating the moisture sensor](#calibrating-the-moisture-sensor)
    - [Moisture Reference](#moisture-reference)
      - [moisture](#moisture-1)
      - [saturation](#saturation)
      - [range](#range)
      - [new_data](#new_data)
      - [active](#active)
  - [Pump](#pump)
    - [Calibrating The Pump](#calibrating-the-pump)
    - [Pump Reference](#pump-reference)
      - [dose](#dose)
      - [set_speed](#set_speed)
      - [get_speed](#get_speed)
      - [stop](#stop)
  - [Light Sensor](#light-sensor)
  - [Display](#display)

## Getting Started

You'll need to install the LTP305 software library and enable i2c on your Raspberry Pi.

### Requirements

#### Python 3 & pip

You should use Python 3, which may need installing on your Pi:

```
sudo apt update
sudo apt install python3 python3-pip python3-setuptools
```

#### Enabling i2c and spi

You can use `sudo raspi-config` on the command line, the GUI Raspberry Pi Configuration app from the Pi desktop menu, or use the following commands to enable i2c and spi:

```
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0
```

### Installing Dependencies

The following dependencies are required:

```
sudo apt install python3-yaml python3-smbus python3-pil python3-spidev python3-rpi.gpio
```

### Installing the library

```python
python3 -m pip install growhat
```

This will also install the display driver - ST7735 - and a driver for the light sensor - LTR559.

## Reference

The Grow library includes several modules for monitoring, watering and conveying status information.

### Moisture

The moisture module is responsible for reading the moisture sensor.

Grow moisture sensors output pulses that correspond to the moisture content of the soil.

Wet soil will produce low frequency pulses, which will gradually become more frequent as the soil dries.

The range runs from about 27-28 pulses per second in air, to <=1 pulse per second in fully saturated soil.

To set up a moisture sensor you must import and initialise the class with the channel number you want to monitor:

```python
from grow.moisture import Moisture

moisture1 = Moisture(1)  # Monitor channel 1
```

Moisture channels are labelled on the PCB from left to right as S1, S2 and S3.

#### Calibrating the moisture sensor

Since every soil substrate and environment is different, you must tell Grow what Wet and Dry soil look like. You can do this using the methods `set_wet_point` and `set_dry_point`.

The wet and dry points are expressed as raw counts. You can read the raw moisture level of the soil at any time by using:

```python
moisture1.moisture()
```

These methods will either use the current read value or, optionally, a value that you supply so that you can save your calibration and load it again if you need to restart your script. A simple calibration process might look like the following:

```python
# Leave the soil dry
moisture1.set_dry_point()
# Water the plant
moisture1.set_wet_point()
```

Or you could have variables that you wish to set as your wet/dry points:

```python
DRY_POINT = 27
WET_POINT = 1
moisture1.set_dry_point(DRY_POINT)
moisture1.set_wet_point(WET_POINT)
```

#### Moisture Reference

##### moisture

```python
value = moisture1.moisture()
```

Reads the raw moisture level of the sensor.

This is expressed in pulses-per-second and is inversely proportional to the moisture content of the soil.

The moisture sensors are deliberately scaled to a very low frequency and range from around 27-28Hz in dry air down to around 1Hz in saturated soil.

##### saturation

```python
value = moisture1.saturation()
```

Returns a value from 0.0 to 1.0 that corresponds to how moist the soil is.

The saturation level is calculated using the wet and dry points and is useful for populating visual indicators, logs or graphs.

##### range

```python
moisture1.range()
```

Returns the distance, in counts per second, between the wet and dry points. Used predominately in the calculation of saturation level, but may be useful.

##### new_data

```python
moisture1.new_data()
```

Returns `True` if the internal moisture reading has been updated since the last time `moisture()` or `saturation()` was called.

This allows you to log or run averaging over each new reading as it is collected or process readings in your program loop.

For example, this snippet will loop ~60 times a second but only append new moisture readings to `log` once every second:

```python
import time
from grow.moisture import Moisture

moisture1 = Moisture(1)  # Monitor channel 1
log = []

while True:
    if moisture1.new_data():
        log.append(moisture1.saturation())

    time.sleep(1.0 / 60)  # 60 updates/sec
```

##### active

```python
moisture1.active()
```

Returns `True` if the moisture sensor is connected and returning valid readings.

Checks if a pulse has happened within the last second, and that the reading is within a sensible range.

### Pump

The Pump module is responsible for driving a pump. It uses PWM to run the pump at variable speeds.

To set up a pump you must import and initialise the class with the channel number you want to control:

```python
from grow.pump import Pump

pump1 = Pump(1)  # Control channel 1
```

Pump channels are labelled on the PCB from left to right as P1, P2 and P3.

#### Calibrating The Pump

In order for your pump/hose setup to reliably deliver a sensible amount of water you will have to calibrate both the speed at which it runs, and the time that it runs for. The speed/time settings are collectively known as a "dose" and we've produced an example - `dose.py` - to help find the right values.

Higher pump speeds are useful for defeating gravity; in case where you water tank might be much lower than your plants. Longer pump times will deliver more water.

Refer to the instructions at the top of `dose.py` for its usage. Generally you should dial in the lowest pump speed that will get water to traverse your hose, and adjust the time to deliver the right amount of water.

These values are then passed into `pump.dose()` when watering.

#### Pump Reference

##### dose

```python
pump1.dose(0.5, 0.5, blocking=False)
```

Delivers a dose of water by running the pump at a specified speed for a specified time. Can be run in blocking (method takes time to return) or non-blocking (returns instantly and pump runs in the background) modes.

This is the recommended way to water plants, since it delivers a controlled, short dose and is less likely to result in unwanted floods.

##### set_speed

```python
pump1.set_speed(0.5)
```

Turns the pump on at the given speed. To stop the pump call `stop()` or `set_speed(0)`.

Unless your setup (vertical hydroponics for example) requires continuous pumping of water then you should not use this function and use the `dose` instead.

##### get_speed

```python
speed = pump1.get_speed()
```

Returns the current pump speed.

##### stop

```python
pump1.stop()
```

Stops the pump by setting the speed to 0.

### Light Sensor

Grow is equipped with an LTR-559 light and proximity sensor that you can use to limit waterings to daytime, or monitor the level of light your plant is receiving.

The LTR-559 has its own library, and should be initialised like so:

```python
from ltr559 import LTR559
light = LTR559()
```

You can then update the sensor and retrieve the `lux` and `proximity` values like so:

```python
while True:
    ltr559.update_sensor()
    lux = ltr559.get_lux()
    prox = ltr559.get_proximity()
```

See the LTR559 library for a full reference: https://github.com/pimoroni/ltr559-python

### Display

The ST7735 display on Grow is 160x80 pixels and a great way to convey current watering status or build an interface for controlling your watering station.

The display must be set up like so:

```python
display = ST7735.ST7735(
    port=0,
    cs=1,               # Chip select 1 (BCM )
    dc=9,               # BCM 9 is the data/command pin
    backlight=12,       # BCM 12 is the backlight
    rotation=270,
    spi_speed_hz=80000000
)
display.begin()
```

You should use the Python Image Library to build up what you want to display, and then display the finished image with:

```python
display.display(image)
```

See the examples for demonstrations of this. See the ST7735 library for a full reference: https://github.com/pimoroni/st7735-python/