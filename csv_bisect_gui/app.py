import tkinter as tk

from csv_bisect_gui.bisect_tool import BisectTool


def create_main_menu():
    file_menu = tk.Menu(tearoff=False)
    file_menu.add_command(label="Open")
    file_menu.add_separator()
    file_menu.add_command(label="Exit")

    main_menu = tk.Menu()
    main_menu.add_cascade(label="File", menu=file_menu)
    return main_menu


def main():
    root = tk.Tk()
    root.config(menu=create_main_menu())

    bisect_tool = BisectTool(root)
    bisect_tool.pack(fill=tk.BOTH, expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
