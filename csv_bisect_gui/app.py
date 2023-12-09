import platform
import shutil
import tkinter as tk
import tkinter.ttk as ttk
from pathlib import Path
from tkinter import filedialog, messagebox

from alternative_encodings import cp866i, viscii

from csv_bisect_gui.bisect_tool import BisectTool

viscii.register()
cp866i.register()

is_windows = platform.system() == "Windows"


class Window(tk.Tk):
    bisect_tool: BisectTool

    file_types: list[tuple[str, str]]

    executable_path: Path | None
    csv_path: Path | None
    csv_backup_path: Path | None

    raw_data: list[bytes] | None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.csv_backup_path = None
        self.config(menu=self.create_main_menu())

        self.combo_encodings = self.init_combo_encodings()

        self.bisect_tool = BisectTool(self)
        self.bisect_tool.pack(fill=tk.BOTH, expand=True)

        self.file_types = self.init_file_types()

    def init_combo_encodings(self):
        frame = tk.Frame(self)

        label = tk.Label(frame, text="csv encoding:")
        label.pack(side=tk.LEFT)

        combo_encodings = ttk.Combobox(frame, state="readonly")
        encodings = ["cp437", "cp1251", "cp850", "cp852", "cp857", "latin3", "latin9", "viscii", "utf-8"]
        combo_encodings.config(values=encodings)
        combo_encodings.pack(fill=tk.X, expand=True)
        combo_encodings.set(encodings[0])
        combo_encodings.bind("<<ComboboxSelected>>", lambda _: self.load_csv())

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
            self.csv_backup_path = self.csv_path.with_suffix(".bac")
            self.check_backup()

            self.raw_data = None
            self.load_csv()

    def load_csv(self):
        if not self.csv_path:
            return

        if not self.raw_data:
            with open(self.csv_path, "rb") as file:
                self.raw_data = file.readlines()

        encoding = self.combo_encodings.get()
        try:
            decoded = [item.rstrip(b"\r\n").decode(encoding) for item in self.raw_data]
            self.bisect_tool.strings = decoded
        except UnicodeDecodeError:
            messagebox.showerror("ERROR", f"Failed to decode using {encoding} encoding")

    def check_backup(self):
        """
        Check if the backup file exists. If it does, ask the user if they want to restore backup.
        """
        if not self.csv_backup_path.exists():
            return

        response = messagebox.askyesno(
            "BACKUP EXISTS",
            "Backup of the csv file is already exists.\n"
            "Restore backup? (otherwise the backup file will be overwritten)",
        )

        if response == tk.YES:
            shutil.copyfile(self.csv_backup_path, self.csv_path)

    def backup_csv(self):
        pass  # TODO


if __name__ == "__main__":
    Window().mainloop()
