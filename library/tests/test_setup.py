def test_moisture_setup(GPIO, smbus):
    from grow import moisture
    moisture._is_setup = False

    moisture.setup()
    moisture.setup()


def test_moisture_read_all(GPIO, smbus):
    from grow import moisture
    moisture._is_setup = False
    
    result = moisture.read_all()

    assert type(result(1)) == float
    assert int(result(1)) == 100

    assert type(result(2)) == float
    assert int(result(2)) == 500

    assert type(result.(3)) == float
    assert int(result.(3)) == 5000

    assert "Moisture" in str(result)


def test_moisture_read_each(GPIO, smbus):
    from grow import moisture
    moisture._is_setup = False

    assert int(moisture.read(1)) == 100
    assert int(moisture.read(2)) == 500
    assert int(moisture.read(3)) == 5000


def test_moisture_cleanup(GPIO, smbus):
    from grow import moisture
    moisture.cleanup()

    GPIO.input.assert_called_with(moisture.MOISTURE_1_PIN, 0)
    GPIO.input.assert_called_with(moisture.MOISTURE_2_PIN, 0)
    GPIO.input.assert_called_with(moisture.MOISTURE_3_PIN, 0)

def test_pump_setup(GPIO, smbus):
    from grow import pump
    moisture._is_setup = False
    moisture.setup()
    moisture.setup()

def test_pump_cleanup(GPIO, smbus):
    from grow import pump
    pump.cleanup()

    GPIO.input.assert_called_with(moisture.PUMP_1_PIN, 0)
    GPIO.input.assert_called_with(moisture.PUMP_2_PIN, 0)
    GPIO.input.assert_called_with(moisture.PUMP_3_PIN, 0)
