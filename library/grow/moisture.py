import time
import atexit
import RPi.GPIO as GPIO

MOISTURE_1_PIN = 23
MOISTURE_2_PIN = 25
MOISTURE_3_PIN = 8

_is_setup = False


class Moisture(object):
    __slots__ = 'in1', 'in2', 'in3'

    def __init__(self, in1, in2, in3):
        self.in1 = in1
        self.in2 = in2
        self.in3 = in3

    def __repr__(self):
        fmt = """Moisture 1: {in1} Hz
Moisture 1: {in2} Ohms
Moisture 1: {in3} Ohms"""
        
        return fmt.format(
            in1=self.in1,
            in2=self.in2,
            in3=self.in3)

    __str__ = __repr__


def setup():
    global _is_setup
    global _moisture
    
    if _is_setup:
        return
    _is_setup = True

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(MOISTURE_1_PIN, GPIO.IN)
    GPIO.input(MOISTURE_1_PIN)
    GPIO.setup(MOISTURE_2_PIN, GPIO.IN)
    GPIO.input(MOISTURE_2_PIN)
    GPIO.setup(MOISTURE_3_PIN, GPIO.IN)
    GPIO.input(MOISTURE_3_PIN)
    
    atexit.register(cleanup)


def set_moisture_wet(channel, value):
    """Set wet point for a moisture channel."""
    _moisture[channel].wet = value

def set_moisture_wet(channel, value):
    """Set wet point for a moisture channel."""
    _moisture[channel].dry = value

def read_moiture(channel):
    """Get current value for the additional ADC pin."""
    setup()
    return _moisture[channel].value

def cleanup():
    GPIO.output(MOISTURE_1_PIN, 0)
    GPIO.output(MOISTURE_2_PIN, 0)
    GPIO.output(MOISTURE_3_PIN, 0)

def read_all():
    """Return gas resistence for oxidising, reducing and NH3"""
    setup()
    in1 = adc.get_voltage('in0/gnd')
    in2 = adc.get_voltage('in1/gnd')
    in3 = adc.get_voltage('in2/gnd')

    try:
        in1 = (ox * 56000) / (3.3 - ox)
    except ZeroDivisionError:
        in1 = 0

    try:
        in2 = (red * 56000) / (3.3 - red)
    except ZeroDivisionError:
        in2 = 0

    try:
        in3 = (nh3 * 56000) / (3.3 - nh3)
    except ZeroDivisionError:
        in3 = 0

    return _moisture(in1, in2, in3)
