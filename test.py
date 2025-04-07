#!/usr/bin/python3

from graphing import get_profile
import datetime as dt

TEST_PROFILE_PATH = "test_profile.csv"


def t_get_profile(time, expected_temp):
    calculated = get_profile(time, expected_temp, TEST_PROFILE_PATH)
    assert (calculated == expected_temp), f"EXP: {
        expected_temp} != {calculated} :CALC"


print("Testing get_profile()")
# Testing if the starting temperature setting is correct.
# i.e. it should be equal to the first set_temp
time = dt.timedelta(hours=0, minutes=0)
t_get_profile(time, 0)

# Testing if the last temperature setting is correct.
# i.e. it should be equal to the last temp_set
time = dt.timedelta(days=1, hours=23, minutes=0)
t_get_profile(time, 100)


# Testing a temperature setting at the moment it is set.
#
time = dt.timedelta(hours=0, minutes=1)
t_get_profile(time, 12.0)


# Testing a temperature setting at th moment it is set for 2nd day.
time = dt.timedelta(days=1, hours=6, minutes=0)
t_get_profile(time, 0)


# Testing if the temperature gradient is working correctly
#
time_0 = 1
time_1 = 10
interval = time_1 - time_0
offset = 2
minutes = time_0 + offset
time = dt.timedelta(hours=0, minutes=minutes + time_0)
temp_0 = 12
temp_1 = 56
temp = temp_0 + (temp_1 - temp_0) * minutes / interval
t_get_profile(time, temp)


# Testing if the temperature gradient is working correctly
# over the day boundary
time_0 = 21*60
time_1 = 1*1440 + 6*60
interval = time_1 - time_0
offset = 3*60 + 2*1
minutes = (time_0 + offset) % 1440
days = (time_0 + offset) // 1440
time = dt.timedelta(days=1, hours=0, minutes=minutes + time_0)
temp_0 = 100
temp_1 = 0
temp = temp_0 + (temp_1 - temp_0) * (minutes) / interval
t_get_profile(time, 100 - 33.7037037)


print("All tests passed successfully")
