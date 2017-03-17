from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from elementium.drivers.se import SeElements
import time


class WebInterface():
    YES = 1
    NO = 0

    def __init__(self, user, pwd):
        self.webdriver = webdriver.Chrome()
        self.se = SeElements(self.webdriver)

    def quit(self):
        self.webdriver.quit()

    def have_position_in_market(self, contract_id):
        # TODO
        pass

    def buy(self, contract, option, quantity, max_price):
        # TODO
        pass

    def sell(self, contract, option, quantity):
        # TODO
        pass
