import time
import RPi.GPIO as GPIO

from PIL import Image, ImageDraw, ImageFont
from fonts.ttf import RobotoMedium as UserFont

import ST7735
from grow.moisture import Moisture
from grow.pump import Pump

# Default watering settings
dry_level = 0.7    # Saturation level considered dry
dose_speed = 0.63  # Pump speed for water dose
dose_time = 0.96   # Time (in seconds) for water dose


p = Pump(3)
m = Moisture(3)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

NUM_SAMPLES = 10

BUTTONS = [5, 6, 16, 24]
LABELS = ['A', 'B', 'X', 'Y']

GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

mode = 0

font = ImageFont.truetype(UserFont, 14)

display = ST7735.ST7735(
    port=0,
    cs=1,
    dc=9,
    backlight=12,
    rotation=270,
    spi_speed_hz=80000000
)

display.begin()

image = Image.new("RGBA", (display.width, display.height), color=(0, 0, 0))
draw = ImageDraw.Draw(image)


def handle_button(pin):
    global mode, dose_time, dose_speed, dry_level
    index = BUTTONS.index(pin)
    label = LABELS[index]
    if label == 'A':
        p.dose(dose_speed, dose_time, blocking=False)
    if label == 'B':
        mode += 1
        mode %= 2
    if label == 'Y':
        if mode == 0:
            dose_time += 0.01
        elif mode == 1:
            dose_speed += 0.01
        elif mode == 2:
            dry_level += 0.01
    if label == 'X':
        if mode == 0:
            dose_time -= 0.01
        elif mode == 1:
            dose_speed -= 0.01
        elif mode == 2:
            dry_level -= 0.01
    print("Button {} pressed! Dose time: {} Dose speed: {} Dry level: {}".format(label, dose_time, dose_speed, dry_level))


for pin in BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=150)

saturation = [1.0 for _ in range(NUM_SAMPLES)]

try:
    while True:
        s = m.saturation
        print(time.time(), s)
        saturation.append(s)
        saturation = saturation[-NUM_SAMPLES:]
        current = sum(saturation) / float(NUM_SAMPLES)
        if current < dry_level:
            p.dose(dose_speed, dose_time)
            print("Auto dosing. Saturation: {}".format(current))
            time.sleep(2.0)
        draw.rectangle((0, 0, display.width, display.height), (0, 0, 0))

        draw.text((10, 0), "Sat: {} AVG: {}".format(s, current), font=font, fill=(255, 255, 255))

        draw.text((10, 16), "Time: {:.2f}".format(dose_time), font=font, fill=(255, 255, 255))
        draw.text((10, 32), "Speed: {:.2f}".format(dose_speed), font=font, fill=(255, 255, 255))
        draw.text((10, 48), "Dry: {:.2f}".format(dry_level), font=font, fill=(255, 255, 255))

        draw.text((0, 16 + (16 * mode)), ">", font=font, fill=(255, 255, 255))

        display.display(image)
        time.sleep(1.0)

except KeyboardInterrupt:
    print("Dose Time: {} Dose Speed: {}, Dry Level: {}".format(dose_time, dose_speed, dry_level))
