from datetime import datetime, timedelta
import csv
import os.path
from shutil import copy

TEMPLATES = 'resources/templates/'
DT_FORMAT = "%d:%H:%M"


def load_profile(path):
    # Loads the current profile as specified in the file
    # resources/templates/profile.csv

    data = []
    with open(path, 'r') as file:
        reader = csv.DictReader(file)
        for line in reader:
            data.append((line['time'], line['temp']))

    return data


def key(time):
    day, hour, minute = time.split(":")
    return int(day)*10000 + int(hour)*100 + int(minute)


def save_profile(data, path):
    # Take data and write it into a file specified by path
    data.sort(key=lambda x: key(x[0]))

    # Remove any data with duplicate time
    index = 0
    while index < len(data) - 1:
        dt1 = datetime.strptime(data[index][0], DT_FORMAT)
        dt2 = datetime.strptime(data[index+1][0], DT_FORMAT)
        while (dt1 == dt2):
            data.pop(index+1)
            if index + 1 >= len(data):
                break
            else:
                dt2 = datetime.strptime(data[index+1][0], DT_FORMAT)
        index += 1

    with open(path, 'w') as file:
        fieldnames = ['time', 'temp']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for (time, temp) in data:
            writer.writerow({'time': time, 'temp': temp})


def create_cycles(num_cycles, path):
    # Append data to itself
    copy(path, os.path.join(TEMPLATES, "before_cycles.csv"))
    contents = load_profile(path)

    if float(contents[0][1]) != float(contents[-1][1]):
        return "Different first and last temperatures"

    data = []

    first_time = contents[0][0]
    first_time = datetime.strptime(first_time, DT_FORMAT)
    last_time = contents[-1][0]
    last_time = datetime.strptime(last_time, DT_FORMAT)
    next_time = last_time - first_time

    time_s, temp = contents[0]
    time = datetime.strptime(time_s, DT_FORMAT)
    data.append((time_s, temp))

    for i in range(num_cycles):
        for j in range(len(contents) - 1):
            time, temp = contents[j + 1]
            time = datetime.strptime(time, DT_FORMAT)
            time = time + i*next_time

            if time - first_time >= timedelta(days=31):
                break

            time_s = datetime.strftime(time, DT_FORMAT)
            data.append((time_s, temp))

    save_profile(data, path)
    return "ok"
