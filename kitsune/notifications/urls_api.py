from rest_framework import routers

from kitsune.notifications.api import NotificationViewSet

router = routers.SimpleRouter()
router.register(r'notification', NotificationViewSet)
urlpatterns = router.urls
