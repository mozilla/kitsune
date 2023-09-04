class MySubscriptionsPageMessages:
    def get_my_subscriptions_url(self, username: str) -> str:
        return f"https://support.allizom.org/en-US/user/{username}/subscriptions"
