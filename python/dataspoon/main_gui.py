import tkinter as tk
import tkinter.messagebox as msg
from tkinter import filedialog
import configparser as cp


class MainGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.ini_file_path = '../../configuration.ini'

    def parse_ini_file(self, ini_file):
        self.active_ini = cp.ConfigParser()
        self.active_ini.read(ini_file)
        self.active_ini_filename = ini_file

        # self.section_select.delete(0, tk.END)

        for index, section in enumerate(self.active_ini.sections()):
            self.section_select.insert(index, section)
        if "DEFAULT" in self.active_ini:
            self.section_select.insert(len(self.active_ini.sections()) + 1, "DEFAULT")

        file_name = ": ".join([ntpath.basename(ini_file), ini_file])
        self.file_name_var.set(file_name)

        self.clear_right_frame()

    def file_open(self, event=None):
        ini_file = filedialog.askopenfilename()

        while ini_file and not ini_file.endswith(".ini"):
            msg.showerror("Wrong Filetype", "Please select an ini file")
            ini_file = filedialog.askopenfilename()

        if ini_file:
            self.parse_ini_file(ini_file)

    def file_save(self, event=None):
        if not self.active_ini:
            msg.showerror("No File Open", "Please open an ini file first")
            return

        chosen_section = self.section_select.get(self.section_select.curselection())

        for key in self.active_ini[chosen_section]:
            self.active_ini[chosen_section][key] = self.ini_elements[key].get()

        with open(self.active_ini_filename, "w") as ini_file:
            self.active_ini.write(ini_file)

        msg.showinfo("Saved", "File Saved Successfully")


if __name__ == "__main__":
    maingui = MainGUI()
    maingui.mainloop()