import csv
import platform
import tkinter as tk
import tkinter.ttk as ttk
from pathlib import Path
from tkinter import filedialog

from csv_bisect_gui.bisect_tool import BisectTool

is_windows = platform.system() == "Windows"


class Window(tk.Tk):
    bisect_tool: BisectTool

    file_types: list[tuple[str, str]]

    executable_path: Path | None
    csv_path: Path | None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config(menu=self.create_main_menu())

        self.combo_encodings = self.init_combo_encodings()

        self.bisect_tool = BisectTool(self)
        self.bisect_tool.pack(fill=tk.BOTH, expand=True)

        self.file_types = self.init_file_types()

    def init_combo_encodings(self):
        frame = tk.Frame(self)

        label = tk.Label(frame, text="csv encoding:")
        label.pack(side=tk.LEFT)

        combo_encodings = ttk.Combobox(frame)
        encodings = ["cp437", "cp1251", "cp850", "cp852", "cp857", "latin3", "latin9", "viscii", "utf-8"]
        combo_encodings.config(values=encodings)
        combo_encodings.pack(fill=tk.X, expand=True)

        frame.pack(fill=tk.X)

        return combo_encodings

    @staticmethod
    def init_file_types():
        file_types = [
            ("exe files", "*.exe"),
            ("dwarfort", "dwarfort"),
            ("csv files", "*.csv"),
            ("All files", "*.*"),
        ]

        if is_windows:
            file_types.remove(("dwarfort", "dwarfort"))

        return file_types

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
            filetypes=self.file_types,
        )

        if not file_path:
            return

        self.process_selected_file(Path(file_path))

    def process_selected_file(self, file_path: Path):
        file_path = Path(file_path)
        if file_path.suffix == ".csv":
            self.executable_path = None
            self.csv_path = file_path
        elif file_path.suffix == ".exe" or file_path.name == "dwarfort":
            self.executable_path = file_path
            self.csv_path = file_path.parent / "dfint_data" / "dfint_dictionary.csv"
        else:
            self.executable_path = None
            self.csv_path = None

        if self.csv_path and self.csv_path.is_file:
            self.load_csv(self.csv_path)

    def load_csv(self, csv_path: Path):
        # TODO: Add encoding selection
        with open(csv_path, "r", encoding="cp437", newline="") as csv_file:
            csv_reader = csv.reader(csv_file)
            self.bisect_tool.strings = list(csv_reader)

    def backup_csv(self):
        pass  # TODO


if __name__ == "__main__":
    Window().mainloop()
