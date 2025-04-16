import datetime as dt
import dataclasses
from src.graphing import get_profile


@dataclasses.dataclass
class Session():
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
    paused: bool = False


class Controller():
    "Control session state and handle data updates, pause/resume"

    def __init__(self):
        self.session = Session()

    def add_data_point(self, measurement: float) -> str:

        # Add new values to the list
        delta_t = (dt.datetime.now() - self.session.delay) - \
            self.session.start_t
        if delta_t > (self.session.day)*dt.timedelta(days=1):
            self.session.day += 1
            return 'day_change'

        temporary = dt.datetime.strptime(
            str(delta_t - (self.session.day - 1)*dt.timedelta(days=1)), "%H:%M:%S.%f")

        # TODO: Change time_list to use normal time format ???
        self.session.times.append(temporary.strftime("%H:%M:%S"))
        self.session.real_temps.append(measurement)
        self.session.target_temps.append(
            get_profile(delta_t, self.session.day))

        self.session.last_event_t = dt.datetime.now()
        return 'ok'

    def pause(self):
        self.session.paused = True

    def resume(self):
        new_delay = dt.datetime.now() - self.session.last_event_t

        if self.session.prev_event_t == self.session.last_event_t:
            self.session.delay += new_delay - self.session.prev_delay
        else:
            self.session.delay += new_delay
            self.session.prev_event_t = self.session.last_event_t

        self.session.prev_delay = new_delay
        self.session.paused = False
