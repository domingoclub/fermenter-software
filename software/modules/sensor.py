import board
import busio
import os
import modules.globals

SENSOR_MODEL = os.getenv('sensor_model')

if SENSOR_MODEL == "sht31d":
    import adafruit_sht31d
if SENSOR_MODEL == "mcp9808":
    import adafruit_mcp9808
if SENSOR_MODEL == "aht20":
    import adafruit_ahtx0

SENSOR_I2C = busio.I2C(board.GP13, board.GP12)



def sensor_start():
    try:
        if SENSOR_MODEL == "sht31d":
            modules.globals.SENSOR = adafruit_sht31d.SHT31D(SENSOR_I2C)
        if SENSOR_MODEL == "mcp9808":
            modules.globals.SENSOR = adafruit_mcp9808.MCP9808(SENSOR_I2C)
        if SENSOR_MODEL == "aht20":
            modules.globals.SENSOR = adafruit_ahtx0.AHTx0(SENSOR_I2C)
    except Exception as e:
        print(e)
