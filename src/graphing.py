import datetime as dt
from csv import DictReader
# import os

# DIR_PATH = os.path.dirname(__file__)
# DIR_PATH = os.getcwd()
# FILE_PATH = os.path.join(DIR_PATH, 'resources/profile.csv')
FILE_PATH = 'resources/templates/profile.csv'


def recalculate(session):
    temp = map(lambda time: dt.datetime.strptime(
        time, "%H:%M:%S"), session.times)
    res = map(lambda time: get_profile(
        dt.timedelta(days=session.day - 1, hours=time.hour, minutes=time.minute, seconds=time.second), session.day), temp)
    session.target_temps.clear()
    session.target_temps.extend(res)
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
