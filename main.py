#!/usr/bin/python3
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
import sys
from time import sleep

if len(sys.argv) > 1 and sys.argv[1] == 'debug':
    from sensor import get_measurement_test as get_measurement
else:
    from sensor import get_measurement

from temp_profile import open_window
from mail import mail
from graphing import recalculate, get_profile

global delay
global last_event_t
global prev_event_t
global prev_delay

delay = dt.timedelta()
last_event_t = dt.datetime
prev_event_t = dt.datetime
prev_delay = 0


def export():
    answer = tk.simpledialog.askstring(
        "Email", "Insert and email address to which data will be exported", parent=root)

    if answer is None or answer.strip() == '':
        status.config(text="No email address inserted!", bg="red")
        root.after(10000, clear_status)
        return
    plt.savefig('figure.png', dpi=1200)
    err = mail(time_list, real_temp_list, temp_profile, answer)

    if err == 0:
        status.config(text="Email sent successfully!", bg="green")
    else:
        status.config(text="Error, please retry or save manually!")
    root.after(10000, clear_status)


def clear_status():
    status.config(text="", bg="#d9d9d9")


# Create figure for plotting
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

time_list = []
real_temp_list = []
temp_profile = []
start_t = dt.datetime.now()
day = 1


def get_new_profile():
    recalculate(time_list, temp_profile, day)

    status.config(text="Graph was refreshed!", bg="green")
    root.after(10000, clear_status)


# This function is called periodically from FuncAnimation


def animate(i, time_list, ys):
    global last_event_t
    global day
    global plt
    # Read temperature (Celsius) from TMP102
    temp_c = round(get_measurement(), 2)

    # Add new values to the list
    delta_t = (dt.datetime.now() - delay) - start_t

    if delta_t > (day)*dt.timedelta(days=1):
        day += 1
        plt.savefig('figure.png', dpi=1200)
        mail(time_list, real_temp_list, temp_profile)
        time_list.clear()
        real_temp_list.clear()
        temp_profile.clear()

#    print(delta_t)
    temporary = dt.datetime.strptime(
        str(delta_t - (day - 1)*dt.timedelta(days=1)), "%H:%M:%S.%f")
#    print(delta_t)
#    print(delta_t.strftime("%H:%M:%S"))
#    time_list.append(delta_t.strftime("%H:%M:%S"))

    time_list.append(temporary.strftime("%H:%M:%S"))
    ys.append(temp_c)
    temp_profile.append(get_profile(delta_t, day))
    # Draw x and y lists
    ax.clear()
    ax.plot(time_list, ys, label="Actual Value", color="blue")
    ax.plot(time_list, temp_profile, label="Set Value", color="red")
    # Format plot
    ax.xaxis.set_major_locator(ticker.MaxNLocator(10))
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('Temperature over Time')
    plt.xlabel('Time')
    plt.ylabel('Temperature (deg C)')
    plt.legend()
    canvas.draw()
    last_event_t = dt.datetime.now()

# Set up plot to call animate() function periodically


ani = animation.FuncAnimation(
    fig, animate, fargs=(time_list, real_temp_list), interval=10000)


def pause_anim():
    global delay
    global prev_event_t
    global last_event_t
    global prev_delay

    if pause_anim.paused:
        if prev_event_t == last_event_t:
            new_delay = dt.datetime.now() - last_event_t
            delay += new_delay - prev_delay
            prev_delay = new_delay

        else:
            new_delay = dt.datetime.now() - last_event_t
            delay += dt.datetime.now() - last_event_t
            prev_event_t = last_event_t
            prev_delay = new_delay

        ani.resume()
        clear_status()

    else:
        ani.pause()
        status.config(text="Paused!", bg="red")

    pause_anim.paused = not pause_anim.paused


pause_anim.paused = False

# Initialize tkinter
root = tk.Tk()
root.configure(background="seashell2")
root.title("Environmental Chamber Control")


def on_closing():
    root.quit()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)

status = tk.Label(root, text="", bd=1, relief=tk.SUNKEN,
                  anchor=tk.N, justify=tk.CENTER)
status.pack(fill=tk.X, side=tk.TOP, pady=1)


default_bg = root.cget('bg')
frame_menu = tk.Frame(root, bg=default_bg)
frame_menu.pack(side="top")

frame_graph = tk.Frame(root)
frame_graph.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

bt_refresh = tk.Button(frame_menu, text="Refresh", command=get_new_profile)
bt_refresh.grid(row=0, column=0, padx=2, pady=1)


bt_edit = tk.Button(frame_menu, text="Edit Profile",
                    command=lambda: open_window(root))
bt_edit.grid(row=0, column=1, padx=2, pady=1)

bt_export = tk.Button(frame_menu, text="Export", command=export)
bt_export.grid(row=0, column=2, padx=2, pady=1)

bt_start = tk.Button(frame_menu, text="Pause/Resume",
                     command=pause_anim)
bt_start.grid(row=0, column=3, padx=2, pady=1)

canvas = FigureCanvasTkAgg(fig, master=frame_graph)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

toolbar = NavigationToolbar2Tk(
    canvas, frame_graph, pack_toolbar=False)
toolbar.update()
toolbar.pack(side="bottom")

root.mainloop()
