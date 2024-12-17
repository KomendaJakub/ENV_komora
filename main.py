#!/usr/bin/python3
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
import sys
import smtplib
from email.message import EmailMessage
import csv
from confidential import EMAIL, PASSWORD, MAIL_SERVER

if len(sys.argv) > 1 and sys.argv[1] == 'debug':
    from sensor import get_measurement_test as get_measurement
else:
    from sensor import get_measurement

from temp_profile import get_profile, open_window


def export():
    answer = tk.simpledialog.askstring(
        "Email", "Insert and email address to which data will be exported", parent=root)

    if answer is None or answer.strip() == '':
        status.config(text="No email address inserted!", bg="red")
        root.after(10000, clear_status)
        return
    else:
        DESTINATION = answer

    try:
        with open("Export.csv", "w") as file:
            fieldnames = ['time', "measurement", "set_temp"]

            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(len(xs)):
                writer.writerow(
                    {'time': xs[i], 'measurement': ys[i], 'set_temp': zs[i]})
    except Exception as err:
        print(err)
        status.config(text="Could not open Export.csv for writing", bg="red")
        root.after(10000, clear_status())

    now = dt.datetime.now()
    msg = EmailMessage()
    msg.set_content("Environmental chamber measurement from " +
                    now.strftime("%d/%m/%Y, %H:%M"))
    msg['Subject'] = "ENV chamber " + now.strftime("%d/%m/%Y, %H:%M")
    msg['From'] = EMAIL
    msg['To'] = DESTINATION

    try:
        with open('Export.csv', 'rb') as fb:
            data = fb.read()
        msg.add_attachment(data, maintype='text',
                           subtype='csv', filename='Raw.csv')

        plt.savefig('figure.png', dpi=1200)
        with open('figure.png', 'rb') as fb:
            image = fb.read()
        msg.add_attachment(image, maintype='image',
                           subtype='png', filename='Figure.png')

        with open('profile.csv', 'rb') as fb:
            prof = fb.read()
        msg.add_attachment(prof, maintype="text",
                           subtype="csv", filename="profile.csv")

    except Exception as err:
        print(err)
        status.config(text="Could not open one of the export files", bg="red")
        root.after(10000, clear_status)
    try:
        with smtplib.SMTP_SSL(MAIL_SERVER, 465) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)
    except Exception as err:
        print(err)
        status.config(
            text="There was an error while sending the email, try again or save manually!", bg="red")
        root.after(30000, clear_status)
        return

    status.config(text="Email sent successfully!", bg="green")
    root.after(10000, clear_status)


def clear_status():
    status.config(text="", bg="#d9d9d9")


# Create figure for plotting
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

xs = []
ys = []
zs = []
start_t = dt.datetime.now()


def recalculate():
    for i in range(len(xs)):
        delta_t = dt.datetime.strptime(xs[i], "%H:%M:%S")
        zs[i] = get_profile(delta_t)

    status.config(text="Graph was refreshed!", bg="green")
    root.after(10000, clear_status)


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


ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=10000)

# Initialize tkinter
root = tk.Tk()
root.configure(background="seashell2")


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
frame_graph.pack(side=tk.BOTTOM, fill=tk.BOTH)

bt_refresh = tk.Button(frame_menu, text="Refresh", command=recalculate)
bt_refresh.grid(row=0, column=0, padx=2, pady=1)

# bt_start = tk.Button(frame_menu1, text="Start")
# bt_start.grid(column=0, row=0, padx=1)
bt_edit = tk.Button(frame_menu, text="Edit Profile",
                    command=lambda: open_window(root))
bt_edit.grid(row=0, column=1, padx=2, pady=1)
bt_export = tk.Button(frame_menu, text="Export", command=export)
bt_export.grid(row=0, column=2, padx=2, pady=1)
canvas = FigureCanvasTkAgg(fig, master=frame_graph)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

toolbar = NavigationToolbar2Tk(
    canvas, frame_graph, pack_toolbar=False)
toolbar.update()
toolbar.pack(side="bottom")

root.mainloop()
