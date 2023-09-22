import random
import logging
import pytest
import inspect
import re
import requests
import time
import json
import os

from requests.exceptions import HTTPError


@pytest.mark.usefixtures("setup")
class TestUtilities:
    with open("test_data/profile_edit.json", "r") as edit_test_data_file:
        profile_edit_test_data = json.load(edit_test_data_file)
    edit_test_data_file.close()

    with open("test_data/question_reply.json", "r") as question_test_data_file:
        question_test_data = json.load(question_test_data_file)
    question_test_data_file.close()

    with open("test_data/aaq_question.json", "r") as aaq_question_test_data_file:
        aaq_question_test_data = json.load(aaq_question_test_data_file)
    aaq_question_test_data_file.close()

    with open("test_data/add_kb_article.json", "r") as kb_article_test_data_file:
        kb_article_test_data = json.load(kb_article_test_data_file)
    kb_article_test_data_file.close()

    with open("test_data/user_message.json", "r") as user_message_test_data_file:
        user_message_test_data = json.load(user_message_test_data_file)
    user_message_test_data_file.close()

    user_secrets_data = {
        "TEST_ACCOUNT_12": os.environ.get("TEST_ACCOUNT_12"),
        "TEST_ACCOUNT_13": os.environ.get("TEST_ACCOUNT_13"),
        "TEST_ACCOUNT_MESSAGE_1": os.environ.get("TEST_ACCOUNT_MESSAGE_1"),
        "TEST_ACCOUNT_MESSAGE_2": os.environ.get("TEST_ACCOUNT_MESSAGE_2"),
        "TEST_ACCOUNT_MESSAGE_3": os.environ.get("TEST_ACCOUNT_MESSAGE_3"),
        "TEST_ACCOUNT_MESSAGE_4": os.environ.get("TEST_ACCOUNT_MESSAGE_4"),
        "TEST_ACCOUNT_MESSAGE_5": os.environ.get("TEST_ACCOUNT_MESSAGE_5"),
        "TEST_ACCOUNT_MESSAGE_6": os.environ.get("TEST_ACCOUNT_MESSAGE_6"),
        "TEST_ACCOUNT_SPECIAL_CHARS": os.environ.get("TEST_ACCOUNT_SPECIAL_CHARS"),
        "TEST_ACCOUNTS_PS": os.environ.get("TEST_ACCOUNTS_PS"),
        "TEST_ACCOUNT_MODERATOR": os.environ.get("TEST_ACCOUNT_MODERATOR"),
    }

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

    # We are polling restmail 5 times in order to fetch the FxA verification code
    def get_fxa_verification_code(self, fxa_username: str, max_attempts=5, poll_interval=5) -> str:
        for attempt in range(max_attempts):
            try:
                # fetching the FxA email verification code
                response = requests.get(f"https://restmail.net/mail/{fxa_username}")
                response.raise_for_status()
                json_response = response.json()
                email_text = json_response[0]["text"]
                print(email_text)
                confirmation_code = re.search(
                    r"If yes, here is your authorization code:\s*\n\n(\d+)", email_text
                ).group(1)

                # clearing the email after the code is fetched
                self.clear_fxa_email(fxa_username)

                return confirmation_code
            except HTTPError as htt_err:
                print(f"HTTP error occurred: {htt_err}. Polling again")
                time.sleep(poll_interval)
            except Exception as err:
                print(f"Other error occurred: {err}. Polling again")
                time.sleep(poll_interval)

    def clear_fxa_email(self, fxa_username: str):
        requests.delete(f"https://restmail.net/mail/{fxa_username}")

    def number_extraction_from_string(self, string_to_analyze: str) -> int:
        return int(re.findall(r"\d+", string_to_analyze)[0])

    def answer_id_extraction(self, string_to_analyze: str) -> str:
        match = re.search(r"#answer-\d+", string_to_analyze)
        if match:
            return match.group(0)

    def username_extraction_from_email(self, string_to_analyze: str) -> str:
        return re.match(r"(.+)@", string_to_analyze).group(1)

    def remove_character_from_string(self, string: str, character_to_remove: str) -> str:
        return string.replace(character_to_remove, "")
