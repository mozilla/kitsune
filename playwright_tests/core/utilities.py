import os
from urllib.error import HTTPError
import requests
import time
import re
import json
import random
from PIL import Image
from PIL import ImageChops
from typing import Any, Union
from datetime import datetime
from dateutil import parser
from dateutil.tz import tz
from nltk import SnowballStemmer, WordNetLemmatizer
from playwright.sync_api import Page, Locator, Response, expect
from playwright_tests.messages.auth_pages_messages.fxa_page_messages import FxAPageMessages
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.pages.top_navbar import TopNavbar
from playwright_tests.test_data.search_synonym import SearchSynonyms
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


class Utilities:
    def __init__(self, page: Page):
        self.page = page

    # Fetching test data from json files.
    with open("test_data/profile_edit.json", "r", encoding="utf-8") as edit_test_data_file:
        profile_edit_test_data = json.load(edit_test_data_file)

    with open("test_data/question_reply.json", "r") as question_test_data_file:
        question_test_data = json.load(question_test_data_file)

    with open("test_data/aaq_question.json", "r") as aaq_question_test_data_file:
        aaq_question_test_data = json.load(aaq_question_test_data_file)

    with open("test_data/add_kb_article.json", "r") as kb_article_test_data_file:
        kb_article_test_data = json.load(kb_article_test_data_file)

    with open("test_data/kb_new_thread.json", "r") as kb_new_thread_test_data_file:
        kb_new_thread_test_data = json.load(kb_new_thread_test_data_file)

    with open("test_data/kb_revision.json", "r") as kb_revision_test_data_file:
        kb_revision_test_data = json.load(kb_revision_test_data_file)

    with open("test_data/user_message.json", "r") as user_message_test_data_file:
        user_message_test_data = json.load(user_message_test_data_file)

    with open("test_data/general_data.json", "r") as general_test_data_file:
        general_test_data = json.load(general_test_data_file)

    with open("test_data/different_endpoints.json", "r") as different_endpoints_file:
        different_endpoints = json.load(different_endpoints_file)

    with open("test_data/discussion_thread_data.json", "r") as discussion_thread_data_file:
        discussion_thread_data = json.load(discussion_thread_data_file)

    with open("test_data/ga4_data.json", "r") as ga4_data_file:
        ga4_data = json.load(ga4_data_file)

    # Fetching user secrets from GH.
    staff_user = os.environ.get("TEST_ACCOUNT_MODERATOR")
    user_secrets_pass = os.environ.get("TEST_ACCOUNTS_PS")
    user_agent = os.environ.get("PLAYWRIGHT_USER_AGENT")

    # Fetching Gmail API credentials for email verification.
    gmail_client_id = os.environ.get("GMAIL_CLIENT_ID")
    gmail_client_secret = os.environ.get("GMAIL_CLIENT_SECRET")
    gmail_refresh_token = os.environ.get("GMAIL_REFRESH_TOKEN")

    # FxA browser challenge.
    fxa_browser_challenge_header = os.environ.get("PLAYWRIGHT_FXA_CHALLENGE_HEADER")
    fxa_browser_challenge_value = os.environ.get("PLAYWRIGHT_FXA_CHALLENGE_HEADER_VALUE")

    def get_session_id(self, username: str) -> dict:
        with open(f"core/sessions/.auth/{username}.json", 'r') as staff_cookies:
            staff_user_session = json.load(staff_cookies)
            return [cookie['value'] for cookie in staff_user_session['cookies'] if cookie[
                'name'] == 'session_id'][0]

    def _get_gmail_service(self):
        """Creates an authenticated Gmail API service from environment variables."""
        creds = Credentials(
            token=None,
            refresh_token=self.gmail_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.gmail_client_id,
            client_secret=self.gmail_client_secret,
            scopes=['https://www.googleapis.com/auth/gmail.modify']
        )
        creds.refresh(Request())
        return build('gmail', 'v1', credentials=creds)

    def clear_email(self, restmail_username: str = None):
        """ Clears FxA verification emails from the Gmail inbox.
        Args:
            restmail_username (str): If using a restmail account.
        """
        if restmail_username:
            requests.delete(f"https://restmail.net/mail/{restmail_username}")
        else:
            try:
                service = self._get_gmail_service()
                results = service.users().messages().list(
                    userId='me',
                    q='from:verification@stage.mozaws.net'
                ).execute()

                messages = results.get('messages', [])
                for message in messages:
                    service.users().messages().trash(
                        userId='me',
                        id=message['id']
                    ).execute()
            except Exception as e:
                print(f"Error clearing Gmail: {e}")

    def get_fxa_verification_code(self, max_attempts=5, poll_interval=5,
                                  restmail_username: str = None, new_account: bool = False,
                                  change_password: bool = False) -> str:
        """
        Polls Gmail for the FxA verification code.
        Args:
            max_attempts (int): Maximum polling attempts.
            poll_interval (int): Seconds between attempts.
            restmail_username (str): Optional. The restmail username (if we need/want to use
            restmail).
            new_account (bool): If we are creating a new fxa account.
            change_password (bool): If we are fetching the fxa code for password change.
        Returns:
            str: The verification code
        """
        for attempt in range(max_attempts):
            if restmail_username:
                try:
                    target = f"https://restmail.net/mail/{restmail_username}"
                    response = requests.get(target)
                    response.raise_for_status()
                    json_response = response.json()
                    if new_account:
                        fxa_verification_code = json_response[0]['headers']['x-verify-short-code']
                    elif change_password:
                        fxa_verification_code = (json_response[0]['headers']
                        ['x-account-change-verify-code'])
                    else:
                        fxa_verification_code = json_response[0]['headers']['x-signin-verify-code']
                    self.clear_email(restmail_username=restmail_username)
                    return fxa_verification_code
                except HTTPError and IndexError as error:
                    print(error)
            else:
                service = self._get_gmail_service()
                try:
                    self.clear_email()
                    results = service.users().messages().list(
                        userId='me',
                        q='from:verification@stage.mozaws.net',
                        maxResults=1
                    ).execute()

                    messages = results.get('messages', [])

                    if messages:
                        msg = service.users().messages().get(
                            userId='me',
                            id=messages[0]['id'],
                            format='full'
                        ).execute()

                        # Try to get code from headers first
                        headers = msg['payload'].get('headers', [])
                        for header in headers:
                            if header['name'].lower() == 'x-signin-verify-code':
                                code = header['value']
                                service.users().messages().trash(
                                    userId='me', id=messages[0]['id']
                                ).execute()
                                self.clear_email()
                                return code

                        # Fallback: parse from subject (e.g., "Use xxx to confirm your account")
                        for header in headers:
                            if header['name'].lower() == 'subject':
                                code = self._extract_code_from_subject(header['value'])
                                if code:
                                    service.users().messages().trash(
                                        userId='me', id=messages[0]['id']
                                    ).execute()
                                    self.clear_email()
                                    return code
                                break

                    print(f"Attempt {attempt + 1}/{max_attempts}: No verification email yet")
                    time.sleep(poll_interval)

                except Exception as e:
                    print(f"Error fetching verification code: {e}")
                    time.sleep(poll_interval)

            raise Exception("Failed to retrieve FxA verification code")

    def _extract_code_from_subject(self, subject: str) -> str:
        """Extracts 6-digit verification code from email subject.

        Expected format: "Use 330759 to confirm your account"
        """
        match = re.search(r'Use\s+(\d{6})\s+to', subject)
        return match.group(1) if match else None

    def username_extraction_from_email(self, string_to_analyze: str) -> str:
        """
        This helper function extracts the username from a given string/e-mail address.

        Args:
            string_to_analyze (str): The string to analyze
        """
        return re.match(r"(.+)@", string_to_analyze).group(1)

    def generate_random_number(self, min_value, max_value) -> str:
        """
        This helper function generates a random number based on a given min and max values.

        Args:
            min_value: The minimum value
            max_value: The maximum value
        """
        return str(random.randint(min_value, max_value))

    def number_extraction_from_string(self, string_to_analyze: str) -> int:
        """
        This helper function extracts the number from a given string.

        Args:
            string_to_analyze (str): The string to analyze
        """
        return int(re.findall(r"\d+", string_to_analyze)[0])

    def number_extraction_from_string_endpoint(self, endpoint: str, string_to_analyze: str) -> int:
        """
        This helper function extracts the number from a given SUMO endpoint.

        Args:
            endpoint (str): The endpoint
            string_to_analyze (str): The string to analyze
        """
        return int(re.findall(fr'{endpoint}(\d+)', string_to_analyze)[0])

    def get_page_url(self) -> str:
        """
        This helper function returns the current URL.
        """
        return self.page.url

    def navigate_back(self, retries: int = 3) -> Response | None:
        """
        Navigates back using the browser back button. If go_back() didn't change the URL,
        retries up to `retries` times. If the resulting response is a 502, reloads the
        destination page up to `retries - 1` times until a non-502 response is received.

        Args:
            retries (int): How many attempts to make in total before giving up.
        Returns:
            The Response of the final navigation, or None if Playwright did not capture one.
        """
        response = None
        for attempt in range(retries):
            url_before = self.page.url
            try:
                response = self.page.go_back(wait_until="domcontentloaded")
            except PlaywrightError as e:
                if "net::ERR_ABORTED" in str(e) or "frame was detached" in str(e):
                    print(f"Ignored benign go_back error: {e}")
                    return None
                raise
            if self.page.url == url_before and attempt < retries - 1:
                print("navigate_back did not change URL. Retrying...")
                self.page.wait_for_timeout(500)
                continue
            break

        for attempt in range(retries - 1):
            if response is None or response.status != 502:
                return response
            print(f"502 after go_back, reload attempt "
                  f"{attempt + 1}/{retries - 1} in 5s...")
            self.page.wait_for_timeout(5000)
            try:
                response = self.page.reload(wait_until="domcontentloaded")
            except PlaywrightError:
                response = None
        return response

    def navigate_forward(self, retries: int = 3) -> Response | None:
        """
        Navigates forward using the browser forward button. If go_forward() didn't change the
        URL, retries up to `retries` times. If the resulting response is a 502, reloads the
        destination page up to `retries - 1` times until a non-502 response is received.

        Args:
            retries (int): How many attempts to make in total before giving up.
        Returns:
            The Response of the final navigation, or None if Playwright did not capture one.
        """
        response = None
        for attempt in range(retries):
            url_before = self.page.url
            try:
                response = self.page.go_forward(wait_until="domcontentloaded")
            except PlaywrightError as e:
                if "net::ERR_ABORTED" in str(e) or "frame was detached" in str(e):
                    print(f"Ignored benign go_forward error: {e}")
                    return None
                raise
            if self.page.url == url_before and attempt < retries - 1:
                print("navigate_forward did not change URL. Retrying...")
                self.page.wait_for_timeout(500)
                continue
            break

        for attempt in range(retries - 1):
            if response is None or response.status != 502:
                return response
            print(f"502 after go_forward, reload attempt "
                  f"{attempt + 1}/{retries - 1} in 5s...")
            self.page.wait_for_timeout(5000)
            try:
                response = self.page.reload(wait_until="domcontentloaded")
            except PlaywrightError:
                response = None
        return response

    def navigate_to_homepage(self):
        """
        This helper function navigates directly to the SUMO hompage.
        """
        self.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)

    def navigate_to_link(self, link: str, retries: int = 3) -> Response | None:
        """
        Navigates to a given link and blocks until DOMContentLoaded. If the navigation response
        is a 502, waits 5s and retries up to `retries` times. Returns the final response (or
        None when the navigation didn't produce one, e.g. ERR_ABORTED on redirects).

        Args:
            link (str): The link to navigate to.
            retries (int): How many attempts to make in total before giving up.
        """
        response = None
        for attempt in range(retries):
            try:
                response = self.page.goto(link, wait_until="domcontentloaded")
            except PlaywrightError as e:
                if "net::ERR_ABORTED" in str(e) or "frame was detached" in str(e):
                    print(f"Ignored benign navigation error to {link}: {e}")
                    return None
                raise
            if response is None or response.status != 502:
                return response
            if attempt < retries - 1:
                print(f"502 on goto({link}), attempt "
                      f"{attempt + 1}/{retries}. Retrying in 5s...")
                self.page.wait_for_timeout(5000)
        return response


    def click_and_wait_for_navigation(self, click_fn, retries: int = 3) -> Response | None:
        """
        Executes a click that triggers a full-page navigation and waits for that navigation.
        If the resulting page is a 502, reloads the destination URL up to `retries - 1` times
        until a non-502 response is received. The click is performed only once: re-clicking
        would target a button on the source page, which no longer exists after navigation.

        Args:
            click_fn: Zero-arg callable that performs the click.
            retries (int): Maximum total navigations (1 click + up to retries-1 reloads).
        Returns:
            The Response of the final navigation, or None if Playwright did not capture one.
        """
        with self.page.expect_navigation(wait_until="domcontentloaded") as nav_info:
            click_fn()
        response = nav_info.value
        for attempt in range(retries - 1):
            if response is None or response.status != 502:
                return response
            print(f"502 after click, reload attempt "
                  f"{attempt + 1}/{retries - 1} in 5s...")
            self.page.wait_for_timeout(5000)
            try:
                response = self.page.reload(wait_until="domcontentloaded")
            except PlaywrightError:
                response = None
        return response

    def upload_file(self, element: Locator, path_to_file: str):
        """This helper function uploads the test-image.png file to a given file element chooser.

        Args:
            element (str): The element file chooser locator's xpath.
            path_to_file (str): The path to the file to be uploaded.
        """
        with self.page.expect_file_chooser() as file_chooser:
            element.click()
        file_chooser_value = file_chooser.value
        file_chooser_value.set_files(os.path.abspath(path_to_file))

    def screenshot_the_locator(self, locator: Locator, path_to_save: str):
        """
        This helper function takes a screenshot of a given locator.

        Args:
            locator (Locator): The locator of the targeted element.
            path_to_save (str): The path where to save the screenshot.
        """
        locator.screenshot(path=path_to_save)

    def are_images_different(self, image1_path: str, image2_path: str) -> tuple:
        """
        This helper function compares two images and returns the bounding box of the difference.
        If there is no difference this helper function will return None.

        Args:
            image1_path (str): The path of the first image
            image2_path (str): The path of the second image
        """
        first_image = Image.open(image1_path).convert('RGB')
        second_image = Image.open(image2_path).convert('RGB')

        return ImageChops.difference(first_image, second_image).getbbox()

    def set_extra_http_headers(self, headers):
        """
        This helper function sets some extra headers to the request.

        Args:
            headers: The headers to be set
        """
        self.page.set_extra_http_headers(headers)

    def wait_for_given_timeout(self, milliseconds: int):
        """
        This helper function awaits for a given timeout.

        Args:
            milliseconds (int): The timeout in milliseconds
        """
        self.page.wait_for_timeout(milliseconds)

    def wait_for_url_to_be(self, expected_url: str, timeout=4000):
        """
        This helper function awaits for a given url based on a given timeout.

        Args:
            expected_url (str): The expected url
            timeout (int): The timeout
        """
        self.page.wait_for_url(expected_url, timeout=timeout)

    def wait_for_page_to_load(self):
        """
        This helper function awaits for the load event to be fired.
        """
        try:
            self.page.wait_for_load_state("load")
        except PlaywrightTimeoutError:
            print("Load event was not fired. Continuing...")

    def wait_for_dom_to_load(self):
        """
        This helper function awaits for the DOMContentLoaded event to be fired.
        """
        try:
            self.page.wait_for_load_state("domcontentloaded")
        except PlaywrightTimeoutError:
            print("DOMContentLoaded event was not fired. Continuing...")

    def wait_for_networkidle(self):
        """
        This helper function waits until there are no network connections for at least 500ms.
        """
        try:
            self.page.wait_for_load_state("networkidle")
        except PlaywrightTimeoutError:
            print("Network idle state was not reached. Continuing...")

    def store_session_cookies(self, session_file_name: str):
        """
        This helper function stores the session state for further usage.

        Args:
            session_file_name (str): The session file name
        """
        self.page.context.storage_state(path=f"core/sessions/.auth/{session_file_name}.json")

    def create_new_context_page(self, **context_kwargs) -> Page:
        """
        This helper function opens a fresh, isolated browser context (its own cookie jar and
        storage) and returns a new page within it. The context includes the FxA browser challenge
        header and the standard user agent so that authentication flows work as expected.

        The caller is responsible for closing the context (``page.context.close()``) once done.

        Args:
            **context_kwargs: Extra keyword arguments forwarded to ``browser.new_context()``.

        Returns:
            Page: A new page belonging to the freshly created, isolated context.
        """
        browser = self.page.context.browser
        # Record this context's video into the same artifacts directory that
        # pytest-playwright uses for the default page. pytest-playwright only
        # wires up `record_video_dir` for the contexts it creates itself, so we
        # mirror it here for manually-created contexts. This lets the failure
        # hook attach the screencast of every window, not just the default page.
        if "record_video_dir" not in context_kwargs and self.page.video:
            try:
                context_kwargs["record_video_dir"] = os.path.dirname(self.page.video.path())
            except PlaywrightError as error:
                print(f"Could not derive the video directory for the new context: {error}")

        context = browser.new_context(
            user_agent=self.user_agent,
            extra_http_headers={
                f"{self.fxa_browser_challenge_header}": f"{self.fxa_browser_challenge_value}"
            },
            **context_kwargs,
        )
        new_page = context.new_page()
        new_page.set_default_navigation_timeout(30000)

        # Wire up the same 502 nav-status tracking the autouse `navigate_to_homepage`
        # fixture sets up for the default page. Without this, `_last_main_nav_status`
        # is never set on manually-created windows (e.g. the admin page), so
        # `BasePage._recover_if_on_error_page` can't detect a 502 and never reloads,
        # leaving the window stuck on the error page.
        new_page._last_main_nav_status = None

        def _track_main_nav_status(response):
            try:
                if (response.request.is_navigation_request()
                        and response.frame == new_page.main_frame):
                    new_page._last_main_nav_status = response.status
            except PlaywrightError as e:
                print(f"Nav-status listener ignored error: {e}")

        new_page.on("response", _track_main_nav_status)

        # Register the page so the failure hook (pytest_runtest_makereport) can
        # attach the screencasts of all windows opened during the test.
        if not hasattr(self.page, "_extra_pages"):
            self.page._extra_pages = []
        self.page._extra_pages.append(new_page)

        return new_page

    def delete_cookies(self, tried_once=False, retries=3):
        """
        This helper function deletes all cookies and performs a page refresh so that the outcome
        is visible immediately.

        Args:
            tried_once (bool): If the cookies deletion was tried once
        """
        top_navbar = TopNavbar(self.page)
        for attempt in range(retries):
            try:
                self.page.context.clear_cookies()
                self.refresh_page()
                if FxAPageMessages.AUTH_PAGE_URL in self.get_page_url():
                    break
                else:
                    top_navbar._wait_for_locator(top_navbar.signin_signup_button,
                                                 raise_exception=True)
                break
            except PlaywrightTimeoutError:
                print("Cookies were not successfully deleted. Retrying...")
                if attempt < retries - 1:
                    continue

        # In order to avoid test flakiness we are trying to delete the cookies again if the sign-in
        # sign-up button is not visible after page refresh.
        if top_navbar.signin_signup_button.is_hidden() and not tried_once:
            self.delete_cookies(tried_once=True)

    def start_existing_session(self, cookies: dict = None, session_file_name: str = None,
                               tried_once=False):
        """
        This helper function starts an existing session by applying the session cookies saved in
        the /sessions/ folder.

        Args:
            session_file_name (str): The session file name
            cookies (dict): The cookies to be applied
            tried_once (bool): If the session was tried once
        """
        top_navbar = TopNavbar(self.page)
        if not tried_once:
            self.delete_cookies()

        if session_file_name is not None:
            with open(f"core/sessions/.auth/{session_file_name}.json", 'r') as file:
                cookies_data = json.load(file)
            self.page.context.add_cookies(cookies=cookies_data['cookies'])
            self.refresh_page()
            if top_navbar.signin_signup_button.is_visible() and not tried_once:
                self.start_existing_session(session_file_name=session_file_name, tried_once=True)
        elif cookies is not None:
            self.page.context.add_cookies(cookies=cookies['cookies'])
            self.refresh_page()
            if top_navbar.signin_signup_button.is_visible() and not tried_once:
                self.start_existing_session(cookies=cookies, tried_once=True)


    def refresh_page(self, retries: int = 3) -> Response | None:
        """
        Reloads the current page and blocks until DOMContentLoaded. If the reload response is a
        502, waits 5s and retries up to `retries` times. Returns the final response (or None
        when the reload produced none, e.g. ERR_ABORTED on redirects).
        """
        response = None
        for attempt in range(retries):
            try:
                response = self.page.reload(wait_until="domcontentloaded")
            except PlaywrightError as e:
                msg = str(e)
                if "net::ERR_ABORTED" in msg or "frame was detached" in msg:
                    print(f"Ignored benign reload error: {msg}")
                    self.wait_for_dom_to_load()
                    return None
                raise
            if response is None or response.status != 502:
                # Scrolling to the top of the page.
                self.page.keyboard.press("Home")
                return response
            if attempt < retries - 1:
                print(f"502 on reload, attempt "
                      f"{attempt + 1}/{retries}. Retrying in 5s...")
                self.page.wait_for_timeout(5000)
        return response

    def get_user_agent(self) -> str:
        """
        This helper function fetches the user agent.
        """
        return self.page.evaluate('window.navigator.userAgent ')

    def remove_character_from_string(self, string: str, character_to_remove: str) -> str:
        """
        This helper function removes a given character from a given target string.

        Args:
            string (str): The target string
            character_to_remove (str): The character to remove
        """
        return string.replace(character_to_remove, "")

    def create_slug_from_title(self, article_title: str) -> str:
        """
        This helper function automatically creates an article title slug based on the given article
        title.

        Args:
            article_title (str): The article title
        """
        initial_title = article_title.split()
        return '-'.join(initial_title).lower()

    def is_descending(self, list_of_items: list[str]):
        """
        This helper function evaluates if a given list of items are displayed in descending order.

        Args:
            list_of_items (list[str]): The list of items
        """
        if all(list_of_items[i] >= list_of_items[i + 1] for i in range(len(list_of_items) - 1)):
            return True
        else:
            return False

    def extract_month_day_year_from_string(self, timestamp_str: str) -> str:
        """
        This helper function extracts the month/day/year from a given string.

        Args:
            timestamp_str (str): The timestamp string
        """
        timestamp = datetime.strptime(timestamp_str, "%b %d, %Y, %I:%M:%S %p")
        return timestamp.strftime("%b %d, %Y")

    def convert_string_to_datetime(self, timestamp_str: str) -> str:
        """
        This helper function converts a given timestamp string to date-time.

        Args:
            timestamp_str (str): The timestamp string
        """
        date_object = datetime.strptime(timestamp_str, "%m.%d.%Y")
        return date_object.strftime("%B {:d}, %Y").format(date_object.day)

    def extract_date_to_digit_format(self, date_str: str) -> int:
        """
        This helper function extracts the given date to digit format.

        Args:
            date_str (str): The date string
        """
        date = datetime.strptime(date_str, "%b %d, %Y")
        return int(date.strftime("%m%d%Y"))

    def parse_date(self, date_time: str, tzinfo: str = None) -> datetime:
        """
        This helper function parses a date string into a datetime object.
        Args:
            date_time (str): The date string to be parsed
            tzinfo (dict[str, str]): The timezone information
        """
        def tzinfo_resolver(tzname, offset):
            if tzname in ('CST', 'CDT'):
                return tz.gettz(tzinfo)
            return None

        return parser.parse(date_time, tzinfos=tzinfo_resolver)

    def tokenize_string(self, text: str) -> list[str]:
        """
        This helper function tokenizes the text into individual words and removes any non
        alphanumeric characters.

        Args:
            text (str): The text to be tokenized
        """
        return re.findall(r'\b\w+\b', text.lower())

    def stem_tokens(self, tokens: list[str], search_term_locale: str):
        """
        This helper function stems each token and returns the list of stemmed tokens.

        Args:
            tokens (list[str]): The list of tokens
            search_term_locale (str): The locale of the search term
        """
        stemmer = SnowballStemmer(search_term_locale)
        return [stemmer.stem(token) for token in tokens]

    def search_result_check(self, search_result, search_term, search_term_locale: str,
                            exact_phrase: bool):
        """
        Checks if the search result contains:
        1. Any variation of the provided keyword.
        2. The search term or any of its synonyms.
        3. The exact phrase or any component of the phrase.
        4. Variations of the search term by stemming.
        5. Variations of the search term by stemming for non-US words.

        Args:
            search_result (str): The search result
            search_term (str): The search term
            search_term_locale (str): The locale of the search term
            exact_phrase (bool): If the search should be for an exact phrase
        """

        search_term_split = search_term.lower().split()
        search_results_lower = search_result.lower()

        # Check if searching for exact phrase.
        if exact_phrase:
            return self._exact_phrase_check(search_result, search_term)

        # Check if keyword variations
        if self._contains_keyword_variation(search_results_lower, search_term_split):
            print(f"The {search_term} was found in search result variation.")
            return True

        # Check synonyms of split terms and the whole term
        match_found, matching_synonym = self._contains_synonym(search_results_lower, search_term,
                                                               search_term_split)
        if match_found:
            print(f"Search result for {search_term} found in synonym: {matching_synonym}")
            return True

        # Check if exact phrase match
        if ' '.join(search_term_split) in search_results_lower:
            print(f"Search results for {search_term} found in exact match")
            return True

        # Check each term component
        if any(term in search_results_lower for term in search_term_split):
            print(f"Search result for {search_term} found in a component of the search result")
            return True

        # Check stemming in search results.
        stemmed_tokens = self.stem_tokens(self.tokenize_string(search_result), search_term_locale)
        stemmed_search_term = self.stem_tokens(self.tokenize_string(search_term),
                                               search_term_locale)

        if any(term in stemmed_tokens for term in stemmed_search_term):
            print(f"Search result for {search_term} found in stemmed word")
            return True

        if self._contains_synonym(search_results_lower, stemmed_search_term, search_term_split)[0]:
            print(f"Search result for {search_term} found in stemmed word synonym")
            return True

        print("Search result not found!")
        return False

    def _contains_synonym(self, search_result_lower, search_term: Union[str, list[str]],
                          search_term_split) -> [bool, Any]:
        """
        This helper function checks if any synonyms of a given search term or its components
        (split term) are present in the search result.

        Args:
            search_result_lower (str): The search result in lowercase
            search_term (Union[str, list[str]]): The search term or its components
            search_term_split (list[str]): The search term split into components
        """
        synonyms = None
        lemmenizer = WordNetLemmatizer()

        if isinstance(search_term, list):
            for term in search_term:
                synonyms = SearchSynonyms.synonym_dict.get(lemmenizer.lemmatize(term.lower(),
                                                                                pos='n'), [])
        else:
            synonyms = SearchSynonyms.synonym_dict.get(lemmenizer.lemmatize(search_term.lower(),
                                                                            pos='n'), [])

        for term in search_term_split:
            synonyms.extend(SearchSynonyms.synonym_dict.get(lemmenizer.lemmatize(term, pos='n'),
                                                            []))

        for synonym in synonyms:
            if synonym.lower() in search_result_lower:
                return True, synonym.lower()
        return False, None

    def _contains_keyword_variation(self, search_result_lower, search_term_split):
        """
        This helper function checks if any variation of the keyword (components of the search term)
        are present in the search results. This includes different cases (lowercase or uppercase)
        and simple stemmed forms (by removing the last character).

        Args:
            search_result_lower (str): The search result in lowercase
            search_term_split (list[str]): The search term split into components
        """
        keyword_variations = [
            variation
            for term in search_term_split
            for variation in [term, term.capitalize(), term.upper(), term[:-1],
                              term[:-1].capitalize()]
        ]
        return any(variation in search_result_lower for variation in keyword_variations)

    def _exact_phrase_check(self, search_result: str, search_term: str) -> bool:
        """Check if the search result contains the exact phrase

        Args:
            search_result (str): The search result
            search_term (str): The search term
        """
        search_term = search_term.replace('"', '').lower()
        print(f"Search term is: {search_term}")
        search_result = search_result.lower()
        print(f"Search result is: {search_result}")
        return search_term in search_result

    def reindex_document(self, doc_type: str, obj_id: int):
        """Force-reindex a specific document in Elasticsearch so it becomes immediately
        searchable.

        Args:
            doc_type (str): The ES document type name (e.g. "WikiDocument",
                "QuestionDocument", "AnswerDocument", "ForumDocument", "ProfileDocument").
            obj_id (int): The primary key of the object to reindex.
        """
        session_id = self.get_session_id(
            self.username_extraction_from_email(self.staff_user)
        )
        endpoint = HomepageMessages.STAGE_HOMEPAGE_URL_EN_US + "search/api/reindex-document"
        headers = {
            "Content-Type": "application/json",
            "Cookie": f"session_id={session_id}",
            "User-Agent": Utilities.user_agent,
        }
        request_body = {"doc_type": doc_type, "obj_id": obj_id}

        for attempt in range(3):
            response = requests.post(url=endpoint, json=request_body, headers=headers)
            if response.status_code == 200:
                print(f"Reindex succeeded: {response.json()}")
                return response.json()
            print(
                f"Reindex attempt {attempt + 1}/3 failed "
                f"(status={response.status_code}): {response.text}"
            )
            self.wait_for_given_timeout(2000)

        raise RuntimeError(
            f"Failed to reindex {doc_type} {obj_id} after 3 attempts. "
            f"Last response: {response.status_code} {response.text}"
        )

    def get_api_response(self, page: Page, api_url: str):
        """Get the API response

        Args:
            page (Page): The page object
            api_url (str): The API URL
        """
        return page.request.get(api_url)

    def post_api_request(self, page: Page, api_url: str, data: dict):
        """Post the API request

        Args:
            page (Page): The page object
            api_url (str): The API URL
            data (dict): The data to be posted
        """

        # It seems that playwright doesn't send the correct origin header by default.
        headers = {
            'origin': HomepageMessages.STAGE_HOMEPAGE_URL
        }

        return page.request.post(api_url, form=data, headers=headers)

    def block_request(self, route):
        """
        This function blocks a certain request
        """
        route.abort()

    def get_ga_logs(self, msg) -> dict:
        """
        This helper function fetches the GA logs from the console and formats them into a dict
        """
        message = msg.text.replace('\n', '')
        if message.startswith('event:'):
            return {"event": message.split(": ", 1)[1].rstrip(':')}
        elif message.startswith('parameters:'):
            return {"parameters": json.loads(message.split(": ", 1)[1])}

    def fetch_scrolly(self) -> int:
        """
        This helper function returns the number of pixels by which the document is currently
        scrolled vertically.
        """
        return self.page.evaluate("() => window.scrollY")

    def fetch_session_storage_banner_key(self, banner_id: str) -> str:
        """
        This helper function returns the value of the announcement banner session storage key.
        """
        return self.page.evaluate(f"() => sessionStorage.getItem('announce-{banner_id}.closed')")

    def set_session_storage_banner_key(self, banner_id: str, value: str):
        """
        This helper functions sets a new value to the announcement banner session storage key.
        """
        self.page.evaluate(f"() => sessionStorage.setItem('announce-{banner_id}.closed',"
                           f"'{value}')")

    def expect_locator_visibility(self, locator: Locator) -> bool:
        for attempt in range(3):
            try:
                expect(locator).to_be_visible(timeout=6000)
                return True
            except AssertionError:
                print("Expected locator not present. Reloading the page.")
                self.page.reload()
        else:
            return False

    def strip_wiki_syntax(self, text: str) -> str:
        # Handle wiki links.
        text = re.sub(r"\[\[(?:[^\|\]]*\|)?([^\]]+)\]\]", r"\1", text)
        # Handle external links.
        text = re.sub(r"\[(https?://[^\s]+)\s+([^\]]+)\]", r"\2", text)
        # Handle bold wiki.
        text = re.sub(r"'''(.*?)'''", r"\1", text)
        # Handle italic wiki.
        text = re.sub(r"''(.*?)''", r"\1", text)
        return " ".join(text.split())  # collapse whitespace


