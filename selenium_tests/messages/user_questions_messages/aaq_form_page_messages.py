class AAQFormPageMessages:
    AAQ_FORM_PAGE_HEADER = "Ask your question "
    AAQ_FORM_PAGE_INTRO = (
        "Be nice. Our volunteers are Mozilla users just like you,"
        " who take the time out of their day to help."
    )
    AAQ_TOPIC_DROPDOWN_FIELD_IS_REQUIRED_ERROR_MESSAGE = "This field is required."
    AAQ_FIELD_REQUIRED_ERROR_MESSAGE = "This field is required."

    def get_not_enough_characters_error_message(self, subject_length: int) -> str:
        return f"Ensure this value has at least 5 characters (it has {subject_length})."
