def test_moisture_setup(gpiod, gpiodevice, smbus2):
    from grow.moisture import Moisture

    _ = Moisture(channel=1)
    _ = Moisture(channel=2)
    _ = Moisture(channel=3)


def test_moisture_read(gpiod, gpiodevice, smbus2):
    from grow.moisture import Moisture

    assert Moisture(channel=1).saturation == 1.0
    assert Moisture(channel=2).saturation == 1.0
    assert Moisture(channel=3).saturation == 1.0

    assert Moisture(channel=1).moisture == 0
    assert Moisture(channel=2).moisture == 0
    assert Moisture(channel=3).moisture == 0


def test_pump_setup(gpiod, gpiodevice, smbus2):
    from grow.pump import Pump
    from grow.pwm import PWM

    _ = Pump(channel=1)
    _ = Pump(channel=2)
    _ = Pump(channel=3)

    # Threads. Not even once.
    PWM.stop_thread()

