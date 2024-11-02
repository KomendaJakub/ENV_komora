#!/usr/bin/python3
from datetime import datetime
import os
import csv
import tkinter as tk


HEADER_LINES = 4
DIR_PATH = os.path.dirname(__file__)
FILE_PATH = os.path.join(DIR_PATH, 'profile.csv')

global entries
entries = []


def open_window(root):

    def refresh():
        global entries
        entries = []
        file = open(FILE_PATH)
        reader = csv.DictReader(file)

        # Skip 2 rows because of other objects
        i = 2
        for line in reader:
            e1 = tk.Entry(menu)
            e1.insert(0, line["time"])
            e1.grid(row=i, column=0)
            e2 = tk.Entry(menu)
            e2.insert(0, line["temp"])
            e2.grid(row=i, column=1)
            entries.append([e1, e2])
            i += 1
        file.close()

    def save():

        def key(time):
            hour, minute = time.split(":")
            return int(hour)*100 + int(minute)

        entries.sort(key=lambda x: key(x[0].get()))

        file = open(FILE_PATH, 'w')
        fieldnames = ['time', 'temp']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        for entry in entries:
            time = entry[0].get()
            temp = entry[1].get()
            writer.writerow({'time': time, 'temp': temp})
        file.close()
        refresh()

    edit_window = tk.Toplevel(root)
    edit_window.title("Profile Editing")
    edit_window.geometry("800x480")

    menu = tk.Frame(edit_window)
    menu.pack()

    l1 = tk.Label(menu, text="Time (HH:MM)")
    l2 = tk.Label(menu, text="Temperature (C)")
    add_time = tk.Entry(menu)
    add_time.grid(row=0, column=0)
    add_temp = tk.Entry(menu)
    add_temp.grid(row=0, column=1)
    bt_save = tk.Button(menu, text="Save", command=save)
    bt_save.grid(row=0, column=2)
    l1.grid(row=1, column=0)
    l2.grid(row=1, column=1)
    refresh()


def get_profile(time):
    file = open(FILE_PATH)
    reader = csv.DictReader(file)

    last_temp = None
    for row in reader:
        hour, minute = row['time'].split(":")
        prof_time = datetime(time.year, time.month,
                             time.day, int(hour), int(minute))

        if (prof_time > time):
            if last_temp is None:
                return None
            return float(last_temp)
        last_temp = float(row['temp'])

    if last_temp is None:
        return None


if __name__ == "__main__":
    get_profile(None)
