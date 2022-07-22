import board
import busio
import time
from digitalio import DigitalInOut, Direction, Pull
import rotaryio
import adafruit_mcp9808
import displayio
import adafruit_displayio_sh1106
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
import terminalio
import pwmio
import simpleio
import math
import adafruit_rgbled

font = bitmap_font.load_font("fonts/cozette.pcf")

class fermenter:

    def __init__(self):

        # General
        self.DELAY_SCREENS = 3
        self.DELAY_ACTIONS = 1
        self.STATUS_SENTENCE = ""
        self.STATUS_SUBSENTENCE = ""

        # Temp
        self.TEMP_SET = 30
        self.TEMP_MARGIN = 1
        self.TEMP_MAX = self.TEMP_SET + self.TEMP_MARGIN
        self.TEMP_MIN = self.TEMP_SET - self.TEMP_MARGIN

        # Colors
        self.COLOR_RED = (20, 0, 0)
        self.COLOR_GREEN = (0, 20, 0)
        self.COLOR_BLUE = (0, 0, 20)
        self.COLOR_BLACK = (0, 0, 0)
        self.COLOR_WHITE = (100, 100, 100)

        # Time
        self.TIME_TIMER_HOURS = 36
        self.TIME_THRESHOLD_DAYS = 73
        self.TIME_STARTUP = time.time()
        self.TIME_LEFT = self.TIME_TIMER_HOURS

        # Heating System
        self.STATUS = True

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
        self.content1_area = label.Label(font, text="", color=0xFFFFFF, x=5, y=5)
        self.content2_area = label.Label(font, text="", color=0xFFFFFF, x=5, y=19)
        self.content3_area = label.Label(font, text="", color=0xFFFFFF, x=5, y=34)
        self.content3_extra_area = label.Label(font, text="", color=0xFFFFFF, x=5, y=41)
        self.content4_area = label.Label(font, text="", color=0xFFFFFF, x=5, y=56)
        self.menu_left_area = label.Label(font, text="", color=0xFFFFFF, x=114, y=56)
        self.menu_right_area = label.Label(font, text="", color=0xFFFFFF, x=123, y=56)
        self.screen.append(self.content1_area)
        self.screen.append(self.content2_area)
        self.screen.append(self.content3_area)
        self.screen.append(self.content3_extra_area)
        self.screen.append(self.content4_area)
        self.screen.append(self.menu_left_area)
        self.screen.append(self.menu_right_area)

        # Screens
        self.screens_intro = ["header", "define_temp", "define_time", "all_set"]
        self.screens_menu = ["dashboard", "define_temp", "define_time", "footer"]
        self.screen_index = 0
        self.menu_on = False
        self.edit_mode = True

        # First screens
        self.display_screen(self.menu_on, 0)
        time.sleep(self.DELAY_SCREENS)
        self.screen_index = 1
        self.display_screen(self.menu_on, 1)

    def display_screen(self, menu, i):
        self.content1_area.text = self.content2_area.text = self.content3_area.text = self.content3_extra_area.text = self.content4_area.text = ""
        self.menu_left_area.text = self.menu_right_area.text = ""
        # intro
        if not menu:
            self.menu_left_area.text = ""
            self.menu_right_area.text = ""
            if self.screens_intro[i] == "header":
                self.content1_area.text = "Hey! Let's ferment."
                self.content4_area.text = "⚙ ⚙ ⚙"
            elif self.screens_intro[i] == "define_temp":
                self.content1_area.text = " What's the ideal"
                self.content2_area.text = "temperature for your"
                self.content3_area.text = "fermentation?"
                self.content4_area.text = "{} C".format(round_down(self.TEMP_SET, 1))
                self.content4_area.color=0x000000
                self.content4_area.background_color=0xFFFFFF
                self.menu_left_area.text = "↓"
                self.menu_right_area.text = "↑"
            elif self.screens_intro[i] == "define_time":
                self.content1_area.text = " For how long do"
                self.content2_area.text = "you want to ferment?"
                self.content4_area.text = timer_unit(int(self.TIME_TIMER_HOURS))
                self.content4_area.color=0x000000
                self.content4_area.background_color=0xFFFFFF
                self.menu_left_area.text = "↓"
                self.menu_right_area.text = "↑"
            elif self.screens_intro[i] == "all_set":
                self.content1_area.text = "It's all set."
                self.content2_area.text = "Remember to check me"
                self.content3_area.text = "every now and then."
                self.content4_area.text = "☺"
        # menu
        if menu:
            self.menu_left_area.text = ""
            self.menu_right_area.text = "→"
            self.content4_area.color=0xFFFFFF
            self.content4_area.background_color=0x000000
            if self.screens_menu[i] == "dashboard":
                self.update_status_sentence()
                self.update_values()
            elif self.screens_menu[i] == "define_temp":
                self.content1_area.text = " Set: Temperature"
                self.content4_area.text = "{} C".format(round_down(self.TEMP_SET, 1))
            elif self.screens_menu[i] == "define_time":
                self.content1_area.text = " Set: Timer"
                self.content4_area.text = timer_unit(int(self.TIME_TIMER_HOURS))
            elif self.screens_menu[i] == "footer":
                self.content1_area.text = "Domingo Fermenter"
                self.content2_area.text = "software v0.9"
                self.content3_area.text = "domingoclub.com"
                self.content4_area.text = "⚙ ⚙ ⚙"

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
        if self.menu_on:
            screens_length = len(self.screens_menu) - 1
            if self.screen_index > screens_length:
                self.screen_index = 0
            elif self.screen_index < 0:
                self.screen_index = screens_length
            self.display_screen(self.menu_on, self.screen_index)

    def button_actions(self):
        self.content4_area.color=0xFFFFFF
        self.content4_area.background_color=0x000000
        if not self.menu_on:
            screen = self.screens_intro[self.screen_index]
            if screen == "define_temp":
                self.goto("define_time", "Set!")
            elif screen == "define_time":
                self.goto("all_set", "Set!")
                time.sleep(self.DELAY_SCREENS)
                self.goto("dashboard", "")
        elif self.menu_on:
            screen = self.screens_menu[self.screen_index]
            if screen == "define_temp" or screen == "define_time":
                if self.edit_mode == False:
                    self.content4_area.color=0x000000
                    self.content4_area.background_color=0xFFFFFF
                    self.menu_left_area.text = "↓"
                    self.menu_right_area.text = "↑"
                    self.edit_mode = True
                else:
                    self.content4_area.color=0xFFFFFF
                    self.content4_area.background_color=0x000000
                    self.edit_mode = False
                    if screen == "define_time":
                        self.TIME_STARTUP = time.time()
                    self.goto("dashboard", "Set!")
            elif screen == "dashboard" or screen == "footer":
                self.content1_area.text = "Turn the knob to "
                self.content2_area.text = "change the settings."
                self.content3_area.text = ""
                self.content3_extra_area.text = ""
                self.content4_area.text = ""
                time.sleep(self.DELAY_ACTIONS)
                self.goto(screen, "")
        
    def edit_handler(self, increment):
        if not self.menu_on:
            screen = self.screens_intro[self.screen_index]
        else:
            screen = self.screens_menu[self.screen_index]
        if screen == "define_temp":
            self.update_temp_values(increment)
            self.content4_area.text = "{} C".format(round_down(self.TEMP_SET, 1))
        elif screen == "define_time":
            if self.TIME_TIMER_HOURS  < 0:
                self.TIME_TIMER_HOURS = 0
            elif self.TIME_TIMER_HOURS >= 0 and self.TIME_TIMER_HOURS < self.TIME_THRESHOLD_DAYS:
                self.TIME_TIMER_HOURS += increment * 2
            else:
                self.TIME_TIMER_HOURS += increment * 48
            self.content4_area.text = timer_unit(int(self.TIME_TIMER_HOURS))

    def update_temp_values(self, increment):
        self.TEMP_SET += increment
        self.TEMP_MAX = self.TEMP_SET + self.TEMP_MARGIN
        self.TEMP_MIN = self.TEMP_SET - self.TEMP_MARGIN

    def update_values(self):
        if self.screens_menu[self.screen_index] == "dashboard":
            if self.STATUS:
                self.content3_extra_area.text = " {} C inside".format(round_down(self.sensor.temperature, 1))
                self.content4_area.text = " {} left".format(timer_unit(int(self.TIME_LEFT // 3600) + 1))
            else:
                self.content3_area.text = "Observe, sense."
                self.content3_extra_area.text = ""
                self.content4_area.text = "{} C inside.".format(round_down(self.sensor.temperature, 1))

    def update_status_sentence(self):
        if self.screens_menu[self.screen_index] == "dashboard":
            self.content1_area.text = self.STATUS_SENTENCE
            self.content2_area.text = self.STATUS_SUBSENTENCE

    def goto(self, screen, message):
        if not self.menu_on:
            self.content4_area.text = message
            time.sleep(self.DELAY_ACTIONS)
            if not screen == "dashboard":
                self.screen_index = self.screens_intro.index(screen)
            else:
                self.menu_on = True
                self.edit_mode = False
                self.screen_index = 0
            self.display_screen(self.menu_on, self.screen_index)
        else:
            self.screen_index = self.screens_menu.index(screen)
            self.content4_area.text = message
            time.sleep(self.DELAY_ACTIONS)
            self.display_screen(self.menu_on, self.screen_index)

    def heating_system(self, temp):
        temp_error = abs(self.TEMP_SET - temp)
        temp_power = simpleio.map_range(temp_error, 0, 12, 0, 100)
        if self.STATUS:
            if temp < self.TEMP_MIN:
                self.HEAT.duty_cycle = percent_to_duty_cycles(temp_power)
                self.LED.color = self.COLOR_RED
                self.STATUS_SENTENCE = "Heating up to the"
                self.STATUS_SUBSENTENCE = "good temperature."
                self.FAN.duty_cycle = percent_to_duty_cycles(temp_power)
            elif temp > self.TEMP_MAX:
                self.LED.color = self.COLOR_BLUE
                self.STATUS_SENTENCE = "Cooling down to"
                self.STATUS_SUBSENTENCE = "the good temperature."
                self.FAN.duty_cycle = percent_to_duty_cycles(temp_power*2)
                self.HEAT.duty_cycle = 0
                if temp > self.TEMP_MAX + 5:
                    self.STATUS_SENTENCE = "⚠ It's too hot here," 
                    self.STATUS_SUBSENTENCE = "open the door please."
            else:
                self.LED.color = self.COLOR_GREEN
                self.STATUS_SENTENCE = "Good temperature."
                self.STATUS_SUBSENTENCE = "It feels great."
                self.HEAT.duty_cycle = 0
                self.FAN.duty_cycle = 9000
        else:
            self.LED.color = self.COLOR_WHITE
            self.STATUS_SENTENCE = " Timer expired."
            self.STATUS_SUBSENTENCE = "How did it go?"
            self.FAN.duty_cycle = percent_to_duty_cycles(100)
            self.HEAT.duty_cycle = 0

        self.update_status_sentence()
        self.update_values()

    def timer(self, timer):
        time_now = time.time()
        timer_sec = self.TIME_TIMER_HOURS * 3600
        time_since_startup = time_now - self.TIME_STARTUP
        self.TIME_LEFT = timer_sec - time_since_startup
        if self.TIME_LEFT > 1:
            self.STATUS = True
        else:
            self.STATUS = False

def percent_to_duty_cycles(percent):
    duty_cycles = int(simpleio.map_range(percent, 0, 100, 0, 65532))
    return duty_cycles

def round_down(n, decimals=0):
    multiplier = 10 ** decimals
    number = math.floor(n * multiplier) / multiplier
    result = 0.0 if number < 0 else number
    return result

def timer_unit(hour):
    time_unit = ""
    if hour <= 0:
        time_unit = "0 hour"
    elif hour == 1:
        time_unit = "1 hour"
    elif hour > 1 and hour < fermenter.TIME_THRESHOLD_DAYS:
        time_unit = str(int(hour)) + " hours"
    elif hour >= fermenter.TIME_THRESHOLD_DAYS:
        time_unit = str(int(hour // 24)) + " days"
    return time_unit

if __name__ == '__main__':
    
    fermenter = fermenter()

    while True:
        temp = fermenter.sensor.temperature
        timer = fermenter.TIME_TIMER_HOURS
        fermenter.encoder_handler()
        fermenter.button_handler()
        fermenter.timer(timer)
        if fermenter.menu_on:
            fermenter.heating_system(temp)
        # time.sleep(0.25)
