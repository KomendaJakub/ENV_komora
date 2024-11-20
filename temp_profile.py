#!/usr/bin/python3
from datetime import datetime, timedelta
import os
import csv
import tkinter as tk
from shutil import copy

DIR_PATH = os.path.dirname(__file__)
FILE_PATH = os.path.join(DIR_PATH, 'profile.csv')
TEMPLATES = os.path.join(DIR_PATH, 'templates')
global entries, add_time, add_temp
entries = []


class TwoEntryDialog(tk.simpledialog.Dialog):

    def __init__(self, parent, title=None, text1=None, text2=None):
        self.text1 = text1
        self.text2 = text2
        super().__init__(parent, title=title)

    def body(self, master):
        tk.Label(master, text=self.text1).grid(row=0, column=0)
        tk.Label(master, text=self.text2).grid(row=1, column=0)

        self.e1 = tk.Entry(master)
        self.e2 = tk.Entry(master)
        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        return self.e1

    def apply(self):
        first = self.e1.get()
        second = self.e2.get()
        self.result = [first, second]


def open_window(root):

    default_bg = root.cget('bg')

    def clear_status():
        status.config(text="", bg=default_bg)

    def refresh():
        global add_time, add_temp

        for widget in menu.winfo_children():
            widget.destroy()

        l1 = tk.Label(menu, text="Time (HH:MM)")
        l1.grid(row=1, column=0, padx=1, pady=1)
        l2 = tk.Label(menu, text="Temperature (C)")
        l2.grid(row=1, column=1, padx=1, pady=1)

        bt_add = tk.Button(menu, text="Add entry", command=add_entry)
        bt_add.grid(row=0, column=0, padx=2, pady=1)
        bt_save = tk.Button(menu, text="Save", command=save)
        bt_save.grid(row=0, column=1, padx=2, pady=1)
        bt_save_as = tk.Button(menu, text="Save profile as", command=save_as)
        bt_save_as.grid(row=0, column=2, padx=2, pady=1)
        bt_load = tk.Button(menu, text="Load Profile", command=load_profile)
        bt_load.grid(row=0, column=3, padx=2, pady=1)
        bt_cycles = tk.Button(menu, text="Create Cycles",
                              command=create_cycles)
        bt_cycles.grid(row=0, column=4, padx=2, pady=1)

        entries.clear()

        try:
            with open(FILE_PATH) as file:
                reader = csv.DictReader(file)
                # Skip 2 rows because of labels
                for i, line in enumerate(reader, start=2):
                    time_entry = tk.Entry(
                        menu)
                    time_entry.insert(0, line["time"])
                    time_entry.grid(row=i, column=0, padx=2, pady=1)
                    temp_entry = tk.Entry(menu)
                    temp_entry.insert(0, line["temp"])
                    temp_entry.grid(row=i, column=1, padx=2, pady=1)
                    entries.append([time_entry, temp_entry])
                    bt_del = tk.Button(menu, text="Delete",
                                       command=lambda idx=i-2: delete(idx))
                    bt_del.grid(row=i, column=2, padx=2, pady=1)
        except Exception as err:
            msg = err
            print(msg)
            status.config(text=msg, bg="red")
            root.after(10000, clear_status)
            refresh()
            return

    def load_profile():
        filename = tk.filedialog.askopenfilename(initialdir=TEMPLATES)
        if filename is None or len(filename) == 0:
            msg = f"File with {filename} does not exist"
            print(msg)
            status.config(text=msg, bg="red")
            root.after(10000, clear_status)
            return

        copy(filename, FILE_PATH)
        refresh()

    def add_entry():
        global entries

        dialog = TwoEntryDialog(
            edit_window, text1="Time (HH:MM)", text2="Temp (C)")
        if dialog is None:
            msg = "Nothing was entered"
            print(msg)
            status.config(text=msg, bg="red")
            root.after(10000, clear_status)
            return

        time = dialog.result[0]
        print(time)
        temp = dialog.result[1]
        add_time = tk.Entry(menu)
        add_time.insert(0, time)
        add_temp = tk.Entry(menu)
        add_temp.insert(0, temp)
        entries.append([add_time, add_temp])
        save()

    def create_cycles():
        dialog = TwoEntryDialog(
            edit_window, text1="Number of cycles: ", text2="Length of last entry (HH:MM): ")
        if dialog is None:
            msg = "Nothing was entered"
            print(msg)
            status.config(text=msg, bg="red")
            root.after(10000, clear_status)
            return

        num_cycles = int(dialog.result[0])
        len_last = dialog.result[1]
        len_last = datetime.strptime(len_last, "%H:%M")
        copy(FILE_PATH, os.path.join(TEMPLATES, "before_cycles.csv"))
        contents = []
        try:
            with open(FILE_PATH) as file:
                reader = csv.DictReader(file)
                for line in reader:
                    contents.append([line['time'], line['temp']])
        except Exception as err:
            msg = err
            print(msg)
            status.config(text=msg, bg="red")
            root.after(10000, clear_status)

        last_time = contents[-1][0]
        last_time = datetime.strptime(last_time, "%H:%M")
        next_time = timedelta(hours=last_time.hour, minutes=last_time.minute) + \
            timedelta(hours=len_last.hour, minutes=len_last.minute)

        try:
            with open(FILE_PATH, 'w') as file:
                fieldnames = ["time", "temp"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for i in range(num_cycles):
                    for value in contents:
                        time = value[0]
                        temp = value[1]
                        time = datetime.strptime(time, "%H:%M")
                        time = timedelta(hours=time.hour, minutes=time.minute)
                        time = time + (i)*next_time
                        if time.days > 0:
                            break

                        time_s = ":".join(
                            [str(time.seconds // 3600), str((time.seconds % 3600) // 60)])
                        writer.writerow({'time': time_s, 'temp': str(temp)})
        except Exception as err:
            msg = err, err.args
            print(msg)
            status.config(text=msg, bg="red")
            root.after(10000, clear_status)
            refresh()
            return

        refresh()

    def delete(index):
        entries[index][0].destroy()
        entries[index][1].destroy()
        entries.pop(index)
        save()

    def save(path=FILE_PATH):
        global entries

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

        try:

            with open(path, 'w') as file:
                fieldnames = ['time', 'temp']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for entry in entries:
                    time = entry[0].get()
                    temp = entry[1].get()
                    writer.writerow({'time': time, 'temp': temp})
        except Exception as err:
            msg = err
            print(msg)

            status.config(text=msg, bg="red")
            root.after(10000, clear_status)
            refresh()
            return

        status.config(text="Changes have been saved!", bg="green")
        root.after(10000, clear_status)
        refresh()

    def save_as():
        path = tk.filedialog.asksaveasfilename(
            initialdir=TEMPLATES, defaultextension=".csv")

        if path is None or path.strip() == "":
            return

        save()
        save(path)

    edit_window = tk.Toplevel(root)
    edit_window.title("Profile Editing")
    edit_window.geometry("800x480")

    status = tk.Label(edit_window, text="", bd=1, relief=tk.SUNKEN,
                      anchor=tk.N, justify=tk.CENTER)
    status.pack(fill=tk.X, side=tk.TOP, pady=1)

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
    try:
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
    except Exception:
        print("Unable to load the profile")
        return None


if __name__ == "__main__":
    get_profile(None)
