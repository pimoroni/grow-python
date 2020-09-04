#!/usr/bin/env python3
import logging
import math
import pathlib
import random
import sys
import threading
import time

import ltr559
import RPi.GPIO as GPIO
import ST7735
from fonts.ttf import RobotoMedium as UserFont
from PIL import Image, ImageDraw, ImageFont

import yaml
from grow import Piezo
from grow.moisture import Moisture
from grow.pump import Pump


FPS = 10

BUTTONS = [5, 6, 16, 24]
LABELS = ["A", "B", "X", "Y"]

DISPLAY_WIDTH = 160
DISPLAY_HEIGHT = 80

COLOR_WHITE = (255, 255, 255)
COLOR_BLUE = (32, 137, 251)
COLOR_GREEN = (100, 255, 124)
COLOR_YELLOW = (254, 219, 82)
COLOR_RED = (254, 82, 82)


# Only the ALPHA channel is used from these images
icon_drop = Image.open("../icons/icon-drop.png").convert("RGBA")
icon_nodrop = Image.open("../icons/icon-nodrop.png").convert("RGBA")
icon_rightarrow = Image.open("../icons/icon-rightarrow.png").convert("RGBA")
icon_alarm = Image.open("../icons/icon-alarm.png").convert("RGBA")
icon_snooze = Image.open("../icons/icon-snooze.png").convert("RGBA")
icon_help = Image.open("../icons/icon-help.png").convert("RGBA")
icon_settings = Image.open("../icons/icon-settings.png").convert("RGBA")


class View:
    def __init__(self, image):
        self._image = image
        self._draw = ImageDraw.Draw(image)

        self.font = ImageFont.truetype(UserFont, 14)
        self.font_small = ImageFont.truetype(UserFont, 10)

    def button_a(self):
        return False

    def button_b(self):
        return False

    def button_x(self):
        return False

    def button_y(self):
        return False

    def update(self):
        pass

    def render(self):
        pass

    def clear(self):
        self._draw.rectangle((0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT), (255, 255, 255))

    def icon(self, icon, position, color):
        col = Image.new("RGBA", icon.size, color=color)
        self._image.paste(col, position, mask=icon)

    def label(
        self,
        position="X",
        text="",
        bgcolor=(0, 0, 0),
        textcolor=(255, 255, 255),
        margin=4,
    ):
        if position not in ["A", "B", "X", "Y"]:
            raise ValueError(f"Invalid label position {position}")

        text_w, text_h = self._draw.textsize(text, font=self.font)
        text_h = 11
        text_w += margin * 2
        text_h += margin * 2

        if position == "A":
            x, y = 0, 0
        if position == "B":
            x, y = 0, DISPLAY_HEIGHT - text_h
        if position == "X":
            x, y = DISPLAY_WIDTH - text_w, 0
        if position == "Y":
            x, y = DISPLAY_WIDTH - text_w, DISPLAY_HEIGHT - text_h

        x2, y2 = x + text_w, y + text_h

        self._draw.rectangle((x, y, x2, y2), bgcolor)
        self._draw.text(
            (x + margin, y + margin - 1), text, font=self.font, fill=textcolor
        )

    def overlay(self, text):
        """Draw an overlay with some auto-sized text."""
        self._draw.rectangle(
            (0, 20, DISPLAY_WIDTH, DISPLAY_HEIGHT), fill=(192, 225, 254)
        )  # Overlay backdrop
        self._draw.rectangle((0, 20, DISPLAY_WIDTH, 21), fill=COLOR_BLUE)  # Top border
        self.text_in_rect(
            text,
            self.font,
            (3, 20, DISPLAY_WIDTH - 3, DISPLAY_HEIGHT - 2),
            line_spacing=1,
        )

    def text_in_rect(self, text, font, rect, line_spacing=1.1, textcolor=(0, 0, 0)):
        x1, y1, x2, y2 = rect
        width = x2 - x1
        height = y2 - y1

        # Given a rectangle, reflow and scale text to fit, centred
        while font.size > 0:
            space_width = font.getsize(" ")[0]
            line_height = int(font.size * line_spacing)
            max_lines = math.floor(height / line_height)
            lines = []

            # Determine if text can fit at current scale.
            words = text.split(" ")

            while len(lines) < max_lines and len(words) > 0:
                line = []

                while (
                    len(words) > 0
                    and font.getsize(" ".join(line + [words[0]]))[0] <= width
                ):
                    line.append(words.pop(0))

                lines.append(" ".join(line))

            if len(lines) <= max_lines and len(words) == 0:
                # Solution is found, render the text.
                y = int(
                    y1
                    + (height / 2)
                    - (len(lines) * line_height / 2)
                    - (line_height - font.size) / 2
                )

                bounds = [x2, y, x1, y + len(lines) * line_height]

                for line in lines:
                    line_width = font.getsize(line)[0]
                    x = int(x1 + (width / 2) - (line_width / 2))
                    bounds[0] = min(bounds[0], x)
                    bounds[2] = max(bounds[2], x + line_width)
                    self._draw.text((x, y), line, font=self.font, fill=textcolor)
                    y += line_height

                return tuple(bounds)

            font = ImageFont.truetype(font.path, font.size - 1)


class MainView(View):
    """Main overview.

    Displays three channels and alarm indicator/snooze.

    """

    def __init__(self, image, channels=None, alarm=None):
        self.channels = channels
        self.alarm = alarm

        View.__init__(self, image)

    def render_channel(self, channel):
        x = [21, 61, 101][channel.channel - 1]

        # Saturation amounts from each sensor
        saturation = channel.sensor.saturation
        active = channel.sensor.active and channel.enabled
        warn_level = channel.warn_level

        self._draw.rectangle((x, 0, x + 37, DISPLAY_HEIGHT), (230, 230, 230))

        if active:
            # Draw background bars
            self._draw.rectangle(
                (x, int((1.0 - saturation) * DISPLAY_HEIGHT), x + 37, DISPLAY_HEIGHT),
                channel.indicator_color(saturation) if active else (229, 229, 229),
            )

        y = int((1.0 - warn_level) * DISPLAY_HEIGHT)
        self._draw.rectangle(
            (x, y, x + 37, y), (255, 0, 0) if channel.alarm else (0, 0, 0)
        )

        # Channel selection icons
        x += 11
        col = channel.indicator_color(saturation, channel.label_colours)
        if channel.alarm:
            self.icon(icon_alarm, (x - 2, 0), col if active else (129, 129, 129))
        else:
            self._draw.rectangle(
                (x, 2, x + 15, 17),
                col if active else (129, 129, 129),
            )

        # TODO: replace number text with graphic
        tw, th = self.font.getsize("{}".format(channel.channel))
        self._draw.text(
            (x + int(math.ceil(8 - (tw / 2.0))), 2),
            "{}".format(channel.channel),
            font=self.font,
            fill=(255, 255, 255) if active else (200, 200, 200),
        )

    def render(self):
        self.clear()

        for channel in self.channels:
            self.render_channel(channel)

        # Icon backdrops
        self._draw.rectangle((0, 0, 19, 19), (32, 138, 251))

        # Icons
        self.icon(icon_rightarrow, (0, 0), (255, 255, 255))

        self.alarm.render((0, DISPLAY_HEIGHT - 19))

        self.icon(icon_settings, (DISPLAY_WIDTH - 19, 0), COLOR_RED)

        self.label("Y", "BL", textcolor=COLOR_WHITE, bgcolor=COLOR_GREEN)


class EditView(View):
    """Baseclass for a settings edit view."""

    def __init__(self, image, options=[]):
        self._options = options
        self._current_option = 0
        self._change_mode = False
        self._help_mode = False
        self.channel = None

        View.__init__(self, image)

    def render(self):
        self.label("X", "Done", textcolor=COLOR_WHITE, bgcolor=COLOR_RED)

        option = self._options[self._current_option]
        title = option["title"]
        prop = option["prop"]
        object = option.get("object", self.channel)
        value = getattr(object, prop)
        text = option["format"](value)
        mode = option.get("mode", "int")
        help = option["help"]

        if self._change_mode:
            self.label(
                "Y",
                "Yes" if mode == "bool" else "++",
                textcolor=COLOR_WHITE,
                bgcolor=COLOR_YELLOW,
            )
            self.label(
                "B",
                "No" if mode == "bool" else "--",
                textcolor=COLOR_WHITE,
                bgcolor=COLOR_BLUE,
            )
        else:
            self.label("B", "Next", textcolor=COLOR_WHITE, bgcolor=COLOR_BLUE)
            self.label("Y", "Change", textcolor=COLOR_WHITE, bgcolor=COLOR_YELLOW)

        self.icon(icon_help, (0, 0), COLOR_BLUE)

        self._draw.text((3, 43), f"{title} : {text}", font=self.font, fill=(0, 0, 0))

        if self._help_mode:
            self.overlay(help)

    def button_a(self):
        self._help_mode = not self._help_mode
        return True

    def button_b(self):
        if self._help_mode:
            return True

        if self._change_mode:
            option = self._options[self._current_option]
            prop = option["prop"]
            mode = option.get("mode", "int")
            object = option.get("object", self.channel)

            value = getattr(object, prop)
            if mode == "bool":
                value = False
            else:
                inc = option["inc"]
                limit = option["min"]
                value -= inc
                if mode == "float":
                    value = round(value, option.get("round", 1))
                if value < limit:
                    value = limit
            setattr(object, prop, value)
        else:
            self._current_option += 1
            self._current_option %= len(self._options)

        return True

    def button_x(self):
        if self._change_mode:
            self._change_mode = False
            return True
        return False

    def button_y(self):
        if self._help_mode:
            return True
        if self._change_mode:
            option = self._options[self._current_option]
            prop = option["prop"]
            mode = option.get("mode", "int")
            object = option.get("object", self.channel)

            value = getattr(object, prop)
            if mode == "bool":
                value = True
            else:
                inc = option["inc"]
                limit = option["max"]
                value += inc
                if mode == "float":
                    value = round(value, option.get("round", 1))
                if value > limit:
                    value = limit
            setattr(object, prop, value)
        else:
            self._change_mode = True

        return True


class SettingsView(EditView):
    """Main settings."""

    def __init__(self, image, options=[]):
        EditView.__init__(self, image, options)

    def render(self):
        self.clear()
        self._draw.text(
            (23, 3),
            "Settings",
            font=self.font,
            fill=(0, 0, 0),
        )
        EditView.render(self)


class ChannelView(View):
    """Base class for a view that deals with a specific channel instance."""

    def __init__(self, image, channel=None):
        self.channel = channel
        View.__init__(self, image)

    def draw_status(self, subtle=False):
        status = f"{self.channel.sensor.saturation * 100:.2f}% ({self.channel.sensor.moisture:.2f}Hz)"

        self._draw.rectangle((0, 20, DISPLAY_WIDTH, 40), (50, 50, 50))

        self._draw.text(
            (3, 23),
            status,
            font=self.font,
            fill=(150, 150, 150) if subtle else (255, 255, 255),
        )


class DetailView(ChannelView):
    """Single channel details.

    Draw the channel graph and status line.

    """

    def render(self):
        width, height = self._image.size
        self._draw.rectangle((0, 0, width, height), (255, 255, 255))

        self._draw.text(
            (23, 3),
            "{}".format(self.channel.title),
            font=self.font,
            fill=(0, 0, 0),
        )

        self.draw_status()

        graph_height = DISPLAY_HEIGHT - 40
        self._draw.rectangle(
            (0, DISPLAY_HEIGHT - graph_height, DISPLAY_WIDTH, DISPLAY_HEIGHT),
            (10, 10, 10),
        )

        for x, value in enumerate(self.channel.sensor.history[:DISPLAY_WIDTH]):
            color = self.channel.indicator_color(value)
            h = value * graph_height
            x = DISPLAY_WIDTH - x - 1
            self._draw.rectangle((x, DISPLAY_HEIGHT - h, x + 1, DISPLAY_HEIGHT), color)

        alarm_line = int(self.channel.warn_level * graph_height)
        r = 255
        if self.channel.alarm:
            r = int(((math.sin(time.time() * 3 * math.pi) + 1.0) / 2.0) * 128) + 127
        self._draw.rectangle(
            (
                0,
                DISPLAY_HEIGHT - alarm_line,
                DISPLAY_WIDTH - 40,
                DISPLAY_HEIGHT - alarm_line,
            ),
            (r, 0, 0),
        )
        self._draw.rectangle(
            (
                DISPLAY_WIDTH - 20,
                DISPLAY_HEIGHT - alarm_line,
                DISPLAY_WIDTH,
                DISPLAY_HEIGHT - alarm_line,
            ),
            (r, 0, 0),
        )

        self.icon(
            icon_alarm,
            (DISPLAY_WIDTH - 40, DISPLAY_HEIGHT - alarm_line - 10),
            (r, 0, 0),
        )

        # Next button
        self._draw.rectangle((0, 0, 19, 19), COLOR_BLUE)
        self.icon(icon_rightarrow, (0, 0), COLOR_WHITE)

        # Edit
        self.label("X", "Edit", textcolor=(255, 255, 255), bgcolor=COLOR_RED)


class ChannelEditView(ChannelView, EditView):
    """Single channel edit."""

    def __init__(self, image, channel=None):
        options = [
            {
                "title": "Alarm Level",
                "prop": "warn_level",
                "inc": 0.05,
                "min": 0,
                "max": 1.0,
                "mode": "float",
                "round": 2,
                "format": lambda value: f"{value * 100:0.2f}%",
                "help": "Saturation at which alarm is triggered",
            },
            {
                "title": "Enabled",
                "prop": "enabled",
                "mode": "bool",
                "format": lambda value: "Yes" if value else "No",
                "help": "Enable/disable this channel",
            },
            {
                "title": "Wet Point",
                "prop": "wet_point",
                "inc": 0.5,
                "min": 1,
                "max": 27,
                "mode": "float",
                "round": 2,
                "format": lambda value: f"{value:0.2f}Hz",
                "help": "Frequency for fully saturated soil",
            },
            {
                "title": "Dry Point",
                "prop": "dry_point",
                "inc": 0.5,
                "min": 1,
                "max": 27,
                "mode": "float",
                "round": 2,
                "format": lambda value: f"{value:0.2f}Hz",
                "help": "Frequency for fully dried soil",
            },
        ]
        EditView.__init__(self, image, options)
        ChannelView.__init__(self, image, channel)

    def render(self):
        self.clear()

        self._draw.text(
            (23, 3), "{}".format(self.channel.title), font=self.font, fill=(0, 0, 0)
        )

        EditView.render(self)

        if not self._help_mode:
            self.draw_status(True)


class Channel:
    bar_colours = [
        (192, 225, 254),  # Blue
        (196, 255, 209),  # Green
        (255, 243, 192),  # Yellow
        (254, 192, 192),  # Red
    ]

    label_colours = [
        COLOR_BLUE,
        COLOR_GREEN,
        COLOR_YELLOW,
        COLOR_RED,
    ]

    def __init__(
        self,
        display_channel,
        sensor_channel,
        pump_channel,
        title=None,
        water_level=0.5,
        warn_level=0.5,
        pump_speed=0.7,
        pump_time=0.7,
        watering_delay=30,
        wet_point=0.7,
        dry_point=26.7,
        icon=None,
        auto_water=False,
        enabled=False,
    ):
        self.channel = display_channel
        self.sensor = Moisture(sensor_channel)
        self.pump = Pump(pump_channel)
        self.water_level = water_level
        self.warn_level = warn_level
        self.auto_water = auto_water
        self.pump_speed = pump_speed
        self.pump_time = pump_time
        self.watering_delay = watering_delay
        self._wet_point = wet_point
        self._dry_point = dry_point
        self.last_dose = time.time()
        self.icon = icon
        self._enabled = enabled
        self.alarm = False
        self.title = f"Channel {display_channel}" if title is None else title

        self.sensor.set_wet_point(wet_point)
        self.sensor.set_dry_point(dry_point)

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        self._enabled = enabled

    @property
    def wet_point(self):
        return self._wet_point

    @property
    def dry_point(self):
        return self._dry_point

    @wet_point.setter
    def wet_point(self, wet_point):
        self._wet_point = wet_point
        self.sensor.set_wet_point(wet_point)

    @dry_point.setter
    def dry_point(self, dry_point):
        self._dry_point = dry_point
        self.sensor.set_dry_point(dry_point)

    def indicator_color(self, value, r=None):
        value = 1.0 - value

        if r is None:
            r = self.bar_colours
        if value == 1.0:
            return r[-1]
        if value == 0.0:
            return r[0]

        value *= len(r) - 1
        a = int(math.floor(value))
        b = a + 1
        blend = float(value - a)

        r, g, b = [int(((r[b][i] - r[a][i]) * blend) + r[a][i]) for i in range(3)]

        return (r, g, b)

    def update_from_yml(self, config):
        if config is not None:
            self.pump_speed = config.get("pump_speed", self.pump_speed)
            self.pump_time = config.get("pump_time", self.pump_time)
            self.warn_level = config.get("warn_level", self.warn_level)
            self.water_level = config.get("water_level", self.water_level)
            self.watering_delay = config.get("watering_delay", self.watering_delay)
            self.auto_water = config.get("auto_water", self.auto_water)
            self.enabled = config.get("enabled", self.enabled)
            self.wet_point = config.get("wet_point", self.wet_point)
            self.dry_point = config.get("dry_point", self.dry_point)

        pass

    def __str__(self):
        return """Channel: {channel}
Enabled: {enabled}
Alarm level: {warn_level}
Auto water: {auto_water}
Water level: {water_level}
Pump speed: {pump_speed}
Pump time: {pump_time}
Delay: {watering_delay}
Wet point: {wet_point}
Dry point: {dry_point}
""".format(
            channel=self.channel,
            enabled=self.enabled,
            warn_level=self.warn_level,
            auto_water=self.auto_water,
            water_level=self.water_level,
            pump_speed=self.pump_speed,
            pump_time=self.pump_time,
            watering_delay=self.watering_delay,
            wet_point=self.wet_point,
            dry_point=self.dry_point,
        )

    def water(self):
        if not self.auto_water:
            return False
        if time.time() - self.last_dose > self.watering_delay:
            self.pump.dose(self.pump_speed, self.pump_time, blocking=False)
            self.last_dose = time.time()
            return True
        return False

    def render(self, image, font):
        pass

    def update(self):
        if not self.enabled:
            return
        sat = self.sensor.saturation
        if sat < self.water_level:
            if self.water():
                logging.info(
                    "Watering Channel: {} - rate {:.2f} for {:.2f}sec".format(
                        self.channel, self.pump_speed, self.pump_time
                    )
                )
        if sat < self.warn_level:
            if not self.alarm:
                logging.warning(
                    "Alarm on Channel: {} - saturation is {:.2f}% (warn level {:.2f}%)".format(
                        self.channel, sat * 100, self.warn_level * 100
                    )
                )
            self.alarm = True
        else:
            self.alarm = False


class Alarm(View):
    def __init__(self, image, enabled=True, interval=10.0, beep_frequency=440):
        self.piezo = Piezo()
        self.enabled = enabled
        self.interval = interval
        self.beep_frequency = beep_frequency
        self._triggered = False
        self._time_last_beep = time.time()
        self._sleep_until = None

        View.__init__(self, image)

    def update_from_yml(self, config):
        if config is not None:
            self.enabled = config.get("alarm_enable", self.enabled)
            self.interval = config.get("alarm_interval", self.interval)

    def update(self, lights_out=False):
        if self._sleep_until is not None:
            if self._sleep_until > time.time():
                return

        if (
            self.enabled
            and not lights_out
            and self._triggered
            and time.time() - self._time_last_beep > self.interval
        ):
            self.piezo.beep(self.beep_frequency, 0.1, blocking=False)
            threading.Timer(
                0.3,
                self.piezo.beep,
                args=[self.beep_frequency, 0.1],
                kwargs={"blocking": False},
            ).start()
            threading.Timer(
                0.6,
                self.piezo.beep,
                args=[self.beep_frequency, 0.1],
                kwargs={"blocking": False},
            ).start()
            self._time_last_beep = time.time()

            self._triggered = False

    def render(self, position=(0, 0)):
        x, y = position
        # Draw the snooze icon- will be pulsing red if the alarm state is True
        self._draw.rectangle((x, y, x + 19, y + 19), (255, 255, 255))
        r = 129
        if self._triggered:
            r = int(((math.sin(time.time() * 3 * math.pi) + 1.0) / 2.0) * 128) + 127

        if self._sleep_until is None:
            self.icon(icon_alarm, (x, y - 1), (r, 129, 129))
        else:
            self.icon(icon_snooze, (x, y - 1), (r, 129, 129))

    def trigger(self):
        self._triggered = True

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

    def sleep(self, duration=500):
        self._sleep_until = time.time() + duration


class ViewController:
    def __init__(self, views):
        self.views = views
        self._current_view = 0
        self._current_subview = 0

    def next_subview(self):
        view = self.views[self._current_view]
        if isinstance(view, tuple):
            self._current_subview += 1
            self._current_subview %= len(view)

    def next_view(self):
        if self._current_subview == 0:
            self._current_view += 1
            self._current_view %= len(self.views)
            self._current_subview = 0

    def get_current_view(self):
        view = self.views[self._current_view]
        if isinstance(view, tuple):
            view = view[self._current_subview]

        return view

    @property
    def view(self):
        return self.get_current_view()

    def update(self):
        self.view.update()

    def render(self):
        self.view.render()

    def button_a(self):
        if not self.view.button_a():
            self.next_view()

    def button_b(self):
        return self.view.button_b()

    def button_x(self):
        if not self.view.button_x():
            self.next_subview()
            return True
        return True

    def button_y(self):
        return self.view.button_y()


class Config:
    def __init__(self):
        self.config = None
        self._last_save = ""

        self.channel_settings = [
            "enabled",
            "warn_level",
            "wet_point",
            "dry_point",
        ]

        self.general_settings = [
            "alarm_enable",
            "alarm_interval",
        ]

    def load(self, settings_file="settings.yml"):
        if len(sys.argv) > 1:
            settings_file = sys.argv[1]

        settings_file = pathlib.Path(settings_file)

        if settings_file.is_file():
            try:
                self.config = yaml.safe_load(open(settings_file))
            except yaml.parser.ParserError as e:
                raise yaml.parser.ParserError(
                    "Error parsing settings file: {} ({})".format(settings_file, e)
                )

    def save(self, settings_file="settings.yml"):
        if len(sys.argv) > 1:
            settings_file = sys.argv[1]

        settings_file = pathlib.Path(settings_file)

        dump = yaml.dump(self.config)

        if dump == self._last_save:
            return

        if settings_file.is_file():
            with open(settings_file, "w") as file:
                file.write(dump)

        self._last_save = dump

    def get_channel(self, channel_id):
        return self.config.get("channel{}".format(channel_id), {})

    def set(self, section, settings):
        if isinstance(settings, dict):
            self.config[section].update(settings)
        else:
            for key in self.channel_settings:
                value = getattr(settings, key, None)
                if value is not None:
                    self.config[section].update({key: value})

    def set_channel(self, channel_id, settings):
        self.set("channel{}".format(channel_id), settings)

    def get_general(self):
        return self.config.get("general", {})

    def set_general(self, settings):
        self.set("general", settings)


backlight = True


def main():
    def handle_button(pin):
        global backlight

        index = BUTTONS.index(pin)
        label = LABELS[index]

        if label == "A":  # Select View
            viewcontroller.button_a()

        if label == "B":  # Sleep Alarm
            if not viewcontroller.button_b():
                alarm.sleep()

        if label == "X":
            viewcontroller.button_x()

        if label == "Y":
            if not viewcontroller.button_y():
                backlight = not backlight
                display.set_backlight(backlight)


    # Set up the ST7735 SPI Display
    display = ST7735.ST7735(
        port=0, cs=1, dc=9, backlight=12, rotation=270, spi_speed_hz=80000000
    )
    display.begin()

    # Set up light sensor
    light = ltr559.LTR559()

    # Set up our canvas and prepare for drawing
    image = Image.new("RGBA", (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=(255, 255, 255))

    # Pick a random selection of plant icons to display on screen
    channels = [
        Channel(1, 1, 1),
        Channel(2, 2, 2),
        Channel(3, 3, 3),
    ]

    alarm = Alarm(image)

    config = Config()

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    for pin in BUTTONS:
        GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=200)

    config.load()

    for channel in channels:
        channel.update_from_yml(config.get_channel(channel.channel))

    alarm.update_from_yml(config.get_general())

    print("Channels:")
    for channel in channels:
        print(channel)

    print(
        """Settings:
Alarm Enabled: {}
Alarm Interval: {:.2f}s
""".format(
            alarm.enabled, alarm.interval
        )
    )

    main_options = [
        {
            "title": "Alarm Interval",
            "prop": "interval",
            "inc": 1,
            "min": 1,
            "max": 60,
            "format": lambda value: f"{value:02.0f}sec",
            "object": alarm,
            "help": "Time between alarm beeps.",
        },
        {
            "title": "Alarm Enable",
            "prop": "enabled",
            "mode": "bool",
            "format": lambda value: "Yes" if value else "No",
            "object": alarm,
            "help": "Enable the piezo alarm beep.",
        },
    ]

    viewcontroller = ViewController(
        [
            (
                MainView(image, channels=channels, alarm=alarm),
                SettingsView(image, options=main_options),
            ),
            (
                DetailView(image, channel=channels[0]),
                ChannelEditView(image, channel=channels[0]),
            ),
            (
                DetailView(image, channel=channels[1]),
                ChannelEditView(image, channel=channels[1]),
            ),
            (
                DetailView(image, channel=channels[2]),
                ChannelEditView(image, channel=channels[2]),
            ),
        ]
    )

    while True:
        for channel in channels:
            config.set_channel(channel.channel, channel)
            channel.update()
            if channel.alarm:
                alarm.trigger()

        alarm.update(light.get_lux() < 4.0)

        viewcontroller.update()
        viewcontroller.render()
        display.display(image.convert("RGB"))

        config.set_general(
            {
                "alarm_enable": alarm.enabled,
                "alarm_interval": alarm.interval,
            }
        )

        config.save()

        time.sleep(1.0 / FPS)


if __name__ == "__main__":
    main()
