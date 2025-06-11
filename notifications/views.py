"""
Views para sistema de notificações
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.utils import APIResponseHandler
from core.permissions import IsOwnerOrReadOnly
from .models import NotificationTemplate, Notification, NotificationPreference
from .serializers import (
    NotificationTemplateSerializer, NotificationSerializer, 
    NotificationCreateSerializer, NotificationPreferenceSerializer,
    NotificationSummarySerializer, NotificationBulkActionSerializer
)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para notificações do usuário
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Retorna apenas notificações do usuário logado"""
        return Notification.objects.filter(
            user=self.request.user
        ).select_related('template').order_by('-created_at')
    
    @extend_schema(
        summary="Lista notificações do usuário",
        description="Retorna todas as notificações do usuário autenticado",
        parameters=[
            OpenApiParameter(
                name='unread_only',
                description='Filtrar apenas notificações não lidas',
                required=False,
                type=bool
            ),
            OpenApiParameter(
                name='type',
                description='Filtrar por tipo de notificação',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='channel',
                description='Filtrar por canal de notificação',
                required=False,
                type=str
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Filtros opcionais
        unread_only = request.query_params.get('unread_only', '').lower() == 'true'
        notification_type = request.query_params.get('type')
        channel = request.query_params.get('channel')
        
        if unread_only:
            queryset = queryset.filter(read_at__isnull=True)
        
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        if channel:
            queryset = queryset.filter(channel=channel)
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return APIResponseHandler.success(data=serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Marca uma notificação como lida"""
        notification = self.get_object()
        
        if notification.is_read():
            return APIResponseHandler.error(
                message="Notificação já foi lida"
            )
        
        notification.mark_as_read()
        
        return APIResponseHandler.success(
            data=self.get_serializer(notification).data,
            message="Notificação marcada como lida"
        )
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Marca todas as notificações como lidas"""
        unread_notifications = self.get_queryset().filter(read_at__isnull=True)
        count = 0
        
        for notification in unread_notifications:
            notification.mark_as_read()
            count += 1
        
        return APIResponseHandler.success(
            data={'marked_count': count},
            message=f"{count} notificações marcadas como lidas"
        )
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Executa ações em lote nas notificações"""
        serializer = NotificationBulkActionSerializer(data=request.data)
        
        if serializer.is_valid():
            notification_ids = serializer.validated_data['notification_ids']
            action = serializer.validated_data['action']
            
            # Filtrar apenas notificações do usuário logado
            notifications = self.get_queryset().filter(id__in=notification_ids)
            count = 0
            
            if action == 'mark_read':
                for notification in notifications.filter(read_at__isnull=True):
                    notification.mark_as_read()
                    count += 1
                message = f"{count} notificações marcadas como lidas"
                
            elif action == 'mark_unread':
                for notification in notifications.filter(read_at__isnull=False):
                    notification.read_at = None
                    notification.notification_status = 'DELIVERED'
                    notification.save(update_fields=['read_at', 'notification_status'])
                    count += 1
                message = f"{count} notificações marcadas como não lidas"
                
            elif action == 'delete':
                count = notifications.count()
                notifications.delete()
                message = f"{count} notificações excluídas"
            
            return APIResponseHandler.success(
                data={'affected_count': count},
                message=message
            )
        
        return APIResponseHandler.error(
            message="Dados inválidos",
            errors=serializer.errors
        )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Resumo das notificações do usuário"""
        user = request.user
        notifications = self.get_queryset()
        
        # Filtros de tempo
        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        
        # Contadores básicos
        total_notifications = notifications.count()
        unread_notifications = notifications.filter(read_at__isnull=True).count()
        notifications_today = notifications.filter(created_at__gte=today).count()
        notifications_this_week = notifications.filter(created_at__gte=week_ago).count()
        
        # Contadores por tipo
        by_type = {}
        for notification_type, _ in NotificationTemplate.NOTIFICATION_TYPES:
            type_count = notifications.filter(notification_type=notification_type).count()
            if type_count > 0:
                by_type[notification_type] = type_count
        
        # Contadores por canal
        by_channel = {}
        for channel, _ in NotificationTemplate.CHANNEL_TYPES:
            channel_count = notifications.filter(channel=channel).count()
            if channel_count > 0:
                by_channel[channel] = channel_count
        
        # Contadores por status
        by_status = {}
        for status_code, _ in Notification.STATUS_CHOICES:
            status_count = notifications.filter(notification_status=status_code).count()
            if status_count > 0:
                by_status[status_code] = status_count
        
        # Notificações recentes
        recent_notifications = notifications[:5]
        
        summary_data = {
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'notifications_today': notifications_today,
            'notifications_this_week': notifications_this_week,
            'by_type': by_type,
            'by_channel': by_channel,
            'by_status': by_status,
            'recent_notifications': self.get_serializer(recent_notifications, many=True).data
        }
        
        return APIResponseHandler.success(
            data=summary_data,
            message="Resumo de notificações carregado com sucesso"
        )
    
    @action(detail=False, methods=['delete'])
    def clear_read(self, request):
        """Remove todas as notificações lidas"""
        read_notifications = self.get_queryset().filter(read_at__isnull=False)
        count = read_notifications.count()
        read_notifications.delete()
        
        return APIResponseHandler.success(
            data={'deleted_count': count},
            message=f"{count} notificações lidas foram removidas"
        )


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para preferências de notificação
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retorna apenas preferências do usuário logado"""
        return NotificationPreference.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Retorna ou cria preferências do usuário"""
        preference, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference
    
    @extend_schema(
        summary="Obter preferências de notificação",
        description="Retorna as preferências de notificação do usuário autenticado"
    )
    def retrieve(self, request, *args, **kwargs):
        """Retorna preferências do usuário (sempre pk=me)"""
        preference = self.get_object()
        serializer = self.get_serializer(preference)
        return APIResponseHandler.success(data=serializer.data)
    
    @extend_schema(
        summary="Atualizar preferências de notificação",
        description="Atualiza as preferências de notificação do usuário autenticado"
    )
    def update(self, request, *args, **kwargs):
        """Atualiza preferências do usuário"""
        preference = self.get_object()
        serializer = self.get_serializer(preference, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return APIResponseHandler.success(
                data=serializer.data,
                message="Preferências atualizadas com sucesso"
            )
        
        return APIResponseHandler.error(
            message="Erro na validação",
            errors=serializer.errors
        )
    
    @action(detail=False, methods=['post'])
    def reset_to_default(self, request):
        """Redefine preferências para o padrão"""
        preference = self.get_object()
        
        # Valores padrão
        preference.email_enabled = True
        preference.sms_enabled = False
        preference.push_enabled = True
        preference.in_app_enabled = True
        preference.notification_types = {}
        preference.quiet_hours_start = None
        preference.quiet_hours_end = None
        preference.digest_frequency = 'IMMEDIATE'
        preference.save()
        
        return APIResponseHandler.success(
            data=self.get_serializer(preference).data,
            message="Preferências redefinidas para o padrão"
        )


class NotificationTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para templates de notificação (admin only)
    """
    queryset = NotificationTemplate.objects.filter(status=True).order_by('notification_type', 'channel')
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @extend_schema(
        summary="Lista templates de notificação",
        description="Retorna todos os templates de notificação disponíveis (admin only)"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Retorna templates agrupados por tipo"""
        templates = self.get_queryset()
        
        grouped_templates = {}
        for template in templates:
            type_key = template.notification_type
            if type_key not in grouped_templates:
                grouped_templates[type_key] = []
            grouped_templates[type_key].append(
                self.get_serializer(template).data
            )
        
        return APIResponseHandler.success(
            data=grouped_templates,
            message="Templates agrupados por tipo"
        )
