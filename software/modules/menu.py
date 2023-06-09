import os
import time
import modules.display
import modules.globals

# First screens
def start_introduction():
    DEFAULT_MODE = os.getenv('default_mode')
    if DEFAULT_MODE == "default":
        modules.display.display_screen(modules.globals.menu_on, modules.globals.manual_on, 0)
        time.sleep(modules.globals.DELAY_SCREENS)
        modules.globals.screen_index = 1
        modules.display.display_screen(modules.globals.menu_on, modules.globals.manual_on, modules.globals.screen_index)
    else:
        modules.display.display_screen('menu', 0)
        goto("dashboard", "")


def goto(screen, message):
    if not modules.globals.menu_on:
        modules.globals.CONTENT_5_AREA.text = message
        time.sleep(modules.globals.DELAY_ACTIONS)
        if not screen == "dashboard":
            modules.globals.screen_index = modules.globals.SCREENS_INTRO.index(screen)
        else:
            modules.globals.menu_on = True
            modules.globals.edit_mode = False
            modules.globals.screen_index = 0
        modules.display.display_screen(modules.globals.menu_on, modules.globals.manual_on, modules.globals.screen_index)
    else:
        modules.globals.screen_index = modules.globals.SCREENS_MENU.index(screen)
        modules.globals.CONTENT_5_AREA.text = message
        time.sleep(modules.globals.DELAY_ACTIONS)
        modules.display.display_screen(modules.globals.menu_on, modules.globals.manual_on, modules.globals.screen_index)
