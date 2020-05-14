import time
import atexit
import RPi.GPIO as GPIO

PUMP_1_PIN = 17
PUMP_2_PIN = 27
PUMP_3_PIN = 22

_is_setup = False


class Pump(object):
    __slots__ = 'out1', 'out2', 'out3'

    def __init__(self, out1, out2, out3):
        self.out1 = out1
        self.out2 = out2
        self.out3 = out3

    def __repr__(self):
        fmt = """Pump 1: {out1}
Pump 1: {out2} Ohms
Pump 1: {out3} Ohms"""
        
        return fmt.format(
            out1=self.out1,
            out2=self.out2,
            out3=self.out3)

    __str__ = __repr__


def setup():
    global _is_setup
    global _pump
    
    if _is_setup:
        return
    _is_setup = True

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PUMP_1_PIN, GPIO.OUT)
    GPIO.input(PUMP_1_PIN, 0)
    GPIO.setup(PUMP_2_PIN, GPIO.OUT)
    GPIO.input(PUMP_2_PIN, 0)
    GPIO.setup(PUMP_3_PIN, GPIO.OUT)
    GPIO.input(PUMP_3_PIN, 0)
    
    atexit.register(cleanup)


def set_pump_on(channel):
    """Set wet point for a moisture channel."""
    _pump[channel] = 1

def set_pump_off(channel, value):
    """Set wet point for a moisture channel."""
    _pump[channel] = 0

def read_pump(channel):
    """Get current value for the additional ADC pin."""
    setup()
    return _pump[channel]

def cleanup():
    GPIO.output(PUMP_1_PIN, 0)
    GPIO.output(PUMP_2_PIN, 0)
    GPIO.output(PUMP_3_PIN, 0)

def read_all():
    """Return pump state"""
    setup()
    in1 = _pump[1]
    in2 = _pump[2]
    in3 = _pump[3]

    return _pump(in1, in2, in3)
