#!/usr/bin/python3
from datetime import datetime
import os
import csv
import tkinter as tk

DIR_PATH = os.path.dirname(__file__)
FILE_PATH = os.path.join(DIR_PATH, 'profile.csv')

global entries
entries = []


def open_window(root):

    def refresh():
        for widget in menu.winfo_children():
            widget.destroy()

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

        entries.clear()
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
            bt_del = tk.Button(menu, text="Delete",
                               command=lambda i=i: delete(i-2))
            bt_del.grid(row=i, column=2)
            i += 1
        file.close()

    def delete(index):
        entries[index][0].destroy()
        entries[index][1].destroy()
        entries.pop(index)
        save()

    def save():

        def key(time):
            hour, minute = time.split(":")
            return int(hour)*100 + int(minute)

        entries.sort(key=lambda x: key(x[0].get()))

        index = 0
        while index < len(entries) - 1:
            while (entries[index][0].get() == entries[index+1][0].get()):
                if index + 1 >= len(entries):
                    break
            index += 1

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
