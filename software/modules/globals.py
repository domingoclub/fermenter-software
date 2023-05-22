import os
import time

def initialize():

    global SOFTWARE_VERSION
    SOFTWARE_VERSION = "software v0.9.8.2"

    global temp
    temp = os.getenv('target_temperature')

    global temp_target
    temp_target = os.getenv('target_temperature')

    global time_startup
    time_startup = time.time()

    global time_heater
    time_heater = time.time()

    global time_sensor
    time_sensor = time.time()

    global timer_hours
    timer_hours = os.getenv('timer_hours')

    global time_left
    time_left = timer_hours

    global TIME_THRESHOLD_DAYS
    TIME_THRESHOLD_DAYS = 72

    global TEMP_MARGIN
    TEMP_MARGIN = 0.4

    global TEMP_SAFE
    TEMP_SAFE = 24

    global sensor_error
    sensor_error = False

    global fermenter_running
    fermenter_running = True

    global screen_index
    screen_index = 0

    global menu_on
    menu_on = False

    global edit_mode
    edit_mode = True

    global DELAY_SCREENS
    DELAY_SCREENS = 3

    global DELAY_ACTIONS
    DELAY_ACTIONS = 1

    global SCREENS_INTRO
    SCREENS_INTRO = ["header", "define_temp", "define_time", "all_set"]

    global SCREENS_MENU
    SCREENS_MENU = ["dashboard", "define_temp", "define_time", "footer"]

    global status_sentence
    status_sentence = ""

    global status_subsentence
    status_subsentence = ""

    global CONTENT_1_AREA
    global CONTENT_2_AREA
    global CONTENT_3_AREA
    global CONTENT_4_AREA
    global CONTENT_5_AREA
    global MENU_LEFT_AREA
    global MENU_RIGHT_AREA
