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


# Sensor
sensor_i2c = busio.I2C(board.GP13, board.GP12)
sensor = adafruit_mcp9808.MCP9808(sensor_i2c)

# Display
WIDTH = 130
HEIGHT = 64
BORDER = 5
displayio.release_displays()
display_i2c = busio.I2C(board.GP27, board.GP26, frequency=400000)
display_bus = displayio.I2CDisplay(display_i2c, device_address=0x3c)
display = adafruit_displayio_sh1106.SH1106(display_bus, width=WIDTH, height=HEIGHT)

# Led
RED_LED = board.GP22
GREEN_LED = board.GP21
BLUE_LED = board.GP20
led = adafruit_rgbled.RGBLED(RED_LED, GREEN_LED, BLUE_LED, invert_pwm=True)

# Button
btn_pin = DigitalInOut(board.GP2)
btn_pin.direction = Direction.INPUT
btn_pin.pull = Pull.UP
button_down = False

# Encoder
encoder = rotaryio.IncrementalEncoder(board.GP4, board.GP3)
last_position = None


# Make the display context
screen = displayio.Group()
display.show(screen)
color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000  # black
bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
screen.append(bg_sprite)

# Text
temp_area = label.Label(terminalio.FONT, text=" "*20, color=0xFFFFFF, x=10, y=10)
button_area = label.Label(terminalio.FONT, text=" "*20, color=0xFFFFFF, x=10, y=30)
screen.append(temp_area)
screen.append(button_area)

# Outputs
fan_pin = DigitalInOut(board.GP6)
fan_pin.direction = Direction.OUTPUT
heat_pin = DigitalInOut(board.GP7)
heat_pin.direction = Direction.OUTPUT

while True:

    # Temperature
    tempC = sensor.temperature
    tempText = "Temperature: {} C".format(int(tempC))
    temp_area.text = tempText

    # Led color
    if tempC > 23.5:
        led.color = (0, 255, 0)
    else:
        led.color = (255, 0, 0)

    # Button
    if btn_pin.value is False and not button_down:
        print('button pressed')
        button_down = True
        fan_pin.value = True
        heat_pin.value = True
    if btn_pin.value is True and button_down:
        button_down = False
        fan_pin.value = False
        heat_pin.value = False

    # Encoder
    position = encoder.position
    if last_position is None or position != last_position:
        print(position)
    last_position = position

    time.sleep(0.01)
