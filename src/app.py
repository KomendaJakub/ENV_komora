#!/usr/bin/python3

# Importing standard python libraries
import tkinter as tk
import tkinter.ttk as ttk

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from functools import partial
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import sys
import pathlib
import io
import tempfile

# Importing source code
if len(sys.argv) > 1 and sys.argv[1] == "debug":
    from src.sensor import get_measurement_test as get_measurement
else:
    from src.sensor import get_measurement

from src.edit_window import Edit_Window
from src.controller import Controller

TEMPLATES = pathlib.Path("resources/templates/")
ICONS = pathlib.Path("resources/icons/")
EM_DASH = u'\u2014'


class App(tk.Tk):

    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller
        self.REFRESH_INTERVAL_MS = 10_000

        # Setting up initial params
        self.title("Environmental Chamber Control")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Set standard window size
        self.geometry("800x600")
        self.update()
        self.geometry()
        self.minsize(self.winfo_width(), self.winfo_height())
        self.resizable(True, True)

        # TODO: Add and iconphoto
        # self.iconphoto(True, tk.PhotoImage(file=path_to_logo))

        self.profile_name = None
        self.measurement_name = None
        self._build_menu()
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def _build_menu(self):
        # Adding the top most row of named buttons
        menu = tk.Menu(self, tearoff=0)
        self.config(menu=menu)

        self.measurement_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Measurement", menu=self.measurement_menu)
        self.measurement_menu.add_command(label="New",
                                          command=self.new_measurement)
        # file_menu.add_command(label="Load")
        self.measurement_menu.add_command(label="Save",
                                          command=self.save)
        self.measurement_menu.entryconfigure("Save", state=tk.DISABLED)
        self.measurement_menu.add_command(
            label="Save as", command=self.save_as)
        self.measurement_menu.entryconfigure("Save as", state=tk.DISABLED)
        self.measurement_menu.add_command(label="Email",
                                          command=self.export)
        self.measurement_menu.entryconfigure("Email", state=tk.DISABLED)
        self.measurement_menu.add_command(label="Pause/Resume",
                                          command=self.toggle_pause)
        self.measurement_menu.entryconfigure("Pause/Resume", state=tk.DISABLED)

        self.profile_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Profile", menu=self.profile_menu)
        self.profile_menu.add_command(label="Load", command=self.load_profile)
        self.profile_menu.add_command(label="Edit",
                                      command=lambda: Edit_Window(self))
        self.profile_menu.entryconfigure("Edit", state=tk.DISABLED)
        self.profile_menu.add_command(label="Save as")
        self.profile_menu.entryconfigure("Save as", state=tk.DISABLED)

        help_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Manual")
        help_menu.add_command(label="About")

        # Adding buttons with pictures
        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.TOP, fill=tk.X, expand=False)

        # The image is stored to avoid GC
        # TODO: Add a function that allows to load a previous measurement
        self.button_open = ttk.Button(
            button_frame, command=self.new_measurement)
        self.button_open.image = tk.PhotoImage(
            file=ICONS.joinpath("open.png"))
        self.button_open.configure(image=self.button_open.image)
        self.button_open.grid(row=0, column=0)

        # self.button_edit = ttk.Button(
        #    button_frame, command=lambda: Edit_Window(self))
        # self.button_edit.image = tk.PhotoImage(file=ICONS.joinpath("edit.png"))
        # self.button_edit.configure(
        #    image=self.button_edit.image, state=tk.DISABLED)
        # self.button_edit.grid(row=0, column=1)

        self.button_save = ttk.Button(
            button_frame, command=self.save)
        self.button_save.image = tk.PhotoImage(
            file=ICONS.joinpath("save.png"))
        self.button_save.configure(
            image=self.button_save.image, state=tk.DISABLED)
        self.button_save.grid(row=0, column=2)

        self.button_save_as = ttk.Button(button_frame,
                                         command=self.save_as)
        self.button_save_as.image = tk.PhotoImage(
            file=ICONS.joinpath("save_as.png"))
        self.button_save_as.configure(
            image=self.button_save_as.image, state=tk.DISABLED)
        self.button_save_as.grid(row=0, column=3)

        self.button_email = ttk.Button(
            button_frame, command=self.export)
        self.button_email.image = tk.PhotoImage(
            file=ICONS.joinpath("email.png"))
        self.button_email.configure(
            image=self.button_email.image, state=tk.DISABLED)
        self.button_email.grid(row=0, column=4)

        self.button_pause = ttk.Button(button_frame,
                                       command=self.toggle_pause)
        self.button_pause.image_resume = tk.PhotoImage(
            file=ICONS.joinpath("resume.png"))
        self.button_pause.image_pause = tk.PhotoImage(
            file=ICONS.joinpath("pause.png"))
        self.button_pause.configure(
            image=self.button_pause.image_pause, state=tk.DISABLED)
        self.button_pause.grid(row=0, column=6)

#    Icons used come from Icons8
# <a target="_blank" href="https://icons8.com/icon/102544/add">Add</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>
#    <a target="_blank" href="https://icons8.com/icon/poyizCBxzCRY/edit-text-file">Document</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>
#    <a target="_blank" href="https://icons8.com/icon/yFBJCjFJpLXw/save">Save</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>
#    <a target="_blank" href="https://icons8.com/icon/wC9budkHyeKg/save-as">Save as</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>
#    <a target="_blank" href="https://icons8.com/icon/6BBCqlzE4iKd/letter">Email</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>
#    <a target="_blank" href="https://icons8.com/icon/yV9PqJWVRl5T/resume-button">Resume Button</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>
#    <a target="_blank" href="https://icons8.com/icon/Z2aInWmsldJ6/pause">Pause</a> icon by <a target="_blank" href="https://icons8.com">Icons8</a>

    def _build_labels(self, main_frame):
        label_frame = ttk.Frame(main_frame)
        label_frame.place(relx=0.8, relwidth=0.2, relheight=1)

        name_frame = ttk.LabelFrame(label_frame, text="Measurement")
        name_frame.pack(fill=tk.X, side=tk.TOP, padx=10, pady=10)

        if self.measurement_name is None:
            self.measurement_name = tk.StringVar()
            file = tempfile.NamedTemporaryFile(delete=False)
            path = pathlib.Path(file.name)
            file.close()
            self.controller.measurement_path = path
            self.measurement_name.set("Untitled")

        ttk.Label(name_frame, textvariable=self.measurement_name,
                  anchor=tk.W, wraplength=200
                  ).pack(side=tk.TOP, fill=tk.X)

        if self.profile_name is None:
            self.profile_name = tk.StringVar()
        ttk.Label(name_frame, textvariable=self.profile_name, anchor=tk.W
                  ).pack(side=tk.TOP, fill=tk.X)

    def new_measurement(self):
        self._build_labels(self.main_frame)
        self.title(
            f"{self.measurement_name.get()} {EM_DASH} Environmental Chamber Control")

        self.button_open.configure(state=tk.DISABLED)
        self.button_save_as.configure(state=tk.NORMAL)
        self.button_pause.configure(state=tk.NORMAL)
        self.button_email.configure(state=tk.NORMAL)

        self.measurement_menu.entryconfigure("New", state=tk.DISABLED)
        self.measurement_menu.entryconfigure("Save as", state=tk.NORMAL)
        self.measurement_menu.entryconfigure("Email", state=tk.NORMAL)
        self.measurement_menu.entryconfigure("Pause/Resume", state=tk.NORMAL)

        self._build_graph(self.main_frame)
        # Set up plot to call animate() function periodically
        self.ani = animation.FuncAnimation(
            self.fig, partial(self.animate), interval=self.REFRESH_INTERVAL_MS, cache_frame_data=False)
        self.canvas.draw()
        self.save(temp=True)

    def _build_graph(self, main_frame):
        graph_frame = ttk.Frame(main_frame)
        graph_frame.place(relwidth=0.8, relheight=1)
        # Create a figure
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1, 1, 1)

        # To display figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(
            self.canvas, graph_frame, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side="bottom")

    def on_closing(self):
        try:
            self.ani.event_source.stop()
            plt.close('all')
        except AttributeError:
            # Animation does not exist.
            pass

        if self.controller.measurement_path is not None:
            if self.controller.temp_save:
                self.save_as()
                path = self.controller.measurement_path
                path.unlink()
            else:
                self.save()

        self.quit()
        self.destroy()

    def animate(self, i):
        # Read temperature (Celsius) from TMP102
        temp = float(round(get_measurement(), 2))
        result = self.controller.add_data_point(temp)

        if result == 'day_change':
            self.save()

        self.update_plot()

    def update_plot(self):

        # Draw x and y lists
        self.ax.clear()
        self.ax.plot(self.controller.times, self.controller.real_temps,
                     label="Actual Value", color="blue")
        self.ax.plot(self.controller.times, self.controller.target_temps,
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
        if self.controller.paused:
            self.controller.resume()
            self.ani.resume()
            self.button_pause.configure(image=self.button_pause.image_pause)
        else:
            self.ani.pause()
            self.controller.pause()
            self.button_pause.configure(image=self.button_pause.image_resume)

    def get_new_profile(self):
        self.controller.recalculate()

    def export(self):
        email = tk.simpledialog.askstring(
            prompt="Insert an email address to which data will be exported.", title="Email")
        if email is None:
            return

        email = email.strip()

        self.save()
        err = self.controller.send_mail(address=email)
        if err == "ok":
            tk.messagebox.showinfo(message="Email sent successfully!")
        elif err == "ERROR":
            tk.messagebox.showerror(title="Error!",
                                    message="""There was an error while sending the mail. Please check your internet connection and consider saving manually.""")

    def save(self, prev_path=None, temp=False):
        fig_buffer = io.BytesIO()
        self.fig.savefig(fig_buffer, format='png', dpi=1200)
        self.controller.save_session(fig_buffer, prev_path, temp)

    def save_as(self):
        res = tk.filedialog.asksaveasfilename(initialdir=pathlib.Path().home(),
                                              filetypes=[("zip archive", "*.zip")])
        if res == '' or res == ():
            return
        res = pathlib.Path(res.strip())
        res = res.with_suffix(".zip")

        prev_path = self.controller.measurement_path
        self.controller.measurement_path = res
        self.measurement_name.set(res.name)
        self.title(
            f"{res.name} {EM_DASH} Environmental Chamber Control")
        self.button_save.configure(state=tk.NORMAL)
        self.measurement_menu.entryconfigure("Save", state=tk.DISABLED)

        return self.save(prev_path)

    def load_profile(self):
        res = tk.filedialog.askopenfilename(initialdir=TEMPLATES)
        if res == '' or res == ():
            return
        res = pathlib.Path(res)

        # Maybe when profile is in memory do sth else
        if self.profile_name is None:
            self.profile_name = tk.StringVar()
        self.controller.profile_path = res
        self.profile_name.set(res.name)
        self.controller.recalculate()
        self.profile_menu.entryconfigure("Save as", state=tk.NORMAL)
        self.profile_menu.entryconfigure("Edit", state=tk.NORMAL)
        # self.button_edit.configure(state=tk.NORMAL)
        if self.controller.measurement_path is not None:
            self.after(self.REFRESH_INTERVAL_MS, self.save)
