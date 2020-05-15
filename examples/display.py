import time
import ST7735
import random
from PIL import Image, ImageDraw, ImageFont

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
    (255, 243, 192)   # Yellow
]

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

draw.rectangle((21, 0, 58, HEIGHT), ramp[0])
draw.rectangle((61, 0, 98, HEIGHT), ramp[1])
draw.rectangle((101, 0, 138, HEIGHT), ramp[2])

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

for p in range(3):
    plant(image, picked[p], p)

image.save("test.png")

while True:
    display.display(image.convert("RGB"))
    time.sleep(1.0)
