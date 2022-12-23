import threading
import time
import datetime
import sqlite3
import os
import functools
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as msg

class CountingThread(threading.Thread):
    def __init__(self, master, start_time, end_time):
        super().__init__()
        self.master = master
        self.start_time = start_time
        self.end_time = end_time

        self.end_now = False
        self.paused = False
        self.force_quit = False

    def run(self):
        while True:
            if not self.paused and not self.end_now and not self.force_quit:
                self.main_loop()
                if datetime.datetime.now() >= self.end_time:
                    if not self.force_quit:
                        self.master.finish()
                        break
            elif self.end_now:
                self.master.finish()
                break
            elif self.force_quit:
                del self.master.worker
                return
            else:
                continue
        return

    def main_loop(self):
        now = datetime.datetime.now()
        if now < self.end_time:
            time_difference = self.end_time - now
            mins, secs = divmod(time_difference.seconds, 60)
            time_string = "{:02d}:{:02d}".format(mins, secs)
            if not self.force_quit:
                self.master.update_time_remaining(time_string)


class LogWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__()

        self.title("Log")
        self.geometry("600x300")

        self.notebook = ttk.Notebook(self)

        dates_sql = "SELECT DISTINCT date FROM pymodoros ORDER BY date DESC"
        dates = self.master.runQuery(dates_sql, None, True)

        for index, date in enumerate(dates):
            dates[index] = date[0].split()[0]

        dates = sorted(set(dates), reverse=True)

        for date in dates:
            tab = tk.Frame(self.notebook)

            columns = ("name", "finished", "time")

            tree = ttk.Treeview(tab, columns=columns, show="headings")

            tree.heading("name", text="Name")
            tree.heading("finished", text="Full 25 Minutes")
            tree.heading("time", text="Time")

            tree.column("name", anchor="center")
            tree.column("finished", anchor="center")
            tree.column("time", anchor="center")

            tasks_sql = "SELECT * FROM pymodoros WHERE date LIKE ?"
            date_like = date + "%"
            data = (date_like,)

            tasks = self.master.runQuery(tasks_sql, data, True)

            for task_name, task_finished, task_date in tasks:
                task_finished_text = "Yes" if task_finished else "No"
                task_time = task_date.split()[1]
                task_time_pieces = task_time.split(":")
                task_time_pretty = "{}:{}".format(task_time_pieces[0], task_time_pieces[1])
                tree.insert("", tk.END, values=(task_name, task_finished_text, task_time_pretty))


            tree.pack(fill=tk.BOTH, expand=1)
            self.notebook.add(tab, text=date)

        self.notebook.pack(fill=tk.BOTH, expand=1)


class Timer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pomodoro Timer")
        self.geometry("500x300")
        self.resizable(False, False)

        self.standard_font = (None, 16)

        self.menubar = tk.Menu(self, bg="lightgrey", fg="black")

        self.log_menu = tk.Menu(self.menubar, tearoff=0, bg="lightgrey", fg="black")
        self.log_menu.add_command(label="View Log", command=self.show_log_window, accelerator="Ctrl+L")

        self.menubar.add_cascade(label="Log", menu=self.log_menu)
        self.configure(menu=self.menubar)

        self.main_frame = tk.Frame(self, width=500, height=300, bg="lightgrey")

        self.task_name_label = tk.Label(self.main_frame, text="Task Name:", bg="lightgrey", fg="black", font=self.standard_font)
        self.task_name_entry = tk.Entry(self.main_frame, bg="white", fg="black", font=self.standard_font)
        self.start_button = tk.Button(self.main_frame, text="Start", bg="lightgrey", fg="black", command=self.start, font=self.standard_font)
        self.time_remaining_var = tk.StringVar(self.main_frame)
        self.time_remaining_var.set("25:00")
        self.time_remaining_label = tk.Label(self.main_frame, textvar=self.time_remaining_var, bg="lightgrey", fg="black", font=(None, 40))
        self.pause_button = tk.Button(self.main_frame, text="Pause", bg="lightgrey", fg="black", command=self.pause, font=self.standard_font, state="disabled")

        self.main_frame.pack(fill=tk.BOTH, expand=1)

        self.task_name_label.pack(fill=tk.X, pady=15)
        self.task_name_entry.pack(fill=tk.X, padx=50, pady=(0,20))
        self.start_button.pack(fill=tk.X, padx=50)
        self.time_remaining_label.pack(fill=tk.X ,pady=15)
        self.pause_button.pack(fill=tk.X, padx=50)

        self.bind("<Control-l>", self.show_log_window)

        self.protocol("WM_DELETE_WINDOW", self.safe_destroy)

    def setup_worker(self):
        now = datetime.datetime.now()
        in_25_mins = now + datetime.timedelta(minutes=25)
        #in_25_mins = now + datetime.timedelta(seconds=3)
        worker = CountingThread(self, now, in_25_mins)
        self.worker = worker

    def start(self):
        if not self.task_name_entry.get():
            msg.showerror("No Task", "Please enter a task name")
            return

        if not hasattr(self, "worker"):
            self.setup_worker()

        self.task_name_entry.configure(state="disabled")
        self.start_button.configure(text="Finish", command=self.finish_early)
        self.time_remaining_var.set("25:00")
        self.pause_button.configure(state="normal")
        self.add_new_task()
        self.task_finished_early = False
        self.worker.start()

    def pause(self):
        self.worker.paused = not self.worker.paused
        if self.worker.paused:
            self.pause_button.configure(text="Resume")
            self.worker.start_time = datetime.datetime.now()
        else:
            self.pause_button.configure(text="Pause")
            end_timedelta = datetime.datetime.now() - self.worker.start_time
            self.worker.end_time = self.worker.end_time + datetime.timedelta(seconds=end_timedelta.seconds)

    def finish_early(self):
        self.start_button.configure(text="Start", command=self.start)
        self.task_finished_early = True
        self.worker.end_now = True

    def finish(self):
        self.task_name_entry.configure(state="normal")
        self.time_remaining_var.set("25:00")
        self.pause_button.configure(text="Pause", state="disabled")
        self.start_button.configure(text="Start", command=self.start)
        if not self.task_finished_early:
            self.mark_finished_task()
        del self.worker
        msg.showinfo("Pomodoro Finished!", "Task completed, take a break!")

    def update_time_remaining(self, time_string):
        self.time_remaining_var.set(time_string)
        self.update_idletasks()

    def add_new_task(self):
        task_name = self.task_name_entry.get()
        self.task_started_time = datetime.datetime.now()
        add_task_sql = "INSERT INTO pymodoros VALUES (?, 0, ?)"
        self.runQuery(add_task_sql, (task_name, self.task_started_time))

    def mark_finished_task(self):
        task_name = self.task_name_entry.get()
        add_task_sql = "UPDATE pymodoros SET finished = ? WHERE task = ? and date = ?"
        self.runQuery(add_task_sql, ("1", task_name, self.task_started_time))

    def show_log_window(self, event=None):
        LogWindow(self)

    def safe_destroy(self):
        if hasattr(self, "worker"):
            self.worker.force_quit = True
            self.after(100, self.safe_destroy)
        else:
            self.destroy()

    @staticmethod
    def runQuery(sql, data=None, receive=False):
        conn = sqlite3.connect("pymodoro.db")
        cursor = conn.cursor()
        if data:
            cursor.execute(sql, data)
        else:
            cursor.execute(sql)

        if receive:
            return cursor.fetchall()
        else:
            conn.commit()

        conn.close()

    @staticmethod
    def firstTimeDB():
        create_tables = "CREATE TABLE pymodoros (task text, finished integer, date text)"
        Timer.runQuery(create_tables)


if __name__ == "__main__":
    timer = Timer()

    if not os.path.isfile("pymodoro.db"):
        timer.firstTimeDB()

    timer.mainloop()

