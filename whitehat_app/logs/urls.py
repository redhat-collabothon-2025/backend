from rest_framework.routers import DefaultRouter
from django.urls import path, include
from whitehat_app.logs.views import LogViewSet

router = DefaultRouter()
router.register(r'', LogViewSet, basename='log')

urlpatterns = [
    path('', include(router.urls)),
]
