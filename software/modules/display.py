import displayio
from adafruit_bitmap_font import bitmap_font
import busio
import board
import os
import adafruit_displayio_sh1106
from adafruit_display_text import label
import modules.utilities

DISPLAY_WIDTH = 133
DISPLAY_HEIGHT = 64

# Font
FONT = bitmap_font.load_font("fonts/cozette.pcf")

# Display
displayio.release_displays()
DISPLAY_I2C = busio.I2C(board.GP27, board.GP26, frequency=400000)
DISPLAY_BUS = displayio.I2CDisplay(DISPLAY_I2C, device_address=0x3c)
DISPLAY_ORIENTATION = os.getenv('display_orientation')
ROTATION = 0 if DISPLAY_ORIENTATION == 'normal' else 180
DISPLAY = adafruit_displayio_sh1106.SH1106(
    DISPLAY_BUS, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, rotation=ROTATION)

# Display context
SCREEN = displayio.Group()
DISPLAY.show(SCREEN)
COLOR_BITMAP = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
COLOR_PALETTE = displayio.Palette(1)
COLOR_PALETTE[0] = 0x000000
BG_SPRITE = displayio.TileGrid(
    COLOR_BITMAP, pixel_shader=COLOR_PALETTE, x=0, y=0)
SCREEN.append(BG_SPRITE)

# Text areas
modules.globals.CONTENT_1_AREA = label.Label(
    FONT, text="", color=0xFFFFFF, x=5, y=5)
modules.globals.CONTENT_2_AREA = label.Label(
    FONT, text="", color=0xFFFFFF, x=5, y=19)
modules.globals.CONTENT_3_AREA = label.Label(
    FONT, text="", color=0xFFFFFF, x=5, y=34)
modules.globals.CONTENT_4_AREA = label.Label(
    FONT, text="", color=0xFFFFFF, x=5, y=41)
modules.globals.CONTENT_5_AREA = label.Label(
    FONT, text="", color=0xFFFFFF, x=5, y=56)
modules.globals.MENU_LEFT_AREA = label.Label(
    FONT, text="", color=0xFFFFFF, x=114, y=56)
modules.globals.MENU_RIGHT_AREA = label.Label(
    FONT, text="", color=0xFFFFFF, x=123, y=56)
SCREEN.append(modules.globals.CONTENT_1_AREA)
SCREEN.append(modules.globals.CONTENT_2_AREA)
SCREEN.append(modules.globals.CONTENT_3_AREA)
SCREEN.append(modules.globals.CONTENT_4_AREA)
SCREEN.append(modules.globals.CONTENT_5_AREA)
SCREEN.append(modules.globals.MENU_LEFT_AREA)
SCREEN.append(modules.globals.MENU_RIGHT_AREA)


def display_screen(menu_on, manual_on, screen_index):
    modules.globals.CONTENT_1_AREA.text = ""
    modules.globals.CONTENT_2_AREA.text = ""
    modules.globals.CONTENT_3_AREA.text = ""
    modules.globals.CONTENT_4_AREA.text = ""
    modules.globals.CONTENT_5_AREA.text = ""
    modules.globals.MENU_LEFT_AREA.text = ""
    modules.globals.MENU_RIGHT_AREA.text = ""

    if not menu_on:
        # Introduction
        if screen_index == 0:
            modules.globals.CONTENT_1_AREA.text = "Hey! Let's ferment."
            modules.globals.CONTENT_5_AREA.text = "⚙ ⚙ ⚙"
        elif screen_index == 1:
            # Select mode
            modules.globals.CONTENT_1_AREA.text = "Choose a mode for"
            modules.globals.CONTENT_2_AREA.text = "your fermentation"
            modules.globals.CONTENT_5_AREA.text = modules.globals.modes[modules.globals.modes_index][0]
            modules.globals.CONTENT_5_AREA.color = 0x000000
            modules.globals.CONTENT_5_AREA.background_color = 0xFFFFFF
            modules.globals.MENU_LEFT_AREA.text = "↓"
            modules.globals.MENU_RIGHT_AREA.text = "↑"
        elif screen_index == 2:
            temp_target = os.getenv('target_temperature')
            modules.globals.CONTENT_1_AREA.text = " What's the ideal"
            modules.globals.CONTENT_2_AREA.text = "temperature for you"
            modules.globals.CONTENT_3_AREA.text = "fermentation?"
            modules.globals.CONTENT_5_AREA.text = "{} C".format(
                modules.utilities.round_down(modules.globals.temp_target, 1))
            modules.globals.CONTENT_5_AREA.color = 0x000000
            modules.globals.CONTENT_5_AREA.background_color = 0xFFFFFF
            modules.globals.MENU_LEFT_AREA.text = "↓"
            modules.globals.MENU_RIGHT_AREA.text = "↑"
        elif screen_index == 3:
            timer_hours = os.getenv('timer_hours')
            modules.globals.CONTENT_1_AREA.text = " For how long do"
            modules.globals.CONTENT_2_AREA.text = "you want to ferment?"
            modules.globals.CONTENT_5_AREA.text = modules.utilities.timer_unit(
                int(modules.globals.timer_hours))
            modules.globals.CONTENT_5_AREA.color = 0x000000
            modules.globals.CONTENT_5_AREA.background_color = 0xFFFFFF
            modules.globals.MENU_LEFT_AREA.text = "↓"
            modules.globals.MENU_RIGHT_AREA.text = "↑"
        elif screen_index == 4:
            modules.globals.CONTENT_1_AREA.text = "It's all set."
            modules.globals.CONTENT_2_AREA.text = "Remember to check me"
            modules.globals.CONTENT_3_AREA.text = "every now and then."
            modules.globals.CONTENT_5_AREA.text = "☺"

    if menu_on:
        # Menu
        modules.globals.MENU_LEFT_AREA.text = ""
        modules.globals.MENU_RIGHT_AREA.text = "→"
        modules.globals.CONTENT_5_AREA.color = 0xFFFFFF
        modules.globals.CONTENT_5_AREA.background_color = 0x000000
        if screen_index == 0:
            modules.heating_system.update_status_sentence()
            modules.heating_system.update_values()
        elif screen_index == 1:
            modules.globals.CONTENT_1_AREA.text = " Set: Temperature"
            modules.globals.CONTENT_5_AREA.text = "{} C".format(modules.utilities.round_down(modules.globals.temp_target, 1))
        elif screen_index == 2:
            modules.globals.CONTENT_1_AREA.text = " Set: Timer"
            modules.globals.CONTENT_5_AREA.text = modules.utilities.timer_unit(int(modules.globals.timer_hours))
        elif screen_index == 3:
            modules.globals.CONTENT_1_AREA.text = "Fermenting in mode"
            modules.globals.CONTENT_2_AREA.text = "↳ {}".format(modules.globals.modes[modules.globals.modes_index][0])
            modules.globals.CONTENT_3_AREA.text = "Want to change?"
            modules.globals.CONTENT_5_AREA.text = modules.globals.bool_string
        elif screen_index == 4:
            modules.globals.CONTENT_1_AREA.text = "Domingo Fermenter"
            modules.globals.CONTENT_2_AREA.text = modules.globals.SOFTWARE_VERSION
            modules.globals.CONTENT_3_AREA.text = "domingoclub.com"
            modules.globals.CONTENT_5_AREA.text = "⚙ ⚙ ⚙"
