import time
import atexit
import threading
import RPi.GPIO as GPIO

PUMP_1_PIN = 17
PUMP_2_PIN = 27
PUMP_3_PIN = 22
PUMP_PWM_FREQ = 10000
PUMP_MAX_DUTY = 60


class Pump(object):
    def __init__(self, channel):
        self._gpio_pin = [PUMP_1_PIN, PUMP_2_PIN, PUMP_3_PIN][channel]

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self._gpio_pin, GPIO.OUT, initial=GPIO.LOW)
        self._pwm = GPIO.PWM(self._gpio_pin, PUMP_PWM_FREQ)
        self._pwm.start(0)

        self._timeout = None

    def set_speed(self, speed):
        """Set pump speed (PWM duty cycle)."""
        if speed > 1.0 or speed < 0:
            raise ValueError("Speed must be between 0 and 1")
        self._pwm.ChangeDutyCycle(int(PUMP_MAX_DUTY * speed))
        self._speed = speed

    def get_speed(self):
        """Return Pump speed (PWM duty cycle)."""
        return self._speed

    def stop(self):
        """Stop the pump."""
        self.set_speed(0)

    def pulse(self, speed, timeout=0.1, blocking=True, force=False):
        """Pulse the pump for timeout seconds.

        :param timeout: Timeout, in seconds, of the pump pulse
        :param blocking: If true, function will block until pump has stopped

        """
        if blocking:
            self.set_speed(speed)
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
            self.set_speed(speed)
            self._timeout.start()
            return True

