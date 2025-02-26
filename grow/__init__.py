__version__ = '0.0.2'

import atexit
import threading
import time

import gpiodevice

from . import pwm

PLATFORMS = {
    "Raspberry Pi 5": {"piezo": ("PIN33", pwm.OUTL)},
    "Raspberry Pi 4": {"piezo": ("GPIO13", pwm.OUTL)},
}


class Piezo():
    def __init__(self, gpio_pin=None):

        if gpio_pin is None:
            gpio_pin = gpiodevice.get_pins_for_platform(PLATFORMS)[0]
        elif isinstance(gpio_pin, str):
            gpio_pin = gpiodevice.get_pin(gpio_pin, "piezo", pwm.OUTL)

        self.pwm = pwm.PWM(gpio_pin)
        self._timeout = None
        pwm.PWM.start_thread()
        atexit.register(pwm.PWM.stop_thread)

    def frequency(self, value):
        """Change the piezo frequency.

        Loosely corresponds to musical pitch, if you suspend disbelief.

        """
        self.pwm.set_frequency(value)

    def start(self, frequency):
        """Start the piezo.

        Sets the Duty Cycle to 50%

        """
        self.pwm.start(frequency=frequency, duty_cycle=0.5)

    def stop(self):
        """Stop the piezo.

        Sets the Duty Cycle to 0%

        """
        self.pwm.stop()

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
