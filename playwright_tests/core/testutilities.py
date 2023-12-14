import logging
import inspect
import requests
import pytest
import time
import re
import json
import random
import os

from playwright_tests.messages.homepage_messages import HomepageMessages
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

    user_secrets_accounts = {
        "TEST_ACCOUNT_12": os.environ.get("TEST_ACCOUNT_12"),
        "TEST_ACCOUNT_13": os.environ.get("TEST_ACCOUNT_13"),
        "TEST_ACCOUNT_MESSAGE_1": os.environ.get("TEST_ACCOUNT_MESSAGE_1"),
        "TEST_ACCOUNT_MESSAGE_2": os.environ.get("TEST_ACCOUNT_MESSAGE_2"),
        "TEST_ACCOUNT_MESSAGE_3": os.environ.get("TEST_ACCOUNT_MESSAGE_3"),
        "TEST_ACCOUNT_MESSAGE_4": os.environ.get("TEST_ACCOUNT_MESSAGE_4"),
        "TEST_ACCOUNT_MESSAGE_5": os.environ.get("TEST_ACCOUNT_MESSAGE_5"),
        "TEST_ACCOUNT_MESSAGE_6": os.environ.get("TEST_ACCOUNT_MESSAGE_6"),
        "TEST_ACCOUNT_MODERATOR": os.environ.get("TEST_ACCOUNT_MODERATOR")
    }
    user_special_chars = os.environ.get("TEST_ACCOUNT_SPECIAL_CHARS")
    user_secrets_pass = os.environ.get("TEST_ACCOUNTS_PS")

    # Clearing restmail.
    def clear_fxa_email(self, fxa_username: str):
        requests.delete(f"https://restmail.net/mail/{fxa_username}")

    # Mechanism of fetching the fxa verification code from restamil
    def get_fxa_verification_code(self, fxa_username: str, max_attempts=5, poll_interval=5) -> str:
        for attempt in range(max_attempts):
            try:
                cleared_username = self.username_extraction_from_email(fxa_username)
                # Fetching the FxA email verification code
                response = requests.get(f"https://restmail.net/mail/{cleared_username}")
                response.raise_for_status()
                json_response = response.json()
                fxa_verification_code = json_response[0]['headers']['x-signin-verify-code']
                print(fxa_verification_code)

                # clearing the email after the code is fetched
                self.clear_fxa_email(cleared_username)

                return fxa_verification_code
            except HTTPError as htt_err:
                print(f"HTTP error occurred: {htt_err}. Polling again")
                time.sleep(poll_interval)
            except Exception as err:
                print(f"Used: {cleared_username} Other error occurred: {err}. Polling again")
                print(fxa_verification_code)
                time.sleep(poll_interval)

    # Extracting username from e-mail mechanism
    def username_extraction_from_email(self, string_to_analyze: str) -> str:
        return re.match(r"(.+)@", string_to_analyze).group(1)

    def generate_random_number(self, min_value, max_value) -> int:
        return random.randint(min_value, max_value)

    def number_extraction_from_string(self, string_to_analyze: str) -> int:
        return int(re.findall(r"\d+", string_to_analyze)[0])

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

    # Returning current page URL
    def get_page_url(self) -> str:
        return self.page.url

    # Navigating back in history (browser back button)
    def navigate_back(self):
        self.page.go_back()

    # Navigating forward in history (browser forward button)
    def navigate_forward(self):
        self.page.go_forward()

    # Navigating to SUMO homepage
    def navigate_to_homepage(self):
        self.page.goto(HomepageMessages.STAGE_HOMEPAGE_URL)

    # Navigating to a specific given link
    def navigate_to_link(self, link: str):
        self.page.goto(link)

    # Wait for a given timeout
    def wait_for_given_timeout(self, milliseconds: int):
        self.page.wait_for_timeout(milliseconds)

    # Store authentication states
    def store_session_cookies(self, session_file_name: str):
        self.context.storage_state(path=f"core/sessions/.auth/{session_file_name}.json")

    def delete_cookies(self):
        self.context.clear_cookies()
        # Reloading the page for the deletion to take immediate action.
        self.page.reload()

    def start_existing_session(self, session_file_name: str):
        with open(f"core/sessions/.auth/{session_file_name}.json", 'r') as file:
            cookies_data = json.load(file)
        self.context.add_cookies(cookies=cookies_data['cookies'])
        # A SUMO action needs to be done in order to have the page refreshed with the correct
        # session
        self.page.reload()

    def replace_special_chars_account(self, account: str) -> str:
        return account.replace(account, "testMozillaSpecialChars")

    def remove_character_from_string(self, string: str, character_to_remove: str) -> str:
        return string.replace(character_to_remove, "")
