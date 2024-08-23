import requests
import time
import re
import json
import random
import os
from datetime import datetime
from playwright.sync_api import Page
from playwright_tests.messages.homepage_messages import HomepageMessages
from requests.exceptions import HTTPError

from playwright_tests.pages.top_navbar import TopNavbar


class Utilities:
    def __init__(self, page: Page):
        self.page = page

    # Fetching test data from json files.
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

    with open("test_data/kb_new_thread.json", "r") as kb_new_thread_test_data_file:
        kb_new_thread_test_data = json.load(kb_new_thread_test_data_file)
    kb_article_test_data_file.close()

    with open("test_data/kb_revision.json", "r") as kb_revision_test_data_file:
        kb_revision_test_data = json.load(kb_revision_test_data_file)
    kb_revision_test_data_file.close()

    with open("test_data/user_message.json", "r") as user_message_test_data_file:
        user_message_test_data = json.load(user_message_test_data_file)
    user_message_test_data_file.close()

    with open("test_data/general_data.json", "r") as general_test_data_file:
        general_test_data = json.load(general_test_data_file)
    general_test_data_file.close()

    with open("test_data/different_endpoints.json", "r") as different_endpoints_file:
        different_endpoints = json.load(different_endpoints_file)
    different_endpoints_file.close()

    # Fetching user secrets from GH.
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

    def clear_fxa_email(self, fxa_username: str):
        """
        This helper function sends a delete request to clear the restmail inbox content for a given
        fxa username.
        """
        requests.delete(f"https://restmail.net/mail/{fxa_username}")

    def get_fxa_verification_code(self, fxa_username: str, max_attempts=5, poll_interval=5) -> str:
        """
        This helper function pols the restmail inbox for the fxa verification code.
        """
        for attempt in range(max_attempts):
            try:
                # Steps:
                # 1. Clearing the inbox for the given fxa username.
                # 2. Parsing the inbox json encoded response for the x-signing-verify-code.
                # 3. Clearing the inbox for the given fxa username if the verification code was
                # fetched.
                # 4. Returning the fxa verification code for furthe usage.
                cleared_username = self.username_extraction_from_email(fxa_username)
                response = requests.get(f"https://restmail.net/mail/{cleared_username}")
                response.raise_for_status()
                json_response = response.json()
                fxa_verification_code = json_response[0]['headers']['x-signin-verify-code']
                self.clear_fxa_email(cleared_username)
                return fxa_verification_code
            except HTTPError as htt_err:
                print(htt_err)
                time.sleep(poll_interval)
            except Exception as err:
                print(err)
                time.sleep(poll_interval)

    def username_extraction_from_email(self, string_to_analyze: str) -> str:
        """
        This helper function extracts the username from a given string/e-mail address.
        """
        return re.match(r"(.+)@", string_to_analyze).group(1)

    def generate_random_number(self, min_value, max_value) -> str:
        """
        This helper function generates a random number based on a given min and max values.
        """
        return str(random.randint(min_value, max_value))

    def number_extraction_from_string(self, string_to_analyze: str) -> int:
        """
        This helper function extracts the number from a given string.
        """
        return int(re.findall(r"\d+", string_to_analyze)[0])

    def number_extraction_from_string_endpoint(self, endpoint: str, string_to_analyze: str) -> int:
        """
        This helper function extracts the number from a given SUMO endpoint.
        """
        return int(re.findall(fr'{endpoint}(\d+)', string_to_analyze)[0])

    def get_page_url(self) -> str:
        """
        This helper function returns the current URL.
        """
        return self.page.url

    def navigate_back(self):
        """
        This helper function navigates back to the previous page. (browser back button)
        """
        self.page.go_back()

    def navigate_forward(self):
        """
        This helper function navigate forward. (browser forward button)
        """
        self.page.go_forward()

    def navigate_to_homepage(self):
        """
        This helper function navigates directly to the SUMO hompage.
        """
        self.page.goto(HomepageMessages.STAGE_HOMEPAGE_URL)

    def navigate_to_link(self, link: str):
        """
        This helper function navigates to a given link and awaits for the dom load to finish.
        If a response error is encountered we are performing a page refresh.
        """
        with self.page.expect_navigation() as navigation_info:
            self.page.goto(link)
        response = navigation_info.value
        self.wait_for_dom_to_load()

        if response.status is not None:
            if response.status >= 400:
                self.refresh_page()

    def set_extra_http_headers(self, headers):
        """
        This helper function sets some extra headers to the request.
        """
        self.page.set_extra_http_headers(headers)

    def wait_for_given_timeout(self, milliseconds: int):
        """
        This helper function awaits for a given timeout.
        """
        self.page.wait_for_timeout(milliseconds)

    def wait_for_url_to_be(self, expected_url: str, timeout=4000):
        """
        This helper function awaits for a given url based on a given timeout.
        """
        self.page.wait_for_url(expected_url, timeout=timeout)

    def wait_for_page_to_load(self):
        """
        This helper function awaits for the load event to be fired.
        """
        self.page.wait_for_load_state("load")

    def wait_for_dom_to_load(self):
        """
        This helper function awaits for the DOMContentLoaded event to be fired.
        """
        self.page.wait_for_load_state("domcontentloaded")

    def wait_for_networkidle(self):
        """
        This helper function waits until there are no network connections for at least 500ms.
        """
        self.page.wait_for_load_state("networkidle")

    def store_session_cookies(self, session_file_name: str):
        """
        This helper function stores the session state for further usage.
        """
        self.page.context.storage_state(path=f"core/sessions/.auth/{session_file_name}.json")

    def delete_cookies(self, tried_once=False):
        """
        This helper function deletes all cookies and performs a page refresh so that the outcome
        is visible immediately.
        """
        top_navbar = TopNavbar(self.page)
        self.page.context.clear_cookies()
        self.refresh_page()

        # In order to avoid test flakiness we are trying to delete the cookies again if the sign-in
        # sign-up button is not visible after page refresh.
        if not top_navbar.is_sign_in_up_button_displayed and not tried_once:
            self.delete_cookies(tried_once=True)

    def start_existing_session(self, session_file_name: str, tried_once=False) -> str:
        """
        This helper function starts an existing session by applying the session cookies saved in
        the /sessions/ folder.
        """
        top_navbar = TopNavbar(self.page)
        if not tried_once:
            self.delete_cookies()
        with open(f"core/sessions/.auth/{session_file_name}.json", 'r') as file:
            cookies_data = json.load(file)
        self.page.context.add_cookies(cookies=cookies_data['cookies'])
        # A SUMO action needs to be done in order to have the page refreshed with the correct
        # session
        self.refresh_page()

        # In order to avoid test flakiness we are trying to re-apply the session cookies again if
        # the sign-in/up button is still displayed instead of the session username.
        if top_navbar.is_sign_in_up_button_displayed() and not tried_once:
            self.start_existing_session(session_file_name, tried_once=True)
        return session_file_name

    def refresh_page(self):
        """
        This helper function performs a page reload.
        """
        self.page.reload()

    def get_user_agent(self) -> str:
        """
        This helper function fetches the user agent.
        """
        return self.page.evaluate('window.navigator.userAgent ')

    def replace_special_chars_account(self, account: str) -> str:
        """
        This helper function replaces the special characters applied to the special chars test
        username.
        """
        return account.replace(account, "testMozillaSpecialChars")

    def remove_character_from_string(self, string: str, character_to_remove: str) -> str:
        """
        This helper function removes a given character from a given target string.
        """
        return string.replace(character_to_remove, "")

    def create_slug_from_title(self, article_title: str) -> str:
        """
        This helper function automatically creates an article title slug based on the given article
        title.
        """
        initial_title = article_title.split()
        return '-'.join(initial_title).lower()

    def is_descending(self, list_of_items: list[str]):
        """
        This helper function evaluates if a given list of items are displayed in descending order.
        """
        if all(list_of_items[i] >= list_of_items[i + 1] for i in range(len(list_of_items) - 1)):
            return True
        else:
            return False

    def extract_month_day_year_from_string(self, timestamp_str: str) -> str:
        """
        This helper function extracts the month/day/year from a given string.
        """
        timestamp = datetime.strptime(timestamp_str, "%b %d, %Y, %I:%M:%S %p")
        return timestamp.strftime("%b %d, %Y")

    def convert_string_to_datetime(self, timestamp_str: str) -> str:
        """
        This helper function converts a given timestamp string to date-time.
        """
        date_object = datetime.strptime(timestamp_str, "%m.%d.%Y")
        return date_object.strftime("%B {:d}, %Y").format(date_object.day)

    def extract_date_to_digit_format(self, date_str: str) -> int:
        """
        This helper function extracts the given date to digit format.
        """
        date = datetime.strptime(date_str, "%b %d, %Y")
        return int(date.strftime("%m%d%Y"))
