#!/usr/bin/env python3
import logging
import math
import pathlib
import random
import sys
import time
import threading

import RPi.GPIO as GPIO
import ST7735
from fonts.ttf import RobotoMedium as UserFont
from PIL import Image, ImageDraw, ImageFont

import yaml
from grow import Piezo
from grow.moisture import Moisture
from grow.pump import Pump


class Channel:
    bar_colours = [
        (192, 225, 254),  # Blue
        (196, 255, 209),  # Green
        (255, 243, 192),  # Yellow
        (254, 192, 192),  # Red
    ]

    label_colours = [
        (32, 137, 251),  # Blue
        (100, 255, 124),  # Green
        (254, 219, 82),  # Yellow
        (254, 82, 82),  # Red
    ]

    def __init__(
        self,
        display_channel,
        sensor_channel,
        pump_channel,
        water_level=0.5,
        alarm_level=0.5,
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
        self.alarm_level = alarm_level
        self.auto_water = auto_water
        self.pump_speed = pump_speed
        self.pump_time = pump_time
        self.watering_delay = watering_delay
        self.wet_point = wet_point
        self.dry_point = dry_point
        self.last_dose = time.time()
        self.icon = icon
        self.enabled = enabled
        self.alarm = False

        self.sensor.set_wet_point(wet_point)
        self.sensor.set_dry_point(dry_point)

    def indicator_color(self, value, r=None):
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
            self.alarm_level = config.get("alarm_level", self.alarm_level)
            self.water_level = config.get("water_level", self.water_level)
            self.watering_delay = config.get("watering_delay", self.watering_delay)
            self.auto_water = config.get("auto_water", self.auto_water)
            self.enabled = config.get("enabled", self.enabled)
            self.wet_point = config.get("wet_point", self.wet_point)
            self.dry_point = config.get("dry_point", self.dry_point)
            icon = config.get("icon", None)
            if icon is not None:
                self.icon = Image.open(icon)

        pass

    def __str__(self):
        return """Channel: {channel}
Enabled: {enabled}
Alarm level: {alarm_level}
Auto water: {auto_water}
Water level: {water_level}
Pump speed: {pump_speed}
Pump time: {pump_time}
Delay: {watering_delay}
Wet point: {wet_point}
Dry point: {dry_point}
""".format(
            **self.__dict__
        )

    def water(self):
        if not self.auto_water:
            return False
        if time.time() - self.last_dose > self.watering_delay:
            self.pump.dose(self.pump_speed, self.pump_time, blocking=False)
            self.last_dose = time.time()
            return True
        return False

    def render(self, image, font, selected=False):
        draw = ImageDraw.Draw(image)
        x = [21, 61, 101][self.channel - 1]

        # Saturation amounts from each sensor
        c = 1.0 - self.sensor.saturation
        active = self.sensor.active and self.enabled

        if active:
            # Draw background bars
            draw.rectangle(
                (x, int(c * HEIGHT), x + 37, HEIGHT),
                self.indicator_color(c) if active else (229, 229, 229),
            )

        # Draw plant image
        x -= 3
        y = HEIGHT - self.icon.height
        pl = self.icon
        if not active:
            pl = pl.convert("LA").convert("RGB")
        image.paste(pl, (x, y), mask=self.icon)

        # Channel selection icons
        x += 15
        draw.rectangle(
            (x, 2, x + 15, 17),
            self.indicator_color(c, self.label_colours) if active else (129, 129, 129),
        )

        if selected:
            selected_x = x - 2
            draw.rectangle(
                (selected_x, 0, selected_x + 19, 20),
                self.indicator_color(c, self.label_colours)
                if active
                else (129, 129, 129),
            )

            # TODO: replace with graphic, since PIL has no anti-aliasing
            draw.polygon(
                [(selected_x, 20), (selected_x + 9, 25), (selected_x + 19, 20)],
                fill=self.indicator_color(c, self.label_colours)
                if active
                else (129, 129, 129),
            )

        # TODO: replace number text with graphic

        tw, th = font.getsize("{}".format(self.channel))
        draw.text(
            (x + int(math.ceil(8 - (tw / 2.0))), 2),
            "{}".format(self.channel),
            font=font,
            fill=(255, 255, 255),
        )

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
            if sat < self.alarm_level and not self.alarm:
                logging.warning(
                    "Alarm on Channel: {} - saturation is {:.2f} (warn level {:.2f})".format(
                        self.channel, sat, self.alarm_level
                    )
                )
                self.alarm = True


BUTTONS = [5, 6, 16, 24]
LABELS = ["A", "B", "X", "Y"]

channel_selected = 0
alarm = False

plants = []

# Load all of the plant icons
for x in range(1, 15):
    plants.append(Image.open("icons/flat-{}.png".format(x)))

# Pick a random selection of plant icons to display on screen
channels = [
    Channel(1, 1, 1, icon=random.choice(plants)),
    Channel(2, 2, 2, icon=random.choice(plants)),
    Channel(3, 3, 3, icon=random.choice(plants)),
]

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


def handle_button(pin):
    global channel_selected, alarm
    index = BUTTONS.index(pin)
    label = LABELS[index]

    if label == "A":  # Select Channel
        channel_selected += 1
        channel_selected %= len(channels)

    if label == "B":  # Cancel Alarm
        alarm = False
        for channel in channels:
            channel.alarm = False

    if label == "X":  # Set Wet Point
        channels[channel_selected].sensor.set_wet_point()

    if label == "Y":  # Set Dry Point
        channels[channel_selected].sensor.set_dry_point()


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for pin in BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=150)


# Only the ALPHA channel is used from these images
icon_drop = Image.open("icons/icon-drop.png")
icon_nodrop = Image.open("icons/icon-nodrop.png")
icon_rightarrow = Image.open("icons/icon-rightarrow.png")
icon_snooze = Image.open("icons/icon-snooze.png")

CHANNEL_W = 40
CHANNEL_M = 2

# Set up the ST7735 SPI Display
display = ST7735.ST7735(
    port=0, cs=1, dc=9, backlight=12, rotation=270, spi_speed_hz=80000000
)
display.begin()
WIDTH, HEIGHT = display.width, display.height

# Set up our canvas and prepare for drawing
image = Image.new("RGBA", (WIDTH, HEIGHT), color=(255, 255, 255))
font = ImageFont.truetype(UserFont, 14)
draw = ImageDraw.Draw(image)


def icon(image, icon, position, color):
    col = Image.new("RGBA", (20, 20), color=color)
    image.paste(col, position, mask=icon)


def update():
    global alarm

    for channel in channels:
        channel.update()
        if channel.alarm:
            alarm = True


def render():
    t = time.time()

    # Icon backdrops
    draw.rectangle((0, 0, 19, 19), (32, 138, 251))
    draw.rectangle((0, HEIGHT - 19, 19, HEIGHT), (255, 255, 255))
    draw.rectangle((WIDTH - 20, 0, WIDTH, 19), (75, 166, 252))
    draw.rectangle((WIDTH - 20, HEIGHT - 19, WIDTH, HEIGHT), (254, 218, 80))

    # Icons
    icon(image, icon_rightarrow, (0, 0), (255, 255, 255))
    icon(image, icon_drop, (WIDTH - 20, 0), (255, 255, 255))
    icon(image, icon_nodrop, (WIDTH - 20, HEIGHT - 20), (255, 255, 255))

    draw.rectangle((21, 0, 138, HEIGHT), (255, 255, 255))  # Erase channel area

    for channel in channels:
        channel.render(image, font, channel_selected == channel.channel - 1)

    # Draw the snooze icon- will be pulsing red if the alarm state is True
    r = 129
    if alarm:
        r = int(((math.sin(t * 3 * math.pi) + 1.0) / 2.0) * 255)
    icon(image, icon_snooze, (0, HEIGHT - 20), (r, 129, 129))


def main():
    alarm_enable = True
    alarm_interval = 10.0
    piezo = Piezo()
    time_last_beep = time.time()

    settings_file = "settings.yml"
    if len(sys.argv) > 1:
        settings_file = sys.argv[1]
    settings_file = pathlib.Path(settings_file)
    if settings_file.is_file():
        try:
            config = yaml.safe_load(open(settings_file))
        except yaml.parser.ParserError as e:
            raise yaml.parser.ParserError(
                "Error parsing settings file: {} ({})".format(settings_file, e)
            )

        for channel in channels:
            ch = config.get("channel{}".format(channel.channel), None)
            channel.update_from_yml(ch)

        settings = config.get("general", None)
        if settings is not None:
            alarm_enable = settings.get("alarm_enable", alarm_enable)
            alarm_interval = settings.get("alarm_interval", alarm_interval)

    print("Channels:")
    for channel in channels:
        print(channel)

    print(
        """Settings:
Alarm Enabled: {}
Alarm Interval: {:.2f}s
""".format(
            alarm_enable, alarm_interval
        )
    )

    while True:
        update()
        render()
        display.display(image.convert("RGB"))

        #w, h = image.size
        #image.convert("RGB").resize((w * 4, h * 4), Image.NEAREST).save("display.png")
        #break

        if alarm_enable and alarm and time.time() - time_last_beep > alarm_interval:
            piezo.beep(440, 0.1, blocking=False)
            threading.Timer(0.3, piezo.beep, args=[440, 0.1], kwargs={"blocking":False}).start()
            threading.Timer(0.6, piezo.beep, args=[440, 0.1], kwargs={"blocking":False}).start()
            time_last_beep = time.time()

        # 5 FPS
        time.sleep(1.0 / 10)


if __name__ == "__main__":
    main()
