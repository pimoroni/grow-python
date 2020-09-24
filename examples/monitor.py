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
COLOR_BLUE = (31, 137, 251)
COLOR_GREEN = (99, 255, 124)
COLOR_YELLOW = (254, 219, 82)
COLOR_RED = (247, 0, 63)
COLOR_BLACK = (0, 0, 0)


# Only the ALPHA channel is used from these images
icon_drop = Image.open("icons/icon-drop.png").convert("RGBA")
icon_nodrop = Image.open("icons/icon-nodrop.png").convert("RGBA")
icon_rightarrow = Image.open("icons/icon-rightarrow.png").convert("RGBA")
icon_alarm = Image.open("icons/icon-alarm.png").convert("RGBA")
icon_snooze = Image.open("icons/icon-snooze.png").convert("RGBA")
icon_help = Image.open("icons/icon-help.png").convert("RGBA")
icon_settings = Image.open("icons/icon-settings.png").convert("RGBA")
icon_channel = Image.open("icons/icon-channel.png").convert("RGBA")
icon_backdrop = Image.open("icons/icon-backdrop.png").convert("RGBA")
icon_return = Image.open("icons/icon-return.png").convert("RGBA")


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
        self._draw.rectangle((0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT), (0, 0, 0))

    def icon(self, icon, position, color):
        col = Image.new("RGBA", icon.size, color=color)
        self._image.paste(col, position, mask=icon)

    def label(
        self,
        position="X",
        text=None,
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

    def overlay(self, text, top=0):
        """Draw an overlay with some auto-sized text."""
        self._draw.rectangle(
            (0, top, DISPLAY_WIDTH, DISPLAY_HEIGHT), fill=(192, 225, 254)
        )  # Overlay backdrop
        self._draw.rectangle((0, top, DISPLAY_WIDTH, top + 1), fill=COLOR_BLUE)  # Top border
        self.text_in_rect(
            text,
            self.font,
            (3, top, DISPLAY_WIDTH - 3, DISPLAY_HEIGHT - 2),
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
        bar_x = 33
        bar_margin = 2
        bar_width = 30
        label_width = 16
        label_height = 16
        label_y = 0

        x = [
            bar_x,
            bar_x + ((bar_width + bar_margin) * 1),
            bar_x + ((bar_width + bar_margin) * 2),
        ][channel.channel - 1]

        # Saturation amounts from each sensor
        saturation = channel.sensor.saturation
        active = channel.sensor.active and channel.enabled
        warn_level = channel.warn_level

        if active:
            # Draw background bars
            self._draw.rectangle(
                (x, int((1.0 - saturation) * DISPLAY_HEIGHT), x + bar_width - 1, DISPLAY_HEIGHT),
                channel.indicator_color(saturation) if active else (229, 229, 229),
            )

        y = int((1.0 - warn_level) * DISPLAY_HEIGHT)
        self._draw.rectangle(
            (x, y, x + bar_width - 1, y), (255, 0, 0) if channel.alarm else (0, 0, 0)
        )

        # Channel selection icons
        x += (bar_width - label_width) // 2

        self.icon(icon_channel, (x, label_y), (200, 200, 200) if active else (64, 64, 64))

        # TODO: replace number text with graphic
        tw, th = self.font.getsize(str(channel.channel))
        self._draw.text(
            (x + int(math.ceil(8 - (tw / 2.0))), label_y + 1),
            str(channel.channel),
            font=self.font,
            fill=(55, 55, 55) if active else (100, 100, 100),
        )

    def render(self):
        self.clear()

        for channel in self.channels:
            self.render_channel(channel)

        # Icons
        self.icon(icon_backdrop, (0, 0), COLOR_WHITE)
        self.icon(icon_rightarrow, (3, 3), (55, 55, 55))

        self.alarm.render((3, DISPLAY_HEIGHT - 23))

        self.icon(icon_backdrop.rotate(180), (DISPLAY_WIDTH - 26, 0), COLOR_WHITE)
        self.icon(icon_settings, (DISPLAY_WIDTH - 19 - 3, 3), (55, 55, 55))


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
        self.icon(icon_backdrop.rotate(180), (DISPLAY_WIDTH - 26, 0), COLOR_WHITE)
        self.icon(icon_return, (DISPLAY_WIDTH - 19 - 3, 3), (55, 55, 55))

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
                textcolor=COLOR_BLACK,
                bgcolor=COLOR_WHITE,
            )
            self.label(
                "B",
                "No" if mode == "bool" else "--",
                textcolor=COLOR_BLACK,
                bgcolor=COLOR_WHITE,
            )
        else:
            self.label("B", "Next", textcolor=COLOR_BLACK, bgcolor=COLOR_WHITE)
            self.label("Y", "Change", textcolor=COLOR_BLACK, bgcolor=COLOR_WHITE)

        self._draw.text((3, 36), f"{title} : {text}", font=self.font, fill=COLOR_WHITE)

        if self._help_mode:
            self.icon(icon_backdrop.rotate(90), (0, 0), COLOR_BLUE)
            self._draw.rectangle((7, 3, 23, 19), COLOR_BLACK)
            self.overlay(help, top=26)

        self.icon(icon_help, (0, 0), COLOR_BLUE)

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
            (28, 5),
            "Settings",
            font=self.font,
            fill=COLOR_WHITE,
        )
        EditView.render(self)


class ChannelView(View):
    """Base class for a view that deals with a specific channel instance."""

    def __init__(self, image, channel=None):
        self.channel = channel
        View.__init__(self, image)

    def draw_status(self, position):
        status = f"Sat: {self.channel.sensor.saturation * 100:.2f}%"

        self._draw.text(
            position,
            status,
            font=self.font,
            fill=(255, 255, 255),
        )

    def draw_context(self, position, metric="Hz"):
        context = f"Now: {self.channel.sensor.moisture:.2f}Hz"
        if metric.lower() == "sat":
            context = f"Now: {self.channel.sensor.saturation * 100:.2f}%"

        self._draw.text(
            position,
            context,
            font=self.font,
            fill=(255, 255, 255),
        )


class DetailView(ChannelView):
    """Single channel details.

    Draw the channel graph and status line.

    """

    def render(self):
        self.clear()

        if self.channel.enabled:
            graph_height = DISPLAY_HEIGHT - 8 - 20
            graph_width = DISPLAY_WIDTH - 64

            graph_x = (DISPLAY_WIDTH - graph_width) // 2
            graph_y = 8

            self.draw_status((graph_x, graph_y + graph_height + 4))

            self._draw.rectangle((graph_x, graph_y, graph_x + graph_width, graph_y + graph_height), (50, 50, 50))

            for x, value in enumerate(self.channel.sensor.history[:graph_width]):
                color = self.channel.indicator_color(value)
                h = value * graph_height
                x = graph_x + graph_width - x - 1
                self._draw.rectangle((x, graph_y + graph_height - h, x + 1, graph_y + graph_height), color)

            alarm_line = int(self.channel.warn_level * graph_height)
            r = 255
            if self.channel.alarm:
                r = int(((math.sin(time.time() * 3 * math.pi) + 1.0) / 2.0) * 128) + 127

            self._draw.rectangle(
                (
                    0,
                    graph_height + 8 - alarm_line,
                    DISPLAY_WIDTH - 40,
                    graph_height + 8 - alarm_line,
                ),
                (r, 0, 0),
            )
            self._draw.rectangle(
                (
                    DISPLAY_WIDTH - 20,
                    graph_height + 8 - alarm_line,
                    DISPLAY_WIDTH,
                    graph_height + 8 - alarm_line,
                ),
                (r, 0, 0),
            )

            self.icon(
                icon_alarm,
                (DISPLAY_WIDTH - 40, graph_height + 8 - alarm_line - 10),
                (r, 0, 0),
            )

        # Channel icons

        x_positions = [40, 72, 104]
        label_x = x_positions[self.channel.channel - 1]
        label_y = 0

        active = self.channel.sensor.active and self.channel.enabled

        for x in x_positions:
            self.icon(icon_channel, (x, label_y - 10), (16, 16, 16))

        self.icon(icon_channel, (label_x, label_y), (200, 200, 200))

        tw, th = self.font.getsize(str(self.channel.channel))
        self._draw.text(
            (label_x + int(math.ceil(8 - (tw / 2.0))), label_y + 1),
            str(self.channel.channel),
            font=self.font,
            fill=(55, 55, 55) if active else (100, 100, 100),
        )

        # Next button
        self.icon(icon_backdrop, (0, 0), COLOR_WHITE)
        self.icon(icon_rightarrow, (3, 3), (55, 55, 55))

        # Prev button
        # self.icon(icon_backdrop, (0, DISPLAY_HEIGHT - 26), COLOR_WHITE)
        # self.icon(icon_return, (3, DISPLAY_HEIGHT - 26 + 3), (55, 55, 55))

        # Edit
        self.icon(icon_backdrop.rotate(180), (DISPLAY_WIDTH - 26, 0), COLOR_WHITE)
        self.icon(icon_settings, (DISPLAY_WIDTH - 19 - 3, 3), (55, 55, 55))


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
                "context": "sat",
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
                "context": "hz",
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
                "context": "hz",
            },
        ]
        EditView.__init__(self, image, options)
        ChannelView.__init__(self, image, channel)

    def render(self):
        self.clear()

        EditView.render(self)

        option = self._options[self._current_option]
        if "context" in option:
            self.draw_context((34, 6), option["context"])


class Channel:
    colors = [
        COLOR_BLUE,
        COLOR_GREEN,
        COLOR_YELLOW,
        COLOR_RED
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

    def warn_color(self):
        value = self.sensor.moisture

    def indicator_color(self, value):
        value = 1.0 - value

        if value == 1.0:
            return self.colors[-1]
        if value == 0.0:
            return self.colors[0]

        value *= len(self.colors) - 1
        a = int(math.floor(value))
        b = a + 1
        blend = float(value - a)

        r, g, b = [int(((self.colors[b][i] - self.colors[a][i]) * blend) + self.colors[a][i]) for i in range(3)]

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
            self._sleep_until = None

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
        #self._draw.rectangle((x, y, x + 19, y + 19), (255, 255, 255))
        r = 129
        if self._triggered and self._sleep_until is None:
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

    def cancel_sleep(self):
        self._sleep_until = None

    def sleeping(self):
        return self._sleep_until is not None

    def sleep(self, duration=500):
        self._sleep_until = time.time() + duration


class ViewController:
    def __init__(self, views):
        self.views = views
        self._current_view = 0
        self._current_subview = 0
    
    @property
    def home(self):
        return self._current_view == 0 and self._current_subview == 0

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

    def prev_view(self):
        if self._current_subview == 0:
            self._current_view -= 1
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
        self.view.button_b()

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


def main():
    def handle_button(pin):
        index = BUTTONS.index(pin)
        label = LABELS[index]

        if label == "A":  # Select View
            viewcontroller.button_a()

        if label == "B":  # Sleep Alarm
            if not viewcontroller.button_b():
                if viewcontroller.home:
                    if alarm.sleeping():
                        alarm.cancel_sleep()
                    else:
                        alarm.sleep()

        if label == "X":
            viewcontroller.button_x()

        if label == "Y":
            viewcontroller.button_y()


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
