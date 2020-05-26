import time
import ST7735
import random
import math
import logging
from PIL import Image, ImageDraw, ImageFont
from fonts.ttf import RobotoMedium as UserFont
import RPi.GPIO as GPIO

from grow.moisture import Moisture
from grow.pump import Pump

# Level at which a watering event is triggered
trigger_level = [
    0.5,
    0.5,
    0.5
]

# Level at which the alarm is sounded (watering has failed?)
alarm_level = [
    0.2,
    0.2,
    0.2
]

# Dose settings: Pump Speed, and Dose Time
dose_settings = [
    (0.7, 0.7),
    (0.7, 0.7),
    (0.7, 0.7)
]

BUTTONS = [5, 6, 16, 24]
LABELS = ['A', 'B', 'X', 'Y']
CHANNEL_COUNT = 3

channel_selected = 0
alarm = False

sensors = [
    Moisture(channel=1),
    Moisture(channel=2),
    Moisture(channel=3)
]

pumps = [
    Pump(channel=1),
    Pump(channel=2),
    Pump(channel=3)
]

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


def handle_button(pin):
    global channel_selected, alarm
    index = BUTTONS.index(pin)
    label = LABELS[index]
    if label == 'A':  # Select Channel
        channel_selected += 1
        channel_selected %= CHANNEL_COUNT
    if label == 'B':  # Cancel Alarm
        alarm = False
    if label == 'X':  # Set Wet Point
        pass
    if label == 'Y':  # Set Dry Point
        pass
    print("Button {} pressed! Channel: {}".format(label, channel_selected))


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for pin in BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=150)


bar_colours = [
    (192, 225, 254),  # Blue
    (196, 255, 209),  # Green
    (255, 243, 192),  # Yellow
    (254, 192, 192)   # Red
]

label_colours = [
    (32, 137, 251),   # Blue
    (100, 255, 124),  # Green
    (254, 219, 82),   # Yellow
    (254, 82, 82),    # Red
]

# Only the ALPHA channel is used from these images
icon_drop = Image.open("icons/icon-drop.png")
icon_nodrop = Image.open("icons/icon-nodrop.png")
icon_rightarrow = Image.open("icons/icon-rightarrow.png")
icon_snooze = Image.open("icons/icon-snooze.png")

plants = []

# Load all of the plant icons
for x in range(1, 15):
    plants.append(Image.open("icons/flat-{}.png".format(x)))

# Pick a random selection of plant icons to display on screen
# TODO: Make this the default, but allow override in settings
picked = random.sample(plants, 3)

CHANNEL_W = 40
CHANNEL_M = 2

# Set up the ST7735 SPI Display
display = ST7735.ST7735(
    port=0,
    cs=1,
    dc=9,
    backlight=12,
    rotation=270,
    spi_speed_hz=80000000
)
display.begin()
WIDTH, HEIGHT = display.width, display.height

# Set up our canvas and prepare for drawing
image = Image.new("RGBA", (WIDTH, HEIGHT), color=(255, 255, 255))
font = ImageFont.truetype(UserFont, 14)
draw = ImageDraw.Draw(image)


def indicator_color(value, r=None):
    if r is None:
        r = bar_colours
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


def icon(image, icon, position, color):
    col = Image.new("RGBA", (20, 20), color=color)
    image.paste(col, position, mask=icon)


def plant(image, plant, channel, available=True):
    x = [18, 58, 98][channel]
    y = HEIGHT - plant.height
    mask = plant
    if not available:
        plant = plant.convert('LA').convert('RGB')
    image.paste(plant, (x, y), mask=mask)


def update():
    pass


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

    # Draw the snooze icon- will be pulsing red if the alarm state is True
    r = 129
    if alarm:
        r = int(((math.sin(t * 3 * math.pi) + 1.0) / 2.0) * 255)
    icon(image, icon_snooze, (0, HEIGHT - 20), (r, 129, 129))

    # Saturation amounts from each sensor
    c1 = 1.0 - sensors[0].saturation
    c2 = 1.0 - sensors[1].saturation
    c3 = 1.0 - sensors[2].saturation

    # Channel presence detection
    # TODO: Implement presence detection that doesn't trigger on random noise!
    ca1 = sensors[0].moisture > 0
    ca2 = sensors[1].moisture > 0
    ca3 = sensors[2].moisture > 0

    draw.rectangle((21, 0, 138, HEIGHT), (255, 255, 255))  # Erase channel area

    # Draw background bars
    draw.rectangle((21, int(c1 * HEIGHT), 58, HEIGHT), indicator_color(c1) if ca1 else (229, 229, 229))
    draw.rectangle((61, int(c2 * HEIGHT), 98, HEIGHT), indicator_color(c2) if ca2 else (229, 229, 229))
    draw.rectangle((101, int(c3 * HEIGHT), 138, HEIGHT), indicator_color(c3) if ca3 else (229, 229, 229))

    # Draw plant images
    for p in range(3):
        plant(image, picked[p], p, [ca1, ca2, ca3][p])

    # Channel selection icons
    draw.rectangle((33, 2, 48, 17), indicator_color(c1, label_colours) if ca1 else (129, 129, 129))
    draw.rectangle((33 + 40, 2, 48 + 40, 17), indicator_color(c2, label_colours) if ca2 else (129, 129, 129))
    draw.rectangle((33 + 80, 2, 48 + 80, 17), indicator_color(c3, label_colours) if ca3 else (129, 129, 129))

    selected_x = 21 + (40 * channel_selected) + 10
    draw.rectangle((selected_x, 0, selected_x + 19, 20), indicator_color([c1, c2, c3][channel_selected], label_colours) if [ca1, ca2, ca3][channel_selected] else (129, 129, 129))

    # TODO: replace with graphic, since PIL has no anti-aliasing
    draw.polygon([
        (selected_x, 20),
        (selected_x + 9, 25),
        (selected_x + 19, 20)
        ],
        fill=indicator_color([c1, c2, c3][channel_selected], label_colours) if [ca1, ca2, ca3][channel_selected] else (129, 129, 129))

    # TODO: replace number text with graphic
    draw.text((33 + 3, 2), "1", font=font, fill=(255, 255, 255))
    draw.text((33 + 40 + 4, 2), "2", font=font, fill=(255, 255, 255))
    draw.text((33 + 80 + 4, 2), "3", font=font, fill=(255, 255, 255))


def main():
    while True:
        update()
        render()
        display.display(image.convert("RGB"))

        # 5 FPS
        time.sleep(1.0 / 5)


if __name__ == "__main__":
    main()
