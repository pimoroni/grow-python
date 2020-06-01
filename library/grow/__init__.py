__version__ = '0.0.1'

import time
import atexit
import threading
import RPi.GPIO as GPIO


class Piezo():
    def __init__(self, gpio_pin=13):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(gpio_pin, GPIO.OUT, initial=GPIO.LOW)
        self.pwm = GPIO.PWM(gpio_pin, 440)
        self.pwm.start(0)
        self._timeout = None
        atexit.register(self._exit)

    def frequency(self, value):
        """Change the piezo frequency.

        Loosely corresponds to musical pitch, if you suspend disbelief.

        """
        self.pwm.ChangeFrequency(value)

    def start(self, frequency=None):
        """Start the piezo.

        Sets the Duty Cycle to 100%

        """
        if frequency is not None:
            self.frequency(frequency)
        self.pwm.ChangeDutyCycle(1)

    def stop(self):
        """Stop the piezo.

        Sets the Duty Cycle to 0%

        """
        self.pwm.ChangeDutyCycle(0)

    def beep(self, frequency=440, timeout=0.1, blocking=True, force=False):
        """Beep the piezo for time seconds.

        :param freq: Frequency, in hertz, of the piezo
        :param timeout: Time, in seconds, of the piezo beep
        :param blocking: If true, function will block until piezo has stopped

        """
        if blocking:
            self.start(frequency=frequency)
            time.sleep(timeout)
            self.stop()
            return True
        else:
            if self._timeout is not None:
                if self._timeout.is_alive():
                    if force:
                        self._timeout.cancel()
                    else:
                        return False
            self._timeout = threading.Timer(timeout, self.stop)
            self.start(frequency=frequency)
            self._timeout.start()
            return True

    def _exit(self):
        self.pwm.stop()
