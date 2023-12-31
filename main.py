import os
import sys
import tkinter as tk
from enum import Enum, IntEnum
from tkinter import *
from tkinter import messagebox, simpledialog
from typing import Callable
import time
import json
import gzip


# GLOBALS
ROWS = 25
COLUMNS = 15
COLUMNS_LEFT = COLUMNS
CURR_INDEX = 0
rows = []
entries: list[list[Entry]] = []
time_list: list[str] = []
root = tk.Tk()





# ENUMS
class ExperimentType(IntEnum):
    CONTROL = 1
    MINUTES_0_5 = 2
    MINUTES_1 = 3
    MINUTES_3 = 4
    MINUTES_5 = 5
    BREAK_1 = 6
    BREAK_3 = 7
    BREAK_4 = 8

class Movement(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4





# CLASSES
class Timer(Frame):
    def __init__(self, timer_time):
        Frame.__init__(self)
        self._left = timer_time
        self._running = False
        self.timestr = StringVar()
        self.l = Label(self, textvariable=self.timestr)
        self._set(self._left)
        self.l.grid(row=0, column=0, columnspan=COLUMNS)
        self.start()

    def _set(self, left):
        minutes = int(left / 60)
        seconds = int(left - minutes * 60.0)
        self.timestr.set('Hey! Take a break! You have %02d:%02d left.' % (minutes, seconds))

    def _update(self):
        self._left = self._left - 1
        if self._left <= 0:
            self._left = 0
            self.timestr.set("Break time over! Please continue the experiment.")
            switch_button_visibility(enable_entries, None, submit_button, 26, 4)
            sw.start()
            self._timer = self.after(1000, self.l.grid_forget)
            return
        self._set(self._left)
        self._timer = self.after(1000, self._update)

    def start(self):
        if not self._running:
            self._update()
            self._running = True


class Stopwatch(Frame):
    def __init__(self, master=None, **kw):
        Frame.__init__(self, master, **kw)
        self._start = 0.0
        self._elapsed = 0.0
        self._running = False
        self.timestr = StringVar()
        self._set(self._elapsed)

    def _update(self):
        self._elapsed = time.time() - self._start
        self._set(self._elapsed)
        self._timer = self.after(20, self._update)

    def _set(self, elap):
        minutes = int(elap / 60)
        seconds = int(elap - minutes * 60.0)
        hseconds = int((elap - minutes * 60.0 - seconds) * 100)
        self.timestr.set('%02d:%02d:%02d' % (minutes, seconds, hseconds))
        self.curr_elap = elap

    def start(self):
        if not self._running:
            self._start = time.time() - self._elapsed
            self._update()
            self._running = True

    def stop(self):
        if self._running:
            self.after_cancel(self._timer)
            self._elapsed = time.time() - self._start
            self._set(self._elapsed)
            self._running = False





# FUNCTIONS
def create_grid(num_rows, num_columns):
    for i in range(num_rows):
        row_entries = []
        for j in range(num_columns):
            entry = tk.Entry(root, width=10, state='disabled')
            entry.grid(row=i, column=j)
            row_entries.append(entry)
        entries.append(row_entries)

def find_selected_entry():
    row = -1
    column = -1
    on_focus: bool = False
    for r in range(ROWS):
        for c in range(COLUMNS):
            if entries[r][c] == root.focus_get():
                on_focus = True
                row = r
                column = c
                break
        if on_focus:
            del r, c
            return row, column
    if not on_focus:
        del r, c
        return False

def jump_to(movement: Movement):
    global CURR_INDEX
    focus = find_selected_entry()
    if not focus:
        return
    row = focus[0]
    column = focus[1]

    match movement:
        case Movement.UP:
            entries[(row - 1 if row > 0 else row)][column].focus_set()
        case Movement.DOWN:
            entries[(row + 1 if row < ROWS - 1 else row)][column].focus_set()
        case Movement.LEFT:
            entries[row][(column - 1 if column > get_columns_free()[CURR_INDEX - 1][1] else column)].focus_set()
        case Movement.RIGHT:
            temp = get_columns_free()[CURR_INDEX - 1]
            entries[row][(column + 1 if column < temp[0] + temp[1] - 1 else column)].focus_set()

def switch_button_visibility(action: Callable, button: Button | None, other: Button | None, row: int, column: int):
    if action is not None:
        action()
    if button is not None:
        button.grid_forget()
    if other is not None:
        other.grid(row=row, column=column)

def get_columns_free():
    match experiment:
        case 1:
            return [[15, 0]]
        case 2 | 3 | 4 | 5:
            return [[5, 0], [5, 5], [5, 10]]
        case 6:
            return [[7, 0], [8, 7]]
        case 7:
            return [[3, 0], [4, 3], [4, 7], [4, 11]]
        case 8:
            return [[3, 0], [3, 3], [3, 6], [3, 9], [3, 12]]

def enable_entries():
    global CURR_INDEX, COLUMNS_LEFT
    curr = get_columns_free()[CURR_INDEX]
    columns_to_enable: int = curr[0]
    COLUMNS_LEFT -= columns_to_enable
    [entries[i][j].config(state='normal') for i in range(ROWS) for j in range(curr[1], columns_to_enable + curr[1])]
    entries[0][curr[1]].focus_set()
    CURR_INDEX += 1

def save_data_to_file():
    amount_wrong = 0
    with open("data.txt", "w") as f:
        f.write(str(sheet_number) + "\n")
        f.write(experiment.name + "\n")
        f.write(sw.timestr.get() + "\n")
        for t in time_list:
            f.write(str(t) + ", ")
        f.write("\n\n")
        for row in range(ROWS):
            for column in range(COLUMNS):
                if not entries[row][column].get().isdigit():
                    amount_wrong += 1
                elif int(entries[row][column].get()) != data[row][column]:
                    amount_wrong += 1
                f.write(entries[row][column].get() + ", ")
            f.write("\n")

        f.write("\n\n" + str(amount_wrong))
        f.write("\n" + str(100 - round(amount_wrong / (ROWS * COLUMNS) * 100, 3)) + "%")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)





# EVENTS
def start_button_event():
    switch_button_visibility(sw.start, start_button, submit_button, 26, 4)
    enable_entries()

def submit_button_event():
    info_var = StringVar()
    info_label = Label(root, textvariable=info_var)

    open_entries = [e for row in entries for e in row if e.cget("state") == "normal"]
    for entry in open_entries:
        if entry.get() == "":
            info_var.set("Please fill in all the entries!")
            info_label.grid(row=26, column=10, columnspan=COLUMNS)
            return root.after(3000, info_label.grid_forget)

    switch_button_visibility(sw.stop, submit_button, None, 26, 4)
    time_list.append(sw.curr_elap - sum(time_list))
    [e.config(state='disabled') for e in open_entries]
    if COLUMNS_LEFT == 0:
        save_data_to_file()
        messagebox.showinfo("Experiment Complete", ("Experiment complete! Thank you for participating!\n"
                                                        "Please send the data.txt file to the experimenter.\n"
                                                        "You may not tamper with the data.txt file.\n"
                                                        "You may now safely close this window and the following below it."))
        info_var.set(sw.timestr.get())
        info_label.grid(row=26, column=10, columnspan=COLUMNS)
        return

    timer_time = 0
    match experiment:
        case 1:
            timer_time = 0
        case 2:
            timer_time = 30
        case 3 | 6 | 7 | 8:
            timer_time = 60
        case 4:
            timer_time = 180
        case 5:
            timer_time = 300

    timer = Timer(timer_time)
    timer.grid(row=26, column=10, columnspan=COLUMNS)

def on_closing():
    if messagebox.askokcancel("Confirm Quit", "Do you really want to quit? All data will be lost and you will have to start the experiment over."):
        root.destroy()






# WINDOWS
def display_instructions():
    rule_window = Toplevel(root)
    rule_window.title = "Instructions"
    rule_window.iconbitmap(resource_path("icon.ico"))
    rule_window.resizable(False, False)
    title = Label(rule_window, text="Instructions", font=("Segoe UI", 18, "bold"), foreground="black")
    title.grid(row=0, column=0)
    rule_text = """    Welcome to the experiment! In this experiment, you will input the numbers given on the paper into the grid.
    
    Basic Instructions:
    - When you click on the 'Submit' button, the timer will stop and you will take a break.
    - When you are taking a break, there are a few guidelines:
    
        - You may not leave your seat. This is to minimize any bias and distractions and keep the experiment fair.
        - You may use your computer, phone, any other approved device, books, etc. to keep yourself occupied. You can even take a nap (if you want to).
        - Make sure to keep an eye on the time! The program will start after the time reaches 0.
        - DO NOT X OUT THE PROGRAM WHEN YOU ARE TAKING THE BREAK. THIS WILL RESULT IN A LOSS OF DATA.
    
    - When this experiment is completed, a 'data.txt' file should appear in the same folder as this program (most likely "Downloads"). This file should be sent to the experimenter (me).
    - You may not tamper with the data.txt file. The best way for me to receive the data.txt file is by email.
    
    Tips:
    - If you want to move to the next entry to the right, you can press the 'Tab' key (like in Spreadsheets and Excel) or use the right arrow.
    - If you want to move to the next entry to the left, you can press the 'Shift' and 'Tab' keys together or use the left arrow.
    - With the 'Tab' and 'Shift-Tab' shortcuts, the cursor will 'loop back' to the beginning of the row or the end of the row.
    
    - If you want to move to the next entry below, you can press the 'Enter' key or use the down arrow.
    - If you want to move to the next entry above, you can press the 'Shift' and 'Enter' keys together or use the up arrow.
    
    - The timer is always ticking when not taking a break. Make sure to complete the experiment on time!
    
    - Be as accurate as possible. Your score will be calculated based on your time and accuracy. You can only click on the "Submit" button once you fill out all of the available entries.
    
    Good luck!
    """
    rules = Label(rule_window, text=rule_text, font=("Segoe UI", 12), foreground="black", anchor="w", justify="left")
    rules.grid(row=1, column=0)






# ! Main program

root.title("Trial")
root.iconbitmap(resource_path("icon.ico"))
root.resizable(False, False)

# Centers the window
w, h = 960, 500
ws, hs = root.winfo_screenwidth(), root.winfo_screenheight()
x, y = (ws / 2) - (w / 2), (hs / 2) - (h / 2)
root.geometry("%dx%d+%d+%d" % (w, h, x, y))
del w, h, ws, hs, x, y

create_grid(ROWS, COLUMNS)

# Loads JSON data from user input
sheet_number: int = -1
while not (0 < sheet_number < 11):
    sheet_number = simpledialog.askinteger("Sheet Number", "Enter the sheet number:")
    if sheet_number is None:
        sheet_number = -1
    if not 0 < sheet_number < 11:
        messagebox.showinfo("Error", "Please enter a valid sheet number between 1 and 10.")

messagebox.showinfo("Data successfully loaded", "Data successfully loaded.")

with gzip.open(resource_path("data.json.gz"), "rt", encoding="utf-8") as f:
    data = json.load(f)
del f
data = data[str(sheet_number)]

experiment_type = -1
while not (0 < experiment_type < 9):
    experiment_type = simpledialog.askinteger("Sheet Number", ("Enter the sheet number:\n"
                                                                    "Here are the choices:\n"
                                                                    "1:  0 breaks\n"
                                                                    "2:  2 breaks, each 0.5 minutes\n"
                                                                    "3:  2 breaks, each 1 minute\n"
                                                                    "4:  2 breaks, each 3 minutes\n"
                                                                    "5:  2 breaks, each 5 minutes\n"
                                                                    "6:  1 break, each 1 minute\n"
                                                                    "7:  3 breaks, each 1 minute\n"
                                                                    "8:  4 breaks, each 1 minute\n"
                                                                    "If you do not know, please check the email for more information."))

    if experiment_type is None:
        experiment_type = -1
    if not 0 < experiment_type < 9:
        messagebox.showinfo("Error", "Please enter a valid sheet number between 1 and 8.")

experiment: ExperimentType
match experiment_type:
    case 1:
        experiment = ExperimentType.CONTROL
    case 2:
        experiment = ExperimentType.MINUTES_0_5
    case 3:
        experiment = ExperimentType.MINUTES_1
    case 4:
        experiment = ExperimentType.MINUTES_3
    case 5:
        experiment = ExperimentType.MINUTES_5
    case 6:
        experiment = ExperimentType.BREAK_1
    case 7:
        experiment = ExperimentType.BREAK_3
    case 8:
        experiment = ExperimentType.BREAK_4
del experiment_type

# Movement of selection. Allows tab loopback
root.bind('<Return>', func=lambda event: jump_to(Movement.DOWN))
root.bind('<Shift-Tab>', func=lambda event: jump_to(Movement.LEFT))
root.bind('<Tab>', func=lambda event: jump_to(Movement.RIGHT))
root.bind('<Shift-Return>', func=lambda event: jump_to(Movement.UP))
root.bind('<Up>', func=lambda event: jump_to(Movement.UP))
root.bind('<Down>', func=lambda event: jump_to(Movement.DOWN))
root.bind('<Left>', func=lambda event: jump_to(Movement.LEFT))
root.bind('<Right>', func=lambda event: jump_to(Movement.RIGHT))

instructions = Button(root, text="Instructions", command=display_instructions, width=8)
instructions.grid(row=26, column=7)

sw = Stopwatch(root)

start_button = Button(root, text="Start", command=lambda: start_button_event(), width=8)
submit_button = Button(root, text="Submit", command=submit_button_event, width=8)

start_button.grid(row=26, column=4)

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
