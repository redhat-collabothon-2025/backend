from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.overview, name='risk-overview'),
    path('distribution/', views.distribution, name='risk-distribution'),
    path('trending/', views.trending, name='risk-trending'),
    path('heatmap/', views.heatmap, name='risk-heatmap'),
]