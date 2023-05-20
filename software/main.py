import modules.globals
import modules.display
import modules.menu
import modules.sensor
import modules.heating_system
import modules.handlers

if __name__ == "__main__":
    modules.globals.initialize()
    modules.menu.start_introduction()
    while True:
        try:
            modules.globals.temp = modules.sensor.SENSOR.temperature
            modules.globals.sensor_error = False
        except:
            modules.globals.sensor_error = True
        modules.handlers.encoder_handler()
        modules.handlers.button_handler()
        modules.heating_system.timer()
        if modules.globals.fermenter_running:
            modules.heating_system.heating_system(modules.globals.temp, modules.globals.temp_target, modules.globals.TEMP_MARGIN)
