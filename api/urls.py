# api/urls.py
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, DepositViewSet

router = DefaultRouter()
router.register(r'plans', PlanViewSet, basename='plan')
router.register(r'deposits', DepositViewSet, basename='deposit')

urlpatterns = router.urls
