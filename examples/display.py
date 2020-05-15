import time
import ST7735
import random
import math
from PIL import Image, ImageDraw, ImageFont
from fonts.ttf import RobotoMedium as UserFont
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

BUTTONS = [5, 6, 16, 24]
LABELS = ['A', 'B', 'X', 'Y']

channel_count = 3
channel_selected = 0

GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

font = ImageFont.truetype(UserFont, 14)

def handle_button(pin):
    global channel_selected
    index = BUTTONS.index(pin)
    label = LABELS[index]
    if label == 'A':
        channel_selected += 1
        channel_selected %= channel_count
    print("Button {} pressed! Channel: {}".format(label, channel_selected))

for pin in BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=150)

display = ST7735.ST7735(
    port=0,
    cs=1,
    dc=9,
    backlight=12,
    rotation=270,
    spi_speed_hz=10000000
)

ramp = [
    (192, 225, 254),  # Blue
    (196, 255, 209),  # Green
    (255, 243, 192),  # Yellow
    (254, 192, 192)   # Red
]

ramp_sat = [
    (32, 137, 251),   # Blue
    (100, 255, 124),  # Green
    (254, 219, 82),   # Yellow
    (254, 82, 82),    # Red
]


def indicator_color(value, r=None):
    if r is None:
        r = ramp
    value *= len(r) - 1
    a = int(math.floor(value))
    b = a + 1
    blend = float(value - a)

    r, g, b = [int(((r[b][i] - r[a][i]) * blend) + r[a][i]) for i in range(3)]

    return (r, g, b)


display.begin()

WIDTH, HEIGHT = display.width, display.height

# Only the ALPHA channel is used from these images
icon_drop = Image.open("icons/icon-drop.png")
icon_nodrop = Image.open("icons/icon-nodrop.png")
icon_rightarrow = Image.open("icons/icon-rightarrow.png")
icon_snooze = Image.open("icons/icon-snooze.png")

plants = []

for x in range(1, 15):
    plants.append(Image.open("icons/flat-{}.png".format(x)))

CHANNEL_W = 40
CHANNEL_M = 2

print(WIDTH, HEIGHT)

image = Image.new("RGBA", (WIDTH, HEIGHT), color=(255, 255, 255))
draw = ImageDraw.Draw(image)

draw.rectangle((0, 0, 19, 19), (32, 138, 251))
draw.rectangle((0, HEIGHT - 19, 19, HEIGHT), (255, 255, 255))
draw.rectangle((WIDTH - 20, 0, WIDTH, 19), (75, 166, 252))
draw.rectangle((WIDTH - 20, HEIGHT - 19, WIDTH, HEIGHT), (254, 218, 80))

def icon(image, icon, position, color):
    col = Image.new("RGBA", (20, 20), color=color)
    image.paste(col, position, mask=icon)

icon(image, icon_rightarrow, (0, 0), (255, 255, 255))
icon(image, icon_snooze, (0, HEIGHT - 20), (129, 129, 129))
icon(image, icon_drop, (WIDTH - 20, 0), (255, 255, 255))
icon(image, icon_nodrop, (WIDTH - 20, HEIGHT - 20), (255, 255, 255))

def plant(image, plant, channel):
    x = [18, 58, 98][channel]
    y = HEIGHT - plant.height
    image.paste(plant, (x, y), mask=plant)

picked = random.sample(plants, 3)

# image.save("test.png")

while True:
    t = time.time() / 10.0
    c1 = (math.sin(math.pi + t * math.pi) + 1.0) / 2.0
    c2 = (math.sin(t * math.pi) + 1.0) / 2.0
    c3 = (math.sin(math.pi + t * math.pi) + 1.0) / 2.0

    draw.rectangle((21, 0, 138, HEIGHT), (255, 255, 255))  # Erase channel area

    # Draw background bars
    draw.rectangle((21, int(c1 * HEIGHT), 58, HEIGHT), indicator_color(c1))
    draw.rectangle((61, int(c2 * HEIGHT), 98, HEIGHT), indicator_color(c2))
    draw.rectangle((101, int(c3 * HEIGHT), 138, HEIGHT), indicator_color(c3))

    # Draw plant images
    for p in range(3):
        plant(image, picked[p], p)

    # Channel selection icons
    draw.rectangle((33, 2, 48, 17), indicator_color(c1, ramp_sat))
    draw.rectangle((33 + 40, 2, 48 + 40, 17), indicator_color(c2, ramp_sat))
    draw.rectangle((33 + 80, 2, 48 + 80, 17), indicator_color(c3, ramp_sat))

    selected_x = 21 + (40 * channel_selected) + 10
    draw.rectangle((selected_x, 0, selected_x + 19, 20), indicator_color([c1, c2, c3][channel_selected], ramp_sat))

    draw.polygon([
        (selected_x, 20),
        (selected_x + 9, 25),
        (selected_x + 19, 20)
    ],
    fill=indicator_color([c1, c2, c3][channel_selected], ramp_sat))

    draw.text((33 + 3, 2), "1", font=font, fill=(255, 255, 255))
    draw.text((33 + 40 + 4, 2), "2", font=font, fill=(255, 255, 255))
    draw.text((33 + 80 + 4, 2), "3", font=font, fill=(255, 255, 255))

    # Erase snooze icon
    draw.rectangle((0, HEIGHT - 19, 19, HEIGHT), (255, 255, 255))
    r = int(((math.sin(time.time() * 3 * math.pi) + 1.0) / 2.0) * 255)
    icon(image, icon_snooze, (0, HEIGHT - 20), (r, 129, 129))

    display.display(image.convert("RGB"))
    time.sleep(1.0 / 30)
