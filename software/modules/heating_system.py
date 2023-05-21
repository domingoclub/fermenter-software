import os
import pwmio
import board
import simpleio
import time
import modules.utilities

FERMENTER_MODEL = os.getenv('fermenter_model')
FAN = pwmio.PWMOut(board.GP6, frequency=20000)
FAN.duty_cycle = 0
HEAT = pwmio.PWMOut(board.GP8)
HEAT.duty_cycle = 0
led_counter = 0
led_rewind = False
LED_MODEL = os.getenv('led_model')
if LED_MODEL == "onboard":
    import adafruit_rgbled
    RED_LED = board.GP20
    GREEN_LED = board.GP18
    BLUE_LED = board.GP16
    LED = adafruit_rgbled.RGBLED(RED_LED, GREEN_LED, BLUE_LED, invert_pwm=True)
elif LED_MODEL == "external":
    import neopixel
    PIN_LED = board.GP28
    LED = neopixel.NeoPixel(PIN_LED, 1, pixel_order=(1, 0, 2, 3))
color_black = (0, 0, 0, 0)
LED.color = color_black if LED_MODEL == "onboard" else LED.fill(color_black)

def timer():
    time_now = time.time()
    timer_sec = modules.globals.timer_hours * 3600
    time_since_startup = time_now - modules.globals.time_startup
    modules.globals.time_left = timer_sec - time_since_startup
    if modules.globals.time_left > 1:
        modules.globals.fermenter_running = True
    else:
        modules.globals.fermenter_running = False

def update_status_sentence():
    if modules.globals.SCREENS_MENU[modules.globals.screen_index] == "dashboard":
        modules.globals.CONTENT_1_AREA.text = modules.globals.status_sentence
        modules.globals.CONTENT_2_AREA.text = modules.globals.status_subsentence

def update_values():
    if modules.globals.SCREENS_MENU[modules.globals.screen_index] == "dashboard":
        if modules.globals.fermenter_running:
            if not modules.globals.sensor_error:
                modules.globals.CONTENT_4_AREA.text = " {} C inside".format(modules.utilities.round_down(modules.globals.temp, 1))
            else:
                modules.globals.CONTENT_4_AREA.text = " .. C inside"
            modules.globals.CONTENT_5_AREA.text = " {} left".format(modules.utilities.timer_unit(int(modules.globals.time_left // 3600) + 1))
            modules.globals.CONTENT_3_AREA.text = ""
        else:
            modules.globals.CONTENT_3_AREA.text = "Observe, sense."
            modules.globals.CONTENT_4_AREA.text = ""
            modules.globals.CONTENT_5_AREA.text = "{} C inside.".format(modules.utilities.round_down(modules.globals.temp, 1))


def update_led(color, steps):
    global led_counter
    global led_rewind

    if modules.globals.screen_index == 0:
        if not led_rewind:
            if led_counter <= 200 - steps: led_counter += steps
            else: led_rewind = True
        else:
            if led_counter >= 30 + steps: led_counter -= steps
            else: led_rewind = False
    else:
        led_counter = 120
    
    if color == "red":
        color_red = (led_counter, 0, 0, 0)
        LED.color = color_red if LED_MODEL == "onboard" else LED.fill(color_red)
    elif color == "green":
        color_green = (0, led_counter, 0, 0)
        LED.color = color_green if LED_MODEL == "onboard" else LED.fill(color_green)
    elif color == "blue":
        color_blue = (0, 0, led_counter, 0)
        LED.color = color_blue if LED_MODEL == "onboard" else LED.fill(color_blue)
    elif color == "black":
        color_black = (0, 0, 0, 0)
        LED.color = color_black if LED_MODEL == "onboard" else LED.fill(color_black)
    elif color == "white":
        color_white = (led_counter, led_counter, led_counter, 0)
        LED.color = color_white if LED_MODEL == "onboard" else LED.fill(color_white)
    elif color == "purple":
        color_purple = (led_counter, 0, led_counter, 0)
        LED.color = color_purple if LED_MODEL == "onboard" else LED.fill(color_purple)
    
        

def air_circulation(time_diff, interval, duration):
    # fan on for x seconds every x seconds
    if interval < time_diff < interval + duration:
        FAN.duty_cycle = modules.utilities.percent_to_duty_cycles(5)
    elif time_diff > interval + duration:
        FAN.duty_cycle = 0
        modules.globals.time_heater = time.time()

def heating_system(temp, temp_target, temp_margin):

    if FERMENTER_MODEL == "lab":
        POWER_HEATER = 85  # between 60 and 100
    elif FERMENTER_MODEL == "mini":
        POWER_HEATER = 70  # between 50 and 75

    temp_error = abs(temp_target - temp)
    power_fan = simpleio.map_range(temp_error, 0, 8, 50, 100)
    time_now = time.time()
    time_diff = time_now - modules.globals.time_heater

    if modules.globals.fermenter_running:
        if not modules.globals.sensor_error:
            if temp > temp_target + temp_margin * 2:
                # cooler on
                FAN.duty_cycle = modules.utilities.percent_to_duty_cycles(power_fan)
                update_led('blue', 30)
                modules.globals.status_sentence = "Cooling down to"
                modules.globals.status_subsentence = "the good temperature."
                if temp > temp_target + 5:
                    modules.globals.status_sentence = "⚠ It's too hot here,"
                    modules.globals.status_subsentence = "open the door please."
            if temp > temp_target + temp_margin:
                # heater off
                HEAT.duty_cycle = 0
            if temp_target - temp_margin/2 < temp < temp_target + temp_margin:
                # set point and cooler off
                FAN.duty_cycle = 0
                update_led('green', 10)
                modules.globals.status_sentence = "Good temperature."
                modules.globals.status_subsentence = "It feels great."
                air_circulation(time_diff, 120, 5)
            if temp < temp_target - temp_margin:
                # heater on
                HEAT.duty_cycle = modules.utilities.percent_to_duty_cycles(POWER_HEATER)
                update_led('red', 15)
                modules.globals.status_sentence = "Heating up to the"
                modules.globals.status_subsentence = "good temperature."
                air_circulation(time_diff, 180, 3)
        else:
            HEAT.duty_cycle = 0
            FAN.duty_cycle = 0
            modules.globals.status_sentence = "The sensor is"
            modules.globals.status_subsentence = "not responding"
            update_led('purple', 40)

        update_status_sentence()
        update_values()
    
    else:
        modules.globals.status_sentence = " Timer expired."
        modules.globals.status_subsentence = "How did it go?"
        update_led('white', 60)
        if temp >= modules.globals.TEMP_SAFE:
            FAN.duty_cycle = modules.utilities.percent_to_duty_cycles(100)
        else:
            FAN.duty_cycle = 0
        HEAT.duty_cycle = 0
