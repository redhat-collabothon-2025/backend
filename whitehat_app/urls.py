from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('auth/', include('whitehat_app.auth.urls')),
    path('campaigns/', include('whitehat_app.campaigns.urls')),
    path('employees/', include('whitehat_app.employees.urls')),
    path('events/', include('whitehat_app.events.urls')),
    path('incidents/', include('whitehat_app.incidents.urls')),
    path('risks/', include('whitehat_app.risks.urls')),

]
