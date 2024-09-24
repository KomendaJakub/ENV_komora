
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.dates as mdates
import tkinter as tk
import os
import shutil

from sensor import get_measurement
from temp_profile import get_profile, set_temp, get_name

def set_profile():
    set_temp(entry_time.get(), entry_temp.get())
    for i in range(len(zs)):
        delta_t = dt.datetime.strptime(str(xs[i]), "%H:%M:%S")
        zs[i] = get_profile(delta_t)

def save():
    file_name = get_name()
    dirpath = "/home/pi/Documents/ENV_komora/saves"
    dirpath = os.path.join(dirpath, file_name)
    os.mkdir(dirpath)

    filepath = os.path.join(dirpath, file_name)
    with open(filepath + ".txt", "w") as file:
        for i in range(len(xs)):
            s = ",".join((str(xs[i]), str(ys[i]), str(zs[i])))
            s += "\n"
            file.write(s)

    shutil.copy("/home/pi/Documents/ENV_komora/profile.csv", filepath + "_profile.csv")

def on_closing():
    if tk.messagebox.askokcancel("Save", "Do you want to save?"):
        save()
    root.destroy()


# Create figure for plotting

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

xs = []
ys = []
zs = []
start_t = dt.datetime.now()

# This function is called periodically from FuncAnimation
def animate(i, xs, ys):

    # Read temperature (Celsius) from TMP102
    temp_c = round(get_measurement(), 2)

    # Add x and y to lists
    delta_t = dt.datetime.now() - start_t
    delta_t = dt.datetime.strptime(str(delta_t), "%H:%M:%S.%f")
    xs.append(delta_t.strftime("%H:%M:%S"))
    #xs.append(dt.datetime.now().strftime("%H:%M:%S"))
    ys.append(temp_c)
    zs.append(get_profile(delta_t))
    # Draw x and y lists
    ax.clear()
    ax.plot(xs, ys, label="Actual Value", color="blue")
    ax.plot(xs, zs, label="Set Value", color="red")
    # Format plot
    ax.xaxis.set_major_locator(ticker.MaxNLocator(10))
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('Temperature over Time')
    plt.xlabel('Time')
    plt.ylabel('Temperature (deg C)')
    plt.legend()
    canvas.draw()

# Set up plot to call animate() function periodically

ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=10000)

# Initialize tkinter
root = tk.Tk()
root.geometry("800x480")
root.protocol("WM_DELETE_WINDOW", on_closing)


frame_menu1 = tk.Frame(root)
frame_menu1.pack(side="top")

frame_menu2 = tk.Frame(root)
frame_menu2.pack(side="top")

frame_graph = tk.Frame(root)
frame_graph.pack(side="bottom")

bt_start = tk.Button(frame_menu1, text="Start")
bt_start.grid(column=0, row=0, padx=1)
bt_save = tk.Button(frame_menu1, text="Save", command=save)
bt_save.grid(column=1, row=0, padx=1)
bt_load = tk.Button(frame_menu1, text="Load")
bt_load.grid(column=2, row=0, padx=1)

label_time = tk.Label(frame_menu2, text="Time (HH:MM)")
label_time.grid(row=0)
label_temp = tk.Label(frame_menu2, text="Temperature (deg C)")
label_temp.grid(row=1)

entry_time = tk.Entry(frame_menu2)
entry_time.grid(row=0, column=1)
entry_temp = tk.Entry(frame_menu2)
entry_temp.grid(row=1, column=1)

bt_submit = tk.Button(frame_menu2, text="Set Temperature", command=set_profile)
bt_submit.grid(row=2, columnspan=2)


canvas = FigureCanvasTkAgg(fig, master = frame_graph)
canvas.get_tk_widget().pack()


toolbar = NavigationToolbar2Tk(canvas, frame_graph, pack_toolbar = False)
toolbar.update()
toolbar.pack()

root.mainloop()
