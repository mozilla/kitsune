import random
import logging
import pytest
import inspect


@pytest.mark.usefixtures("setup")
class TestUtilities:
    # Defining the logging mechanism
    def get_logger(self):
        logger_name = inspect.stack()[1][3]
        logger = logging.getLogger(logger_name)

        file_handler = logging.FileHandler("reports/logs/logfile.log")

        formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(name)s : %(message)s")

        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        logger.setLevel(logging.INFO)

        return logger

    def generate_random_number(self, min_value, max_value) -> int:
        return random.randint(min_value, max_value)
