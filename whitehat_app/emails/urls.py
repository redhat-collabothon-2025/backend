from django.urls import path
from . import views

urlpatterns = [
    path('send/', views.send_phishing_email, name='send_phishing_email'),
    path('bulk-send/', views.send_bulk_phishing, name='send_bulk_phishing'),
    path('click/<str:tracking_id>/', views.track_click, name='track_click'),
    path('track/<str:tracking_id>/', views.track_open, name='track_open'),
]