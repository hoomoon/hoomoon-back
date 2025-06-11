from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'payments'

router = DefaultRouter()
router.register('deposits', views.DepositViewSet, basename='deposit')
router.register('onchain-transactions', views.OnchainTransactionViewSet, basename='onchain-transaction')

urlpatterns = [
    path('', include(router.urls)),
    # URLs específicas para webhooks (implementar posteriormente)
    # path('webhooks/coinpayments/', views.CoinPaymentsWebhookView.as_view(), name='coinpayments-webhook'),
    # path('webhooks/connectpay/', views.ConnectPayWebhookView.as_view(), name='connectpay-webhook'),
] 