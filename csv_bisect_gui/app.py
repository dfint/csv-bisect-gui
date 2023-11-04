import tkinter as tk

from csv_bisect_gui.bisect_tool import BisectTool


def main():
    root = tk.Tk()

    bisect_tool = BisectTool(root)
    bisect_tool.pack(fill=tk.BOTH, expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
