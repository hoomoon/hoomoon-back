# config/urls.py
from django.contrib import admin
from django.urls import path, include
from api.views import (
    RegisterView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    LogoutView,
    UserProfileView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth via cookies
    path('api/register/', RegisterView.as_view(), name='auth_register'),
    path('api/token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('api/logout/', LogoutView.as_view(), name='auth_logout'),
    path('api/me/', UserProfileView.as_view(), name='user_profile'),

    # Demais endpoints da app api
    path('api/', include('api.urls')),
]
