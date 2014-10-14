from django.core.exceptions import ValidationError
from rest_framework import serializers, viewsets, permissions, mixins

from kitsune.notifications.models import PushNotificationRegistration
from kitsune.sumo.api import CORSMixin, OnlyCreatorEdits


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


class PushNotificationRegistrationViewSet(CORSMixin,
                                          mixins.CreateModelMixin,
                                          mixins.DestroyModelMixin,
                                          viewsets.GenericViewSet):
    model = PushNotificationRegistration
    serializer_class = PushNotificationRegistrationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        # Here "edit" means "delete"
        OnlyCreatorEdits,
    ]
