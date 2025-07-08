# Import standard python libraries
import tkinter as tk
import tkinter.ttk as ttk
import pathlib

# Importing source code
from src.edit_controller import load_profile, save_profile, create_cycles

TEMPLATES = pathlib.Path("resources/templates")


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


class Edit_Window(tk.Toplevel):

    def __init__(self, root):
        self.root = root
        super().__init__(self.root)

        # Set standard window size
        self.geometry("854x480")
        self.update()
        self.geometry()
        self.minsize(self.winfo_width(), self.winfo_height())
        self.resizable(True, True)

        self.title("Edit profile")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        main_frame = ttk.Frame(self)
        main_frame.pack(side="top", fill="both", expand=True)

        self.menu_frame = ttk.Frame(main_frame)
        self.menu_frame.pack(side="top", fill="x")
        self._build_menu()

        self.canvas = tk.Canvas(main_frame)
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            main_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.entries_frame = ttk.Frame(self.canvas)
        self.entries_frame.pack(anchor=tk.CENTER)
        self.canvas.create_window(
            (0, 0), window=self.entries_frame, anchor="n")
        self.entries_frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))

        self.bind_all("<Button-4>", self.on_mousewheel)
        self.bind_all("<Button-5>", self.on_mousewheel)

        self.entries = []
        self.refresh()

    def _build_menu(self):
        menu = tk.Menu(self.menu_frame, tearoff=0)
        self.config(menu=menu)

        self.profile_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Profile", menu=self.profile_menu)
        self.profile_menu.add_command(label="Add entry",
                                      command=self.add_entry)
        self.profile_menu.add_command(label="Save",
                                      command=self.save)
        self.profile_menu.add_command(label="Save as",
                                      command=self.save_as)
        self.profile_menu.add_command(label="Load",
                                      command=self.load)
        self.profile_menu.add_command(label="Create Cycles",
                                      command=self.generate_cycles)

        buttons_frame = ttk.Frame(self.menu_frame)
        buttons_frame.grid(row=0, column=0)

        ttk.Button(buttons_frame, text="Add entry", command=self.add_entry,
                   image=self.root.button_open.image).grid(row=0, column=0)
        ttk.Button(buttons_frame, text="Save", command=self.save,
                   image=self.root.button_save.image).grid(row=0, column=1)
        ttk.Button(buttons_frame, text="Save as", command=self.save_as,
                   image=self.root.button_save_as.image).grid(row=0, column=2)
        ttk.Button(buttons_frame, text="Load Profile",
                   command=self.load).grid(row=0, column=3)
        ttk.Button(buttons_frame, text="Create Cycles",
                   command=self.generate_cycles).grid(row=0, column=4)

    def on_closing(self):
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")
        self.destroy()

    def on_mousewheel(self, event):
        if event.num == 4:
            direction = -1
        elif event.num == 5:
            direction = 1

        self.canvas.yview_scroll(direction, "units")

    def refresh(self):

        for widget in self.entries_frame.winfo_children():
            widget.destroy()

        l1 = ttk.Label(self.entries_frame, text="Time (HH:MM)")
        l1.grid(row=0, column=0)
        l2 = ttk.Label(self.entries_frame, text="Temperature (C)")
        l2.grid(row=0, column=1)

        self.entries.clear()

        try:
            path = self.root.controller.profile_path
            data = load_profile(path)
        except Exception as err:
            print(err)
            tk.messagebox.showerror(
                title="Error!", message="Could not load profile.")
            return

        for i, (time, temp) in enumerate(data, start=1):
            time_entry = ttk.Entry(self.entries_frame)
            time_entry.insert(0, time)
            time_entry.grid(row=i, column=0, padx=2, pady=1)

            temp_entry = ttk.Entry(self.entries_frame)
            temp_entry.insert(0, temp)
            temp_entry.grid(row=i, column=1, padx=2, pady=1)

            bt_del = ttk.Button(self.entries_frame, text="Delete",
                                command=lambda idx=i-1: self.delete(idx))
            bt_del.grid(row=i, column=2, padx=2, pady=1)

            self.entries.append([time_entry, temp_entry])

    def add_entry(self):
        dialog = TwoEntryDialog(
            self, text1="Time (HH:MM)", text2="Temp (C)")
        if not dialog.result:
            return
        time = dialog.result[0]
        temp = dialog.result[1]

        add_time = ttk.Entry(self.entries_frame)
        add_temp = ttk.Entry(self.entries_frame)
        add_time.insert(0, time)
        add_temp.insert(0, temp)
        self.entries.append([add_time, add_temp])
        self.save()

    def save(self):
        path = self.root.controller.profile_path
        try:
            entry_data = [(e[0].get(), e[1].get()) for e in self.entries]
            save_profile(entry_data, path)
        except Exception:
            tk.messagebox.showerror(
                title="Error!", message="Unable to save profile!")
        self.refresh()
        self.root.get_new_profile()

    def save_as(self):
        path = tk.filedialog.asksaveasfilename(initialdir=TEMPLATES, filetypes=[
            ("*.csv", "*.csv")])
        if path == ():
            return
        self.root.controller.profile_path = pathlib.Path(path)
        self.save()

    def delete(self, index):
        self.entries[index][0].destroy()
        self.entries[index][1].destroy()
        self.entries.pop(index)
        self.save()

    def load(self):
        self.root.load_profile()
        self.refresh()

    def generate_cycles(self):
        num_cycles = tk.simpledialog.askinteger(
            title="Create Cycles", prompt="Enter the number x of cycles. x>=2", minvalue=2)
        if not num_cycles:
            return

        path = self.root.controller.profile_path
        create_cycles(num_cycles, path)
        self.refresh()
        self.root.get_new_profile()
