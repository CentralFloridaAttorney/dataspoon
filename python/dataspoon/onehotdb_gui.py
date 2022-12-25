import configparser as cp
import ntpath
import tkinter as tk
import tkinter.messagebox as msg
from pathlib import Path
from tkinter import filedialog

import pandas

from python.dataspoon.dbtool import OneHotWords
from python.dataspoon.onehotdb import OneHotDB
from python.dataspoon.textprocessor import TextProcessor

ONE_HOT_KEY = 'onehotdb_gui'

class OneHotDBGUI(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("OneHotDB")
        self.geometry("600x600")

        self.active_ini = ""
        self.active_ini_filename = ""
        self.ini_elements = {}

        self.menubar = tk.Menu(self, bg="lightgrey", fg="black")

        self.file_menu = tk.Menu(self.menubar, tearoff=0, bg="lightgrey", fg="black")
        self.file_menu.add_command(label="Select File", command=self.get_processed_text, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Save Words", command=self.save_words, accelerator="Ctrl+W")
        self.file_menu.add_command(label="Save", command=self.file_save, accelerator="Ctrl+S")

        self.menubar.add_cascade(label="File", menu=self.file_menu)

        self.config(menu=self.menubar)

        self.left_frame = tk.Frame(self, width=200, bg="grey")
        self.left_frame.pack_propagate(0)

        self.right_frame = tk.Frame(self, width=400, bg="lightgrey")
        self.right_frame.pack_propagate(0)

        self.file_name_var = tk.StringVar(self)
        self.file_name_label = tk.Label(self, textvar=self.file_name_var, fg="black", bg="white", font=(None, 12))
        self.file_name_label.pack(side=tk.TOP, expand=1, fill=tk.X, anchor="n")

        self.section_select = tk.Listbox(self.left_frame, selectmode=tk.SINGLE)
        self.section_select.configure(exportselection=False)
        self.section_select.pack(expand=1)
        self.section_select.bind("<<ListboxSelect>>", self.display_section_contents)

        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH)
        self.right_frame.pack(side=tk.LEFT, expand=1, fill=tk.BOTH)

        self.right_frame.bind("<Configure>", self.frame_height)

        self.bind("<Control-o>", self.get_processed_text)
        self.bind("<Control-s>", self.file_save)

    def frame_height(self, event=None):
        new_height = self.winfo_height()
        self.right_frame.configure(height=new_height)

    @staticmethod
    def save_words():
        dataframe = OneHotWords().get_dataframe()
        dataframe.to_csv('../../data/txt/words.csv', index=False)

    def get_processed_text(self, event=None):
        data_file = filedialog.askopenfilename(initialdir='../../data/txt/')

        while data_file and not (data_file.endswith(".pkl") or data_file.endswith(".txt")):
            msg.showerror("Wrong Filetype", "Please select an pkl or txt file")
            data_file = filedialog.askopenfilename()

        if data_file:
            result = self.parse_data_file(data_file)

        onehot_file_path = Path(data_file)
        onehot_file_name = onehot_file_path.with_suffix('.hot')
        onehot_file = open(onehot_file_name, 'w+')
        onehot_file.write(result)
        onehot_file.close()
        print('get_processed_text done!')
        return result

    def file_save(self, event=None):
        if not self.active_ini:
            msg.showerror("No File Open", "Please open an ini file first")
            return

        for section in self.active_ini:
            for key in self.active_ini[section]:
                try:
                    self.active_ini[section][key] = self.ini_elements[section][key].get()
                except KeyError:
                    # wasn't changed, no need to save it
                    pass

        with open(self.active_ini_filename, "w") as ini_file:
            self.active_ini.write(ini_file)

        msg.showinfo("Saved", "File Saved Successfully")

    @staticmethod
    def parse_data_file(_file_path):
        if _file_path.endswith('.pkl'):
            processed_string = pandas.read_pickle(_file_path)
        elif _file_path.endswith('.txt'):
            file = open(_file_path, 'r+')
            file_text = file.read()
            file.close()
            processed_string = TextProcessor(_given_string=file_text).get_processed_string()
        else:
            processed_string = "OneHotDBGUI.parse_data_file expected a _file_path ending with .txt or .pkl"
        onehotdb = OneHotDB()
        result = onehotdb.put_onehot(ONE_HOT_KEY, processed_string)
        return result

    def parse_ini_file(self, ini_file):
        self.active_ini = cp.ConfigParser()
        self.active_ini.read(ini_file)
        self.active_ini_filename = ini_file

        self.section_select.delete(0, tk.END)

        for index, section in enumerate(self.active_ini.sections()):
            self.section_select.insert(index, section)
            self.ini_elements[section] = {}
        if "DEFAULT" in self.active_ini:
            self.section_select.insert(len(self.active_ini.sections()) + 1, "DEFAULT")
            self.ini_elements["DEFAULT"] = {}

        file_name = ": ".join([ntpath.basename(ini_file), ini_file])
        self.file_name_var.set(file_name)

        self.clear_right_frame()

    def clear_right_frame(self):
        for child in self.right_frame.winfo_children():
            child.destroy()

    def display_section_contents(self, event=None):
        if not self.active_ini:
            msg.showerror("No File Open", "Please open an ini file first")
            return

        chosen_section = self.section_select.get(self.section_select.curselection())

        for child in self.right_frame.winfo_children():
            child.pack_forget()

        for key in sorted(self.active_ini[chosen_section]):
            new_label = tk.Label(self.right_frame, text=key, font=(None, 12), bg="black", fg="white")
            new_label.pack(fill=tk.X, side=tk.TOP, pady=(10, 0))

            try:
                section_elements = self.ini_elements[chosen_section]
            except KeyError:
                section_elements = {}

            try:
                ini_element = section_elements[key]
            except KeyError:
                value = self.active_ini[chosen_section][key]

                if value.isnumeric():
                    spinbox_default = tk.IntVar(self.right_frame)
                    spinbox_default.set(int(value))
                    ini_element = tk.Spinbox(self.right_frame, from_=0, to=99999, textvariable=spinbox_default,
                                             bg="white", fg="black", justify="center")
                else:
                    ini_element = tk.Entry(self.right_frame, bg="white", fg="black", justify="center")
                    ini_element.insert(0, value)

                self.ini_elements[chosen_section][key] = ini_element

            ini_element.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))

        save_button = tk.Button(self.right_frame, text="Save Changes", command=self.file_save)
        save_button.pack(side=tk.BOTTOM, pady=(0, 20))


if __name__ == "__main__":
    ini_editor = OneHotDBGUI()
    ini_editor.mainloop()
