"""
URLs para sistema de referrals
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'referrals'

router = DefaultRouter()
router.register('programs', views.ReferralProgramViewSet, basename='referral-program')
router.register('links', views.ReferralLinkViewSet, basename='referral-link')
router.register('referrals', views.ReferralViewSet, basename='referral')
router.register('earnings', views.ReferralEarningViewSet, basename='referral-earning')

urlpatterns = [
    path('', include(router.urls)),
] 