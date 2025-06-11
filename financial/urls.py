# financial/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'financial'

router = DefaultRouter()
router.register('earnings', views.EarningViewSet, basename='earning')
router.register('reports', views.FinancialReportViewSet, basename='financial-report')

urlpatterns = [
    path('', include(router.urls)),
    # URLs específicas para relatórios (implementar posteriormente)
    # path('dashboard/', views.FinancialDashboardView.as_view(), name='dashboard'),
    # path('user-balance/<int:user_id>/', views.UserBalanceView.as_view(), name='user-balance'),
] 