import time
from trader.web_interface import WebInterface
from tinydb import *
import datetime
import arrow

class Trader:

    def __init__(self, result_queue, logger, config):
        self.result_queue = result_queue
        self.logger = logger
        self.config = config
        self.web_interface = WebInterface(config["trader"]["user"], config["trader"]["pass"])
        self.position_db = TinyDB("db/positions.db.json")

    def sell_positions(self):
        q = Query()
        test_func = lambda closed: not closed
        docs = self.position_db.search(q.closed.test(test_func))

        # Sell and remove position if >1hr old
        for doc in docs:
            if arrow.get(doc["at"]) < (arrow.now() - datetime.timedelta(hours=1)):
                self.logger.log("Trader/Seller", "informative", "Selling position for contract " + doc["contract_id"] + "!")

                if self.web_interface.have_position_in_market(doc["contract_id"]):
                    self.web_interface.sell(doc["contract_id"], doc["side"], doc["amount"])

                self.position_db.update({ "closed": True }, eids=[doc.eid])

    # Make a trade based on the result
    def handle_result(self, result):
        contract = result["market"]["contract_id"]

        self.logger.log("Trader", "informative", "Received article for market " + contract + ": " + result["article"]["title"])

        what_to_buy = None
        scores = list(result["score"])
        max_index = scores.index(max(scores))

        # Skip if we already have a position in this market
        # (prevents duplicate trades)
        if self.web_interface.have_position_in_market(contract):
            self.logger.log("Trader", "informative", "Skipping article, already have position in market " + contract + ": " + result["article"]["title"])
            return

        # Make a trade if the score > 0.5 (i.e. we're confident)
        if scores[max_index] > 0.5:
            if max_index == 2:
                self.logger.log("Trader", "informative", "Buying YES shares for market " + contract + ": " + result["article"]["title"])
                self.position_db.insert({
                    "contract_id": contract,
                    "side": WebInterface.YES,
                    "amount": 1,
                    "closed": False,
                    "at": str(arrow.now())
                })
                self.web_interface.buy(contract, WebInterface.YES, 1, 50)
            elif max_index == 1:
                self.logger.log("Trader", "informative", "Buying NO shares for market " + contract + ": " + result["article"]["title"])
                self.position_db.insert({
                    "contract_id": contract,
                    "side": WebInterface.NO,
                    "amount": 1,
                    "closed": False,
                    "at": str(arrow.now())
                })
                self.web_interface.buy(contract, WebInterface.NO, 1, 50)
            else:
                # The machine learning algorithm thinks this article is irrelevant,
                # so skip it.
                self.logger.log("Trader", "informative", "Not buying shares for market " + contract + ": " + result["article"]["title"])

    # Entry point for process
    def run(self):
        try:
            while True:
                result = self.result_queue.get(True)     # Continuously gets results from the queue
                self.handle_result(result)             # Makes trades based on the result
        except Exception as e:
            self.logger.log("Trader", "error", "Crashed: " + str(e))

    def quit(self):
        self.web_interface.quit()
