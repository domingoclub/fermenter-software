import simpleio
import math
import modules.globals

def percent_to_duty_cycles(percent):
    if percent > 100:
        percent = 100
    duty_cycles = int(simpleio.map_range(percent, 0, 100, 0, 65535))
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
    elif hour > 1 and hour < modules.globals.TIME_THRESHOLD_DAYS:
        time_unit = str(int(hour)) + " hours"
    elif hour >= modules.globals.TIME_THRESHOLD_DAYS:
        time_unit = str(int(hour // 24)) + " days"
    return time_unit

def map_range(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
