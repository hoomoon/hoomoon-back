# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, DepositViewSet, MyNetworkView, sponsor_by_code

router = DefaultRouter()
router.register(r'plans', PlanViewSet, basename='plan')
router.register(r'deposits', DepositViewSet, basename='deposit')

urlpatterns = [
    path('', include(router.urls)),
    path('minha-rede/', MyNetworkView.as_view(), name='minha-rede'),
    path('sponsor/<str:code>/', sponsor_by_code),
]
