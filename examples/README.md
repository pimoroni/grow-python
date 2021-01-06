# Monitoring Your Plants

The example `monitor.py` monitors the moisture level of your soil and sounds an alarm when it drops below a defined threshold.

It's configured using `settings.yml`. Your settings for monitoring will look something like this:

```yaml
channel1:
        warn_level: 0.2
channel2:
        warn_level: 0.2
channel3:
        warn_level: 0.2
general:
        alarm_enable: True
        alarm_interval: 1.0
```

`monitor.py` includes a main view showing the moisture status of each channel and the level beyond which the alarm will sound.

The controls from the main view are as follows:

* `A` - cycle through the main screen and each channel
* `B` - snooze the alarm
* `X` - configure global settings or the selected channel

The warning moisture level can be configured for each channel, along with the Wet and Dry points that store the frequency expected from the sensor when soil is fully wet/dry.

## Watering

If you've got pumps attached to Grow and want to automatically water your plants, you'll need some extra configuration options.

See [Channel Settings](#channel-settings) and [General Settings](#general-settings) for more information on what these do.

```yaml
channel1:
        water_level: 0.8
        warn_level: 0.2
        pump_speed: 0.7
        pump_time: 0.7
        wet_point: 0.7
        dry_point: 27.6
        auto_water: True
channel2:
        water_level: 0.8
        warn_level: 0.2
        pump_speed: 0.7
        pump_time: 0.7
        wet_point: 0.7
        dry_point: 27.6
        auto_water: True
channel3:
        water_level: 0.8
        warn_level: 0.2
        pump_speed: 0.7
        pump_time: 0.7
        wet_point: 0.7
        dry_point: 27.6
        auto_water: True
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
* `wet_point` - Value for the sensor in saturated soil (in Hz)
* `dry_point` - Value for the sensor in totally dry soil (in Hz)

## General Settings

An additional `general` section can be used for global settings:

* `alarm_enable` - Whether to enable the alarm
* `alarm_interval` - The interval at which the alarm should beep (in seconds)


## MQTT Settings
If you want to send the moisture saturation levels somewhere to build a dashboard, or log to a database, MQTT is a great way to do this. You'll need an MQTT broker set up somwhere, [Mosquitto](https://mosquitto.org/) is great choice and runs really well on a Raspberry Pi.

Add the following settings to your `settings.yml` file:

```yaml
mqtt:
  mqtt_host: localhost
  mqtt_port: 1883
  mqtt_client_id: plantMonitor
  mqtt_username: plantpi
  mqtt_password: pimoroni
  mqtt_topic_root: plants/moisture
  mqtt_qos: 2
  mqtt_interval : 30
```

* `mqtt_host` - This is the hostname or IP address of the server where your MQTT broker is.
* `mqtt_port` - This is the port number for the broker, usually `1883`.
* `mqtt_client_id` - This is the Client ID for your monitor service, can be ignored if you dont mind what the broker sees this device as.
* `mqtt_username` - If you have authentication enabled, this is the username.
* `mqtt_password` - If you have authentication enabled, this is the password.
* `mqtt_topic_root` - This is the MQTT topic where the sensor data will be sent.
* `mqtt_qos` - The QoS Level to publish messages at. Default: `2`.
* `mqtt_interval` - This is the time interval between publishing readings, in seconds.