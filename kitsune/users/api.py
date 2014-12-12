import random
import re
from datetime import datetime, timedelta
from string import letters

from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.views.decorators.http import require_GET

import waffle
from statsd import statsd

from rest_framework import viewsets, serializers, mixins, filters, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.authtoken.models import Token

from kitsune.access.decorators import login_required
from kitsune.sumo.api import DateTimeUTCField, GenericAPIException, PermissionMod
from kitsune.sumo.decorators import json_view
from kitsune.users.helpers import profile_avatar
from kitsune.users.models import Profile, RegistrationProfile, Setting


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
            Profile.uncached.filter(Q(name__istartswith=pre))
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


class OnlySelf(permissions.BasePermission):
    """
    Only allows operations when the current user is the object in question.

    Intended for use with PermissionsFields.

    TODO: This should be tied to user and object permissions better, but
    for now this is a bandaid.
    """

    def has_object_permission(self, request, view, obj):
        request_user = getattr(request, 'user', None)
        user = getattr(obj, 'user', None)
        return request_user == user


class OnlySelfEdits(OnlySelf):
    """
    Only allow users/profiles to be edited and deleted by themselves.

    TODO: This should be tied to user and object permissions better, but
    for now this is a bandaid.
    """

    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS is a list containing all the read-only methods.
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            return super(OnlySelfEdits, self).has_object_permission(request, view, obj)


class UserSettingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(required=False, write_only=True)

    class Meta:
        model = Setting
        fields = ('name', 'value', 'user')

    def get_identity(self, obj):
        return obj['name']

    def restore_object(self, attrs, instance=None):
        """
        Given a dictionary of deserialized field values, either update
        an existing model instance, or create a new model instance.
        """
        if instance is not None:
            for key in self.Meta.fields:
                setattr(instance, key, attrs.get(key, getattr(instance, key)))
            return instance
        else:
            user = attrs['user'] or self.context['view'].object
            obj, created = self.Meta.model.uncached.get_or_create(
                user=user, name=attrs['name'], defaults={'value': attrs['value']})
            if not created:
                obj.value = attrs['value']
                obj.save()
            return obj


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.WritableField(source='user.username')
    display_name = serializers.WritableField(source='name', required=False)
    date_joined = DateTimeUTCField(source='user.date_joined', read_only=True)
    avatar = serializers.SerializerMethodField('get_avatar_url')
    email = (PermissionMod(serializers.WritableField, permissions=[OnlySelf])
             (source='user.email', required=False))
    settings = (PermissionMod(UserSettingSerializer, permissions=[OnlySelf])
                (many=True, read_only=True))
    helpfulness = serializers.Field(source='answer_helpfulness')
    # These are write only fields. It is very important they stays that way!
    password = serializers.WritableField(source='user.password', write_only=True)

    class Meta:
        model = Profile
        fields = [
            'username',
            'display_name',
            'date_joined',
            'avatar',
            'bio',
            'website',
            'twitter',
            'facebook',
            'irc_handle',
            'timezone',
            'country',
            'city',
            'locale',
            'email',
            'settings',
            'helpfulness',
            # Password and email are here so they can be involved in write
            # operations. They is marked as write-only above, so will not be
            # visible.
            'password',
        ]

    def get_avatar_url(self, obj):
        return profile_avatar(obj.user)

    def restore_object(self, attrs, instance=None):
        """
        Override the default behavior to make a user if one doesn't exist.

        This user may not be saved here, but will be saved if/when the .save()
        method of the serializer is called.
        """
        instance = (super(ProfileSerializer, self)
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

    def validate_username(self, attrs, source):
        obj = self.object
        if obj is None:
            # This is a create
            if User.objects.filter(username=attrs['user.username']).exists():
                raise ValidationError('A user with that username exists')
        else:
            # This is an update
            new_username = attrs.get('user.username', obj.user.username)
            if new_username != obj.user.username:
                raise ValidationError("Can't change this field.")

        if re.match(r'^[\w.-]{4,30}$', attrs['user.username']) is None:
            raise ValidationError(
                'Usernames may only be letters, numbers, "." and "-".')

        return attrs

    def validate_display_name(self, attrs, source):
        if attrs.get('name') is None:
            attrs['name'] = attrs.get('user.username')
        return attrs

    def validate_email(self, attrs, source):
        email = attrs.get('user.email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('A user with that email address '
                                  'already exists.')
        return attrs


class ProfileFKSerializer(ProfileSerializer):

    class Meta(ProfileSerializer.Meta):
        fields = [
            'username',
            'display_name',
        ]


class ProfileViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    model = Profile
    serializer_class = ProfileSerializer
    paginate_by = 20
    # User usernames instead of ids in urls.
    lookup_field = 'user__username'
    permission_classes = [
        OnlySelfEdits,
    ]
    filter_backends = [
        filters.DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filter_fields = []
    ordering_fields = []
    # Default, if not overwritten
    ordering = ('-user__date_joined',)

    username_parts = [
        ['Big', 'Small', 'Cuddly', 'Happy'],  # adjectives
        ['Red', 'Green', 'Blue', 'Yellow'],  # colors
        ['Dog', 'Cat', 'Fox', 'Monkey'],  # animals
    ]
    number_blacklist = ['666', '69']

    # This is routed to /api/2/user/generate/
    def generate(self, request, **kwargs):
        """
        Generate a user with a random username and password.

        The method used here has a fairly low chance of collision. In
        the case that there are 3 username parts, and each part has 4
        options, and we include random numbers between 0 and 1000 on
        usernames, there are about 60K possible usernames. Using 20
        attempts to find a username means that in order for this method
        to have a 1% chance of failing, there would need to be about 50K
        users using this method already.

        Increasing the number of items in each username part category
        would make this even more favorable fairly quickly. With 5 items
        in each category, this algorithm can support almost 90K users
        before there is a 1% chance of failure.
        """
        if not (settings.STAGE or settings.DEBUG):
            raise GenericAPIException(503, 'User generation temporarily only available on stage.')

        digits = ''
        # The loop counter isn't used. This is an escape hatch.
        for i in range(20):
            # Build a name consistenting of a random choice from each of the
            # name parts lists.
            name = ''.join(map(random.choice, self.username_parts)) + digits
            # Check if it is taken yet.
            if not User.objects.filter(username=name).exists():
                break
            # Names after the first start to get numbers.
            digits = str(random.randint(0, 1000))
            if digits in self.number_blacklist:
                digits = ''
        else:
            # At this point, we just have too many users.
            return Response({"error": 'Unable to generate username.'},
                            status=500)

        password = ''.join(random.choice(letters) for _ in range(10))

        u = User.objects.create(username=name)
        u.set_password(password)
        u.save()
        p = Profile.uncached.create(user=u)
        token, _ = Token.objects.get_or_create(user=u)
        serializer = ProfileSerializer(instance=p)

        return Response({
            'user': serializer.data,
            'password': password,
            'token': token.key,
        })

    @action(methods=['POST'])
    def set_setting(self, request, user__username=None):
        data = request.DATA
        data['user'] = self.get_object().pk

        serializer = UserSettingSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            raise GenericAPIException(400, serializer.errors)

    @action(methods=['POST', 'DELETE'])
    def delete_setting(self, request, user__username=None):
        profile = self.get_object()

        if 'name' not in request.DATA:
            raise GenericAPIException(400, {'name': 'This field is required'})

        try:
            meta = (Setting.uncached
                    .get(user=profile.user, name=request.DATA['name']))
            meta.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Setting.DoesNotExist:
            raise GenericAPIException(404, {'detail': 'No matching user setting found.'})
