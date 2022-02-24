import board
import busio
import time
import displayio
import terminalio
import rotaryio
from digitalio import DigitalInOut, Direction, Pull
import adafruit_mcp9808
import adafruit_displayio_sh1106
from adafruit_display_text import label
import adafruit_rgbled

# Variables
TEMP_SET = 30
TEMP_MARGIN = 1
fan_on = False
heat_on = False
temp = 0.0
temp_set = 30.0
timer_set = 30.0
current_screen = "temp_display"

# Sensor
sensor_i2c = busio.I2C(board.GP13, board.GP12)
sensor = adafruit_mcp9808.MCP9808(sensor_i2c)

# Led
RED_LED = board.GP22
GREEN_LED = board.GP21
BLUE_LED = board.GP20
led = adafruit_rgbled.RGBLED(RED_LED, GREEN_LED, BLUE_LED, invert_pwm=True)

# Button
BTN = DigitalInOut(board.GP2)
BTN.direction = Direction.INPUT
BTN.pull = Pull.UP
btn_down = False

# Encoder
encoder = rotaryio.IncrementalEncoder(board.GP4, board.GP3)
last_position = 0

# Display
WIDTH = 130
HEIGHT = 64
displayio.release_displays()
display_i2c = busio.I2C(board.GP27, board.GP26, frequency=400000)
display_bus = displayio.I2CDisplay(display_i2c, device_address=0x3c)
display = adafruit_displayio_sh1106.SH1106(display_bus, width=WIDTH, height=HEIGHT)

# Display context
screen = displayio.Group()
display.show(screen)
color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000  # black
bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
screen.append(bg_sprite)

# Text
label_area = label.Label(terminalio.FONT, text=" "*20, color=0xFFFFFF, x=5, y=5)
value_area = label.Label(terminalio.FONT, text=" "*20, color=0xFFFFFF, x=48, y=32)
menu_left_area = label.Label(terminalio.FONT, text="<", color=0xFFFFFF, x=5, y=55)
menu_right_area = label.Label(terminalio.FONT, text=">", color=0xFFFFFF, x=123, y=55)
screen.append(label_area)
screen.append(value_area)
screen.append(menu_left_area)
screen.append(menu_right_area)


# Outputs
FAN = DigitalInOut(board.GP6)
FAN.direction = Direction.OUTPUT
HEAT = DigitalInOut(board.GP7)
HEAT.direction = Direction.OUTPUT

def menu_handler(pos):
    global current_screen
    if current_screen == "temp_display" and pos == "next": next_screen = "temp_set"
    if current_screen == "temp_display" and pos == "prev": next_screen = "timer_set"
    if current_screen == "temp_set" and pos == "next": next_screen = "timer_set"
    if current_screen == "temp_set" and pos == "prev": next_screen = "temp_display"
    if current_screen == "timer_set" and pos == "next": next_screen = "temp_display"
    if current_screen == "timer_set" and pos == "prev": next_screen = "temp_set"
    current_screen = next_screen
    display_screen(current_screen)

def display_screen(screen):
    if screen == "temp_display":
        label_area.text = "Temperature"
        update_temp(temp)
    if screen == "temp_set":
        label_area.text = "Set temperature"
        value_area.text = "{} C".format(round(temp_set, 1))
    if screen == "timer_set":
        label_area.text = "Set timer"
        value_area.text = "{} H".format(round(timer_set, 1))

def update_temp(temp):
    tempText = "{} C".format(round(temp, 1))
    value_area.text = tempText


display_screen(current_screen)

while True:
    
    # Temperature
    temp = sensor.temperature
    if current_screen == "temp_display":
        update_temp(temp)

    # Led color
    if temp > 23.5:
        led.color = (0, 30, 0)
    else:
        led.color = (30, 0, 0)

    # Button
    if BTN.value is False and not btn_down:
        print('button pressed')
        btn_down = True
    if BTN.value is True and btn_down:
        btn_down = False

    # Encoder
    position = encoder.position
    if last_position is None or position != last_position:
        if position > last_position:
            menu_handler('prev')
        else:
            menu_handler('next')
    last_position = position

    # time.sleep(0.1)
