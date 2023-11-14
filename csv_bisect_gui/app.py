import platform
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from csv_bisect_gui.bisect_tool import BisectTool

is_windows = platform.system() == "Windows"


class Window(tk.Tk):
    bisect_tool: BisectTool

    file_types: list[tuple[str, str]]

    executable_path: Path | None
    csv_path: Path | None

    def __init__(self):
        super().__init__()
        self.config(menu=self.create_main_menu())

        self.bisect_tool = BisectTool(self)
        self.bisect_tool.pack(fill=tk.BOTH, expand=True)

        self.init_file_types()

    def init_file_types(self):
        self.file_types = [
            ("exe files", "*.exe"),
            ("dwarfort", "dwarfort"),
            ("csv files", "*.csv"),
            ("All files", "*.*"),
        ]

        if is_windows:
            self.file_types.remove(("dwarfort", "dwarfort"))

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

        messagebox.showinfo(title="Selected file", message=file_path)

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


def main():
    Window().mainloop()


if __name__ == "__main__":
    main()
