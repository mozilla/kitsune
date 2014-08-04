import json

from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from kitsune.access.decorators import permission_required
from kitsune.customercare.models import TwitterAccount


class TwitterAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterAccount


class BannedList(generics.ListAPIView):
    """Get all banned users."""
    queryset = TwitterAccount.uncached.filter(banned=True)
    serializer_class = TwitterAccountSerializer


@permission_required('customercare.ban_account')
@api_view(['POST'])
def ban(request):
    username = json.loads(request.body).get('username')
    if not username:
        return Response({'error': 'Error: Username not provided.'},
                        status.HTTP_400_BAD_REQUEST)

    account = TwitterAccount.uncached.filter(username=username).first()
    if account:
        if account.banned:
            return Response({'error': 'This account is already banned!'},
                            status.HTTP_409_CONFLICT)
        account.banned = True
        account.save()
    else:
        TwitterAccount.uncached.create(username=username, banned=True)
    return Response({'success': 'Account banned successfully!'})


@permission_required('customercare.ban_account')
@api_view(['POST'])
def unban(request):
    usernames = json.loads(request.body).get('usernames')
    if not usernames:
        return Response({'error': 'Usernames not provided.'},
                        status.HTTP_400_BAD_REQUEST)

    accounts = TwitterAccount.uncached.filter(username__in=usernames).all()
    for account in accounts:
        if account and account.banned:
            account.banned = False
            account.save()

    # Small hack to keep correct grammar.
    message = {'success': '{0} user{1} unbanned successfully.'
               .format(len(accounts), 's' * (len(accounts) > 1))}
    return Response(message)
