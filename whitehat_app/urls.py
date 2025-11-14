from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('auth/', include('whitehat_app.auth.urls')),
    path('campaigns/', include('whitehat_app.campaigns.urls')),
    path('employees/', include('whitehat_app.employees.urls')),

]
