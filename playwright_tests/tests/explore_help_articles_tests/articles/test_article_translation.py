from playwright_tests.core.utilities import Utilities
import pytest
import allure
from pytest_check import check
from playwright.sync_api import expect, Page
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages)
from playwright_tests.messages.explore_help_articles.kb_translation_messages import \
    KbTranslationMessages
from playwright_tests.messages.homepage_messages import HomepageMessages
from kitsune.settings import SUMO_LANGUAGES, FALLBACK_LANGUAGES, NON_SUPPORTED_LOCALES
from playwright_tests.pages.sumo_pages import SumoPages


# C2489548, C2490043, C946153
@pytest.mark.kbArticleTranslation
def test_not_ready_for_localization_articles_dashboard_status(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    kb_translation_messages = KbTranslationMessages()
    with allure.step("Signing in with an Admin account"):
        username = utilities.start_existing_session(
            utilities.username_extraction_from_email(
                utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

    with allure.step("Create a new simple article and approving it without marking it as "
                     "ready for localization"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True
        )
        parent_article_url = utilities.get_page_url()

    with allure.step("Clicking on the Translate Article Editing Tools option and selecting "
                     "the ro locale"):
        sumo_pages.kb_article_page._click_on_translate_article_option()
        sumo_pages.translate_article_page._click_on_romanian_locale_from_list()
        translation_url = utilities.get_page_url()

    with check, allure.step("Verifying that the correct banner is displayed"):
        check.equal(
            sumo_pages.translate_article_page._get_text_of_article_unready_for_translation_banner(
            ), KBArticlePageMessages.KB_ARTICLE_NOT_READY_FOR_TRANSLATION_BANNER
        )

    with allure.step("Navigating to the localization dashboard and verifying that the "
                     "article is not listed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        expect(sumo_pages.most_visited_translations_page._get_a_particular_article_title_locator(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Navigating to the localization unreviewed page and verifying that the "
                     "article is not listed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['localization_unreviewed']
        )
        expect(sumo_pages.localization_unreviewed_page._get_listed_article(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Navigating back to the translation page and performing a translation"):
        utilities.navigate_to_link(translation_url)
        translation = sumo_pages.submit_kb_translation_flow._add_article_translation(
            approve_translation_revision=False
        )

    with allure.step("Navigating to the localization dashboard and verifying that the "
                     "article is not listed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        expect(sumo_pages.most_visited_translations_page._get_a_particular_article_title_locator(
            translation['translation_title'])).to_be_hidden()

    with allure.step("Navigating to the localization unreviewed page and verifying that the "
                     "article is displayed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['localization_unreviewed']
        )
        expect(sumo_pages.localization_unreviewed_page._get_listed_article(
            translation['translation_title'])).to_be_visible()

    with check, allure.step("Verifying that the correct modified by text is displayed"):
        check.equal(sumo_pages.localization_unreviewed_page._get_modified_by_text(
            translation['translation_title']),
            kb_translation_messages.get_unreviewed_localization_modified_by_text(username)
        )
    with allure.step("Clicking on the article approving the revision"):
        sumo_pages.localization_unreviewed_page._click_on_a_listed_article(
            translation['translation_title']
        )
        sumo_pages.submit_kb_translation_flow.approve_kb_translation(translation['revision_id'])

    with allure.step("Navigating to the localization unreviewed page and verifying that the "
                     "article is not displayed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        expect(sumo_pages.localization_unreviewed_page._get_listed_article(
            translation['translation_title'])).to_be_hidden()

    with check, allure.step("Navigating to the localization dashboard and verifying that the "
                            "article is not displayed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        expect(sumo_pages.localization_unreviewed_page._get_listed_article(
            translation['translation_title'])).to_be_hidden()

    with allure.step("Navigating to the parent article and marking it as ready for l10n"):
        utilities.navigate_to_link(parent_article_url)
        sumo_pages.kb_article_show_history_page._click_on_ready_for_l10n_option(
            article_details['first_revision_id']
        )
        sumo_pages.kb_article_show_history_page._click_on_submit_l10n_readiness_button()

    with check, allure.step("Navigating to the localization dashboard and verifying that the "
                            "article is displayed with the correct status"):
        utilities.wait_for_given_timeout(2000)
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        check.equal(sumo_pages.most_visited_translations_page._get_updated_localization_status(
            translation['translation_title']),
            kb_translation_messages.LOCALIZATION_DASHBOARD_TRANSLATED_STATUS
        )

    with allure.step("Deleting the parent article"):
        utilities.navigate_to_link(parent_article_url)
        sumo_pages.kb_article_deletion_flow.delete_kb_article()

    with check, allure.step("Manually navigating to the 'Discuss' endpoint and verifying "
                            "that the 404 page is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(translation_url)
        response = navigation_info.value
        assert response.status == 404


# C2489548
@pytest.mark.kbArticleTranslation
def test_ready_for_localization_articles_dashboard_status(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    kb_translation_messages = KbTranslationMessages()
    with allure.step("Signing in with an Admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Create a new simple article and marking it as ready for localization"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True, ready_for_localization=True
        )
        parent_article_url = utilities.get_page_url()

    with check, allure.step("Navigating to the localization dashboard and verifying that the "
                            "correct status is displayed"):
        utilities.wait_for_given_timeout(2000)
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        check.equal(sumo_pages.most_visited_translations_page._get_a_particular_translation_status(
            article_details['article_title']),
            kb_translation_messages.LOCALIZATION_DASHBOARD_NEEDS_TRANSLATION_STATUS
        )

    with allure.step("Navigating to the article translation page and verifying that no "
                     "banner is displayed"):
        sumo_pages.most_visited_translations_page._click_on_a_particular_article_status(
            article_details['article_title'])
        translation_url = utilities.get_page_url()
        expect(sumo_pages.translate_article_page._get_unready_for_translation_banner()
               ).to_be_hidden()

    with allure.step("Performing an article translation"):
        translation = sumo_pages.submit_kb_translation_flow._add_article_translation(
            approve_translation_revision=False
        )

    with check, allure.step("Navigating to the localization dashboard and verifying that the "
                            "correct status is displayed"):
        utilities.wait_for_given_timeout(2000)
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        check.equal(sumo_pages.most_visited_translations_page._get_a_particular_translation_status(
            translation['translation_title']),
            kb_translation_messages.LOCALIZATION_DASHBOARD_NEEDS_REVIEW_STATUS
        )

    with check, allure.step("Navigating to the article translation and approving the "
                            "translation revision"):
        sumo_pages.most_visited_translations_page._click_on_a_particular_article_status(
            translation['translation_title']
        )
        sumo_pages.submit_kb_translation_flow.approve_kb_translation(translation['revision_id'])

    with check, allure.step("Navigating to the localization dashboard an verifying that the "
                            "correct status is displayed"):
        utilities.wait_for_given_timeout(2000)
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        check.equal(
            sumo_pages.most_visited_translations_page._get_updated_localization_status(
                translation['translation_title']
            ), kb_translation_messages.LOCALIZATION_DASHBOARD_TRANSLATED_STATUS
        )

    with allure.step("Deleting the parent article"):
        utilities.navigate_to_link(parent_article_url)
        sumo_pages.kb_article_deletion_flow.delete_kb_article()

    with check, allure.step("Manually navigating to the 'Discuss' endpoint and verifying "
                            "that the 404 page is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(translation_url)
        response = navigation_info.value
        assert response.status == 404


# C2490043
@pytest.mark.kbArticleTranslation
def test_revisions_cannot_be_marked_as_ready_for_l10n_if_lacking_permissions(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an Admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Create a new simple article and marking it as ready for localization"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True
        )
    article_url = utilities.get_page_url()

    with allure.step("Signing in with a different account that has no permissions to mark a "
                     "revision as ready for l10n"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_2"]
        ))

    with allure.step("Clicking on the ready for l10n button and verifying that it has no "
                     "effect"):
        sumo_pages.kb_article_show_history_page._click_on_ready_for_l10n_option(
            article_details['first_revision_id']
        )
        utilities.wait_for_given_timeout(2000)
        expect(sumo_pages.kb_article_show_history_page._get_l10n_modal_locator()).to_be_hidden()

        expect(
            sumo_pages.kb_article_show_history_page._get_ready_for_localization_status(
                article_details['first_revision_id']
            )
        ).to_be_hidden()

    with allure.step("Navigating to the localization dashboard and verifying that the "
                     "article is not listed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations']
        )
        expect(sumo_pages.most_visited_translations_page._get_a_particular_article_title_locator(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Navigating to the localization unreviewed page and verifying that the "
                     "article is not listed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['localization_unreviewed']
        )
        expect(sumo_pages.localization_unreviewed_page._get_listed_article(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Navigating back to the article and deleting it"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        utilities.navigate_to_link(article_url)
        sumo_pages.kb_article_deletion_flow.delete_kb_article()


# C2316346, C2316347
@pytest.mark.kbArticleTranslation
def test_unsupported_locales_fallback(page: Page):
    utilities = Utilities(page)
    with allure.step("Verifying the unsupported locales fallback"):
        for key, value in NON_SUPPORTED_LOCALES.items():
            utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL + f"/{key}/")
            if value is None:
                expect(
                    page
                ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)
            else:
                expect(
                    page
                ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + f"/{value}/")


# C2625000
@pytest.mark.kbArticleTranslation
def test_fallback_languages(self):
    with allure.step("Verifying the language fallback"):
        for key, value in FALLBACK_LANGUAGES.items():
            self.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL + f"/{value}/")
            expect(
                self.page
            ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + f"/{key}/")


# C2316347
@pytest.mark.kbArticleTranslation
def test_supported_languages(page: Page):
    utilities = Utilities(page)
    with allure.step("Verifying that the users are redirected to the supported locales "
                     "successfully"):
        for locale in SUMO_LANGUAGES:
            if locale == 'xx':
                continue
            else:
                with page.expect_navigation() as navigation_info:
                    utilities.navigate_to_link(
                        HomepageMessages.STAGE_HOMEPAGE_URL + f"/{locale}/")
                response = navigation_info.value
                assert response.status == 200
                assert locale in utilities.get_page_url()


# C2316350, C2316349
@pytest.mark.kbArticleTranslation
def test_sumo_locale_priority(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-admin account and changing the preferred profile "
                     "language"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))

    with allure.step("Accessing the edit profile page and changing the language to ro"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.select_preferred_language_dropdown_option_by_value("ro")
        sumo_pages.edit_my_profile_page.click_update_my_profile_button()

    with allure.step("Navigating to the SUMO homepage without specifying the path in the "
                     "locale and verifying that the preferred locale is set"):
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/ro/")

    with allure.step("Navigating to the SUMO homepage while using a lang query parameter and "
                     "verifying that the user is redirected to the specified locale inside "
                     "the param"):
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL + "/?lang=de")
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/de/")

    with allure.step("Navigating back to the ro locale"):
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)

    with allure.step("Sending a request by modifying the 'Accept-Language' header to a "
                     "different locale"):
        headers = {
            'Accept-Language': 'it'
        }
        utilities.set_extra_http_headers(headers)
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/ro/")

    with allure.step("Changing the preferred language back to english and signing out"):
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL + '/en-US/')
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.select_preferred_language_dropdown_option_by_value(
            "en-US")
        sumo_pages.edit_my_profile_page.click_update_my_profile_button()
        utilities.delete_cookies()

    with allure.step("Sending the request with the modified 'Accept-Language' header set to "
                     "a different locale and verifying that the correct locale is displayed"):
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/it/")

    with allure.step("Sending the request with the modified 'Accept-Language' to point out "
                     "to an invalid locale and a fallback and verifying that the user is "
                     "redirected to the correct first fallback locale"):
        headers = {
            'Accept-Language': 'test, de, it'
        }
        utilities.set_extra_http_headers(headers)
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL + "/de/")
