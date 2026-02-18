class UserGroupMessages:
    DELETE_AVATAR_PAGE_INFO = ("You are about to permanently delete the avatar. "
                               "This cannot be undone! You can always upload another avatar to "
                               "replace the current one.")
    GROUP_INFORMATION_UPDATE_NOTIFICATION = "Group information updated successfully!"

    @staticmethod
    def get_user_added_success_message(username: str, to_leaders=False) -> str:
        if to_leaders:
            return f"{username} added to the group leaders successfully!"
        else:
            return f"{username} added to the group successfully!"

    @staticmethod
    def get_user_removed_success_message(username: str, from_leaders=False) -> str:
        if from_leaders:
            return f"{username} removed from the group leaders successfully!"
        else:
            return f"{username} removed from the group successfully!"

    @staticmethod
    def get_change_avatar_page_header(group_name: str) -> str:
        return f"Change {group_name} group avatar"

    @staticmethod
    def get_change_uploaded_avatar_page_header(group_name: str) -> str:
        return f"Change {group_name} group avatar"

    @staticmethod
    def get_delete_uploaded_avatar_page_header(group_name: str) -> str:
        return f"Are you sure you want to delete the {group_name} group avatar?"

    @staticmethod
    def get_delete_user_header(username: str, group: str, delete_leader=False) -> str:
        if delete_leader:
            return f"Are you sure you want to remove {username} from {group} leaders?"
        else:
            return f"Are you sure you want to remove {username} from {group}?"

    @staticmethod
    def get_edit_profile_information_page_header(group_name: str) -> str:
        return f"Edit {group_name} profile information"
