import mock


def test_moisture_setup(gpiod, smbus2):
    from grow.moisture import Moisture

    ch1 = Moisture(channel=1)
    ch2 = Moisture(channel=2)
    ch3 = Moisture(channel=3)

    GPIO.setup.assert_has_calls([
        mock.call(ch1._gpio_pin, GPIO.IN),
        mock.call(ch2._gpio_pin, GPIO.IN),
        mock.call(ch3._gpio_pin, GPIO.IN)
    ])


def test_moisture_read(gpiod, smbus2):
    from grow.moisture import Moisture

    assert Moisture(channel=1).saturation == 1.0
    assert Moisture(channel=2).saturation == 1.0
    assert Moisture(channel=3).saturation == 1.0

    assert Moisture(channel=1).moisture == 0
    assert Moisture(channel=2).moisture == 0
    assert Moisture(channel=3).moisture == 0


def test_pump_setup(gpiod, smbus2):
    from grow.pump import PUMP_PWM_FREQ, Pump

    ch1 = Pump(channel=1)
    ch2 = Pump(channel=2)
    ch3 = Pump(channel=3)

    GPIO.setup.assert_has_calls([
        mock.call(ch1._gpio_pin, GPIO.OUT, initial=GPIO.LOW),
        mock.call(ch2._gpio_pin, GPIO.OUT, initial=GPIO.LOW),
        mock.call(ch3._gpio_pin, GPIO.OUT, initial=GPIO.LOW)
    ])

    GPIO.PWM.assert_has_calls([
        mock.call(ch1._gpio_pin, PUMP_PWM_FREQ),
        mock.call().start(0),
        mock.call(ch2._gpio_pin, PUMP_PWM_FREQ),
        mock.call().start(0),
        mock.call(ch3._gpio_pin, PUMP_PWM_FREQ),
        mock.call().start(0)
    ])
