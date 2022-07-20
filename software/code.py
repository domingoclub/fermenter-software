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

font = terminalio.FONT

class fermenter:

    def __init__(self):

        # Temp
        self.TEMP_SET = 30
        self.TEMP_MARGIN = 1
        self.TEMP_MAX = self.TEMP_SET + self.TEMP_MARGIN
        self.TEMP_MIN = self.TEMP_SET - self.TEMP_MARGIN

        # Colors
        self.COLOR_RED = (20, 0, 0)
        self.COLOR_GREEN = (0, 20, 0)
        self.COLOR_BLUE = (0, 0, 20)

        # Time
        self.TIME_TIMER_HOURS = 38
        self.TIME_STARTUP = time.time()
        self.TIMER_ON = False

        # Heating System
        self.STATUS = 0

        # Button
        self.BTN = DigitalInOut(board.GP2)
        self.BTN.direction = Direction.INPUT
        self.BTN.pull = Pull.UP
        self.btn_down = False

        # Encoder
        self.encoder = rotaryio.IncrementalEncoder(board.GP4, board.GP3)
        self.encoder_last_position = 0

        # Led
        self.RED_LED = board.GP20
        self.GREEN_LED = board.GP18
        self.BLUE_LED = board.GP16
        self.LED = adafruit_rgbled.RGBLED(self.RED_LED, self.GREEN_LED, self.BLUE_LED, invert_pwm=True)

        # Sensor
        self.sensor_i2c = busio.I2C(board.GP13, board.GP12)
        self.sensor = adafruit_mcp9808.MCP9808(self.sensor_i2c)

        # Fan
        self.FAN = pwmio.PWMOut(board.GP6, frequency=20000)
        self.FAN.duty_cycle = 2 ** 15

        # Heating pad
        self.HEAT = pwmio.PWMOut(board.GP8)
        self.HEAT.duty_cycle = 2 ** 15

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

        # Text areas
        self.title_area = label.Label(font, text=" "*20, color=0xFFFFFF, x=5, y=5)
        self.subtitle_area = label.Label(font, text=" "*20, color=0xFFFFFF, x=5, y=5)
        self.label_area = label.Label(font, text=" "*20, color=0xFFFFFF, x=5, y=5)
        self.sublabel_area = label.Label(font, text=" "*20, color=0xFFFFFF, x=5, y=20)
        self.subsublabel_area = label.Label(font, text=" "*20, color=0xFFFFFF, x=5, y=35)
        self.value_area = label.Label(font, text=" "*20, color=0xFFFFFF, x=48, y=32)
        self.subvalue_area = label.Label(font, text=" "*20, color=0xFFFFFF, x=48, y=32)
        self.menu_left_area = label.Label(font, text="", color=0xFFFFFF, x=5, y=55)
        self.menu_right_area = label.Label(font, text="", color=0xFFFFFF, x=123, y=55)
        self.footer_area = label.Label(font, text="", color=0xFFFFFF, x=5, y=55)
        self.screen.append(self.title_area)
        self.screen.append(self.subtitle_area)
        self.screen.append(self.label_area)
        self.screen.append(self.sublabel_area)
        self.screen.append(self.subsublabel_area)
        self.screen.append(self.value_area)
        self.screen.append(self.subvalue_area)
        self.screen.append(self.menu_left_area)
        self.screen.append(self.menu_right_area)
        self.screen.append(self.footer_area)


        # Screens
        self.screens_intro = ["header", "define_temp", "define_time", "all_set"]
        self.screens_menu = ["dashboard", "define_temp", "define_time", "header"]
        self.screen_index = 0
        self.menu_on = False
        self.edit_mode = True

        # First screens
        # self.display_screen(self.menu_on, 0)
        # time.sleep(2)
        self.screen_index = 1
        self.display_screen(self.menu_on, 1)

    def display_screen(self, menu, i):
        # intro
        if not menu:
            self.menu_left_area.text = ""
            self.menu_right_area.text = ""
            if self.screens_intro[i] == "header":
                self.label_area.text = "Hey! Let's ferment."
                self.sublabel_area.text = ""
                self.subsublabel_area.text = ""
                self.footer_area.text = ""
            elif self.screens_intro[i] == "define_temp":
                self.label_area.text = "What's the ideal"
                self.sublabel_area.text = "temperature for your"
                self.subsublabel_area.text = "fermentation?"
                self.footer_area.text = "{} C".format(round_down(self.TEMP_SET, 1))
                self.menu_right_area.text = ">"
            elif self.screens_intro[i] == "define_time":
                self.label_area.text = "For how long do you"
                self.sublabel_area.text = "want to ferment?"
                self.subsublabel_area.text = ""
                self.footer_area.text = "{} hours".format(self.TIME_TIMER_HOURS)
                self.menu_right_area.text = ">"
            elif self.screens_intro[i] == "all_set":
                self.label_area.text = "It's all set."
                self.sublabel_area.text = "Remember to come"
                self.subsublabel_area.text = "and see sometimes."
                self.footer_area.text = ""
                self.menu_right_area.text = ""
        # menu
        if menu:
            self.label_area.text = ""
            self.sublabel_area.text = ""
            self.subsublabel_area.text = ""
            self.footer_area.text = ""
            self.menu_left_area.text = "<"
            self.menu_right_area.text = ">"
            if self.screens_menu[i] == "dashboard":
                self.label_area.text = "Fermenter"
                self.update_temp
                self.value_area.text = "{} C".format(round_down(self.sensor.temperature, 1))
            elif self.screens_menu[i] == "define_temp":
                self.label_area.text = "Set: Temperature"
                self.value_area.text = "{} C".format(round_down(self.TEMP_SET, 1))
            elif self.screens_menu[i] == "define_time":
                self.label_area.text = "Set: Timer"
                self.value_area.text = "{} H".format(round_down(self.TIME_TIMER_HOURS, 1))
            elif self.screens_menu[i] == "header":
                self.label_area.text = "header"

    def encoder_handler(self):
        if self.encoder_last_position is None or self.encoder_last_position != self.encoder.position:
            if self.encoder.position > self.encoder_last_position:
                self.edit_handler(-0.5) if self.edit_mode else self.menu_handler(-0.5)
            else:
                self.edit_handler(0.5) if self.edit_mode else self.menu_handler(0.5)
        self.encoder_last_position = self.encoder.position

    def button_handler(self):
        if self.BTN.value is False and not self.btn_down:
            self.button_actions()
            self.btn_down = True
        elif self.BTN.value is True and self.btn_down:
            self.btn_down = False
    
    def menu_handler(self, increment):
        self.screen_index += int(increment * 2)
        print(self.menu_on)
        if self.menu_on:
            screens_length = len(self.screens_menu) - 1
            if self.screen_index > screens_length:
                self.screen_index = 0
            elif self.screen_index < 0:
                self.screen_index = screens_length
            self.display_screen(self.menu_on, self.screen_index)

    def button_actions(self):
        if not self.menu_on:
            screen = self.screens_intro[self.screen_index]
            if screen == "define_temp":
                self.goto("define_time", "Set!")
            elif screen == "define_time":
                self.goto("dashboard", "Set!")
        elif self.menu_on:
            screen = self.screens_menu[self.screen_index]
            if screen == "define_temp" or screen == "define_time":
                if self.edit_mode == False:
                    self.value_area.color=0x000000
                    self.value_area.background_color=0xFFFFFF
                    self.edit_mode = True
                else:
                    self.value_area.color=0xFFFFFF
                    self.value_area.background_color=0x000000
                    self.edit_mode = False
        
    def edit_handler(self, increment):
        if self.menu_on:
            if self.screens_menu[self.screen_index] == "define_temp":
                self.update_temp_values(increment)
                self.value_area.text = "{} C".format(round_down(self.TEMP_SET, 1))
            elif self.screens_menu[self.screen_index] == "define_time":
                self.TIME_TIMER_HOURS += increment
                self.value_area.text = "{} H".format(round_down(self.TIME_TIMER_HOURS, 1))
        else:
            print(self.screens_intro[self.screen_index])
            if self.screens_intro[self.screen_index] == "define_temp":
                self.update_temp_values(increment)
                self.footer_area.text = "{} C".format(round_down(self.TEMP_SET, 1))
            elif self.screens_intro[self.screen_index] == "define_time":
                self.TIME_TIMER_HOURS += increment
                self.footer_area.text = "{} H".format(round_down(self.TIME_TIMER_HOURS, 1))

    def update_temp_values(self, increment):
        self.TEMP_SET += increment
        self.TEMP_MAX = self.TEMP_SET + self.TEMP_MARGIN
        self.TEMP_MIN = self.TEMP_SET - self.TEMP_MARGIN

    def update_temp(self, temp):
        if self.screens_menu[self.screen_index] == "dashboard":
            self.value_area.text = "{} C".format(round_down(temp, 1))

    def goto(self, screen, message):
        if not self.menu_on:
            self.footer_area.text = message
            time.sleep(1)
            if not screen == "dashboard":
                self.screen_index = self.screens_intro.index(screen)
            else:
                self.menu_on = True
                self.edit_mode = False
                self.screen_index = 0
            self.display_screen(self.menu_on, self.screen_index) 
        else:
            self.screen_index = self.screens_menu.index(screen)
            self.value_area.text = message
            time.sleep(1)
            self.display_screen(self.menu_on, self.screen_index)

    def heating_system(self, temp):
        temp_error = abs(self.TEMP_SET - temp)
        temp_power = simpleio.map_range(temp_error, 0, 12, 0, 100)
        if temp < self.TEMP_MIN:
            self.HEAT.duty_cycle = percent_to_duty_cycles(temp_power)
            self.LED.color = self.COLOR_RED
            self.STATUS = 1
            self.FAN.duty_cycle = percent_to_duty_cycles(temp_power)
        elif temp > self.TEMP_MAX:
            self.LED.color = self.COLOR_BLUE
            self.STATUS = -1
            self.FAN.duty_cycle = percent_to_duty_cycles(temp_power*2)
            self.HEAT.duty_cycle = 0
        else:
            self.LED.color = self.COLOR_GREEN
            self.HEAT.duty_cycle = 0
            self.STATUS = 0
            self.FAN.duty_cycle = 9000
        self.update_temp(temp)

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
