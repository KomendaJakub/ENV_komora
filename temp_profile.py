#!/usr/bin/python3
from datetime import datetime
import os
import csv
import tkinter as tk

DIR_PATH = os.path.dirname(__file__)
FILE_PATH = os.path.join(DIR_PATH, 'profile.csv')

global entries, add_time, add_temp
entries = []


def open_window(root):

    def refresh():
        global add_time, add_temp

        menu.pack_forget()

        l1 = tk.Label(menu, text="Time (HH:MM)")
        l1.grid(row=1, column=0)
        l2 = tk.Label(menu, text="Temperature (C)")
        l2.grid(row=1, column=1)

        add_time = tk.Entry(menu)
        add_time.grid(row=0, column=0)
        add_temp = tk.Entry(menu)
        add_temp.grid(row=0, column=1)
        bt_save = tk.Button(menu, text="Save", command=save)
        bt_save.grid(row=0, column=2)

        entries.clear()

        with open(FILE_PATH) as file:
            reader = csv.DictReader(file)
            # Skip 2 rows because of labels
            for i, line in enumerate(reader, start=2):
                time_entry = tk.Entry(menu)
                time_entry.insert(0, line["time"])
                time_entry.grid(row=i, column=0)
                temp_entry = tk.Entry(menu)
                temp_entry.insert(0, line["temp"])
                temp_entry.grid(row=i, column=1)
                entries.append([time_entry, temp_entry])
                bt_del = tk.Button(menu, text="Delete",
                                   command=lambda idx=i-2: delete(idx))
                bt_del.grid(row=i, column=2)

    def delete(index):
        entries[index][0].destroy()
        entries[index][1].destroy()
        entries.pop(index)
        save()

    def save():
        global entries
        if add_time.get() and add_temp.get():
            entries.append([add_time, add_temp])

        def key(time):
            hour, minute = time.split(":")
            return int(hour)*100 + int(minute)

        entries.sort(key=lambda x: key(x[0].get()))

        unique_times = {}
        for entry in entries:
            time = entry[0].get()
            if time not in unique_times:
                unique_times[time] = entry
        entries = list(unique_times.values())

        with open(FILE_PATH, 'w') as file:
            fieldnames = ['time', 'temp']
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            for entry in entries:
                time = entry[0].get()
                temp = entry[1].get()
                writer.writerow({'time': time, 'temp': temp})

        refresh()

    edit_window = tk.Toplevel(root)
    edit_window.title("Profile Editing")
    edit_window.geometry("800x480")

    main_frame = tk.Frame(edit_window)
    main_frame.pack(fill="both", expand=1)

    canvas = tk.Canvas(main_frame)
    canvas.pack(side="left", fill="both", expand=1)

    scrollbar = tk.Scrollbar(
        main_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")

    canvas.configure(yscrollcommand=scrollbar.set)

    menu = tk.Frame(canvas)
    canvas.create_window((0, 0), window=menu, anchor="n")
    menu.bind('<Configure>', lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")))

    refresh()


def get_profile(time):
    if time is None:
        return None

    last_temp = None
    with open(FILE_PATH) as file:
        reader = csv.DictReader(file)
        for row in reader:
            hour, minute = map(int, row['time'].split(":"))
            prof_time = datetime(time.year, time.month,
                                 time.day, hour, minute)

            if (prof_time > time):
                return float(last_temp) if last_temp is not None else None
            last_temp = float(row['temp'])

        return last_temp


if __name__ == "__main__":
    get_profile(None)
