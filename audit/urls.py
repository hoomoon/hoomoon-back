from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuditLogViewSet, SecurityEventViewSet, DataChangeHistoryViewSet,
    AuditSettingsViewSet, AuditReportsViewSet
)

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='auditlog')
router.register(r'security-events', SecurityEventViewSet, basename='securityevent')
router.register(r'data-changes', DataChangeHistoryViewSet, basename='datachangehistory')
router.register(r'settings', AuditSettingsViewSet, basename='auditsettings')
router.register(r'reports', AuditReportsViewSet, basename='auditreports')

app_name = 'audit'

urlpatterns = [
    path('', include(router.urls)),
] 