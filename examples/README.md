# Watering Settings

The `grow-monitor-and-water.py` example can monitor and, optionally, automatically water all three Grow channels.

It's configured using a settings file - `water.yml` - that looks like the following:

```yaml
channel1:
        water_level: 0.8
        warn_level: 0.2
        pump_speed: 0.7
        pump_time: 0.7
        auto_water: False
        icon: icons/flat-4.png
channel2:
        water_level: 0.8
        warn_level: 0.2
        pump_speed: 0.7
        pump_time: 0.7
        auto_water: False
channel3:
        water_level: 0.8
        warn_level: 0.2
        pump_speed: 0.7
        pump_time: 0.7
        auto_water: False
general:
        alarm_enable: True
        alarm_interval: 1.0
```

By default auto-watering is disabled and an alarm will sound every 1s if the `warn_level` is reached.

## Channel Settings

* `water_level` - The level at which auto-watering should be triggered (soil saturation from 0.0 to 1.0)
* `warn_level` - The level at which the alarm should be triggered (soil saturation from 0.0 to 1.0)
* `pump_speed` - The speed at which the pump should be run (from 0.0 low speed to 1.0 full speed)
* `pump_time` - The time that the pump should run for (in seconds)
* `auto_water` - Whether to run the attached pump (True to auto-water, False for manual watering)
* `icon` - Optional icon image for the channel, see the icons directory for images.

## General Settings

* `alarm_enable` - Whether to enable the alarm
* `alarm_interval` - The interval at which the alarm should beep (in seconds)
