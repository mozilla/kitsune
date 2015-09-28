import random
import re
from datetime import datetime, timedelta
from string import letters

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from django.core.exceptions import ValidationError
from django.db.models import Q, Count
from django.utils.http import int_to_base36
from django.views.decorators.http import require_GET

import waffle
from statsd import statsd
from tower import ugettext_lazy as _

from rest_framework import viewsets, serializers, mixins, filters, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.authtoken.models import Token

from kitsune.access.decorators import login_required
from kitsune.questions.models import Answer
from kitsune.questions.utils import num_answers, num_solutions, num_questions
from kitsune.sumo import email_utils
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
            obj, created = self.Meta.model.objects.get_or_create(
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
    email = (PermissionMod(serializers.EmailField, permissions=[OnlySelf])
             (source='user.email', required=True))
    settings = (PermissionMod(UserSettingSerializer, permissions=[OnlySelf])
                (many=True, read_only=True))
    helpfulness = serializers.Field(source='answer_helpfulness')
    answer_count = serializers.SerializerMethodField('get_answer_count')
    question_count = serializers.SerializerMethodField('get_question_count')
    solution_count = serializers.SerializerMethodField('get_solution_count')
    last_answer_date = serializers.SerializerMethodField('get_last_answer_date')
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
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
            'mozillians',
            'irc_handle',
            'timezone',
            'country',
            'city',
            'locale',
            'email',
            'settings',
            'helpfulness',
            'question_count',
            'answer_count',
            'solution_count',
            'last_answer_date',
            # Password and email are here so they can be involved in write
            # operations. They is marked as write-only above, so will not be
            # visible.
            'password',
            'is_active',
        ]

    def get_avatar_url(self, profile):
        request = self.context.get('request')
        size = request.REQUEST.get('avatar_size', 48) if request else 48
        return profile_avatar(profile.user, size=size)

    def get_question_count(self, profile):
        return num_questions(profile.user)

    def get_answer_count(self, profile):
        return num_answers(profile.user)

    def get_solution_count(self, profile):
        return num_solutions(profile.user)

    def get_last_answer_date(self, profile):
        last_answer = profile.user.answers.order_by('-created').first()
        return last_answer.created if last_answer else None

    def save_object(self, obj, **kwargs):
        """It is universally a bad idea to force_insert=True on this object. So don't."""
        kwargs.pop('force_insert', None)
        return super(ProfileSerializer, self).save_object(obj, **kwargs)

    def restore_object(self, attrs, instance=None):
        """
        Override the default behavior to make a user if one doesn't exist.

        This user may not be saved here, but will be saved if/when the .save()
        method of the serializer is called.
        """
        instance = (super(ProfileSerializer, self)
                    .restore_object(attrs, instance))
        if instance.user_id is None:
            # This is a bit of cheat. The user shouldn't be saved yet, but
            # ``create_inactive_user`` saves it, so their isn't much of a choice.
            u = RegistrationProfile.objects.create_inactive_user(
                attrs['user.username'],
                attrs['user.password'],
                attrs['user.email'])
            instance.user_id = u.id
            instance.save()
        return instance

    def validate_username(self, attrs, source):
        obj = self.object
        if obj is None:
            # This is a create
            if User.objects.filter(username=attrs['user.username']).exists():
                raise ValidationError(_('A user with that username exists'))
        else:
            # This is an update
            new_username = attrs.get('user.username', obj.user.username)
            if new_username != obj.user.username:
                raise ValidationError(_("Can't change this field."))

        if re.match(r'^[\w.-]{4,30}$', attrs['user.username']) is None:
            raise ValidationError(
                _('Usernames may only be letters, numbers, "." and "-".'))

        return attrs

    def validate_display_name(self, attrs, source):
        if attrs.get('name') is None:
            attrs['name'] = attrs.get('user.username')
        return attrs

    def validate_email(self, attrs, source):
        email = attrs.get('user.email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError(_('A user with that email address already exists.'))
        return attrs


class ProfileFKSerializer(ProfileSerializer):

    class Meta(ProfileSerializer.Meta):
        fields = [
            'username',
            'display_name',
            'avatar',
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

    number_blacklist = [666, 69]

    # This is routed to /api/2/user/generate/
    def generate(self, request, **kwargs):
        """
        Generate a user with a random username and password.
        """
        # The loop counter isn't used. This is an escape hatch.
        for __ in range(10):
            # Generate a user of the form "buddy#"
            digits = random.randint(100, 10000)
            if digits in self.number_blacklist:
                continue
            username = 'buddy{}'.format(digits)
            # Check if it is taken yet.
            if not User.objects.filter(username=username).exists():
                break
        else:
            # At this point, we just have too many users.
            return Response({"error": _('Unable to generate username.')},
                            status=500)

        password = ''.join(random.choice(letters) for __ in range(10))
        # Capitalize the 'b' in 'buddy'
        display_name = 'B' + username[1:]

        u = User.objects.create(username=username)
        u.set_password(password)
        u.settings.create(name='autogenerated', value='true')
        u.save()
        p = Profile.objects.create(user=u, name=display_name)

        # This simulates the user being logged in, for purposes of exposing
        # fields in the serializer below.
        request.user = u
        token, __ = Token.objects.get_or_create(user=u)
        serializer = ProfileSerializer(instance=p, context={'request': request})

        return Response({
            'user': serializer.data,
            'password': password,
            'token': token.key,
        })

    # This is routed to /api/2/user/weekly-solutions/
    def weekly_solutions(self, request, **kwargs):
        """
        Return the most helpful users in the past week.
        """
        start = datetime.now() - timedelta(days=7)
        # Get a list of users and the number of solutions they have in the last week.
        # It looks like [{'creator__username': 'bob', 'creator__count': 12}, ...]
        # This uses ``username`` instead of ``id``, because ``username`` appears
        # in the output of ``ProfileFKSerializer``, whereas ``id`` does not.
        raw_counts = (
            Answer.objects
            .exclude(solution_for=None)
            .filter(created__gt=start)
            .values('creator__username')
            .annotate(Count('creator'))
            )

        # Turn that list into a dictionary from username -> count.
        username_to_count = {u['creator__username']: u['creator__count'] for u in raw_counts}

        # Get all the profiles mentioned in the above.
        profiles = Profile.objects.filter(user__username__in=username_to_count.keys())
        result = ProfileFKSerializer(instance=profiles, many=True).data

        # Pair up the profiles and the solution counts.
        for u in result:
            u['weekly_solutions'] = username_to_count[u['username']]

        # Return the top 10.
        result.sort(key=lambda u: u['weekly_solutions'], reverse=True)
        return Response(result[:10])

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
            raise GenericAPIException(400, {'name': _('This field is required')})

        try:
            meta = (Setting.objects
                    .get(user=profile.user, name=request.DATA['name']))
            meta.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Setting.DoesNotExist:
            raise GenericAPIException(404, {'detail': _('No matching user setting found.')})

    @action(methods=['GET'])
    def request_password_reset(self, request, user__username=None):
        profile = self.get_object()

        current_site = get_current_site(request)
        site_name = current_site.name
        domain = current_site.domain

        c = {
            'email': profile.user.email,
            'domain': domain,
            'site_name': site_name,
            'uid': int_to_base36(profile.user.id),
            'user': profile.user,
            'token': default_token_generator.make_token(profile.user),
            'protocol': 'https' if request.is_secure() else 'http',
        }

        subject = email_utils.render_email('users/email/pw_reset_subject.ltxt', c)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())

        @email_utils.safe_translation
        def _make_mail(locale):
            mail = email_utils.make_mail(
                subject=subject,
                text_template='users/email/pw_reset.ltxt',
                html_template='users/email/pw_reset.html',
                context_vars=c,
                from_email=None,
                to_email=profile.user.email)

            return mail

        email_utils.send_messages([_make_mail(profile.locale)])

        return Response('', status=204)
