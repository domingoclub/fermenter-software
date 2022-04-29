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
import math
import adafruit_rgbled

class fermenter:

    def __init__(self):

        # Time
        self.TIME_STARTUP = time.time()
        self.TIME_TIMER_HOURS = 0
        self.TIMER_ON = False

        # Heating System
        self.STATUS = 0

        # Settings
        self.TEMP_SET = 30
        self.TEMP_MARGIN = 1
        self.TEMP_MAX = self.TEMP_SET + self.TEMP_MARGIN
        self.TEMP_MIN = self.TEMP_SET - self.TEMP_MARGIN
        self.COLOR_RED = (20, 0, 0)
        self.COLOR_GREEN = (0, 20, 0)
        self.COLOR_BLUE = (0, 0, 20)

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

        # Led
        self.RED_LED = board.GP22
        self.GREEN_LED = board.GP21
        self.BLUE_LED = board.GP20
        self.LED = adafruit_rgbled.RGBLED(self.RED_LED, self.GREEN_LED, self.BLUE_LED, invert_pwm=True)

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
        # self.FAN = pwmio.PWMOut(board.GP6, frequency=80)
        # self.FAN.duty_cycle = 2 ** 15
        self.HEAT = pwmio.PWMOut(board.GP7)
        # self.HEAT.duty_cycle = 2 ** 15

        # Menu
        self.screens = ["dashboard", "temp_set", "timer_set"]
        self.screen_index = 0
        self.edit_mode = False
        self.display_screen(self.screen_index)

    def encoder_handler(self):
        if self.encoder_last_position is None or self.encoder_last_position != self.encoder.position:
            if self.encoder.position > self.encoder_last_position:
                self.edit_handler(-0.5) if self.edit_mode else self.menu_handler(-0.5)
            else:
                self.edit_handler(0.5) if self.edit_mode else self.menu_handler(0.5)
        self.encoder_last_position = self.encoder.position

    def button_handler(self):
        if self.BTN.value is False and not self.btn_down:
            self.switch_edit_mode()
            self.btn_down = True
        elif self.BTN.value is True and self.btn_down:
            self.btn_down = False

    def menu_handler(self, increment):
        self.screen_index += int(increment * 2)
        if self.screen_index > len(self.screens) - 1:
            self.screen_index = 0
        elif self.screen_index < 0:
            self.screen_index = len(self.screens) - 1
        self.display_screen(self.screen_index)

    def switch_edit_mode(self):
        screen = self.screens[self.screen_index]
        if screen == "temp_set" or screen == "timer_set":
            if self.edit_mode == False:
                self.value_area.color=0x000000
                self.value_area.background_color=0xFFFFFF
                self.edit_mode = True
            else:
                self.value_area.color=0xFFFFFF
                self.value_area.background_color=0x000000
                self.edit_mode = False
                if self.TIME_TIMER_HOURS > 0:
                    self.TIMER_ON = True
                    fermenter.timer()
                else:
                    self.TIMER_ON = False
                self.goto("dashboard", "Set!")

    def edit_handler(self, increment):
        if self.screens[self.screen_index] == "temp_set":
            self.TEMP_SET += increment
            self.value_area.text = "{} C".format(round_down(self.TEMP_SET, 1))
        elif self.screens[self.screen_index] == "timer_set":
            self.TIME_TIMER_HOURS += increment
            self.value_area.text = "{} H".format(round_down(self.TIME_TIMER_HOURS, 1))

    def display_screen(self, i):
        if self.screens[i] == "dashboard":
            self.label_area.text = "Fermenter"
            self.update_temp
            self.value_area.text = "{} C".format(round_down(self.sensor.temperature, 1))
        elif self.screens[i] == "temp_set":
            self.label_area.text = "Set: Temperature"
            self.value_area.text = "{} C".format(round_down(self.TEMP_SET, 1))
        elif self.screens[i] == "timer_set":
            self.label_area.text = "Set: Timer"
            self.value_area.text = "{} H".format(round_down(self.TIME_TIMER_HOURS, 1))

    def update_temp(self, temp):
        if self.screens[self.screen_index] == "dashboard":
            self.value_area.text = "{} C".format(round_down(temp, 1))

    def goto(self, screen, message):
        self.screen_index = self.screens.index(screen)
        self.value_area.text = message
        time.sleep(1)
        self.display_screen(self.screen_index)
    
    def heating_system(self, temp):
        temp_error = abs(self.TEMP_SET - temp)
        temp_power = simpleio.map_range(temp_error, 0, 5, 0, 100)
        if temp < self.TEMP_MIN:
            self.HEAT.duty_cycle = percent_to_duty_cycles(temp_power)
            self.LED.color = self.COLOR_RED
            self.STATUS = 1
            # self.FAN.duty_cycle = percent_to_duty_cycles(temp_power)
            # print('Fermenter heating up. Current: ' + str(temp))
        elif temp > self.TEMP_MAX:
            self.LED.color = self.COLOR_BLUE
            self.STATUS = -1
            # self.FAN.duty_cycle = percent_to_duty_cycles(temp_power)
            self.HEAT.duty_cycle = 0
            # print('Fermenter cooling down. Current: ' + str(temp))
        else:
            self.LED.color = self.COLOR_GREEN
            self.HEAT.duty_cycle = 0
            self.STATUS = 0
            # self.FAN.duty_cycle = 0
            # print('Fermenter at the desired temperature. Current: ' + str(temp))
        self.update_temp(temp)

    def timer(self):
        time_now = time.time()
        time_active_sec = time_now - self.TIME_STARTUP
        time_active_hours = time_active_sec // 3600
        if self.TIMER_ON:
            pass
            # TODO: TIMER



def percent_to_duty_cycles(percent):
    duty_cycles = int(simpleio.map_range(percent, 0, 100, 0, 65532))
    return duty_cycles

def round_down(n, decimals=0):
    multiplier = 10 ** decimals
    number = math.floor(n * multiplier) / multiplier
    result = 0.0 if number < 0 else number
    return result
        
if __name__ == '__main__':
    
    fermenter = fermenter()

    while True:
        temp = fermenter.sensor.temperature
        fermenter.encoder_handler()
        fermenter.button_handler()
        fermenter.heating_system(temp)
        # time.sleep(0.25)
