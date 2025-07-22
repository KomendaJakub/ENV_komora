import datetime as dt
import dataclasses
import zipfile
import io
from email.message import EmailMessage
import smtplib
import json
import openpyxl as xl
import pathlib
import tempfile
import shutil
from typing import Generator
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


CONFIG_PATH = pathlib.Path("resources/confidential.json")
TIME_FORMAT = "%d:%H:%M:%S"
PROFILE_TIME_FORMAT = "%d:%H:%M"
EM_DASH = u'\u2014'


def skip_first(func, *args, **kwargs):
    def wrapper(*args, **kwargs):
        gen = func(*args, **kwargs)
        next(gen)
        return gen
    return wrapper


class DataPoint():
    # duration of internal time from the beginning of measurement
    def __init__(self, duration: dt.timedelta, real_temp: float, target_temp: float):
        self.duration = duration
        self.real_temp = real_temp
        self.target_temp = target_temp

    @classmethod
    def from_str(cls, string: str):
        duration, real_temp, target_temp = string.strip().split(",")
        hours, minutes, seconds = duration.strip().split(":")
        duration = dt.timedelta(hours=hours, minutes=minutes, seconds=seconds)
        real_temp = float(real_temp)
        target_temp = float(target_temp)
        return cls(duration, real_temp, target_temp)

    def __repr__(self):
        return f"DataPoint(duration={repr(self.duration)}, real_temp={repr(self.real_temp)}, target_temp={repr(self.target_temp)})"

    def __str__(self):
        seconds = int(self.duration.total_seconds())
        quot, seconds = divmod(seconds, 60)
        hours, minutes = divmod(quot, 60)
        duration = f"{hours:02}:{minutes:02}:{seconds:02}"
        return f"{duration},{self.real_temp},{self.target_temp}"


class ProfilePoint():
    # duration of internal time from the beginning of measurement
    def __init__(self, duration: dt.datetime, target_temp: float):
        self.duration = duration
        self.target_temp = target_temp

    @classmethod
    def from_str(cls, string: str):
        duration, target_temp = string.strip().split(",")
        hours, minutes, _ = map(int, duration.strip().split(":"))
        duration = dt.timedelta(hours=hours, minutes=minutes)
        target_temp = float(target_temp)
        return cls(duration, target_temp)

    @classmethod
    def from_xl(cls, time: str, temp: str):
        duration = time
        target_temp = float(temp)
        return cls(duration, target_temp)

    def __repr__(self):
        return f"ProfilePoint(duration={repr(self.duration)}, target_temp={repr(self.target_temp)})"

    def __str__(self):
        seconds = int(self.duration.total_seconds())
        quot, seconds = divmod(seconds, 60)
        hours, minutes = divmod(quot, 60)
        duration = f"{hours:02}:{minutes:02}:{seconds:02}"
        return f"{duration},{self.target_temp}"


@dataclasses.dataclass
class Controller():
    "Keeping track of the values used in the application"
    last_event_t: dt.datetime = None
    prev_event_t: dt.datetime = None
    delay: dt.timedelta = dataclasses.field(default_factory=dt.timedelta)
    prev_delay: dt.timedelta = dataclasses.field(default_factory=dt.timedelta)
    data: list[DataPoint] = dataclasses.field(default_factory=list)
    start_t: dt.datetime = None
    day: int = 1
    hour: int = 1
    paused: bool = False
    measurement_path: pathlib.Path = None
    profile_path: pathlib.Path = None
    temp_save: bool = True
    partial_save: io.StringIO = dataclasses.field(default_factory=io.StringIO)
    profiler: Generator[float | None, dt.datetime, None] = None

    def add_data_point(self, real_temp: float) -> str:
        duration = dt.datetime.now() - (self.start_t + self.delay)

        if duration > (self.hour)*dt.timedelta(hours=1):
            self.hour += 1
            return "hour_change"

        if duration > (self.day)*dt.timedelta(days=1):
            self.daily_save()
            self.hour = 1
            self.day += 1
            return "day_change"

        if self.profiler is not None:
            target_temp = self.profiler.send(duration)
        else:
            target_temp = None

        data_point = DataPoint(
            duration=duration, real_temp=real_temp, target_temp=target_temp)
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
        self.profiler = self.get_profiler()
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
                data_point.target_temp = self.profiler.send(
                    data_point.duration)
                self.partial_save.write(f"{data_point}\n")
            self.partial_save.truncate()

        target_temps = []
        # Recalculate today's data
        for data_point in self.data:
            data_point.target_temp = self.profiler.send(data_point.duration)
            target_temps.append(data_point.target_temp)

        return target_temps

    @skip_first
    def get_profiler(self) -> float | None:
        # Expects time values to come in a monotonically increasing order
        # Assumes profile exists
        path = self.profile_path

        if path is None:
            while True:
                time = yield None

        profile = self.parse_profile(path)
        time = yield None

        prev_point: ProfilePoint = None
        profile_point = profile.pop(0)
        while True:
            while time > profile_point.duration:
                if len(profile) > 0:
                    prev_point = profile_point
                    profile_point = profile.pop(0)
                else:
                    while True:
                        if prev_point is not None:
                            time = yield prev_point.target_temp
                        else:
                            time = yield None
            if prev_point is None:
                time = yield profile_point.target_temp
            else:
                # Linear interpolation of temperature
                time_between = profile_point.duration - prev_point.duration
                time_since = time - prev_point.duration
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

        # Permanent save
        path = self.measurement_path
        was_zip = zipfile.is_zipfile(path)
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

        assert False, "Unreachable!"

    def save_as_session(self) -> IOError | None:
        with zipfile.ZipFile(self.measurement_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            self.write_profile(archive)
            length = self.partial_save.seek(0, io.SEEK_END)
            # Plot previous data
            if length != 0:
                self.partial_save.seek(0, io.SEEK_SET)
                self.partial_save.readline()
                day = 1
                data: list[DataPoint] = []
                for line in self.partial_save.readlines():
                    data_point = DataPoint.from_str(line.strip())
                    if data_point.duration.day <= day:
                        data.append(data_point)
                    else:
                        self.plot(archive, data, day)
                        data.clear()
                        data.append(data_point)
                        day += 1

            # Plot todays data
            self.plot(archive, self.data, self.day)
        self.temp_save = False

    def plot(self, dst: zipfile.ZipFile, data: list[DataPoint], day: int) -> None:
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.clear()
        # Assumes data is just one day

        times = []

        for data_point in data:
            quot, seconds = divmod(data_point.duration.seconds, 60)
            hours, minutes = divmod(quot, 60)
            time = f"{hours:02}:{minutes:02}:{seconds:02}"
            times.append(time)

        real_temps = [
            data_point.real_temp for data_point in data]
        target_temps = [
            data_point.target_temp for data_point in data]
        ax.plot(times, real_temps,
                label="Actual", color="blue")
        ax.plot(times, target_temps,
                label="Target", color="red")
        # Format plot
        ax.xaxis.set_major_locator(ticker.MaxNLocator(10))
        plt.xticks(rotation=45, ha="right")
        plt.subplots_adjust(bottom=0.30)
        measurement_name = self.measurement_path.stem
        plt.title(f"{measurement_name}"
                  f"{EM_DASH} Day {day}")
        plt.xlabel("Time (hh:mm:ss)")
        plt.ylabel("Temperature (°C)")
        plt.legend()
        with dst.open(f"figures/day{day}", 'w') as file:
            fig.savefig(file, format='png', dpi=1200)
        plt.close(fig)

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
            self.partial_save.write("duration,measurement,set_temp\n")
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
            self.partial_save.write("duration,measurement,set_temp\n")
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

    def preview_profile(self, path):
        duration = []
        target = []
        profile = self.parse_profile(path)

        for point in profile:
            target.append(point.target_temp)
            # dur = int(point.duration.total_seconds())
            # quot = dur // 60
            # hours, minutes = divmod(quot, 60)
            # duration.append(f"{hours:02}:{minutes:02}")
            duration.append(int(point.duration.total_seconds()))

        return duration, target

    def parse_profile(self, path: pathlib.Path) -> [ProfilePoint]:
        profile: [ProfilePoint] = []
        file_format = path.suffix

        if file_format == ".csv":
            with path.open() as file:
                # Skip header
                next(file)
                for line in file:
                    line = line.strip()
                    profile_point = ProfilePoint.from_str(line)
                    profile.append(profile_point)

        elif file_format == ".xlsx":
            wb = xl.load_workbook(filename=path, data_only=True)
            ws = wb.active
            rows = iter(ws)
            next(rows)
            for row in rows:
                time = row[0].value
                temp = row[1].value
                if time is None or temp is None:
                    break
                point = ProfilePoint.from_xl(time=time, temp=temp)
                profile.append(point)
        else:
            raise ValueError(f"Unsupported file format {file_format} for a profile."
                             f"Supported formats are '.csv' and '.xlsx'.")
        return profile
