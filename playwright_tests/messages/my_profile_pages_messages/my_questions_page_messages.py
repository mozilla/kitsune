class MyQuestionsPageMessages:
    MY_QUESTIONS_PAGE_HEADER = "My Questions"
    NO_POSTED_QUESTIONS_MESSAGE = "You haven't posted any questions yet."

    def get_stage_my_questions_url(username: str) -> str:
        return f"https://support.allizom.org/en-US/user/{username}/questions"

    def get_no_posted_questions_other_user_message(username: str) -> str:
        return f"{username} hasn't posted any questions yet."
