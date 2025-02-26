import atexit
import select
import threading
import time
from datetime import timedelta

import gpiodevice
from gpiod import LineSettings
from gpiod.line import Bias, Edge

MOISTURE_1_PIN = 23
MOISTURE_2_PIN = 8
MOISTURE_3_PIN = 25
MOISTURE_INT_PIN = 4


class Moisture(object):
    """Grow moisture sensor driver."""

    def __init__(self, channel=1, wet_point=None, dry_point=None):
        """Create a new moisture sensor.

        Uses an interrupt to count pulses on the GPIO pin corresponding to the selected channel.

        The moisture reading is given as pulses per second.

        :param channel: One of 1, 2 or 3. 4 can optionally be used to set up a sensor on the Int pin (BCM4)
        :param wet_point: Wet point in pulses/sec
        :param dry_point: Dry point in pulses/sec

        """
        self._gpio_pin = [MOISTURE_1_PIN, MOISTURE_2_PIN, MOISTURE_3_PIN, MOISTURE_INT_PIN][channel - 1]

        self._count = 0
        self._reading = 0
        self._history = []
        self._history_length = 200
        self._new_data = False
        self._wet_point = wet_point if wet_point is not None else 0.7
        self._dry_point = dry_point if dry_point is not None else 27.6

        self._last_reading = 0

        self._int, self._offset = gpiodevice.get_pin(self._gpio_pin, f"grow-m-ch{channel}", LineSettings(
            edge_detection=Edge.RISING, bias=Bias.PULL_DOWN, debounce_period=timedelta(milliseconds=10)
        ))

        self._poll_thread_event = threading.Event()
        self._poll_thread = threading.Thread(target=self._thread_poll)
        self._poll_thread.start()

        atexit.register(self._thread_stop)

    def __del__(self):
        self._thread_stop()

    def _thread_stop(self):
        self._poll_thread_event.set()
        self._poll_thread.join()

    def _thread_poll(self):
        poll = select.poll()
        try:
            poll.register(self._int.fd, select.POLLIN)
        except TypeError:
            return
        while not self._poll_thread_event.wait(1.0):
            if not poll.poll(0):
                # No pulses in 1s, this is not a valid reading
                continue

            # We got pulses, since we waited for 1s we can be relatively
            # sure the number of pulses is approximately the sensor frequency
            events = self._int.read_edge_events()
            self._last_reading = time.time()
            self._reading = len(events)  # Pulse frequency
            self._history.insert(0, self._reading)
            self._history = self._history[:self._history_length]
            self._new_data = True

        poll.unregister(self._int.fd)

    @property
    def history(self):
        history = []

        for moisture in self._history:
            saturation = float(moisture - self._dry_point) / self.range
            saturation = round(saturation, 3)
            history.append(max(0.0, min(1.0, saturation)))

        return history

    def set_wet_point(self, value=None):
        """Set the sensor wet point.

        This is the watered, wet state of your soil.

        It should be set shortly after watering. Leave ~5 mins for moisture to permeate.

        :param value: Wet point value to set in pulses/sec, leave as None to set the last sensor reading.

        """
        self._wet_point = value if value is not None else self._reading

    def set_dry_point(self, value=None):
        """Set the sensor dry point.

        This is the unwatered, dry state of your soil.

        It should be set when the soil is dry to the touch.

        :param value: Dry point value to set in pulses/sec, leave as None to set the last sensor reading.

        """
        self._dry_point = value if value is not None else self._reading

    @property
    def moisture(self):
        """Return the raw moisture level.

        The value returned is the pulses/sec read from the soil moisture sensor.

        This value is inversely proportional to the amount of moisture.

        Full immersion in water is approximately 50 pulses/sec.

        Fully dry (in air) is approximately 900 pulses/sec.

        """
        self._new_data = False
        return self._reading

    @property
    def active(self):
        """Check if the moisture sensor is producing a valid reading."""
        return (time.time() - self._last_reading) <= 1.0 and self._reading > 0 and self._reading < 28

    @property
    def new_data(self):
        """Check for new reading.

        Returns True if moisture value has been updated since last reading moisture or saturation.

        """
        return self._new_data

    @property
    def range(self):
        """Return the range sensor range (wet - dry points)."""
        return self._wet_point - self._dry_point

    @property
    def saturation(self):
        """Return saturation as a float from 0.0 to 1.0.

        This value is calculated using the wet and dry points.

        """
        saturation = float(self.moisture - self._dry_point) / self.range
        saturation = round(saturation, 3)
        return max(0.0, min(1.0, saturation))
