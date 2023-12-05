class MyProfileMessages:
    STAGE_MY_PROFILE_PAGE_HEADER = "Your Account"
    TWITTER_REDIRECT_LINK = "https://twitter.com/"
    COMMUNITY_PORTAL_LINK = "https://community.mozilla.org"
    PEOPLE_DIRECTORY_LINK = "https://people.mozilla.org"

    def get_my_profile_stage_url(username: str) -> str:
        return f"https://support.allizom.org/en-US/user/{username}/"
