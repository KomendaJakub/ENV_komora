#!/usr/bin/python3

# Importing standard python libraries
import tkinter as tk

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from functools import partial
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import sys

# Importing source code
if len(sys.argv) > 1 and sys.argv[1] == 'debug':
    from src.sensor import get_measurement_test as get_measurement
else:
    from src.sensor import get_measurement

from src.temp_profile import open_window
from src.mail import mail
from src.graphing import recalculate


class App(tk.Tk):

    REFRESH_INTERVAL_MS = 10000

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

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

        self._build_menu()
        self._build_graph()

        # Create an animation
        # TODO: finish this up
        # Set up plot to call animate() function periodically
        self.ani = animation.FuncAnimation(
            self.fig, partial(self.animate), interval=self.REFRESH_INTERVAL_MS)

    def _build_menu(self):
        # Create a menu
        menu = tk.Frame(self, bg="white")  # bg=default_bg)
        menu.pack(side="top")

        # Define the buttons
        tk.Button(menu, text="Refresh",
                  command=self.get_new_profile).grid(row=0, column=0, padx=2, pady=1)
        # TODO: Change how opening of the edit_window is handled
        tk.Button(menu, text="Edit Profile",
                  command=lambda: open_window(self)).grid(row=0, column=1, padx=2, pady=1)
        tk.Button(menu, text="Export", command=self.export).grid(
            row=0, column=2, padx=2, pady=1)
        tk.Button(menu, text="Pause/Resume",
                  command=self.toggle_pause).grid(row=0, column=3, padx=2, pady=1)

    def _build_graph(self):
        # Create the tkinter graph
        self.frame_graph = tk.Frame(self)
        self.frame_graph.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Create a figure
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1, 1, 1)

        # To display figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(
            self.canvas, self.frame_graph, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side="bottom")

    def on_closing(self):
        self.quit()
        self.destroy()

    def clear_status(self):
        self.status.config(text="", bg="#d9d9d9")

    def set_status(self, message, color):
        self.status.config(text=message, bg=color)
        self.after(self.REFRESH_INTERVAL_MS, self.clear_status)

    def animate(self, i):
        # Read temperature (Celsius) from TMP102
        temp = round(get_measurement(), 2)
        result = self.controller.add_data_point(temp)

        if result == 'day_change':
            plt.savefig(f'figure_{self.controller.session.day}.png', dpi=1200)
            mail(self.controller.session)

        self.update_plot()

    def update_plot(self):
        session = self.controller.session

        # Draw x and y lists
        self.ax.clear()
        self.ax.plot(session.times, session.real_temps,
                     label="Actual Value", color="blue")
        self.ax.plot(session.times, session.target_temps,
                     label="Target", color="red")

        # Format plot
        self.ax.xaxis.set_major_locator(ticker.MaxNLocator(10))
        plt.xticks(rotation=45, ha='right')
        plt.subplots_adjust(bottom=0.30)
        plt.title('Temperature over Time')
        plt.xlabel('Time')
        plt.ylabel('Temperature (deg C)')
        plt.legend()
        self.canvas.draw()

    def toggle_pause(self):
        if self.controller.session.paused:
            self.controller.resume()
            self.ani.resume()
            self.clear_status()
        else:
            self.ani.pause()
            self.controller.pause()
            self.status.configure(text="Paused!", bg="red")

    def get_new_profile(self):
        # TODO: Change recalculate to accept a Session
        recalculate(self.controller.session.times,
                    self.controller.session.target_temps,
                    self.controller.session.day)
        self.set_status("Graph was refreshed!", "green")

    def export(self):
        answer = tk.simpledialog.askstring(
            "Email", "Insert and email address to which data will be exported", parent=self)

        if not answer:
            self.set_status("No email address inserted!", "red")
            return

        plt.savefig('data/export/figure.png', dpi=1200)
        # TODO: Change mail to accept a Session
        err = mail(self.controller.session, address=answer)
        if err == 0:
            self.set_status("Email sent successfully!", "green")
        else:
            self.set_status("Error, please retry or save manually!", "green")


# TODO: Get this into the state class
# default_bg = root.cget('bg')
