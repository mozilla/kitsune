class AAQFormMessages:
    COMPLETED_MILESTONE_ONE = "Change Product"
    COMPLETED_MILESTONE_TWO = "Explore Solutions"
    IN_PROGRESS_MILESTONE = "Get Support"
    SUMO_PAGE_INTRO = ("Be nice. Our volunteers are Mozilla users just like you, who take the "
                       "time out of their day to help.")
    INFO_CARD = ("Be descriptive. Saying “playing video on YouTube is always choppy” will help us "
                 "understand the issue better than saying “something is wrong” or “the app is "
                 "broken”.")
    ERROR_MESSAGE = "This field is required."
    LOGINLESS_RATELIMIT_REACHED_MESSAGE = "You've exceeded the number of submissions for today."

    def get_premium_ticket_submission_success_message(self, user_email: str) -> str:
        return (f"Thank you for reaching out to Mozilla Support. We're reviewing your submission "
                f"and will send a confirmation email to {user_email} shortly.")
