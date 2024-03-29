from digitalio import DigitalInOut, Direction, Pull
import rotaryio
import board
import time
import modules.globals
import os


ENCODER = rotaryio.IncrementalEncoder(board.GP4, board.GP3)
encoder_last_position = 0

BTN = DigitalInOut(board.GP2)
BTN.direction = Direction.INPUT
BTN.pull = Pull.UP
btn_down = False


def encoder_handler():
    global encoder_last_position
    if encoder_last_position is None or encoder_last_position != ENCODER.position:
        if ENCODER.position > encoder_last_position:
            edit_handler(-0.5) if modules.globals.edit_mode else menu_handler(-0.5)
        else:
            edit_handler(0.5) if modules.globals.edit_mode else menu_handler(0.5)
    encoder_last_position = ENCODER.position


def edit_handler(increment):
    if not modules.globals.menu_on:
        screen = modules.globals.SCREENS_INTRO[modules.globals.screen_index]
    else:
        screen = modules.globals.SCREENS_MENU[modules.globals.screen_index]
    if screen == "select_mode":
        modules.globals.modes_index += increment * 2
        if modules.globals.modes_index >= len(modules.globals.modes):
            modules.globals.modes_index = 0
        elif  modules.globals.modes_index < 0:
            modules.globals.modes_index = len(modules.globals.modes) -1
        else:
            modules.globals.modes_index = int(modules.globals.modes_index)
        modules.globals.CONTENT_5_AREA.text = modules.globals.modes[modules.globals.modes_index][0]
    elif screen == "change_mode":
        modules.globals.total_increment += increment * 2
        if not modules.globals.total_increment % 2 == 0:
            modules.globals.bool_string = "Yes please"
        else:
            modules.globals.bool_string = "No thanks"
        modules.globals.CONTENT_5_AREA.text = modules.globals.bool_string
    elif screen == "define_temp":
        update_temp_values(increment)
        modules.globals.CONTENT_5_AREA.text = "{} C".format(modules.utilities.round_down(modules.globals.temp_target, 1))
    elif screen == "define_time":
        if modules.globals.timer_hours < 0:
            modules.globals.timer_hours = 0
        elif modules.globals.timer_hours > modules.globals.TIME_THRESHOLD_DAYS:
            modules.globals.timer_hours += increment * 48
        else:
            modules.globals.timer_hours += increment * 2
        modules.globals.CONTENT_5_AREA.text = modules.utilities.timer_unit(int(modules.globals.timer_hours))


def button_handler():
    global btn_down
    if BTN.value is False and not btn_down:
        button_actions()
        btn_down = True
    elif BTN.value is True and btn_down:
        btn_down = False


def menu_handler(increment):
    modules.globals.screen_index += int(increment * 2)
    if modules.globals.menu_on:
        screens_length = len(modules.globals.SCREENS_MENU) - 1
        if modules.globals.screen_index > screens_length:
            modules.globals.screen_index = 0
        elif modules.globals.screen_index < 0:
            modules.globals.screen_index = screens_length
        if not modules.globals.manual_on:
            # Skip set temperature and timer
            if modules.globals.screen_index == 1:
                modules.globals.screen_index = 3
            if modules.globals.screen_index == 2:
                modules.globals.screen_index = 0
        modules.display.display_screen(modules.globals.menu_on, modules.globals.manual_on, modules.globals.screen_index)

def update_temp_values(increment):
    modules.globals.temp_target += increment

def button_actions():
        modules.globals.CONTENT_5_AREA.color = 0xFFFFFF
        modules.globals.CONTENT_5_AREA.background_color = 0x000000

        if not modules.globals.menu_on:
            screen = modules.globals.SCREENS_INTRO[modules.globals.screen_index]
            if screen == "select_mode":
                if modules.globals.modes[modules.globals.modes_index][0] == "Manual":
                    modules.globals.manual_on =  True
                    modules.menu.goto("define_temp", "Set!")
                else:
                    modules.menu.goto("all_set", "Set!")
                    modules.globals.timer_hours = modules.globals.modes[modules.globals.modes_index][1][-1]
                    time.sleep(modules.globals.DELAY_SCREENS)
                    modules.menu.goto("dashboard", "")
            elif screen == "define_temp":
                modules.menu.goto("define_time", "Set!")
            elif screen == "define_time":
                modules.menu.goto("all_set", "Set!")
                time.sleep(modules.globals.DELAY_SCREENS)
                modules.menu.goto("dashboard", "")
        elif modules.globals.menu_on:
            screen = modules.globals.SCREENS_MENU[modules.globals.screen_index]
            if screen == "define_temp" or screen == "define_time" or screen == "change_mode":
                if modules.globals.edit_mode == False:
                    modules.globals.CONTENT_5_AREA.color = 0x000000
                    modules.globals.CONTENT_5_AREA.background_color = 0xFFFFFF
                    modules.globals.MENU_LEFT_AREA.text = "↓"
                    modules.globals.MENU_RIGHT_AREA.text = "↑"
                    modules.globals.edit_mode = True
                else:
                    modules.globals.CONTENT_5_AREA.color = 0xFFFFFF
                    modules.globals.CONTENT_5_AREA.background_color = 0x000000
                    modules.globals.edit_mode = False
                    if screen == "define_time":
                        modules.globals.time_startup = time.time()
                    if screen == "change_mode" and modules.globals.bool_string == "Yes please":
                        # re initialize
                        modules.globals.menu_on = False
                        modules.globals.manual_on = False
                        modules.globals.edit_mode = True
                        modules.globals.modes_index = 0
                        modules.globals.time_startup = time.time()
                        modules.globals.time_heater = time.time()
                        modules.globals.time_sensor = time.time()
                        modules.globals.temp = os.getenv('manual_target_temperature')
                        modules.globals.temp_target = os.getenv('manual_target_temperature')
                        modules.globals.timer_hours = os.getenv('manual_timer_hours')
                        modules.globals.time_left = modules.globals.timer_hours
                        modules.menu.goto("select_mode", "Set!")
                    else:
                        modules.menu.goto("dashboard", "Set!")
                    modules.globals.bool_string = "No thanks"
            elif screen == "dashboard" or screen == "footer":
                modules.globals.CONTENT_1_AREA.text = "Turn the knob to "
                modules.globals.CONTENT_2_AREA.text = "change the settings."
                modules.globals.CONTENT_3_AREA.text = ""
                modules.globals.CONTENT_4_AREA.text = ""
                modules.globals.CONTENT_5_AREA.text = ""
                time.sleep(modules.globals.DELAY_ACTIONS)
                modules.menu.goto(screen, "")
