# Import standard python libraries
import tkinter as tk
import tkinter.simpledialog
from shutil import copy

# Importing source code
from src.edit_controller import load_profile, save_profile, create_cycles

FILE_PATH = '/resources/templates/profile.csv'
TEMPLATES = '/resources/templates'


class TwoEntryDialog(tkinter.simpledialog.Dialog):

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


class Edit_Window(tk.Toplevel):

    REFRESH_INTERVAL_MS = 10000

    def __init__(self, root):
        self.root = root
        self.default_bg = self.root.cget('bg')
        super().__init__(self.root, bg=self.default_bg)

        self.title("HELLO!")
        self.geometry("800x400")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.status = tk.Label(self, text="", bd=1, relief=tk.SUNKEN,
                               anchor=tk.N, justify=tk.CENTER)
        self.status.pack(fill=tk.X, side=tk.TOP, pady=1)

        main_frame = tk.Frame(self)
        main_frame.pack(side="top", fill="x")

        self.menu = tk.Frame(main_frame, bg=self.default_bg)
        self.menu.pack(side="top", fill="x")

        self._build_menu()

        self.canvas = tk.Canvas(main_frame)
        self.canvas.pack(side="left", fill="both", expand=1)

        scrollbar = tk.Scrollbar(
            main_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.entries_frame = tk.Frame(self.canvas)
        self.canvas.create_window(
            (0, 0), window=self.entries_frame, anchor="n")
        self.entries_frame.bind('<Configure>', lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))

        # TODO: Is root really necessary here?
        self.root.bind_all("<Button-4>", self.on_mousewheel)
        self.root.bind_all("<Button-5>", self.on_mousewheel)

        self.entries = []
        self.refresh()

    def _build_menu(self):
        buttons_frame = tk.Frame(self.menu, bg=self.default_bg)
        buttons_frame.grid(row=1)

        tk.Button(buttons_frame, text="Add entry", command=self.add_entry).grid(
            row=0, column=0, padx=2, pady=1)
        tk.Button(buttons_frame, text="Save", command=self.save).grid(
            row=0, column=1, padx=2, pady=1)
        tk.Button(buttons_frame, text="Save profile as", command=self.save_as).grid(
            row=0, column=2, padx=2, pady=1)
        tk.Button(buttons_frame, text="Load Profile", command=self.load_from_file).grid(
            row=0, column=3, padx=2, pady=1)
        tk.Button(buttons_frame, text="Create Cycles", command=self.generate_cycles).grid(
            row=0, column=4, padx=2, pady=1)

    def on_closing(self):
        # TODO: Is root really necessary here?
        self.root.unbind_all("<Button-4>")
        self.root.unbind_all("<Button-5>")
        # Inserted self.quit() not so sure about it we will see
        self.quit()
        self.destroy()

    def on_mousewheel(self, event):
        if event.num == 4:
            direction = -1
        elif event.num == 5:
            direction = 1

        self.canvas.yview_scroll(direction, "units")

    def set_status(self, message, color):
        self.status.config(text=message, bg=color)
        # TODO: Is root really necessary here?
        self.root.after(self.REFRESH_INTERVAL_MS, self.clear_status)

    def clear_status(self):
        self.status.config(text="", bg="d9d9d9")

    def refresh(self):
        for widget in self.entries_frame.winfo_children():
            widget.destroy()

        self.entries.clear()

        try:
            data = load_profile(FILE_PATH)
        except Exception:
            self.set_status("Could not load profile", "red")
            return

        # TODO: Is this start really necessary? If so why?
        for i, (time, temp) in enumerate(data, start=2):
            time_entry = tk.Entry(self.entries_frame)
            time_entry.insert(0, time)
            time_entry.grid(row=i, column=0, padx=2, pady=1)

            temp_entry = tk.Entry(self.entries_frame)
            temp_entry.insert(0, temp)
            temp_entry.grid(row=i, column=1, padx=2, pady=1)

            bt_del = tk.Button(self.entries_frame, text="Delete", activebackground="firebrick1",
                               command=lambda idx=i-2: self.delete(idx))
            bt_del.grid(row=i, column=2, padx=2, pady=1)

            self.entries.append([time_entry, temp_entry])

    def add_entry(self):
        dialog = TwoEntryDialog(
            self, text1="Time (DD:HH:MM)", text2="Temp (C)")
        # TODO: Replace this with if not dialog.result?
        if dialog is None:
            self.set_status("Nothing was entered", "red")
            return
        time = dialog.result[0]
        temp = dialog.result[1]
        add_time = tk.Entry(self.entries_frame)
        add_time.insert(0, time)
        add_temp = tk.Entry(self.entries_frame)
        add_temp.insert(0, temp)
        self.entries.append([add_time, add_temp])
        self.save()

    def save(self, path=FILE_PATH):
        try:
            entry_data = [(e[0].get(), e[1].get()) for e in self.entries]
            save_profile(entry_data, path)
            self.set_status("Saved!", "green")
        except Exception:
            self.set_status("Error while trying to save profile!", "red")
        self.refresh()

    def save_as(self):
        path = tk.filedialog.asksaveasfilename(
            initialdir=TEMPLATES, defaultextension=".csv")
        if path is None or path == () or path.strip() == "":
            return
        self.save()
        self.save(path)

    def delete(self, index):
        self.entries[index][0].destroy()
        self.entries[index][1].destroy()
        self.entries.pop(index)
        self.save()

    def load_from_file(self):
        filename = tk.filedialog.askopenfilename(initialdir=TEMPLATES)

        if filename is None or len(filename) == 0:
            msg = f"File with {filename} does not exist"
            self.set_status(msg, "red")
            return

        copy(filename, FILE_PATH)
        self.refresh()

    def generate_cycles(self):
        num_cycles = tk.simpledialog.askinteger(
            self, "Enter the number of cycles (>= 2)")

        if num_cycles is None:
            msg = "Nothing was entered"
            self.set_status("Nothing was entered!", "red")
            return

        if num_cycles < 2:
            msg = "Incorrect number of cycles specified: " + str(num_cycles)
            self.set_status(msg, "red")
            return

        create_cycles(num_cycles)
        self.refresh()
