import tkinter as tk

from csv_bisect_gui.bisect_tool import BisectTool


class Window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config(menu=self.create_main_menu())
        
        bisect_tool = BisectTool(self)
        bisect_tool.pack(fill=tk.BOTH, expand=True)

    def create_main_menu(self):
        file_menu = tk.Menu(tearoff=False)
        file_menu.add_command(label="Open")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)

        main_menu = tk.Menu()
        main_menu.add_cascade(label="File", menu=file_menu)
        return main_menu


def main():
    Window().mainloop()


if __name__ == "__main__":
    main()
