# config/urls.py
from django.contrib import admin
from django.urls import path, include
# Temporariamente comentado para migração
# from api.views import (
#     RegisterView,
#     CookieTokenObtainPairView,
#     CookieTokenRefreshView,
#     LogoutView,
#     UserProfileView,
# )
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth via cookies (temporariamente desabilitado para migração)
    # path('api/register/', RegisterView.as_view(), name='auth_register'),
    # path('api/token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    # path('api/logout/', LogoutView.as_view(), name='auth_logout'),
    # path('api/me/', UserProfileView.as_view(), name='user_profile'),

    # Core system endpoints
    path('api/system/', include('core.urls')),

    # API - URLs modulares (arquitetura atual)
    path('api/users/', include('users.urls')),
    path('api/investments/', include('investments.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/financial/', include('financial.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/referrals/', include('referrals.urls')),
    path('api/audit/', include('audit.urls')),

    # Documentação da API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
