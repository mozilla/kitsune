class UserGroupMessages:
    DELETE_AVATAR_PAGE_INFO = ("You are about to permanently delete the avatar. "
                               "This cannot be undone! You can always upload another avatar to "
                               "replace the current one.")
    GROUP_INFORMATION_UPDATE_NOTIFICATION = "Group information updated successfully!"

    def get_user_added_success_message(username: str) -> str:
        """Get the user added success message.

        Args:
            username (str): The username of the user added to the group
        """
        return f"{username} added to the group successfully!"

    def get_user_removed_success_message(username: str) -> str:
        """Get the user removed success message.

        Args:
            username (str): The username of the user removed from the group
        """
        return f"{username} removed from the group successfully!"

    def get_change_avatar_page_header(user_group: str) -> str:
        """Get the change avatar page header.

        Args:
            user_group (str): The group name.
        """
        return f"Change {user_group} group avatar"

    def get_change_uploaded_avatar_page_header(user_group: str) -> str:
        """Get the change uploaded avatar page header.

        Args:
            user_group (str): The group name.
        """
        return f"Change {user_group} group avatar"

    def get_delete_uploaded_avatar_page_header(user_group: str) -> str:
        """Get the delete uploaded avatar page header.

        Args:
            user_group (str): The group name.
        """
        return f"Are you sure you want to delete the {user_group} group avatar?"

    def get_delete_user_header(username: str, group: str) -> str:
        """Get the delete user page header.

        Args:
            username (str): The username of the user to delete.
            group (str): The group name.
        """
        return f"Are you sure you want to remove {username} from {group}?"

    def get_edit_profile_information_page_header(group_name: str) -> str:
        """Get the edit profile information page header.

        Args:
            group_name (str): The group name.
        """
        return f"Edit {group_name} profile information"
