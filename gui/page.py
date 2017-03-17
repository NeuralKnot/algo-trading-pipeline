import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from matplotlib import style

style.use("dark_background")

BG_COLOR = "#303030"
BG_ALT_COLOR = "#202020"
FONT_COLOR = "#FFFFFF"
FONT_ALT_COLOR = "#DDDDDD"
LARGE_FONT = ("Helvetica Light", 20)
FONT = ("Courier New", 16)


class MainPage(tk.Frame):

    running = False

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.configure(bg=BG_COLOR)
        self.pack(fill=tk.BOTH, expand=1)

        style = ttk.Style()
        style.configure('TButton', background=BG_COLOR, borderthickness=0, highlightthickness=0, width=10)

        p1 = tk.PanedWindow(self, orient=tk.VERTICAL, bg=BG_COLOR)
        p1.pack(fill=tk.BOTH, expand=1)

        p2 = tk.PanedWindow(p1, bg=BG_COLOR)
        p2.grid_columnconfigure(0, weight=1)
        p2.grid_columnconfigure(1, weight=1)
        p1.add(p2)

        control = tk.Frame(p2, bg=BG_COLOR)
        control.grid_rowconfigure(1, weight=1)
        pbutton = ttk.Button(control, text="Start", command=lambda: power())
        pbutton.grid(row=0, column=0)
        statsbutton = ttk.Button(control, text="Statistics", command=lambda: controller.show_frame(StatsPage))
        statsbutton.grid(row=1, column=0)
        control.grid(row=0, column=0)

        trades = tk.Frame(p2, bg=BG_COLOR)
        ltrades = tk.Label(trades, text="Trades", font=LARGE_FONT, bg=BG_COLOR, fg=FONT_COLOR)
        ltrades.pack(pady=15)
        tradescroll = tk.Scrollbar(trades, width=12)
        tradescroll.pack(side=tk.RIGHT, fill=tk.Y)
        tradelist = tk.Listbox(trades, width=80, height=20, yscrollcommand=tradescroll.set, bg=BG_ALT_COLOR, fg=FONT_ALT_COLOR, font=FONT, selectbackground="#404040")
        tradelist.pack(side=tk.BOTTOM, fill=tk.BOTH)
        self.tradelist = tradelist
        tradescroll.config(command=tradelist.yview)
        trades.grid(row=0, column=1)

        readout = tk.Frame(p1, bg=BG_COLOR)
        scrollbar = tk.Scrollbar(readout, width=12)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        treadout = tk.Text(readout, yscrollcommand=scrollbar.set, state=tk.DISABLED, highlightthickness=0, bg=BG_ALT_COLOR, fg=FONT_ALT_COLOR, font=("Menlo", 12))
        treadout.pack(side=tk.BOTTOM, fill=tk.BOTH)
        self.console = treadout
        scrollbar.config(command=treadout.yview)
        p1.add(readout, padx=20, pady=20)

        def power():
            if not self.running:
                controller.start()
                pbutton.configure(text="Quit")
                self.running = True
            else:
                controller.stop()
                pbutton.configure(text="Start")
                self.running = False

    def printtrade(self, str):
        self.tradelist.insert(0, str)

    def print(self, str):
        self.console.configure(state=tk.NORMAL)
        self.console.insert(index=tk.END, chars=" > " + str + "\n")
        self.console.configure(state=tk.DISABLED)


class StatsPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.configure(bg=BG_COLOR)

        self.trends = Figure(figsize=(5, 5), dpi=100)
        self.a = self.trends.add_subplot(111)

        canvas = FigureCanvasTkAgg(self.trends, self)
        canvas.show()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=1)

        self.animation = FuncAnimation(self.trends, self.animate, 5000)

    def animate(self, i):
        self.a.clear()
        self.a.plot([1,2,3,4,5,6,7,8], [0,5,7,4,12,15,23,20])

