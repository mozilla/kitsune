class EditMyProfilePageMessages:
    STAGE_EDIT_MY_PROFILE_URL = "https://support.allizom.org/en-US/users/edit"
    USERNAME_INPUT_ERROR_MESSAGE = (
        "Enter a valid username. This value may "
        "contain only letters, numbers, and @/./+/-/_ characters."
    )
    DUPLICATE_USERNAME_ERROR_MESSAGE = "A user with that username already exists."
    EMPTY_USERNAME_TOOLTIP_ERROR = "Please fill out this field."
    MAKE_EMAIL_ADDRESS_VISIBLE_PSEUDO_ELEMENT_CHECKBOX_COLOR = "rgb(0, 96, 223)"
    PROFILE_ACCESS_DENIED_HEADING = "Access denied"
    PROFILE_ACCESS_DENIED_SUBHEADING = "You do not have permission to access this page."

    def get_url_of_other_profile_edit_page(username: str) -> str:
        return f"https://support.allizom.org/en-US/user/{username}/edit"
