import time
import modules.globals
import modules.menu
import modules.sensor
import modules.heating_system
import modules.handlers

if __name__ == "__main__":
    modules.globals.initialize()
    modules.menu.start_introduction()
    while True:
        modules.handlers.encoder_handler()
        modules.handlers.button_handler()
        if modules.globals.menu_on:
            time_now = time.time()
            time_sensor_diff = time_now - modules.globals.time_sensor
            if time_sensor_diff >= 2:
                try:
                    modules.globals.temp = modules.sensor.SENSOR.temperature
                    modules.globals.sensor_error = False
                except:
                    modules.globals.sensor_error = True
                modules.globals.time_sensor = time.time()
            modules.heating_system.timer()
            if modules.globals.fermenter_running:
                modules.heating_system.heating_system(modules.globals.temp, modules.globals.temp_target, modules.globals.TEMP_MARGIN)
