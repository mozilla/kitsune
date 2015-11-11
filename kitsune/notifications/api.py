from django.db.models import Q

import django_filters
from actstream.models import Action
from rest_framework import serializers, viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from kitsune.notifications.models import (
    PushNotificationRegistration, Notification, RealtimeRegistration)
from kitsune.sumo.api_utils import OnlyCreatorEdits, DateTimeUTCField, GenericRelatedField


class OnlyOwner(permissions.BasePermission):
    """
    Only allow objects to affected by their owner.

    TODO: This should be tied to user and object permissions better, but
    for now this is a bandaid.
    """

    def has_object_permission(self, request, view, obj):
        user = getattr(request, 'user', None)
        owner = getattr(obj, 'owner', None)
        # Only the creator can modify things.
        return user == owner


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.Field(source='is_read')
    timestamp = DateTimeUTCField(source='action.timestamp')
    actor = GenericRelatedField(source='action.actor')
    verb = serializers.CharField(source='action.verb')
    action_object = GenericRelatedField(source='action.action_object')
    target = GenericRelatedField(source='action.target')

    class Meta:
        model = PushNotificationRegistration
        fields = (
            'action_object',
            'actor',
            'id',
            'is_read',
            'target',
            'timestamp',
            'verb',
        )


class NotificationFilter(django_filters.FilterSet):
    is_read = django_filters.MethodFilter(action='filter_is_read')

    class Meta(object):
        model = Notification
        fields = [
            'is_read',
        ]

    # This has to be a method filter because ``is_read`` is not a database field
    # of ``Notification``, so BooleanFilter (and friends) don't work on it.
    def filter_is_read(self, queryset, value):
        if value in ['1', 'true', 'True', 1, True]:
            return queryset.exclude(read_at=None)
        elif value in ['0', 'false', 'False', 0, False]:
            return queryset.filter(read_at=None)
        else:
            return queryset


class NotificationViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    model = Notification
    serializer_class = NotificationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        OnlyOwner,
    ]
    filter_class = NotificationFilter
    filter_fields = ['is_read']

    def get_queryset(self, *args, **kwargs):
        qs = super(NotificationViewSet, self).get_queryset(*args, **kwargs)
        return qs.filter(owner=self.request.user)

    @action(methods=['POST'])
    def mark_read(self, request, pk=None):
        """Mark the notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST'])
    def mark_unread(self, request, pk=None):
        """Mark the notification as unread."""
        notification = self.get_object()
        notification.is_read = False
        notification.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PushNotificationRegistrationSerializer(serializers.ModelSerializer):
    # Use usernames to reference users.
    creator = serializers.SlugRelatedField(slug_field='username',
                                           required=False)

    class Meta:
        model = PushNotificationRegistration
        fields = (
            'creator',
            'id',
            'push_url',
        )

    def validate_creator(self, attrs, source):
        authed_user = getattr(self.context.get('request'), 'user')
        creator = attrs.get('creator')

        if creator is None:
            attrs['creator'] = authed_user
        elif creator != authed_user:
            raise serializers.ValidationError(
                "Can't register push notifications for another user.")

        return attrs


class PushNotificationRegistrationViewSet(mixins.CreateModelMixin,
                                          mixins.DestroyModelMixin,
                                          viewsets.GenericViewSet):
    model = PushNotificationRegistration
    serializer_class = PushNotificationRegistrationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        OnlyCreatorEdits,
    ]


class RealtimeRegistrationSerializer(serializers.ModelSerializer):
    endpoint = serializers.CharField(write_only=True)
    creator = serializers.SlugRelatedField(slug_field='username', required=False)
    content_type = serializers.SlugRelatedField(slug_field='name')

    class Meta:
        model = RealtimeRegistration
        fields = [
            'id',
            'creator',
            'created',
            'endpoint',
            'content_type',
            'object_id',
        ]

    def validate_creator(self, attrs, source):
        authed_user = getattr(self.context.get('request'), 'user')
        creator = attrs.get('creator')

        if creator is None:
            attrs['creator'] = authed_user
        elif creator != authed_user:
            raise serializers.ValidationError(
                "Can't register push notifications for another user.")

        return attrs


class RealtimeActionSerializer(serializers.ModelSerializer):
    action_object = GenericRelatedField(serializer_type='full')
    actor = GenericRelatedField(serializer_type='full')
    target = GenericRelatedField(serializer_type='full')
    verb = serializers.CharField()
    timestamp = DateTimeUTCField()

    class Meta:
        model = PushNotificationRegistration
        fields = (
            'action_object',
            'actor',
            'id',
            'target',
            'timestamp',
            'verb',
        )


class RealtimeRegistrationViewSet(mixins.CreateModelMixin,
                                  mixins.DestroyModelMixin,
                                  viewsets.GenericViewSet):
    model = RealtimeRegistration
    serializer_class = RealtimeRegistrationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        OnlyCreatorEdits,
    ]

    @action(methods=['GET'])
    def updates(self, request, pk=None):
        """Get all the actions that correspond to this registration."""
        reg = self.get_object()

        query = Q(actor_content_type=reg.content_type, actor_object_id=reg.object_id)
        query |= Q(target_content_type=reg.content_type, target_object_id=reg.object_id)
        query |= Q(action_object_content_type=reg.content_type,
                   action_object_object_id=reg.object_id)

        actions = Action.objects.filter(query)
        serializer = RealtimeActionSerializer(actions, many=True)

        return Response(serializer.data)
