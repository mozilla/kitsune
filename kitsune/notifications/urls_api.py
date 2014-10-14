from rest_framework import routers

from kitsune.notifications.api import PushNotificationRegistrationViewSet

router = routers.SimpleRouter()
router.register(r'pushnotification', PushNotificationRegistrationViewSet)
urlpatterns = router.urls
