import time
import modules.globals
import modules.menu
import modules.sensor
import modules.heating_system
import modules.handlers

if __name__ == "__main__":

    modules.globals.initialize()
    modules.menu.start_introduction()
    modules.sensor.sensor_start()

    while True:

        modules.handlers.encoder_handler()
        modules.handlers.button_handler()

        if modules.globals.menu_on:

            time_now = time.time()
            time_sensor_diff = time_now - modules.globals.time_sensor

            if time_sensor_diff >= 2:
                try:
                    modules.globals.temp = modules.globals.SENSOR.temperature
                    modules.globals.sensor_error = False
                except Exception as e:
                    print(e)
                    modules.globals.sensor_error = True
                    modules.sensor.sensor_start()
                modules.globals.time_sensor = time.time()

            modules.heating_system.timer()

            if modules.globals.fermenter_running:
                modules.heating_system.update_target_temp(modules.globals.time_left, modules.globals.modes[modules.globals.modes_index])
                modules.heating_system.heating_system(modules.globals.temp, modules.globals.temp_target, modules.globals.TEMP_MARGIN)
