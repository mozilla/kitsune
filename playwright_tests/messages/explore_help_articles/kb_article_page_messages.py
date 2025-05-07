class KBArticlePageMessages:
    CREATE_NEW_KB_ARTICLE_STAGE_URL = "https://support.allizom.org/en-US/kb/new"
    KB_ARTICLE_PAGE_URL = "https://support.allizom.org/en-US/kb/"
    KB_ARTICLE_HISTORY_URL_ENDPOINT = "/history"
    KB_ARTICLE_DISCUSSIONS_ENDPOINT = "/discuss/"
    KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT = "/discuss/new"
    KB_ARTICLE_LOCKED_THREAD_MESSAGE = ("This thread has been locked. It is no longer possible to "
                                        "post new replies.")
    KB_ARTICLE_LOCK_THIS_THREAD_OPTION = "Lock this thread"
    KB_ARTICLE_UNLOCK_THIS_THREAD_OPTION = "Unlock this thread"
    KB_ARTICLE_STICKY_THIS_THREAD_OPTION = "Sticky this thread"
    KB_ARTICLE_UNSTICKY_OPTION = "Unsticky this thread"
    GET_COMMUNITY_SUPPORT_ARTICLE_LINK = ("https://support.allizom.org/en-US/kb/get-community"
                                          "-support?exit_aaq=1")
    UNREVIEWED_REVISION_STATUS = "Unreviewed"
    REVIEW_REVISION_STATUS = "Review"
    CURRENT_REVISION_STATUS = "Current"
    PREVIOUS_APPROVED_REVISION_STATUS = "Approved"
    MINOR_SIGNIFICANCE = ''
    NORMAL_SIGNIFICANCE = 'M'
    MAJOR_SIGNIFICANCE = 'MT'
    KB_ARTICLE_NOT_APPROVED_CONTENT = "This article doesn't have approved content yet."
    KB_ARTICLE_SUBMISSION_TITLE_ERRORS = ["Document with this Title and Locale already exists.",
                                          "Document with this Slug and Locale already exists."]
    KB_ARTICLE_PRODUCT_ERROR = "Please select at least one product."
    KB_ARTICLE_TOPIC_ERROR = "Please select at least one topic."
    KB_ARTICLE_RESTRICTED_BANNER = "This document is restricted."
    KB_ARTICLE_NOT_READY_FOR_TRANSLATION_BANNER = ("Traduci un document în engleză care nu este "
                                                   "încă gata de localizare.")
    KB_SURVEY_FEEDBACK = "Thanks for your feedback!"
    KB_SURVEY_FEEDBACK_NO_ADDITIONAL_DETAILS = ("Thanks for voting! Your additional feedback "
                                                "wasn't submitted.")

    def get_template_error(self, article_title) -> str:
        return (f'Documents in the Template category must have titles that start with '
                f'"Template:". (Current title is "{article_title}")')
