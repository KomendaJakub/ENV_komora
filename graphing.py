import datetime as dt
from csv import DictReader
import os

DIR_PATH = os.path.dirname(__file__)
FILE_PATH = os.path.join(DIR_PATH, 'profile.csv')


def recalculate(time_list, set_temp_list, elapsed_days):
    temp = map(lambda time: dt.datetime.strptime(time, "%H:%M:%S"), time_list)
    res = map(lambda time: get_profile(
        dt.timedelta(days=elapsed_days - 1, hours=time.hour, minutes=time.minute, seconds=time.second), elapsed_days), temp)
    set_temp_list.clear()
    set_temp_list.extend(res)
    return


def get_profile(time, elapsed_days, file=FILE_PATH):
    if time is None:
        return None
    time = time + dt.timedelta(days=1)
#    print("Time at input: " + str(time))
    last_temp = None
    last_time = None

    with open(file) as file:
        reader = DictReader(file)
        for row in reader:
            prof_time = dt.datetime.strptime(row['time'], "%d:%H:%M")
#            prof_time.replace(year=time.year, month=time.month, day=time.day)
            prof_time = dt.timedelta(days=prof_time.day, hours=prof_time.hour,
                                     minutes=prof_time.minute, seconds=prof_time.second)
            prof_temp = row['temp']

            if (prof_time > time):
                #                print("Time at output: " + str(prof_time))
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
