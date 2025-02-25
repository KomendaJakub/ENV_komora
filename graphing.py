import datetime as dt
from csv import DictReader
import os

DIR_PATH = os.path.dirname(__file__)
FILE_PATH = os.path.join(DIR_PATH, 'profile.csv')


def recalculate(time_list, set_temp_list):
    res = map(lambda time: get_profile(
        dt.datetime.strptime(time, "%H:%M:%S")), time_list)
    set_temp_list.clear()
    set_temp_list.extend(res)
    return


def get_profile(time):
    if time is None:
        return None

    last_temp = None
    last_time = None

    with open(FILE_PATH) as file:
        reader = DictReader(file)
        for row in reader:
            prof_time = dt.datetime.strptime(row['time'], "%H:%M")
            prof_time.replace(year=time.year, month=time.month, day=time.day)
            prof_temp = row['temp']

            if (prof_time > time):
                if (last_time is None):
                    return float(prof_temp)
                time_since_last = time - last_time
                time_between = prof_time - last_time
                delta_temp = float(prof_temp) - float(last_temp)
                ret = float(last_temp) + delta_temp * \
                    (time_since_last/time_between)
                return float(ret)

            else:
                last_time = prof_time
                last_temp = prof_temp

    return float(prof_temp)
