import time
from threading import Thread

import gpiod
import gpiodevice
from gpiod.line import Direction, Value

OUTL = gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)


class PWM:
    _pwms: list = []
    _t_pwm: Thread = None
    _pwm_running: bool = False

    @staticmethod
    def start_thread():
        if PWM._t_pwm is None:
            PWM._pwm_running = True
            PWM._t_pwm = Thread(target=PWM._run)
            PWM._t_pwm.start()

    @staticmethod
    def stop_thread():
        if PWM._t_pwm is not None:
            PWM._pwm_running = False
            PWM._t_pwm.join()
            PWM._t_pwm = None

    @staticmethod
    def _add(pwm):
        PWM._pwms.append(pwm)

    @staticmethod
    def _remove(pwm):
        index = PWM._pwms.index(pwm)
        del PWM._pwms[index]
        if len(PWM._pwms) == 0:
            PWM.stop_thread()

    @staticmethod
    def _run():
        while PWM._pwm_running:
            PWM.run()

    @staticmethod
    def run():
        for pwm in PWM._pwms:
            pwm.next(time.time())

    def __init__(self, pin, frequency=0, duty_cycle=0, lines=None, offset=None):
        self.duty_cycle = 0
        self.frequency = 0
        self.duty_period = 0
        self.period = 0
        self.running = False
        self.time_start = None
        self.state = Value.ACTIVE

        self.set_frequency(frequency)
        self.set_duty_cycle(duty_cycle)

        if isinstance(pin, tuple):
            self.lines, self.offset = pin
        else:
            self.lines, self.offset = gpiodevice.get_pin(pin, "PWM", OUTL)

        PWM._add(self)

    def set_frequency(self, frequency):
        if frequency == 0:
            return
        self.frequency = frequency
        self.period = 1.0 / frequency
        self.duty_period = self.duty_cycle * self.period

    def set_duty_cycle(self, duty_cycle):
        self.duty_cycle = duty_cycle
        self.duty_period = self.duty_cycle * self.period

    def start(self, duty_cycle=None, frequency=None, start_time=None):
        if duty_cycle is not None:
            self.set_duty_cycle(duty_cycle)

        if frequency is not None:
            self.set_frequency(frequency)

        self.time_start = time.time() if start_time is None else start_time

        self.running = True

    def next(self, t):
        if not self.running:
            return
        d = t - self.time_start
        d %= self.period
        new_state = Value.ACTIVE if d < self.duty_period else Value.INACTIVE
        if new_state != self.state:
            self.lines.set_value(self.offset, new_state)
            self.state = new_state

    def stop(self):
        self.running = False

    def __del__(self):
        PWM._remove(self)
