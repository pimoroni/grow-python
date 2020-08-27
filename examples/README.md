# Monitoring and/or Watering Your Plants

The `grow-monitor-and-water.py` example can monitor and, optionally, automatically water all three Grow channels.

By default auto-watering is disabled and an alarm will sound every 1s if the `warn_level` is reached.

Run it with `python3 grow-monitor-and-water.py`.

## Monitoring

Grow can monitor the moisture level of your soil, sounding an alarm when it dries out.

Grow is configured using `settings.yml`. Your settings for monitoring only will look something like this:

```yaml
channel1:
        warn_level: 0.2
        icon: icons/flat-4.png
channel2:
        warn_level: 0.2
channel3:
        warn_level: 0.2
general:
        alarm_enable: True
        alarm_interval: 1.0
```

## Watering

If you've got pumps attached to Grow and want to automatically water your plants, you'll need some extra configuration options.

See [Channel Settings](#channel-settings) and [General Settings](#general-settings) for more information on what these do.

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

## Channel Settings

Grow has three channels which are separated into the sections `channel1`, `channel2` and `channel3`, each of these sections has the following configuration options:

* `water_level` - The level at which auto-watering should be triggered (soil saturation from 0.0 to 1.0)
* `warn_level` - The level at which the alarm should be triggered (soil saturation from 0.0 to 1.0)
* `pump_speed` - The speed at which the pump should be run (from 0.0 low speed to 1.0 full speed)
* `pump_time` - The time that the pump should run for (in seconds)
* `auto_water` - Whether to run the attached pump (True to auto-water, False for manual watering)
* `icon` - Optional icon image for the channel, see the icons directory for images.

## General Settings

An additional `general` section can be used for global settings:

* `alarm_enable` - Whether to enable the alarm
* `alarm_interval` - The interval at which the alarm should beep (in seconds)
