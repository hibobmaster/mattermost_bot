import logging


def getlogger():
    # create a custom logger if not already created
    logger = logging.getLogger(__name__)
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)

        # create handlers
        info_handler = logging.StreamHandler()
        error_handler = logging.FileHandler("bot.log", mode="a")
        error_handler.setLevel(logging.ERROR)
        info_handler.setLevel(logging.INFO)

        # create formatters
        error_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s"
        )
        info_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # set formatter
        error_handler.setFormatter(error_format)
        info_handler.setFormatter(info_format)

        # add handlers to logger
        logger.addHandler(error_handler)
        logger.addHandler(info_handler)

    return logger
