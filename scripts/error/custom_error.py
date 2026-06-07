import logging


class MissingOCBudgetException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        logging.exception(msg)
