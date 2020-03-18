import json

from rest_framework import generics, serializers, status, decorators
from rest_framework.response import Response

from kitsune.customercare.models import TwitterAccount
from kitsune.sumo.api_utils import GenericAPIException, GenericDjangoPermission


class TwitterAccountBanPermission(GenericDjangoPermission):
    permissions = ["customercare.ban_account"]


class TwitterAccountIgnorePermission(GenericDjangoPermission):
    permissions = ["customercare.ignore_account"]


class TwitterAccountSerializer(serializers.ModelSerializer):
    """Serializer for the TwitterAccount model."""

    class Meta:
        model = TwitterAccount
        fields = "__all__"


class BannedList(generics.ListAPIView):
    """Get all banned users."""

    queryset = TwitterAccount.objects.filter(banned=True)
    serializer_class = TwitterAccountSerializer
    permission_classes = (TwitterAccountBanPermission,)
    pagination_class = None


class IgnoredList(generics.ListAPIView):
    """Get all banned users."""

    queryset = TwitterAccount.objects.filter(ignored=True)
    serializer_class = TwitterAccountSerializer
    permission_classes = (TwitterAccountIgnorePermission,)
    pagination_class = None


@decorators.api_view(["POST"])
@decorators.permission_classes([TwitterAccountBanPermission])
def ban(request):
    """Bans a twitter account from using the AoA tool."""
    username = json.loads(request.body).get("username")
    if not username:
        raise GenericAPIException(status.HTTP_400_BAD_REQUEST, "Username not provided.")

    username = username[1:] if username.startswith("@") else username
    account, created = TwitterAccount.objects.get_or_create(
        username=username, defaults={"banned": True}
    )
    if not created and account.banned:
        raise GenericAPIException(
            status.HTTP_409_CONFLICT, "This account is already banned!"
        )
    else:
        account.banned = True
        account.save()

    return Response({"success": "Account banned successfully!"})


@decorators.api_view(["POST"])
@decorators.permission_classes([TwitterAccountBanPermission])
def unban(request):
    """Unbans a twitter account from using the AoA tool."""
    usernames = json.loads(request.body).get("usernames")
    if not usernames:
        raise GenericAPIException(
            status.HTTP_400_BAD_REQUEST, "Usernames not provided."
        )

    accounts = TwitterAccount.objects.filter(username__in=usernames)
    for account in accounts:
        if account and account.banned:
            account.banned = False
            account.save()

    message = {"success": "{0} users unbanned successfully.".format(len(accounts))}
    return Response(message)


@decorators.api_view(["POST"])
@decorators.permission_classes([TwitterAccountIgnorePermission])
def ignore(request):
    """Ignores a twitter account from showing up in the AoA tool."""
    username = json.loads(request.body).get("username")
    if not username:
        raise GenericAPIException(status.HTTP_400_BAD_REQUEST, "Username not provided.")

    username = username[1:] if username.startswith("@") else username
    account, created = TwitterAccount.objects.get_or_create(
        username=username, defaults={"ignored": True}
    )
    if not created and account.ignored:
        raise GenericAPIException(
            status.HTTP_409_CONFLICT, "This account is already in the ignore list!"
        )
    else:
        account.ignored = True
        account.save()

    return Response({"success": "Account is now being ignored!"})


@decorators.api_view(["POST"])
@decorators.permission_classes([TwitterAccountIgnorePermission])
def unignore(request):
    """Unignores a twitter account from showing up in the AoA tool."""
    usernames = json.loads(request.body).get("usernames")
    if not usernames:
        raise GenericAPIException(
            status.HTTP_400_BAD_REQUEST, "Usernames not provided."
        )

    accounts = TwitterAccount.objects.filter(username__in=usernames)
    for account in accounts:
        if account and account.ignored:
            account.ignored = False
            account.save()

    message = {"success": "{0} users unignored successfully.".format(len(accounts))}
    return Response(message)
