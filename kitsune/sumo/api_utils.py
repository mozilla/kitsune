from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.utils.timezone import localtime
from django.utils.translation import pgettext

import pytz
from rest_framework import fields, permissions, serializers
from rest_framework.authentication import SessionAuthentication, CSRFCheck
from rest_framework.exceptions import APIException, AuthenticationFailed
from rest_framework.filters import BaseFilterBackend
from rest_framework.renderers import JSONRenderer as DRFJSONRenderer

from kitsune.sumo.utils import uselocale
from kitsune.sumo.urlresolvers import get_best_language
from kitsune.users.models import Profile


class GenericAPIException(APIException):
    """Generic Exception, since DRF doesn't provide one.

    DRF allows views to throw subclasses of APIException to cause non-200
    status codes to be sent back to API consumers. These subclasses are
    expected to have a ``status_code`` and ``detail`` property.

    DRF doesn't give a generic way to make an object with these properties.
    Instead you are expected to make many specific subclasses and make
    instances of those. That seemed lame, so this class creates instances
    instead of lots of subclasses.
    """
    def __init__(self, status_code, detail, **kwargs):
        self.status_code = status_code
        self.detail = detail
        for key, val in kwargs.items():
            setattr(self, key, val)


class LocaleNegotiationMixin(object):
    """A mixin for CBV to select a locale based on Accept-Language headers."""

    def get_locale(self):
        accept_language = self.request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        lang = get_best_language(accept_language)
        return lang or settings.WIKI_DEFAULT_LANGUAGE

    def get_serializer_context(self):
        context = super(LocaleNegotiationMixin, self).get_serializer_context()
        context['locale'] = self.get_locale()
        return context


class LocalizedCharField(fields.CharField):
    """
    This is a field for DRF that localizes itself based on the current locale.

    There should be a locale field on the serialization context. If the view
    that uses this serializer subclasses LocaleNegotiationMixin, the context
    will get a locale field automatically.

    A serializer can use this field like this:

        class FooSerializer(serializers.ModelSerializer):
            title = LocalizedCharField(source='title',
                                       l10n_context='DB: bar.Foo.title')
            class Meta:
                model = Foo
                fields = ('id', 'title')

    :args l10n_context: Set the localization context, mainly for fields that
        come from the DB.
    """
    type_name = 'LocalizedCharField'
    type_label = 'string'
    form_field_class = forms.CharField
    read_only = True

    def __init__(self, l10n_context=None, **kwargs):
        self.l10n_context = l10n_context
        super(LocalizedCharField, self).__init__(**kwargs)

    def to_native(self, value):
        value = super(LocalizedCharField, self).from_native(value)
        locale = self.context.get('locale')

        if locale is None:
            return value
        with uselocale(locale):
            return pgettext(self.l10n_context, value)


class SplitSourceField(fields.Field):
    """
    This allows reading from one field and writing to another under the same
    name in the serialized/deserialized data.

    A serializer can use this field like this:

        class FooSerializer(serializers.ModelSerializer):
            content = SplitSourceField(read_source='content_parsed', write_source='content')

            class Meta:
                model = Foo
                fields = ('id', 'content')

    The normal field parameter ``source`` is no longer allowed. Instead use
    ``read_source`` and ``write_source``.

    :args read_source: The field to read from for serialization.
    :args write_source: The field to write to for deserialization.
    """
    type_name = 'SplitSourceField'
    read_only = False

    def __init__(self, write_source=None, read_source=None, source=None, **kwargs):
        if source is not None:
            raise ValueError("Use read_source and write_source with SplitSourceField.")
        self.read_source = read_source
        self.write_source = write_source
        super(SplitSourceField, self).__init__(**kwargs)

    def get_value(self, dictionary):
        """
        Given the *incoming* primitive data, return the value for this field
        that should be validated and transformed to a native value.
        """
        # NB: This doesn't support reading from HTML input, unlike normal fields.
        return dictionary.get(self.write_source, fields.empty)

    def get_attribute(self, instance):
        """
        Given the *outgoing* object instance, return the primitive value
        that should be used for this field.
        """
        # NB: This is a lot less robust than the DRF original, but it
        # should be fine for our purposes.
        return getattr(instance, self.read_source)

    def to_representation(self, obj):
        return obj

    def to_internal_value(self, data):
        return data


class DateTimeUTCField(fields.DateTimeField):
    """
    This is like DateTimeField, except it outputs in UTC by default.
    """

    def default_timezone(self):
        return pytz.utc

    def to_representation(self, value):
        tz = pytz.timezone(settings.TIME_ZONE)
        val = localtime(tz.localize(value), pytz.UTC)
        return super(DateTimeUTCField, self).to_representation(val)


class _IDSerializer(serializers.Serializer):
    id = fields.Field(source='pk')

    class Meta:
        fields = ('id', )


class GenericRelatedField(fields.ReadOnlyField):
    """
    Serializes GenericForeignKey relations using specified type of serializer.
    """

    def __init__(self, serializer_type='fk', **kwargs):
        self.serializer_type = serializer_type
        super(GenericRelatedField, self).__init__(**kwargs)

    def to_representation(self, value):
        content_type = ContentType.objects.get_for_model(value)
        data = {'type': content_type.model}

        if isinstance(value, User):
            value = Profile.objects.get(user=value)

        if hasattr(value, 'get_serializer'):
            SerializerClass = value.get_serializer(self.serializer_type)
        else:
            SerializerClass = _IDSerializer
        data.update(SerializerClass(instance=value).data)

        return data


class InequalityFilterBackend(BaseFilterBackend):
    """A filter backend that allows for field__gt style filtering."""

    def filter_queryset(self, request, queryset, view):
        filter_fields = getattr(view, 'filter_fields', [])

        for key, value in request.query_params.items():
            splits = key.split('__')
            if len(splits) != 2:
                continue
            field, opname = splits
            if field not in filter_fields:
                continue
            op = getattr(self, 'op_' + opname, None)
            if op:
                queryset = op(queryset, field, value)

        return queryset

    def op_gt(self, queryset, key, value):
        arg = {key + '__gt': value}
        return queryset.filter(**arg)

    def op_lt(self, queryset, key, value):
        arg = {key + '__lt': value}
        return queryset.filter(**arg)

    def op_gte(self, queryset, key, value):
        arg = {key + '__gte': value}
        return queryset.filter(**arg)

    def op_lte(self, queryset, key, value):
        arg = {key + '__lte': value}
        return queryset.filter(**arg)


class GenericDjangoPermission(permissions.BasePermission):

    @property
    def permissions(self):
        raise NotImplementedError

    def has_permission(self, request, view):
        u = request.user
        not_inactive = u.is_anonymous() or u.is_active
        return not_inactive and all(u.has_perm(p) for p in self.permissions)


class OnlyCreatorEdits(permissions.BasePermission):
    """
    Only allow objects to be edited and deleted by their creators.

    TODO: This should be tied to user and object permissions better, but
    for now this is a bandaid.
    """

    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS is a list containing all the read-only methods.
        if request.method in permissions.SAFE_METHODS:
            return True
        # If flow gets here, the method will modify something.
        user = getattr(request, 'user', None)
        creator = getattr(obj, 'creator', None)
        # Only the creator can modify things.
        return user == creator


PermissionListSerializer = None


def PermissionMod(field, permissions):
    """
    Takes a class and modifies it to conditionally hide based on permissions.
    """

    class Modded(field):
        @classmethod
        def many_init(cls, *args, **kwargs):
            kwargs['child'] = field()
            return PermissionMod(serializers.ListSerializer, permissions)(*args, **kwargs)

        def get_attribute(self, instance):
            if self.check_permissions(instance):
                return super(Modded, self).get_attribute(instance)
            else:
                raise fields.SkipField()

        def check_permissions(self, obj):
            request = self.context.get('request')
            for Perm in permissions:
                perm = Perm()
                if not perm.has_permission(request, self):
                    return False
                if not perm.has_object_permission(request, self, obj):
                    return False
            return True

    return Modded


class InactiveSessionAuthentication(SessionAuthentication):
    """
    Use Django's session framework for authentication.

    Allows inactive users.
    """

    def authenticate(self, request):
        """
        Returns a `User` if the request session currently has a logged in user.
        Otherwise returns `None`.
        """

        # Get the underlying HttpRequest object
        request = request._request
        user = getattr(request, 'user', None)

        # Unauthenticated, CSRF validation not required
        if not user or user.is_anonymous():
            return None

        self.enforce_csrf(request)

        # CSRF passed with authenticated user
        return (user, None)

    def enforce_csrf(self, request):
        """
        Enforce CSRF validation for session based authentication.
        """
        reason = CSRFCheck().process_view(request, None, (), {})
        if reason:
            # CSRF failed, bail with explicit error message
            raise AuthenticationFailed('CSRF Failed: %s' % reason)


class ImageUrlField(fields.ImageField):
    """An image field that serializes to a url instead of a file name.

    Additionally, if there is no file associated with this image, this
    returns ``None`` instead of erroring.
    """

    def to_native(self, value):
        try:
            return value.url
        except ValueError:
            return None


class JSONRenderer(DRFJSONRenderer):

    def render(self, data, accepted_media_type=None, renderer_context=None):
        json = super(JSONRenderer, self).render(data, accepted_media_type, renderer_context)

        # In HTML (such as in <script> tags), "</" is an illegal sequence in a
        # <script> tag. In JSON, "\/" is a legal representation of the "/"
        # character. Replacing "</" with "<\/" is compatible with both the
        # HTML and JSON specs.
        #
        # HTML spec: http://www.w3.org/TR/REC-html32-19970114#script
        # JSON spec: http://json.org/

        return json.replace('</', '<\\/')
