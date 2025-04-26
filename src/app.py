#!/usr/bin/python3

# Importing standard python libraries
import tkinter as tk

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from functools import partial
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import sys
import os.path
from datetime import datetime

# Importing source code
if len(sys.argv) > 1 and sys.argv[1] == 'debug':
    from src.sensor import get_measurement_test as get_measurement
else:
    from src.sensor import get_measurement

from src.edit_window import Edit_Window
# from src.temp_profile import open_window
from src.mail import mail
from src.export import save_session
from src.graphing import recalculate

SAVE_DIR = "data/saves/"
ICONS = "resources/icons/"


class App(tk.Tk):

    REFRESH_INTERVAL_MS = 10000

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        # Setting up initial params
        self.configure(background="seashell2")
        self.title("Environmental Chamber Control")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Set standard window size
        self.geometry("854x480")
        self.update()
        self.geometry()
        self.minsize(self.winfo_width(), self.winfo_height())
        self.resizable(True, True)

        # TODO: Add and iconphoto
        # self.iconphoto(True, tk.PhotoImage(file=path_to_logo))

        self.default_bg = self.cget('bg')

        self._build_menu()

        # Define a field to display status messages
        self.status = tk.Label(self, text="", bd=1, relief=tk.SUNKEN,
                               anchor=tk.N, justify=tk.CENTER)
        self.status.pack(fill=tk.X, side=tk.TOP, pady=1)

        self._build_graph()

        # Set up plot to call animate() function periodically
        self.ani = animation.FuncAnimation(
            self.fig, partial(self.animate), interval=self.REFRESH_INTERVAL_MS)

        self.mainloop()

        """
        name = tk.filedialog.askdirectory(title="Chose a directory for autosaves",
                                          parent=self,
                                          initialdir=os.path.join(
                                              SAVE_DIR, date)
                                          )
        name = tk.simpledialog.askstring(
            "Measurement name", "Insert the name under which this measurement will be saved.", parent=self,
            initialvalue=date)

        self.name_label["text"] = f"Measurement: {
            self.controller.session.measurement_name}"

        """

    def _build_menu(self):
        # Adding the top most row of named buttons
        menu = tk.Menu(self, tearoff=0)
        self.config(menu=menu)

        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New")
        file_menu.add_command(label="Load")
        file_menu.add_command(label="Save",
                              command=self.save)
        file_menu.add_command(label="Save as",
                              command=self.save)
        file_menu.add_command(label="Email",
                              command=self.export)

        measurement_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=measurement_menu)
        measurement_menu.add_command(label="Refresh",
                                     command=self.get_new_profile)
        measurement_menu.add_command(label="Pause/Resume",
                                     command=self.toggle_pause)

        profile_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Profile", menu=profile_menu)
        profile_menu.add_command(label="Load")
        profile_menu.add_command(label="Edit",
                                 command=lambda: Edit_Window(self))
        profile_menu.add_command(label="Save as")

        help_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About")

        # Adding buttons with pictures
        button_frame = tk.Frame(self)
        button_frame.pack(side=tk.TOP, fill=tk.X, expand=False)

        # The image is stored to avoid GC
        # TODO:Add a function that allows to load a previous measurement
        self.icon_open = tk.PhotoImage(
            file=os.path.join(ICONS, "open.png"))
        tk.Button(button_frame, image=self.icon_open).grid(row=0, column=0)

        self.icon_edit = tk.PhotoImage(file=os.path.join(
            ICONS, "edit.png"))
        tk.Button(button_frame, image=self.icon_edit,
                  command=lambda: Edit_Window(self)).grid(row=0, column=1)

        self.icon_save = tk.PhotoImage(
            file=os.path.join(ICONS, "save.png"))
        tk.Button(button_frame, image=self.icon_save,
                  command=self.save).grid(row=0, column=2)

        # TODO:Add separate save as functionality default name Untitled n
        self.icon_save_as = tk.PhotoImage(
            file=os.path.join(ICONS, "save_as.png"))
        tk.Button(button_frame, image=self.icon_save_as,
                  command=self.save).grid(row=0, column=3)

        self.icon_email = tk.PhotoImage(
            file=os.path.join(ICONS, "email.png"))
        tk.Button(button_frame, image=self.icon_email,
                  command=self.export).grid(row=0, column=4)

        self.icon_refresh = tk.PhotoImage(
            file=os.path.join(ICONS, "refresh.png"))
        tk.Button(button_frame, image=self.icon_refresh,
                  command=self.get_new_profile).grid(row=0, column=5)

        # TODO: Change the icons based on state
        self.icon_resume = tk.PhotoImage(
            file=os.path.join(ICONS, "resume.png"))
        self.icon_pause = tk.PhotoImage(
            file=os.path.join(ICONS, "pause.png"))
        tk.Button(button_frame, image=self.icon_resume,
                  command=self.toggle_pause).grid(row=0, column=6)

#    Icons used come from Icons8
#    <a target="_blank" href="https://icons8.com/icon/Ygov9LJC2LzE/document">Document</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>
#    <a target="_blank" href="https://icons8.com/icon/poyizCBxzCRY/edit-text-file">Document</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>
#    <a target="_blank" href="https://icons8.com/icon/yFBJCjFJpLXw/save">Save</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>
#    <a target="_blank" href="https://icons8.com/icon/wC9budkHyeKg/save-as">Save as</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>
#    <a target="_blank" href="https://icons8.com/icon/6BBCqlzE4iKd/letter">Email</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>
#    <a target="_blank" href="https://icons8.com/icon/K2njhUKeLfle/reset">Refresh</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>
#    <a target="_blank" href="https://icons8.com/icon/yV9PqJWVRl5T/resume-button">Resume Button</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>
#    <a target="_blank" href="https://icons8.com/icon/Z2aInWmsldJ6/pause">Pause</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>

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
        self.ani.event_source.stop()
        plt.close('all')
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
            fig_path = os.path.join(SAVE_DIR,
                                    f"{self.controller.session.measurement_name}/figure_{self.controller.session.day}.png")
            plt.savefig(
                f'data/saves/figure_{self.controller.session.day}.png', dpi=1200)

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
        recalculate(self.controller.session)
        self.set_status("Graph was refreshed!", "green")

    def export(self):
        answer = tk.simpledialog.askstring(
            "Email", "Insert and email address to which data will be exported", parent=self)

        if not answer:
            self.set_status("No email address inserted!", "red")
            return

        plt.savefig('data/export/figure.png', dpi=1200)
        err = mail(self.controller.session, address=answer)
        connection_failed = "Error while connecting to the mailing server. Please try to save manually."
        if err == "ok":
            self.set_status("Email sent successfully!", "green")
        elif err == connection_failed:
            answer = tk.messagebox.askyesno(
                title="Error while sending mail!",
                message=""" There was an error while
                sending the mail!
                Would you like to save manually instead?
                """
            )
            if answer:
                self.save()

            else:
                self.set_status(err, "red")

    def save(self):
        path = tk.filedialog.asksaveasfilename(
            initialdir=SAVE_DIR, defaultextension=".zip",
            filetypes=[('zip archive', '.zip')],
            initialfile=self.controller.session.measurement_name + ".zip")
        if path is None or path == () or path.strip() == "":
            return

        err = save_session(self.controller.session, path)
