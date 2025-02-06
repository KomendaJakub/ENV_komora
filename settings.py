# Imports
import tkinter as tk
import json
from os import path

# Constants
CONFIG_PATH = path.join(path.dirname(__file__), 'config.json')


def get_settings():
    with open(CONFIG_PATH, "r") as file:
        settings = file.read()

    return json.loads(settings)


def open_settings(root):
    #    default_bg = root.cget()

    settings = get_settings()

    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("800x480")

    menu_frame = tk.Frame(settings_window)
    menu_frame.pack()
    bt_save = tk.Button(menu_frame, text="Save settings")
    bt_save.pack()

    entries_frame = tk.Frame(settings_window)
    entries_frame.pack()

    email_label = tk.Label(entries_frame, text="Default Email Address:")
    email_label.grid(row=0, column=0, padx=2, pady=1)
    email_entry = tk.Entry(entries_frame)
    email_entry.insert(0, settings["default_email"])
    email_entry.grid(row=0, column=1, padx=2, pady=1)

    period_label = tk.Label(entries_frame, text="Measurement period (s):")
    period_label.grid(row=1, column=0, padx=2, pady=1)
    period_entry = tk.Entry(entries_frame)
    period_entry.insert(0, settings["measurement_period"])
    period_entry.grid(row=1, column=1, padx=2, pady=1)
