import time
import atexit
import RPi.GPIO as GPIO

MOISTURE_1_PIN = 23
MOISTURE_2_PIN = 8
MOISTURE_3_PIN = 25
MOISTURE_INT_PIN = 4


class Moisture(object):
    def __init__(self, channel=0):
        self._gpio_pin = [MOISTURE_1_PIN, MOISTURE_2_PIN, MOISTURE_3_PIN, MOISTURE_INT_PIN][channel]

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._gpio_pin, GPIO.IN)

        self._count = 0
        self._reading = 0
        self._wet_point = 0
        self._dry_point = 0
        self._time_start = time.time()
        GPIO.add_event_detect(self._gpio_pin, GPIO.RISING, callback=self._event_handler, bouncetime=1)

    def set_wet_point(self, value=None):
        self._wet_point = value if value is not None else self.raw_moisture

    def set_dry_point(self, value=None):
        self._dry_point = value if value is not None else self.raw_moisture

    def _event_handler(self, pin):
        self._count += 1
        if self.time_elapsed >= 1.0:
            self._reading = self._count / self.time_elapsed
            self._count = 0
            self._time_start = time.time()

    @property
    def time_elapsed(self):
        return time.time() - self._time_start

    @property
    def raw_moisture(self):
        return self._reading

    @property
    def moisture(self):
        return self.raw_moisture

    @property
    def range(self):
        return self._wet_point - self._dry_point

    @property
    def saturation(self):
        return float(self.moisture - self._dry_point) / self.range
