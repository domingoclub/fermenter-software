import board
import busio
import os

SENSOR_MODEL = os.getenv('sensor_model')

if SENSOR_MODEL == "sht31d":
    import adafruit_sht31d
if SENSOR_MODEL == "mcp9808":
    import adafruit_mcp9808
if SENSOR_MODEL == "aht20":
    import adafruit_ahtx0

try:
    SENSOR_I2C = busio.I2C(board.GP13, board.GP12)
    if SENSOR_MODEL == "sht31d":
        SENSOR = adafruit_sht31d.SHT31D(SENSOR_I2C)
    if SENSOR_MODEL == "mcp9808":
        SENSOR = adafruit_mcp9808.MCP9808(SENSOR_I2C)
    if SENSOR_MODEL == "aht20":
        SENSOR = adafruit_ahtx0.AHTx0(SENSOR_I2C)
except:
    print("sensor disconnected")