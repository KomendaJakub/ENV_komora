import datetime as dt
import dataclasses
from csv import DictReader
import zipfile
import io
from email.message import EmailMessage
import smtplib
import json
import pathlib
import tempfile
import shutil
from typing import Generator


CONFIG_PATH = pathlib.Path("resources/confidential.json")
TIME_FORMAT = "%H:%M:%S"


@dataclasses.dataclass
class Controller():
    "Keeping track of the values used in the application"
    last_event_t: dt.datetime = None
    prev_event_t: dt.datetime = None
    delay: dt.timedelta = dataclasses.field(default_factory=dt.timedelta)
    prev_delay: dt.timedelta = dataclasses.field(default_factory=dt.timedelta)
    real_temps: list[float] = dataclasses.field(default_factory=list)
    times: list = dataclasses.field(default_factory=list)
    target_temps: list[float] = dataclasses.field(default_factory=list)
    start_t: dt.datetime = dataclasses.field(default_factory=dt.datetime.now)
    day: int = 1
    hour: int = 1
    paused: bool = False
    measurement_path: pathlib.Path = None
    profile_path: pathlib.Path = None
    temp_save: bool = True
    partial_data: io.StringIO = dataclasses.field(default_factory=io.StringIO)
    profiler: Generator[float | None, dt.datetime, None] = None

    def add_data_point(self, measurement: float) -> str:
        delta_t = (dt.datetime.now() - self.delay) - \
            self.start_t

        if delta_t > (self.hour)*dt.timedelta(hours=1):
            self.hour += 1
            return "hour_change"

        if delta_t > (self.day)*dt.timedelta(days=1):
            self.daily_save()
            self.day += 1
            return "day_change"

        temporary = dt.datetime.strptime(
            str(delta_t - (self.day - 1)*dt.timedelta(days=1)), TIME_FORMAT + ".%f")

        self.times.append(temporary.strftime(TIME_FORMAT))
        self.real_temps.append(measurement)
        if self.profiler is not None:
            self.target_temps.append(
                self.profiler.send(delta_t + dt.timedelta(days=1)))
        else:
            self.target_temps.append(None)

        self.last_event_t = dt.datetime.now()
        return "ok"

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        new_delay = dt.datetime.now() - self.last_event_t

        if self.prev_event_t == self.last_event_t:
            self.delay += new_delay - self.prev_delay
        else:
            self.delay += new_delay
            self.prev_event_t = self.last_event_t

        self.prev_delay = new_delay
        self.paused = False

    def recalculate(self):
        self.profiler = self.get_profiler(None)
        next(self.profiler)
        # Using a generator
        # The order of recalculation matters
        # old data -> today's data

        # Recalculate old data
        pos = self.partial_data.seek(0, io.SEEK_END)
        if pos != 0:
            time_vals = []
            real_temps = []
            self.partial_data.seek(0, io.SEEK_SET)
            for line in self.partial_data:
                line = line.strip()
                time, real_temp, _ = line.split(',')
                time_vals.append(time)
                real_temps.append(real_temp)

            temp = map(lambda time: dt.datetime.strptime(
                time, "%d:" + TIME_FORMAT))
            targets = []
            for time in temp:
                time = dt.timedelta(
                    days=time.day, hours=time.hour, minutes=time.minute, seconds=time.second)
                targets.append(self.profiler.send(time))
                #            targets = map(lambda time: self.get_profile(dt.timedelta(
                #                days=time.day, hours=time.hour, minutes=time.minute, seconds=time.second)), temp)
            self.partial_data.seek(0, io.SEEK_SET)
            self.partial_data.write("time,measurement,set_temp\n")
            for time, real, target in zip(time_vals, real_temps, targets):
                self.partial_data.write(f"{time},{real},{target}\n")
            self.partial_data.truncate()

        # Recalculate this today's data
        temp = map(lambda time: dt.datetime.strptime(
            time, TIME_FORMAT), self.times)
        res = []
        for time in temp:
            time = dt.timedelta(days=self.day, hours=time.hour,
                                minutes=time.minute, seconds=time.second)
            res.append(self.profiler.send(time))
#        res = map(lambda time: self.get_profile(
#            dt.timedelta(days=self.day - 1, hours=time.hour, minutes=time.minute, seconds=time.second)), temp)

        self.target_temps.clear()
        self.target_temps.extend(res)

#    def get_profile(self, time: dt.datetime) -> float | None:
#        if time is None or self.profile_path is None:
#            return None
#
#        if not self.profile_path.is_file():
#            return None
#
#        time = time + dt.timedelta(days=1)
#        last_temp = None
#        last_time = None
#
#        with self.profile_path.open() as file:
#            reader = DictReader(file)
#            for row in reader:
#                prof_time = dt.datetime.strptime(row['time'], "%d:%H:%M")
#    #            prof_time.replace(year=time.year, month=time.month, day=time.day)
#                prof_time = dt.timedelta(days=prof_time.day, hours=prof_time.hour,
#                                         minutes=prof_time.minute, seconds=prof_time.second)
#                prof_temp = row['temp']
#
#                if (prof_time > time):
#                    if (last_time is None):
#                        return float(prof_temp)
#                    time_since_last = time - last_time
#                    time_between = prof_time - last_time
#                    delta_temp = float(prof_temp) - float(last_temp)
#                    ret = float(last_temp) + delta_temp * \
#                        (time_since_last/time_between)
#                    return float(ret)
#
#                else:
#                    last_time = prof_time
#                    last_temp = prof_temp
#
#        return float(prof_temp)

    def get_profiler(self, time: dt.datetime) -> float | None:
        # Expects time values to come in a monotonically increasing manner
        # Assumes profile exists
        time = yield None
        profile = []

        with self.profile_path.open() as file:
            reader = DictReader(file)
            for row in reader:
                prof_time = dt.datetime.strptime(row['time'], "%d:%H:%M")
                prof_time = dt.timedelta(days=prof_time.day, hours=prof_time.hour,
                                         minutes=prof_time.minute, seconds=prof_time.second)

                prof_temp = float(row['temp'])
                profile.append({"time": prof_time, "temp": prof_temp})

        prev_entry = None
        entry = profile.pop(0)
        while True:
            while time > entry["time"]:
                if len(profile) > 0:
                    prev_entry = entry
                    entry = profile.pop(0)
                else:
                    while True:
                        time = yield prev_entry["temp"]
            if prev_entry is None:
                time = yield entry["temp"]
            else:
                # Linear interpolation of temperature
                time_between = entry["time"] - prev_entry["time"]
                time_since = time - prev_entry["time"]
                delta_temp = entry["temp"] - prev_entry["temp"]
                target = prev_entry["temp"] + delta_temp * \
                    (time_since/time_between)
                time = yield target

    def save_session(self, fig_buf: io.BytesIO, prev_path: pathlib.Path, temporary: bool) -> IOError | None:
        if temporary:
            # No user saves yet
            assert (prev_path is None)
            new_file = tempfile.NamedTemporaryFile(delete=False)
            new_path = pathlib.Path(new_file.name)
            new_file.close()
            new_zip = zipfile.ZipFile(
                new_path, 'w', compression=zipfile.ZIP_DEFLATED)
            if zipfile.is_zipfile(self.measurement_path):
                old_zip = zipfile.ZipFile(self.measurement_path)
                self.write_figures(old_zip, new_zip, fig_buf)
                old_zip.close()

            self.measurement_path.unlink()
            self.write_profile(new_zip)
            new_zip.close()
            self.measurement_path = pathlib.Path(new_path)
            return

        if prev_path is None:
            # Not comming from save as
            prev_path = self.measurement_path

        # !Symlinks not handled
        if prev_path.match(self.measurement_path):
            # Saving to the same file
            was_zip = zipfile.is_zipfile(self.measurement_path)
            if was_zip:
                tempdir = tempfile.TemporaryDirectory()
                temp_path = pathlib.Path(tempdir.name)
                old_zip = pathlib.Path(shutil.move(
                    self.measurement_path, temp_path.joinpath("temp.zip")))
                old_zip = zipfile.ZipFile(old_zip, 'r')

            new_zip = zipfile.ZipFile(
                self.measurement_path, 'w', compression=zipfile.ZIP_DEFLATED)

            if was_zip:
                self.write_figures(old_zip, new_zip, fig_buf)
                old_zip.close()
                tempdir.cleanup()

            self.write_profile(new_zip)
            new_zip.close()
            return

        if self.temp_save:
            # This was the first save as
            new_zip = zipfile.ZipFile(
                self.measurement_path, 'w', compression=zipfile.ZIP_DEFLATED)
            if zipfile.is_zipfile(prev_path):
                old_zip = zipfile.ZipFile(prev_path, 'r')
                self.write_figures(old_zip, new_zip, fig_buf)
                old_zip.close()

            self.write_profile(new_zip)
            new_zip.close()
            prev_path.unlink()
            self.temp_save = False
            return

        assert (False and "Error while saving: Unreachable!")

    def write_figures(self, src: zipfile.ZipFile, dst: zipfile.ZipFile, fig_buf: io.BytesIO):
        figures = src.namelist()
        figures = [fig for fig in figures if fig.startswith("figures/")]
        today = f"figures/day{self.day}.png"
        if len(figures) == 0:
            fig_buf.seek(0)
            dst.writestr(today, fig_buf.read())
            return

        for fig in figures:
            if fig == today:
                fig_buf.seek(0)
                dst.writestr(today, fig_buf.read())
            else:
                dst.writestr(fig, src.read(fig))

    def write_profile(self, new_file: zipfile.ZipFile):
        rollback = self.partial_data.tell()
        if rollback == 0:
            self.partial_data.write("time,measurement,set_temp\n")
        for time, real, target in zip(self.times, self.real_temps, self.target_temps):
            time = dt.datetime.strptime(time, TIME_FORMAT)
            delta = time - dt.datetime.min
            days = delta.days
            rem, seconds = divmod(delta.seconds, 60)
            hours, minutes = divmod(rem, 60)
            time = f"{days:02}:{hours:02}:{minutes:02}:{seconds:02}"
            self.partial_data.write(f"{time},{real},{target}\n")
        new_file.writestr("measurement.csv", self.partial_data.getvalue())
        # Clean up
        self.partial_data.seek(rollback, io.SEEK_SET)
        self.partial_data.truncate()

        if self.profile_path is not None:
            new_file.write(self.profile_path, self.profile_path.name)

    def daily_save(self):
        pos = self.partial_data.tell()
        if pos == 0:
            # This is the first day change
            self.partial_data.write("time,measurement,set_temp\n")
        for time, real, target in zip(self.times, self.real_temps, self.target_temps):
            time = dt.datetime.strptime(TIME_FORMAT, time)
            delta = time - dt.datetime()
            days = delta.days
            rem, seconds = divmod(delta.seconds, 60)
            hours, minutes = divmod(rem, 60)
            time = f"{days:02}:{hours:02}:{minutes:02}:{seconds:02}"
            self.partial_data.write(f"{time},{real},{target}\n")

    def send_mail(self, address: str) -> str:
        # Load confidential data from config file
        with CONFIG_PATH.open() as file:
            config = json.load(file)

        # Create the email message
        now = dt.datetime.now()
        msg = EmailMessage()
        msg.set_content("Environmental chamber measurement from " +
                        now.strftime("%d/%m/%Y, %H:%M"))
        msg['Subject'] = "ENV chamber " + now.strftime("%d/%m/%Y, %H:%M")
        msg['From'] = config['EMAIL']
        msg['To'] = address

        # Add attachment to the email
        try:
            if self.temp_save:
                filename = "attachment.zip"
            else:
                filename = self.measurement_path.name
            with self.measurement_path.open('rb') as fb:
                prof = fb.read()
            msg.add_attachment(prof, maintype="Content-Disposition",
                               subtype="zip", filename=filename)
        except Exception as err:
            print(err)
            return "ERROR"

        # Connect to the mailing server and send the email
        try:
            with smtplib.SMTP_SSL(config['MAIL_SERVER'], 465) as smtp:
                smtp.login(config['EMAIL'], config['PASSWORD'])
                smtp.send_message(msg)
        except Exception as err:
            print(err)
            return "ERROR"

        return "ok"
