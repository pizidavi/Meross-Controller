import sys
import logging
import logging.handlers as handlers

StreamHandler = logging.StreamHandler(sys.stdout)
StreamHandler.setLevel(logging.INFO)
StreamHandler.setFormatter(logging.Formatter('%(levelname)s:%(asctime)s: %(message)s'))

FileHandler = handlers.TimedRotatingFileHandler('syslog.log', when='W0', backupCount=3)
FileHandler.setLevel(logging.WARNING)
FileHandler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))


def get_logger(name):
    """
    Auto-set important options in logger
    :param name: logger's name
    :return: logger
    """
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    logger.addHandler(StreamHandler)
    logger.addHandler(FileHandler)
    return logger
