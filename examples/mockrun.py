#!/usr/bin/env python

import threading
import tkinter
from PIL import ImageTk, Image
import time

WIDTH = 160 * 4
HEIGHT = 80 * 4

from unittest import mock
import sys
mock_ltr559 = mock.MagicMock()
mock_ltr559.LTR559().get_lux.return_value = 0.0
sys.modules['ltr559'] = mock_ltr559

mock_gpio = mock.MagicMock()
sys.modules['RPi'] = mock.MagicMock()
sys.modules['RPi'].GPIO = mock_gpio
sys.modules['RPi.GPIO'] = mock_gpio


BUTTONS = [5, 6, 16, 24]
LABELS = ["Q", "A", "P", "L"]  # A B X Y on PCB


MOISTURE_1_PIN = 23
MOISTURE_2_PIN = 8
MOISTURE_3_PIN = 25


tk_canvas = None
tk_root = None
running = False
image = None
button_handlers = {}


def update_display(new_image):
    global image
    image = new_image

mock_st7735 = mock.MagicMock()
sys.modules['ST7735'] = mock_st7735


def grab_dem_button_handlers(pin, edge, callback=None, bouncetime=None):
    global button_handlers
    button_handlers[pin] = callback
    print(f"Adding handler for {pin} on edge {edge}")


lib = __import__(sys.argv.pop(1))

def bringup():
    global mock_st7735, mock_gpio
    st7735 = mock_st7735.ST7735(
        port=0, cs=1, dc=9, backlight=12, rotation=270, spi_speed_hz=80000000
    )
    st7735.display = update_display
    mock_gpio.add_event_detect = grab_dem_button_handlers
    lib.main()

t_main = threading.Thread(target=bringup)

def resize_window(event):
    pass

def input_window(event):
    key = event.char
    try:
        i = LABELS.index(key.upper())
    except ValueError:
        return
    pin = BUTTONS[i]
    print(f"You pressed {event.char}, GPIO: {pin}")
    button_handlers[pin](pin)

def close_window():
    global running
    running = False
    print("You gon' have to press Ctrl+C now 'cos the examples use while True")
    sys.exit(0)

tk_root = tkinter.Tk()
tk_root.title("Grow Simulator")
tk_root.geometry(f"{WIDTH}x{HEIGHT}")
tk_root.aspect(2, 1, 2, 1)
tk_root.resizable(False, False)
tk_root.protocol("WM_DELETE_WINDOW", close_window)
tk_root.bind('<KeyPress>', input_window)

def wait_for_window_close():
    global running, tk_canvas, tk_root, image
    running = True

    m1_last = time.time()
    m2_last = time.time()
    m3_last = time.time()

    m1_delay = 1.0 / 15
    m2_delay = 1.0 / 2
    m3_delay = 1.0 / 27

    update_last = time.time()
    update_delay = 1.0 / 10

    while running:
        try:
            if time.time() - m1_last >= m1_delay:
                button_handlers[MOISTURE_1_PIN](MOISTURE_1_PIN)
                m1_last = time.time()
            if time.time() - m2_last >= m2_delay:
                button_handlers[MOISTURE_2_PIN](MOISTURE_2_PIN)
                m2_last = time.time()
            if time.time() - m3_last >= m3_delay:
                button_handlers[MOISTURE_3_PIN](MOISTURE_3_PIN)
                m3_last = time.time()
        except KeyError:
            pass

        if time.time() - update_last < update_delay:
            continue

        update_last = time.time()

        if image is not None:
            if tk_canvas is None:
                tk_canvas = tkinter.Canvas(tk_root, width=WIDTH, height=HEIGHT)
            tk_photo = ImageTk.PhotoImage(image.copy().resize((WIDTH, HEIGHT), Image.NEAREST))
            tk_canvas.pack(side='top', fill='both', expand='yes')
            tk_image = tk_canvas.create_image(0, 0, image=tk_photo, anchor='nw')
            tk_canvas.bind('<Configure>', resize_window)
            tk_root.update()

        tk_root.update_idletasks()
        tk_root.update()

t_main.start()
wait_for_window_close()
