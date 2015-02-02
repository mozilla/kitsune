from rest_framework import serializers, viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from kitsune.notifications.models import PushNotificationRegistration, Notification
from kitsune.sumo.api import OnlyCreatorEdits, DateTimeUTCField, GenericRelatedField


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
            'is_read',
            # 'read_at',
            'timestamp',
            'actor',
            'verb',
            'action_object',
            'target'
        )


class NotificationViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    model = Notification
    serializer_class = NotificationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        OnlyOwner,
    ]

    def get_queryset(self, *args, **kwargs):
        return self.model.objects.filter(owner=self.request.user)

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
