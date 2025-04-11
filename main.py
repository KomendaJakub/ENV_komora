#!/usr/bin/python3


import tkinter as tk

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from functools import partial
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import sys
import datetime as dt
from time import sleep
import dataclasses

if len(sys.argv) > 1 and sys.argv[1] == 'debug':
    from sensor import get_measurement_test as get_measurement
else:
    from sensor import get_measurement

from temp_profile import open_window
from mail import mail
from graphing import recalculate, get_profile


@dataclasses.dataclass
class Session():
    "Keeping track of the values used in the application"
    last_event_t: dt.datetime = None
    prev_event_t: dt.datetime = None
    delay: dt.timedelta = dataclasses.field(default_factory=dt.timedelta)
    prev_delay: int = 0
    real_temp_list: list[float] = dataclasses.field(default_factory=list)
    time_list: list = dataclasses.field(default_factory=list)
    temp_profile: list[float] = dataclasses.field(default_factory=list)
    start_t: dt.datetime = dataclasses.field(default_factory=dt.datetime.now)
    day: int = 1
    paused: bool = False


# This function is called periodically from FuncAnimation


class App(tk.Tk):

    second = 1000

    def __init__(self):
        super().__init__()

        # Setting up initial params
        self.configure(background="seashell2")
        self.title("Environmental Chamber Control")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # TODO: Cannot resize window with mouse
        self.resizable(True, True)

        # TODO: Add and iconphoto
        # self.iconphoto(True, tk.PhotoImage(file=path_to_logo))

        # Define a field to display status messages
        self.status = tk.Label(self, text="", bd=1, relief=tk.SUNKEN,
                               anchor=tk.N, justify=tk.CENTER)
        self.status.pack(fill=tk.X, side=tk.TOP, pady=1)

        # Create a menu
        self.frame_menu = tk.Frame(self, bg="white")  # bg=default_bg)
        self.frame_menu.pack(side="top")

        self.bt_refresh = tk.Button(self.frame_menu, text="Refresh",
                                    command=self.get_new_profile)
        self.bt_refresh.grid(row=0, column=0, padx=2, pady=1)

        # TODO: Change how opening of the edit_window is handled
        self.bt_edit = tk.Button(self.frame_menu, text="Edit Profile",
                                 command=lambda: open_window(self))

        self.bt_edit.grid(row=0, column=1, padx=2, pady=1)

        self.bt_export = tk.Button(
            self.frame_menu, text="Export", command=self.export)
        self.bt_export.grid(row=0, column=2, padx=2, pady=1)

        self.bt_start = tk.Button(self.frame_menu, text="Pause/Resume",
                                  command=lambda: self.pause_anim())
        self.bt_start.grid(row=0, column=3, padx=2, pady=1)

        # Create the tkinter graph
        self.frame_graph = tk.Frame(self)
        self.frame_graph.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Create a figure
        self.fig = plt.figure()

        # To display figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(
            self.canvas, self.frame_graph, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side="bottom")

        # Create an animation
        self.ax = self.fig.add_subplot(1, 1, 1)
        # TODO: finish this up
        # Set up plot to call animate() function periodically
        self.ani = animation.FuncAnimation(
            self.fig, partial(self.animate), interval=10*self.second)

    def on_closing(self):
        self.quit()
        self.destroy()

    def clear_status(self):
        self.status.config(text="", bg="#d9d9d9")

    def set_status(self, message, color):
        self.status.config(text=message, bg=color)
        self.after(10*self.second, self.clear_status)

    def animate(self, i):
        # Read temperature (Celsius) from TMP102
        temp_c = round(get_measurement(), 2)
        # Add new values to the list
        delta_t = (dt.datetime.now() - session.delay) - session.start_t
        if delta_t > (session.day)*dt.timedelta(days=1):
            session.day += 1
            plt.savefig(f'figure_{session.day}.png', dpi=1200)
            # TODO: Change mail implementation to accept Session
            mail(session.time_list, session.real_temp_list, session.temp_profile)
            session.time_list.clear()
            session.real_temp_list.clear()
            session.temp_profile.clear()
    #    print(delta_t)
        temporary = dt.datetime.strptime(
            str(delta_t - (session.day - 1)*dt.timedelta(days=1)), "%H:%M:%S.%f")
    #    print(delta_t)
    #    print(delta_t.strftime("%H:%M:%S"))
    #    time_list.append(delta_t.strftime("%H:%M:%S"))
        # TODO: Change time_list to use normal time format ???
        session.time_list.append(temporary.strftime("%H:%M:%S"))
        session.real_temp_list.append(temp_c)
        session.temp_profile.append(get_profile(delta_t, session.day))
        # Draw x and y lists
        self.ax.clear()
        self.ax.plot(session.time_list, session.real_temp_list,
                     label="Actual Value", color="blue")
        self.ax.plot(session.time_list, session.temp_profile,
                     label="Set Value", color="red")
        # Format plot
        self.ax.xaxis.set_major_locator(ticker.MaxNLocator(10))
        plt.xticks(rotation=45, ha='right')
        plt.subplots_adjust(bottom=0.30)
        plt.title('Temperature over Time')
        plt.xlabel('Time')
        plt.ylabel('Temperature (deg C)')
        plt.legend()
        self.canvas.draw()
        session.last_event_t = dt.datetime.now()

    def pause_anim(self):
        if session.paused:
            new_delay = dt.datetime.now() - session.last_event_t
            if session.prev_event_t == session.last_event_t:
                session.delay += session - session.prev_delay
            else:
                session.delay += dt.datetime.now() - session.last_event_t
                session.prev_event_t = session.last_event_t
            session.prev_delay = new_delay
            self.ani.resume()
            self.clear_status()
        else:
            self.ani.pause()
            self.status.config(text="Paused!", bg="red")
        session.paused = not session.paused

    def get_new_profile(self):
        # TODO: Change recalculate to accept a Session
        recalculate(session.time_list, session.temp_profile, session.day)
        self.set_status("Graph was refreshed!", "green")

    def export(self):
        answer = tk.simpledialog.askstring(
            "Email", "Insert and email address to which data will be exported", parent=self)
        if answer is None or answer.strip() == '':
            self.set_status("No email address inserted!", "red")
            return
        plt.savefig('figure.png', dpi=1200)
        # TODO: Change mail to accept a Session
        err = mail(session.time_list, session.real_temp_list,
                   session.temp_profile, answer)
        if err == 0:
            self.set_status("Email sent successfully!", "green")
        else:
            self.set_status("Error, please retry or save manually!", "green")


# TODO: Get this into the state class
# default_bg = root.cget('bg')

if __name__ == "__main__":
    session = Session()

    app = App()
    app.mainloop()
