import time
import logging
import RPi.GPIO as GPIO

from PIL import Image, ImageDraw, ImageFont
from fonts.ttf import RobotoMedium as UserFont

import ST7735
from grow.moisture import Moisture
from grow.pump import Pump


"""
Auto water a single target with the channel/pump selected below.

This example is useful for calibrating watering settings and will give you a good idea
what speed/time you need to run your pump for in order to deliver a thorough watering.

The buttons allow you to find tune and test the pump settings.

A = Test settings
B = Select setting to change
X = Decrease value
Y = Increase value
"""

# Channel settings
pump_channel = 3
moisture_channel = 3

# Default watering settings
dry_level = 0.7  # Saturation level considered dry
dose_speed = 0.63  # Pump speed for water dose
dose_time = 0.96  # Time (in seconds) for water dose

# Here be dragons!
FPS = 15  # Display framerate
NUM_SAMPLES = 10  # Number of saturation level samples to average over
DOSE_FREQUENCY = 30.0  # Minimum time between automatic waterings (in seconds)

BUTTONS = [5, 6, 16, 24]
LABELS = ["A", "B", "X", "Y"]

p = Pump(pump_channel)
m = Moisture(moisture_channel)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

mode = 0
last_dose = time.time()
saturation = [1.0 for _ in range(NUM_SAMPLES)]

display = ST7735.ST7735(
    port=0, cs=1, dc=9, backlight=12, rotation=270, spi_speed_hz=80000000
)

display.begin()

font = ImageFont.truetype(UserFont, 12)
image = Image.new("RGBA", (display.width, display.height), color=(0, 0, 0))
draw = ImageDraw.Draw(image)

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


def handle_button(pin):
    global mode, last_dose, dose_time, dose_speed, dry_level
    index = BUTTONS.index(pin)
    label = LABELS[index]
    if label == "A":  # Test
        logging.info("Manual watering triggered.")
        p.dose(dose_speed, dose_time, blocking=False)
        last_dose = time.time()

    if label == "B":  # Switch setting
        mode += 1
        mode %= 3  # Wrap 0, 1, 2 (Time, Speed, Dry level)

    if label == "Y":  # Inc. setting
        if mode == 0:
            dose_time += 0.01
            logging.info("Dose time increased to: {:.2f}".format(dose_time))
        elif mode == 1:
            dose_speed += 0.01
            logging.info("Dose speed increased to: {:.2f}".format(dose_speed))
        elif mode == 2:
            dry_level += 0.01
            logging.info("Dry level increased to: {:.2f}".format(dry_level))

    if label == "X":  # Dec. setting
        if mode == 0:
            dose_time -= 0.01
            logging.info("Dose time decreased to: {:.2f}".format(dose_time))
        elif mode == 1:
            dose_speed -= 0.01
            logging.info("Dose speed decreased to: {:.2f}".format(dose_speed))
        elif mode == 2:
            dry_level -= 0.01
            logging.info("Dry level decreased to: {:.2f}".format(dry_level))


# Bind the button handler (above) to all buttons
for pin in BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=150)


current_saturation = 0

try:
    while True:
        # New moisture readings are available approximately 1/sec
        # push them into the list for averagering
        if m.new_data:
            current_saturation = m.saturation
            saturation.append(current_saturation)
            saturation = saturation[-NUM_SAMPLES:]

        avg_saturation = sum(saturation) / float(NUM_SAMPLES)

        # Trigger a dose of water if the average saturation is less than the specified dry level
        # dose frequency is rate limited, so this doesn't re-trigger before the moistrure sensor
        # has had the opportunity to catch up.
        if avg_saturation < dry_level and (time.time() - last_dose) > DOSE_FREQUENCY:
            p.dose(dose_speed, dose_time)
            logging.info(
                "Auto watering. Saturation: {:.2f} (Dry: {:.2f})".format(
                    avg_saturation, dry_level
                )
            )
            last_dose = time.time()

        draw.rectangle((0, 0, display.width, display.height), (0, 0, 0))

        # Current and average saturation
        draw.text(
            (5 + display.width // 2, 16),
            "Sat: {:.3f}".format(current_saturation),
            font=font,
            fill=(255, 255, 255),
        )
        draw.text(
            (5 + display.width // 2, 32),
            "AVG: {:.3f}".format(avg_saturation),
            font=font,
            fill=(255, 255, 255),
        )

        # Selected setting box
        draw.rectangle(
            (0, 16 + (16 * mode), display.width // 2, 31 + (16 * mode)), (30, 30, 30)
        )

        draw.text(
            (5, 16),
            "Time: {:.2f}".format(dose_time),
            font=font,
            fill=(255, 255, 255) if mode == 0 else (128, 128, 128),
        )
        draw.text(
            (5, 32),
            "Speed: {:.2f}".format(dose_speed),
            font=font,
            fill=(255, 255, 255) if mode == 1 else (128, 128, 128),
        )
        draw.text(
            (5, 48),
            "Dry lvl: {:.2f}".format(dry_level),
            font=font,
            fill=(255, 255, 255) if mode == 2 else (128, 128, 128),
        )

        # Button lavel backgrounds
        draw.rectangle((0, 0, 42, 14), (255, 255, 255))
        draw.rectangle((display.width - 15, 0, display.width, 14), (255, 255, 255))
        draw.rectangle(
            (display.width - 15, display.height - 14, display.width, display.height),
            (255, 255, 255),
        )
        draw.rectangle((0, display.height - 14, 42, display.height), (255, 255, 255))

        # Button labels
        draw.text((5, 0), "test", font=font, fill=(0, 0, 0))
        draw.text((5, display.height - 16), "next", font=font, fill=(0, 0, 0))
        draw.text((display.width - 10, 0), "-", font=font, fill=(0, 0, 0))
        draw.text(
            (display.width - 12, display.height - 15), "+", font=font, fill=(0, 0, 0)
        )

        display.display(image)
        time.sleep(1.0 / FPS)

except KeyboardInterrupt:
    print(
        "Dose Time: {:.2f} Dose Speed: {:.2f}, Dry Level: {:.2f}".format(
            dose_time, dose_speed, dry_level
        )
    )
