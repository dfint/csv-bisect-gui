import platform
import shutil
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

import alternative_encodings
from tkinter_layout_helpers import pack_manager

from csv_bisect_gui.bisect_tool import BisectTool

alternative_encodings.register_all()

encodings = [
    "cp437",
    "cp850",
    "cp852",
    "cp857",
    "cp859",
    "cp866",
    "cp866i",
    "cp866u",
    "cp1251",
    "latin3",
    "latin9",
    "romaji",
    "viscii",
    "utf-8",
]

is_windows = platform.system() == "Windows"


class Window(tk.Tk):
    bisect_tool: BisectTool[str]

    file_types: list[tuple[str, str]]

    executable_path: Path | None
    csv_path: Path | None
    csv_backup_path: Path | None = None

    raw_data: list[bytes] | None

    def __init__(self, *args: list[Any], **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)

        self.file_types = self.init_file_types()
        self.config(menu=self.create_main_menu())

        self.combo_encodings = self.init_combo_encodings()

        self.bisect_tool = BisectTool[str](self)
        self.bisect_tool.pack(fill=tk.BOTH, expand=True)

        with pack_manager(self, side=tk.LEFT, expand=True, fill=tk.X, padx=1) as toolbar:
            toolbar.pack_all(
                ttk.Button(text="Write selection to csv", command=self.write_csv),
                ttk.Button(text="Exclude selection from csv", command=self.exclude_from_csv),
                ttk.Button(text="Restore csv from backup", command=self.restore_backup),
            )

    def init_combo_encodings(self) -> ttk.Combobox:
        frame = tk.Frame(self)

        label = tk.Label(frame, text="csv encoding:")
        label.pack(side=tk.LEFT)

        combo_encodings = ttk.Combobox(frame, state="readonly")
        combo_encodings.config(values=encodings)
        combo_encodings.pack(fill=tk.X, expand=True)
        combo_encodings.set(encodings[0])
        combo_encodings.bind("<<ComboboxSelected>>", lambda _: self.load_csv())

        frame.pack(fill=tk.X)

        return combo_encodings

    @staticmethod
    def init_file_types() -> list[tuple[str, str]]:
        dwarfort = ("dwarfort", "dwarfort")
        file_types = [
            ("exe files", "*.exe"),
            dwarfort,
            ("csv files", "*.csv"),
            ("All files", "*.*"),
        ]

        if is_windows:
            file_types.remove(dwarfort)

        return file_types

    def create_main_menu(self) -> tk.Menu:
        file_menu = tk.Menu(tearoff=False)
        file_menu.add_command(label="Open", command=self.select_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)

        main_menu = tk.Menu()
        main_menu.add_cascade(label="File", menu=file_menu)
        return main_menu

    def select_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select an executable or a csv file",
            filetypes=self.file_types,
        )

        if not file_path:
            return

        self.process_selected_file(Path(file_path))

    def process_selected_file(self, file_path: Path) -> None:
        file_path = Path(file_path)
        if file_path.suffix == ".csv":
            self.executable_path = None
            self.csv_path = file_path
        elif file_path.suffix == ".exe" or file_path.name == "dwarfort":
            self.executable_path = file_path
            self.csv_path = file_path.parent / "dfint_data" / "dfint_dictionary.csv"
            if not self.csv_path.exists():
                self.csv_path = file_path.parent / "dfint-data" / "dictionary.csv"
        else:
            self.executable_path = None
            self.csv_path = None

        if self.csv_path and self.csv_path.is_file:
            self.csv_backup_path = self.csv_path.with_suffix(".bac")
            self.backup_csv()

            self.raw_data = None
            self.load_csv()

    def load_csv(self) -> None:
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

    def write_csv(self) -> None:
        if not self.csv_path:
            return

        with open(self.csv_path, "wb") as file:
            for node in self.bisect_tool.selected_nodes:
                file.writelines(self.raw_data[node.slice])

    def exclude_from_csv(self) -> None:
        if not self.csv_path:
            return

        selection = list(self.bisect_tool.selected_nodes)

        if len(selection) > 1:
            messagebox.showerror("ERROR", "Select one row")
            return

        node = selection[0]
        selection_slice = node.slice

        before_selection = slice(0, selection_slice.start)
        after_selection = slice(selection_slice.stop, -1)

        with open(self.csv_path, "wb") as file:
            file.writelines(self.raw_data[before_selection])

            file.writelines(self.raw_data[after_selection])

    def backup_csv(self) -> None:
        if self.csv_backup_path.exists() and self.csv_backup_path.read_bytes() == self.csv_path.read_bytes():
            return

        self.check_backup()

        shutil.copyfile(self.csv_path, self.csv_backup_path)

    def restore_backup(self) -> None:
        if not self.csv_backup_path:
            return

        shutil.copyfile(self.csv_backup_path, self.csv_path)

    def check_backup(self) -> None:
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
            self.restore_backup()

    def report_callback_exception(self, exc, val, tb) -> None:  # noqa: ANN001
        if issubclass(exc, KeyboardInterrupt):
            self.quit()
            return

        super().report_callback_exception(exc, val, tb)

        filename, line, *_ = traceback.extract_tb(tb).pop()
        messagebox.showerror("Unhandled Exception", f"{exc.__name__}: {val}\n{filename}, line: {line}")


def main() -> None:
    Window().mainloop()


if __name__ == "__main__":
    main()
