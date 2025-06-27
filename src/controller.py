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
import matplotlib as plt


CONFIG_PATH = pathlib.Path("resources/confidential.json")
TIME_FORMAT = "%d:%H:%M:%S"
PROFILE_TIME_FORMAT = "%d:%H:%M"
EM_DASH = u'\u2014'


class DataPoint():
    def __init__(self, time: dt.datetime, real_temp: float, target_temp: float):
        self.time = time
        self.real_temp = real_temp
        self.target_temp = target_temp

    @classmethod
    def from_str(cls, string: str):
        time, real_temp, target_temp = string.strip().split(",")
        time = dt.datetime.strptime(time, TIME_FORMAT)
        real_temp = float(real_temp)
        target_temp = float(target_temp)
        return cls(time, real_temp, target_temp)

    def __repr__(self):
        return f"DataPoint(time={repr(self.time)}, real_temp={repr(self.real_temp)}, target_temp={repr(self.target_temp)})"

    def __str__(self):
        delta = self.time - dt.datetime.min
        days = delta.days
        rem, seconds = divmod(delta.seconds, 60)
        hours, minutes = divmod(rem, 60)
        time = f"{days:02}:{hours:02}:{minutes:02}:{seconds:02}"
        return f"{time},{self.real_temp},{self.target_temp}"


class ProfilePoint():
    def __init__(self, time: dt.datetime, target_temp: float):
        self.time = time
        self.target_temp = target_temp

    @classmethod
    def from_str(cls, string: str):
        time, target_temp = string.strip().split(",")
        time = dt.datetime.strptime(time, PROFILE_TIME_FORMAT)
        target_temp = float(target_temp)
        return cls(time, target_temp)

    def __repr__(self):
        return f"ProfilePoint(time={repr(self.time)}, target_temp={repr(self.target_temp)})"

    def __str__(self):
        time = self.time.strftime(PROFILE_TIME_FORMAT)
        return f"{time},{self.target_temp}"


@dataclasses.dataclass
class Controller():
    "Keeping track of the values used in the application"
    last_event_t: dt.datetime = None
    prev_event_t: dt.datetime = None
    delay: dt.timedelta = dataclasses.field(default_factory=dt.timedelta)
    prev_delay: dt.timedelta = dataclasses.field(default_factory=dt.timedelta)
    data: list[DataPoint] = dataclasses.field(default_factory=list)
    start_t: dt.datetime = dataclasses.field(default_factory=dt.datetime.now)
    day: int = 1
    hour: int = 1
    paused: bool = False
    measurement_path: pathlib.Path = None
    profile_path: pathlib.Path = None
    temp_save: bool = True
    partial_save: io.StringIO = dataclasses.field(default_factory=io.StringIO)
    profiler: Generator[float | None, dt.datetime, None] = None

    def add_data_point(self, real_temp: float) -> str:
        delta_t = (dt.datetime.now() - self.delay) - \
            self.start_t

        if delta_t > (self.hour)*dt.timedelta(hours=1):
            self.hour += 1
            return "hour_change"

        if delta_t > (self.day)*dt.timedelta(days=1):
            self.daily_save()
            self.day += 1
            return "day_change"

        # TODO: This may be broken because of the new TIME_FORMAT
        time = dt.datetime.strptime(
            str(delta_t - (self.day - 1)*dt.timedelta(days=1)), "%H:%M:%S.%f")

        if self.profiler is not None:
            target_temp = self.profiler.send(time)
            # target_temp = self.profiler.send(delta_t + dt.timedelta(days=1))
        else:
            target_temp = None

        data_point = DataPoint(
            time=time, real_temp=real_temp, target_temp=target_temp)
        self.data.append(data_point)

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
        pos = self.partial_save.seek(0, io.SEEK_END)
        if pos != 0:
            data = []
            self.partial_save.seek(0, io.SEEK_SET)
            for line in self.partial_save:
                line = line.strip()
                data_point = DataPoint.from_str(line)
                data.append(data_point)

            self.partial_save.seek(0, io.SEEK_SET)
            self.partial_save.write("time,measurement,set_temp\n")
            for data_point in data:
                data_point.target_temp = self.profiler.send(data_point.time)
                self.partial_save.write(f"{data_point}\n")
            self.partial_save.truncate()

        # Recalculate today's data
        for data_point in self.data:
            data_point.target_temp = self.profiler.send(data_point.time)

    # TODO: Refactor so that you dont have to skip first iteration see: James Powell
    def get_profiler(self, time: dt.datetime) -> float | None:
        # Expects time values to come in a monotonically increasing manner
        # Assumes profile exists
        time = yield None
        profile = []

        if self.profile_path is None:
            while True:
                time = yield None

        with self.profile_path.open() as file:
            # Skip header
            next(file)
            for line in file:
                line = line.strip()
                profile_point = ProfilePoint.from_str(line)
                profile.append(profile_point)

        prev_point: ProfilePoint = None
        profile_point = profile.pop(0)
        while True:
            while time > profile_point.time:
                if len(profile) > 0:
                    prev_point = profile_point
                    profile_point = profile.pop(0)
                else:
                    while True:
                        if prev_point is not None:
                            time = yield prev_point.time
                        else:
                            time = yield None
            if prev_point is None:
                time = yield profile_point.target_temp
            else:
                # Linear interpolation of temperature
                time_between = profile_point.time - prev_point.time
                time_since = time - prev_point.time
                delta_temp = profile_point.target_temp - prev_point.target_temp
                target = prev_point.target_temp + delta_temp * \
                    (time_since/time_between)
                time = yield target

    def save_session(self, fig_buf: io.BytesIO, temporary: bool) -> IOError | None:
        if temporary:
            # No user saves yet
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

        # TODO: refactor this
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

        assert False, "Unreachable!"

    def save_as_session(self, fig_buf: io.BytesIO) -> IOError | None:
        assert False, "Not fully implemented"
        self.profiler = self.get_profiler()
        next(self.profiler)
        day = 1
        line = self.partial_save.readline()
        real_temps = []
        target_temps = []
        times = []
        while line != "":
            line = self.partial_save.readline()
            time, real_temp, target_temp = line.strip().split(',')
            real_temp = float(real_temp)
            target_temp = float(target_temp)
            time = dt.datetime.strptime(time, "%d:" + TIME_FORMAT)
            if time.day < day:
                times.append(time)
                real_temps.append(real_temp)
                target_temps.append(target_temp)
            else:
                # plot values that you have collected
                fig = plt.figure()
                ax = fig.add_subplot(1, 1, 1)
                ax.plot(times, real_temps, label="Actual", color="blue")
                ax.plot(times, target_temps,
                        label="Target", color="red")

                # Format plot
                ax.xaxis.set_major_locator(plt.ticker.MaxNLocator(10))
                plt.xticks(rotation=45, ha="right")
                plt.subplots_adjust(bottom=0.30)
                plt.title(f"{self.measurement_name.get()} {
                          EM_DASH} Day {self.controller.day}")
                plt.xlabel("Time (hh:mm:ss)")
                plt.ylabel("Temperature (°C)")
                plt.legend()

                # dispose of the values and append new values
                times.clear()
                real_temps.clear()
                target_temps.clear()
                times.append(time)
                real_temps.append(real_temp)
                target_temps.append(target_temp)
                day += 1

        pass

    def plot(self, dst: zipfile.ZipFile, times: [dt.datetime], ) -> None:
        pass

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
        rollback = self.partial_save.seek(0, io.SEEK_END)
        self.partial_save.seek(0, io.SEEK_SET)
        if rollback == 0:
            self.partial_save.write("time,measurement,set_temp\n")
        for data_point in self.data:
            self.partial_save.write(f"{data_point}\n")
        new_file.writestr("measurement.csv", self.partial_save.getvalue())
        # Clean up
        self.partial_save.seek(rollback, io.SEEK_SET)
        self.partial_save.truncate()

        if self.profile_path is not None:
            new_file.write(self.profile_path, self.profile_path.name)

    def daily_save(self):
        pos = self.partial_save.seek(0, io.SEEK_END)
        if pos == 0:
            # This is the first day change
            self.partial_save.write("time,measurement,set_temp\n")
        for data_point in self.data:
            self.partial_save.write(f"{data_point}\n")

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
