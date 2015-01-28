from rest_framework import routers

from kitsune.notifications import api

router = routers.SimpleRouter()
router.register(r'pushnotification', api.PushNotificationRegistrationViewSet)
router.register(r'notification', api.NotificationViewSet)
urlpatterns = router.urls
