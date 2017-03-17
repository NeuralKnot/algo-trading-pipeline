from multiprocessing import Process, Queue
import json
import tkinter as tk

from gui.page import MainPage, StatsPage
from data_analysis.data_analysis import DataAnalysis
from data_input.data_input import DataInput
from trader.trader import Trader
from logger import Logger
from pyvirtualdisplay import Display
import psutil
import uuid


# Main process
class Bot:
    # Start pyvirtualdisplay for headless runs
    display = Display(visible=0, size=(800, 800))
    display.start()

    # Process variables
    scraper = None
    trader = None
    processes = []

    # Queues to be delegated to sub-processes
    message_queue = Queue()
    article_queue = Queue()
    result_queue = Queue()

    running = False

    # Initializes all of the processes
    def __init__(self, config):
        # Assign random session ID for logs, etc
        self.session_id = str(uuid.uuid4())

        self.config = config
        self.log_file = open("logs/" + self.session_id + ".txt", "w")
        self.logger = Logger(self.message_queue)

        self.scraper = DataInput(self.article_queue, self.logger, self.config)
        self.processes.append(Process(target=self.scraper.run))
        for num in range(config["data_analysis"]["num_workers"]):
            obj = DataAnalysis(self.config, self.logger, self.article_queue, self.result_queue)
            self.processes.append(
                Process(target=obj.run)
            )
        self.trader = Trader(self.result_queue, self.logger, self.config)
        self.processes.append(Process(target=self.trader.run))

        self.gui = tk.Tk()
        self.gui.geometry("1080x720")

        tk.Tk.wm_title(self.gui, "Algo Trading Bot")

        container = tk.Frame(self.gui)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        menu = tk.Menu(container)
        viewmenu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="View", menu=viewmenu)
        viewmenu.add_command(label="Control", command=lambda: self.show_frame(MainPage))
        viewmenu.add_command(label="Stats", command=lambda: self.show_frame(StatsPage))
        tk.Tk.config(self.gui, menu=menu)

        self.frames = {}

        for frameType in (MainPage, StatsPage):
            frame = frameType(container, self)
            self.frames[frameType] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(MainPage)

        self.gui.after(10, self.poll_messages)
        self.gui.after(10, self.prune_databases)
        self.gui.after(10, self.sell_positions)
        self.gui.after(10, self.check_processes)
        self.gui.after(1, self.start)

        while True:
            try:
                self.gui.mainloop()
            except UnicodeDecodeError:
                pass

    def poll_messages(self):
        try:
            msg = self.message_queue.get(True)
            if msg is not None:
                self.print_to_screen(msg)
                print(msg)
                self.log_file.write(msg + "\n")
                self.log_file.flush()
                self.gui.after(100, self.poll_messages)
            else:
                self.gui.after(100, self.poll_messages)
        except Exception as e:
            self.logger.log("Main", "error", "Error polling messages: " + str(e))

        self.gui.after(100, self.poll_messages)

    def prune_databases(self):
        try:
            self.logger.log("Main", "informative", "Triggering db prune...")
            self.scraper.prune_databases()
        except Exception as e:
            self.logger.log("Main", "error", "Error pruning databases: " + str(e))

        self.gui.after(600000, self.prune_databases) # Prune every 10 mins

    def sell_positions(self):
        try:
            self.logger.log("Main", "informative", "Triggering position sell-off...")
            self.trader.sell_positions()
        except Exception as e:
            self.logger.log("Main", "error", "Error selling positions: " + str(e))

        self.gui.after(600000, self.sell_positions) # Sell every 10 mins

    def check_processes(self):
        try:
            self.logger.log("Main", "informative", "Checking processes...")
            for process in self.processes:
                proc = psutil.Process(process.pid)
                if not proc.is_running():
                    self.logger.log("Main", "error", "Process crashed!  Exiting program.")
                    self.stop() # We can't trust the program after a process crashes.
            self.logger.log("Main", "informative", "Processes OK!")
        except Exception as e:
            self.logger.log("Main", "error", "Error checking processes: " + str(e))
            self.stop() # Stop here sinc a process probably died, causing this error

        self.gui.after(100, self.check_processes) # Check again in 100ms

    # Starts the processes
    def start(self):
        self.running = True
        self.print_to_screen('Starting bot...')

        for process in self.processes:
            process.start()

    # Shuts down the program
    def stop(self):
        self.running = False
        self.trader.quit()
        for process in self.processes:
            process.terminate()
        exit()

    def print_trade(self, str):
        self.frames[MainPage].print_trade(str)

    def print_to_screen(self, str):
        self.frames[MainPage].print(str)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

if __name__ == "__main__":
    bot = Bot(json.load(open("config.json")))
