#!/usr/bin/python3
from datetime import datetime
import os
import csv

HEADER_LINES = 4
DIR_PATH = os.path.dirname(__file__)
FILE_PATH = os.path.join(DIR_PATH, 'profile.csv')


def get_profile(time):
    file = open(FILE_PATH)
    reader = csv.DictReader(file)

    last_temp = None
    for row in reader:
        hour, minute = row['time'].split(":")
        prof_time = datetime(time.year, time.month,
                             time.day, int(hour), int(minute))

        if (prof_time > time):
            if (last_temp == None):
                return None
            return float(last_temp)
        last_temp = float(row['temp'])

    if (last_temp == None):
        return None


def set_temp(time, t):

    hour, minute = time.strip().split(":")
    now = datetime.now()
    time = datetime(now.year, now.month, now.day, int(hour), int(minute))
    t = float(t)

    with open(FILE_PATH, "r", encoding=ENCODING) as file:
        contents = file.readlines()

    index = HEADER_LINES
    for row in contents[HEADER_LINES:]:
        time_str, temp, _ = row.strip().split(",", 2)
        hour, minute = time_str.split(":")
        prof_time = datetime(time.year, time.month,
                             time.day, int(hour), int(minute))
        if prof_time > time:
            break
        index += 1

    contents.insert(index, f"{time.hour}:{time.minute},{t},,,\n")

    with open(FILE_PATH, "w", encoding=ENCODING) as file:
        contents = "".join(contents)
        file.write(contents)


if __name__ == "__main__":
    get_profile(None)
