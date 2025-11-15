from django.urls import path, include, re_path
from whitehat_app.minio_proxy import views as minio_views

urlpatterns = [
    path('auth/', include('whitehat_app.auth.urls')),
    path('users/', include('whitehat_app.users.urls')),
    path('campaigns/', include('whitehat_app.campaigns.urls')),
    path('employees/', include('whitehat_app.employees.urls')),
    path('events/', include('whitehat_app.events.urls')),
    path('incidents/', include('whitehat_app.incidents.urls')),
    path('risks/', include('whitehat_app.risks.urls')),
    path('phishing/', include('whitehat_app.emails.urls')),
    path('logs/', include('whitehat_app.logs.urls')),
    path('agent/', include('whitehat_app.agent.urls')),
    re_path(r'^minio/(?P<bucket>[^/]+)/(?P<object_name>.+)$', minio_views.minio_proxy),
]
