#!/usr/bin/python3
import sys
from datetime import datetime, date, time, timedelta
import sqlite3

# Expect a filename in argv
filename = sys.argv[1]

# Set up the database
con = sqlite3.connect("/usr/share/env_komora/data.db")
cur = con.cursor()
table_name = "profiles"


# Reading the header
file = open(filename, newline='', encoding='latin-1')
_ = file.readline()
company, test_name, date_string, current_temp, end_time_string = file.readline().split(",")
current_temp = float(current_temp)
day, month, year = date_string.split(".")
date = date(int(year), int(month), int(day))
end_hour, end_minute = end_time_string.strip().split(":")
end_time = time(int(end_hour), int(end_minute))
_ = file.readline()
_ = file.readline()

row = file.readline()
time_string, temp, rate, _, _ = row.strip().split(",")
temp = float(temp)
rate = float(rate)
hour, minute = time_string.split(":")
t = time(int(hour), int(minute))
dt = datetime.combine(date, t)

last_pos = file.tell()
row = file.readline()
time_string, _, _, _, _ = row.strip().split(",")
hour, minute = time_string.split(":")
t = time(int(hour), int(minute))
next_dt = datetime.combine(date, t)
file.seek(last_pos)

if(temp < current_temp):
    direction = -1
else:
    direction = 1

for step in (dt + timedelta(minutes=1*min) for min in range(1000)):
    if step > next_dt:
        break

    print(step, current_temp)
    cur.execute("INSERT INTO {tn} VALUES(?, ?)".format(tn=table_name), (step.timestamp(), current_temp))
    current_temp += direction*rate
    if((direction > 0 and current_temp > temp) or (direction < 0 and current_temp < temp)):
        current_temp = temp

row = file.readline()
while row:
    time_string, temp, rate, _, _ = row.strip().split(",")
    temp = float(temp)
    rate = float(rate)
    dt = next_dt

    last_pos = file.tell()
    row = file.readline()
    if row:
        time_string, _, _, _, _ = row.strip().split(",")
        hour, minute = time_string.split(":")
        t = time(int(hour), int(minute))
        next_dt = datetime.combine(date, t)
        file.seek(last_pos)
    else:
        next_dt = datetime.combine(date, end_time)

    if(temp < current_temp):
        direction = -1
    else:
        direction = 1

    for step in (dt + timedelta(minutes=1*min) for min in range(1000)):
        if step > next_dt:
            break

        cur.execute("INSERT INTO {tn} VALUES(?, ?)".format(tn=table_name), (step.timestamp(), current_temp))
        print(step, current_temp)
        current_temp += direction*rate
        if((direction > 0 and current_temp > temp) or (direction < 0 and current_temp < temp)):
            current_temp = temp
    row = file.readline()

con.commit()
