from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db.models import Q
from django.views.decorators.http import require_GET

import waffle
from statsd import statsd

from rest_framework import viewsets, serializers, mixins, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import permission_classes, api_view
from rest_framework.authtoken import views as authtoken_views

from kitsune.access.decorators import login_required
from kitsune.sumo.api import CORSMixin
from kitsune.sumo.decorators import json_view
from kitsune.users.models import Profile, RegistrationProfile


def display_name_or_none(user):
    try:
        return user.profile.name
    except (Profile.DoesNotExist, AttributeError):
        return None


@login_required
@require_GET
@json_view
def usernames(request):
    """An API to provide auto-complete data for user names."""
    term = request.GET.get('term', '')
    query = request.GET.get('query', '')
    pre = term or query

    if not pre:
        return []
    if not request.user.is_authenticated():
        return []
    with statsd.timer('users.api.usernames.search'):
        profiles = (
            Profile.objects.filter(Q(name__istartswith=pre))
            .values_list('user_id', flat=True))
        users = (
            User.objects.filter(
                Q(username__istartswith=pre) | Q(id__in=profiles))
            .extra(select={'length': 'Length(username)'})
            .order_by('length').select_related('profile'))

        if not waffle.switch_is_active('users-dont-limit-by-login'):
            last_login = datetime.now() - timedelta(weeks=12)
            users = users.filter(last_login__gte=last_login)

        return [{'username': u.username,
                 'display_name': display_name_or_none(u)}
                for u in users[:10]]


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def test_auth(request):
    return Response({
        'username': request.user.username,
        'authorized': True,
    })


class GetToken(CORSMixin, authtoken_views.ObtainAuthToken):
    """Add CORS headers to the ObtainAuthToken view."""


class ProfileShortSerializer(serializers.ModelSerializer):
    username = serializers.WritableField(source='user.username')
    display_name = serializers.WritableField(source='name', required=False)
    date_joined = serializers.Field(source='user.date_joined')
    email = serializers.WritableField(
        source='user.email', write_only=True, required=False)
    # This is a write only field. It is very very important it stays that way!
    password = serializers.WritableField(
        source='user.password', write_only=True)

    class Meta:
        model = Profile
        fields = [
            'username',
            'display_name',
            'date_joined',
            'email',
            # Password is here so it can be involved in write operations.
            # It is marked as write-only above, so it will not be visible.
            'password',
        ]

    def restore_object(self, attrs, instance=None):
        """
        Override the default behavior to make a user if one doesn't exist.

        This user may not be saved here, but will be saved if/when the .save()
        method of the serializer is called.
        """
        instance = (super(ProfileShortSerializer, self)
                    .restore_object(attrs, instance))
        if instance.user_id is None:
            # The Profile doesn't have a user, so create one. If an email is
            # specified, the user will be inactive until the email is
            # confirmed. Otherwise the user can be created immediately.
            if 'user.email' in attrs:
                u = RegistrationProfile.objects.create_inactive_user(
                    attrs['user.username'],
                    attrs['user.password'],
                    attrs['user.email'])
            else:
                u = User(username=attrs['user.username'])
                u.set_password(attrs['user.password'])
            instance._nested_forward_relations['user'] = u
        return instance

    def validate_display_name(self, attrs, source):
        if attrs.get('name') is None:
            attrs['name'] = attrs['user.username']
        return attrs

    def validate_email(self, attrs, source):
        email = attrs.get('user.email')
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError('A user with that email address '
                                              'already exists.')
        return attrs


class ProfileViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    model = Profile
    serializer_class = ProfileShortSerializer
    paginate_by = 20
    # User usernames instead of ids in urls.
    lookup_field = 'user__username'
    filter_backends = [
        filters.DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filter_fields = [
        'user__date_joined',
    ]
    ordering_fields = [
        'user__username',
        'name',
        'user__date_joined',
    ]
    # Default, if not overwritten
    ordering = ('-user__date_joined',)
