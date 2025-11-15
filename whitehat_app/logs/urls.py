from django.urls import path, include
from rest_framework.routers import DefaultRouter
from whitehat_app.logs.views import LogViewSet

router = DefaultRouter()
router.register('', LogViewSet, basename='log')

urlpatterns = router.urls
