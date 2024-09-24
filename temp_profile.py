from datetime import datetime

HEADER_LINES = 4
ENCODING = "latin-1"
FILE_PATH = "/home/pi/Documents/ENV_komora/profile.csv"

def get_name():
    with open(FILE_PATH, "r", encoding=ENCODING) as file:
        file.readline()
        company, test, _ = file.readline().strip().split(",", 2)

    now = datetime.now()
    str = company.strip() + "_" + test.strip() + "_" + now.strftime("%Y_%m_%d_%H:%M")
    str = str.replace(" ", "_")
    return str

def get_profile(time):
    with open(FILE_PATH, "r", encoding=ENCODING) as file:
        contents = file.readlines()

    last_temp = None
    for row in contents[HEADER_LINES:]:
        time_str, temp, _ = row.strip().split(",", 2)
        hour, minute = time_str.split(":")
        prof_time = datetime(time.year, time.month, time.day, int(hour), int(minute))

        if(prof_time > time):
            if(last_temp == None):
                return None
            return float(last_temp)
        last_temp = temp

    if(last_temp == None):
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
        prof_time = datetime(time.year, time.month, time.day, int(hour), int(minute))
        if prof_time > time:
            break
        index += 1

    contents.insert(index, f"{time.hour}:{time.minute},{t},,,\n")

    with open(FILE_PATH, "w", encoding=ENCODING) as file:
        contents = "".join(contents)
        file.write(contents)


if __name__ == "__main__":
    dt = datetime.now()
    print(get_name())
