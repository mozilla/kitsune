from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

import pytz
from rest_framework import fields, permissions, relations, serializers
from rest_framework.exceptions import APIException
from rest_framework.filters import BaseFilterBackend
from rest_framework.fields import get_component
from tower import ugettext as _

from kitsune.sumo.utils import uselocale
from kitsune.sumo.urlresolvers import get_best_language


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
            return _(value, self.l10n_context)


class SplitSourceField(fields.WritableField):
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

    def field_to_native(self, obj, field_name):
        """
        Get a value for serialization from an object.

        This is mostly copy/paste from ``fields.Field``.

        :args obj: The object to reead the value from.
        :args field_name: The name of the field to read from obj.
        """
        if obj is None:
            return self.empty

        if self.read_source == '*':
            return self.to_native(obj)

        source = self.read_source or field_name
        value = obj

        for component in source.split('.'):
            value = get_component(value, component)
            if value is None:
                break

        return self.to_native(value)

    def field_from_native(self, data, files, field_name, into):
        """
        Update a ``field_name`` on a dictionary ``into`` with a deserialized value.

        This is mostly copy/paste from ``fields.WritableField``.

        :arg data: The serialized data to process.
        :arg files: The serialized files to process.
        :arg field_name: The name of the field to store the value on in ``into``.
        :arg into: The dictionary to update.
        """
        if self.read_only:
            return

        try:
            data = data or {}
            if self.use_files:
                files = files or {}
                try:
                    native = files[field_name]
                except KeyError:
                    native = data[field_name]
            else:
                native = data[field_name]
        except KeyError:
            if self.default is not None and not self.partial:
                # Note: partial updates shouldn't set defaults
                native = self.get_default_value()
            else:
                if self.required:
                    raise serializers.ValidationError(self.error_messages['required'])
                return

        value = self.from_native(native)
        if self.source == '*':
            if value:
                into.update(value)
        else:
            self.validate(value)
            self.run_validators(value)
            into[self.write_source or field_name] = value


class DateTimeUTCField(fields.DateTimeField):
    """
    This is like DateTimeField, except it always outputs in UTC.
    """

    def to_native(self, value):
        if value.tzinfo is None:
            default_tzinfo = pytz.timezone(settings.TIME_ZONE)
            value = default_tzinfo.localize(value)
        value = value.astimezone(pytz.utc)
        return super(DateTimeUTCField, self).to_native(value)


class _IDSerializer(serializers.Serializer):
    id = fields.Field(source='pk')

    class Meta:
        fields = ('id', )


class GenericRelatedField(relations.RelatedField):
    """
    Serializes GenericForeignKey relations using specified type of serializer.
    """

    def __init__(self, serializer_type='fk', **kwargs):
        self.serializer_type = serializer_type
        super(GenericRelatedField, self).__init__(**kwargs)

    def to_native(self, value):
        content_type = ContentType.objects.get_for_model(value)
        data = {'type': content_type.model}

        if isinstance(value, User):
            value = value.get_profile()

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

        for key, value in request.QUERY_PARAMS.items():
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
        raise NotImplemented

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


def PermissionMod(cls, permissions):
    """
    Takes a class and modifies it to conditionally hide based on permissions.
    """
    class Modded(cls):

        def __init__(self, **kwargs):
            super(Modded, self).__init__(**kwargs)
            self._stealth = False

        def field_to_native(self, obj, field_name):
            """
            Return null value if request has no access to that field
            """
            if self.check_permissions() and self.check_object_permissions(obj):
                self._stealth = False
                return super(Modded, self).field_to_native(obj, field_name)
            self._stealth = True
            return None

        # write_only is converted to a property, so that it can be "stealthed."
        # The write only field is how DRF chooses to include or not include a field
        # in serialization, so by controlling it, this field can choose when it
        # is included in serialization output.

        @property
        def write_only(self):
            return self._stealth or self._write_only

        @write_only.setter
        def write_only(self, value):
            self._write_only = value

        # These methods mimic the methods found on DRF views.

        def get_permissions(self):
            return (p() for p in permissions)

        def check_permissions(self):
            request = self.context.get('request', None)
            return all(p.has_permission(request, self) for p in self.get_permissions())

        def check_object_permissions(self, obj):
            request = self.context.get('request', None)
            return all(p.has_object_permission(request, self, obj) for p in self.get_permissions())

    return Modded
