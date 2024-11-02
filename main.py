#!/usr/bin/python3
import sys


import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk


if len(sys.argv) > 1 and sys.argv[1] == 'test':
    from sensor import get_measurement_test as get_measurement
else:
    from sensor import get_measurement

from temp_profile import get_profile, set_temp


def on_closing():
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
    # xs.append(dt.datetime.now().strftime("%H:%M:%S"))
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


ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=1000)

# Initialize tkinter
root = tk.Tk()
root.geometry("800x480")
root.protocol("WM_DELETE_WINDOW", root.destroy)

frame_graph = tk.Frame(root)
frame_graph.pack(side="bottom")


# bt_start = tk.Button(frame_menu1, text="Start")
# bt_start.grid(column=0, row=0, padx=1)


canvas = FigureCanvasTkAgg(fig, master=frame_graph)
canvas.get_tk_widget().pack()

toolbar = NavigationToolbar2Tk(canvas, frame_graph, pack_toolbar=False)
toolbar.update()
toolbar.pack()

root.mainloop()
