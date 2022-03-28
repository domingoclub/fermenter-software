import board
import busio
import time
from digitalio import DigitalInOut, Direction, Pull
import rotaryio
import adafruit_mcp9808
import displayio
import adafruit_displayio_sh1106
from adafruit_display_text import label
import terminalio
import pwmio
import simpleio

class fermenter:

    def __init__(self):

        # Settings
        self.TEMP_SET = 30
        self.TEMP_MARGIN = 1
        self.TEMP_MAX = self.TEMP_SET + self.TEMP_MARGIN
        self.TEMP_MIN = self.TEMP_SET - self.TEMP_MARGIN

        # Sensor
        self.sensor_i2c = busio.I2C(board.GP13, board.GP12)
        self.sensor = adafruit_mcp9808.MCP9808(self.sensor_i2c)

        # Button
        self.BTN = DigitalInOut(board.GP2)
        self.BTN.direction = Direction.INPUT
        self.BTN.pull = Pull.UP
        self.btn_down = False

        # Encoder
        self.encoder = rotaryio.IncrementalEncoder(board.GP4, board.GP3)
        self.encoder_last_position = 0

        # Display
        displayio.release_displays()
        display_i2c = busio.I2C(board.GP27, board.GP26, frequency=400000)
        display_bus = displayio.I2CDisplay(display_i2c, device_address=0x3c)
        self.DISPLAY_WIDTH = 130
        self.DISPLAY_HEIGHT = 64
        self.display = adafruit_displayio_sh1106.SH1106(display_bus, width=self.DISPLAY_WIDTH, height=self.DISPLAY_HEIGHT)

        # Display context
        self.screen = displayio.Group()
        self.display.show(self.screen)
        color_bitmap = displayio.Bitmap(self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = 0x000000
        bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
        self.screen.append(bg_sprite)

        # Text
        self.label_area = label.Label(terminalio.FONT, text=" "*20, color=0xFFFFFF, x=5, y=5)
        self.value_area = label.Label(terminalio.FONT, text=" "*20, color=0xFFFFFF, x=48, y=32)
        self.menu_left_area = label.Label(terminalio.FONT, text="<", color=0xFFFFFF, x=5, y=55)
        self.menu_right_area = label.Label(terminalio.FONT, text=">", color=0xFFFFFF, x=123, y=55)
        self.screen.append(self.label_area)
        self.screen.append(self.value_area)
        self.screen.append(self.menu_left_area)
        self.screen.append(self.menu_right_area)

        # Outputs
        self.FAN = pwmio.PWMOut(board.GP6, frequency=1000)
        self.HEAT = pwmio.PWMOut(board.GP7, frequency=1000)

    def update_temp(self):
        self.temp = self.sensor.temperature
        return self.temp
    
    def heating_system(self, temp):
        temp_error = abs(self.TEMP_SET - temp*4)
        temp_power = simpleio.map_range(temp_error, -20, 20, 200, 1000)
        if temp < self.TEMP_MIN:
            self.HEAT.duty_cycle = int(temp_power)
            self.FAN.duty_cycle = 1000
            # self.FAN.duty_cycle = int(temp_power / 3) if temp_power / 3 > 200 else 200
            print('Fermenter heating up')
        elif temp > self.TEMP_MAX:
            self.FAN.duty_cycle = int(temp_power)
            self.HEAT.duty_cycle = 0
            print('Fermenter cooling down')
        else:
            self.HEAT.duty_cycle = 0
            self.FAN.duty_cycle = 0
            print('Fermenter at the desired temperature')

        
if __name__ == '__main__':
    time.sleep(0.25)
    fermenter = fermenter()

    while True:
        
        temp = fermenter.update_temp()
        fermenter.heating_system(temp)
