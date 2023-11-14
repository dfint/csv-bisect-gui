import tkinter as tk
from tkinter import filedialog, messagebox

from csv_bisect_gui.bisect_tool import BisectTool


class Window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config(menu=self.create_main_menu())

        self.bisect_tool = BisectTool(self)
        self.bisect_tool.pack(fill=tk.BOTH, expand=True)

    def create_main_menu(self):
        file_menu = tk.Menu(tearoff=False)
        file_menu.add_command(label="Open", command=self.select_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)

        main_menu = tk.Menu()
        main_menu.add_cascade(label="File", menu=file_menu)
        return main_menu

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Select an executable or a csv file",
            filetypes = (
                ("exe files", "*.exe"),
                ("dwarfort", "dwarfort"),
                ("csv files", "*.csv"),
                ("All files", "*.*"),
            ),
        )

        if not file_path:
            return

        messagebox.showinfo(title="Selected file", message=file_path)


def main():
    Window().mainloop()


if __name__ == "__main__":
    main()
