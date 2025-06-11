"""
URLs para sistema de notificações
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'notifications'

router = DefaultRouter()
router.register('notifications', views.NotificationViewSet, basename='notification')
router.register('preferences', views.NotificationPreferenceViewSet, basename='notification-preference')
router.register('templates', views.NotificationTemplateViewSet, basename='notification-template')

urlpatterns = [
    path('', include(router.urls)),
] 