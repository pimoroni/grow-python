import atexit
import threading
import time

import gpiodevice

from . import pwm

PUMP_1_PIN = "PIN11" # 17
PUMP_2_PIN = "PIN13" # 27
PUMP_3_PIN = "PIN15" # 22
PUMP_PWM_FREQ = 10000
PUMP_MAX_DUTY = 0.9

PLATFORMS = {
    "Raspberry Pi 5": {"pump1": ("PIN11", pwm.OUTL), "pump2": ("PIN12", pwm.OUTL), "pump3": ("PIN15", pwm.OUTL)},
    "Raspberry Pi 4": {"pump1": ("GPIO17", pwm.OUTL), "pump2": ("GPIO27", pwm.OUTL), "pump3": ("GPIO22", pwm.OUTL)},
}


global_lock = threading.Lock()


class Pump(object):
    """Grow pump driver."""

    PINS = None

    def __init__(self, channel=1):
        """Create a new pump.

        Uses soft PWM to drive a Grow pump.

        :param channel: One of 1, 2 or 3.

        """

        if Pump.PINS is None:
            Pump.PINS = gpiodevice.get_pins_for_platform(PLATFORMS)

        self._gpio_pin = Pump.PINS[channel - 1]

        self._pwm = pwm.PWM(self._gpio_pin, PUMP_PWM_FREQ)
        self._pwm.start(0)

        pwm.PWM.start_thread()
        atexit.register(pwm.PWM.stop_thread)

        self._timeout = None

    def set_speed(self, speed):
        """Set pump speed (PWM duty cycle)."""
        if speed > 1.0 or speed < 0:
            raise ValueError("Speed must be between 0 and 1")

        if speed == 0:
            global_lock.release()
        elif not global_lock.acquire(blocking=False):
            return False

        self._pwm.set_duty_cycle(PUMP_MAX_DUTY * speed)
        self._speed = speed
        return True

    def get_speed(self):
        """Return Pump speed (PWM duty cycle)."""
        return self._speed

    def stop(self):
        """Stop the pump."""
        if self._timeout is not None:
            self._timeout.cancel()
            self._timeout = None
        self.set_speed(0)

    def dose(self, speed, timeout=0.1, blocking=True, force=False):
        """Pulse the pump for timeout seconds.

        :param timeout: Timeout, in seconds, of the pump pulse
        :param blocking: If true, function will block until pump has stopped
        :param force: Applies only to non-blocking. If true, any previous dose will be replaced

        """

        if blocking:
            if self.set_speed(speed):
                time.sleep(timeout)
                self.stop()
                return True

        else:
            if self._timeout is not None:
                if self._timeout.is_alive():
                    if force:
                        self._timeout.cancel()

            self._timeout = threading.Timer(timeout, self.stop)
            if self.set_speed(speed):
                self._timeout.start()
                return True

        return False
