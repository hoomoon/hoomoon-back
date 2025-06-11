"""
URLs para o app de usuários
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Criar router para ViewSets
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'activities', views.UserActivityViewSet, basename='user-activity')
# O endpoint de notifications foi migrado para o app notifications

app_name = 'users'

urlpatterns = [
    # URLs para autenticação
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', views.UserLoginView.as_view(), name='login'),
    path('auth/logout/', views.UserLogoutView.as_view(), name='logout'),
    path('auth/refresh/', views.RefreshTokenView.as_view(), name='refresh-token'),
    
    # URLs para verificação de disponibilidade
    path('check/username/<str:username>/', views.CheckUsernameView.as_view(), name='check-username'),
    path('check/email/<str:email>/', views.CheckEmailView.as_view(), name='check-email'),
    
    # URL para buscar patrocinador
    path('sponsor/<str:code>/', views.SponsorByCodeView.as_view(), name='sponsor-by-code'),
    
    # Incluir URLs do router
    path('', include(router.urls)),
] 