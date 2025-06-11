from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import HttpResponse
import csv
import json
from django.contrib.auth import get_user_model

from .models import AuditLog, SecurityEvent, DataChangeHistory, AuditSettings
from .serializers import (
    AuditLogSerializer, AuditLogSummarySerializer, SecurityEventSerializer,
    DataChangeHistorySerializer, AuditSettingsSerializer, AuditStatsSerializer,
    AuditReportSerializer, UserActivitySummarySerializer, SystemHealthSerializer
)
from .utils import AuditLogger

User = get_user_model()

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para logs de auditoria
    
    Permissions:
    - Lista e detalhes: Apenas administradores
    - Filtros disponíveis: event_type, severity, user, timestamp, module
    - Busca: description, user__username, ip_address
    """
    
    queryset = AuditLog.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['event_type', 'severity', 'user', 'module', 'content_type']
    search_fields = ['description', 'user__username', 'ip_address', 'user_agent']
    ordering_fields = ['timestamp', 'event_type', 'severity']
    ordering = ['-timestamp']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AuditLogSummarySerializer
        return AuditLogSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por data
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__lte=end_date)
            except ValueError:
                pass
        
        return queryset.select_related('user', 'content_type')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retorna estatísticas dos logs de auditoria"""
        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Estatísticas básicas
        total_events = AuditLog.objects.count()
        events_today = AuditLog.objects.filter(timestamp__date=today).count()
        events_this_week = AuditLog.objects.filter(timestamp__gte=week_ago).count()
        events_this_month = AuditLog.objects.filter(timestamp__gte=month_ago).count()
        
        # Eventos de segurança
        security_events_total = SecurityEvent.objects.count()
        security_events_unresolved = SecurityEvent.objects.filter(resolved=False).count()
        
        # Eventos por tipo
        events_by_type = dict(
            AuditLog.objects.values('event_type')
            .annotate(count=Count('id'))
            .values_list('event_type', 'count')
        )
        
        # Eventos por severidade
        events_by_severity = dict(
            AuditLog.objects.values('severity')
            .annotate(count=Count('id'))
            .values_list('severity', 'count')
        )
        
        # Eventos por usuário (top 10)
        events_by_user = dict(
            AuditLog.objects.filter(user__isnull=False)
            .values('user__username')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
            .values_list('user__username', 'count')
        )
        
        # Top usuários
        top_users = list(
            AuditLog.objects.filter(user__isnull=False)
            .values('user__username', 'user__id')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        # Top IPs
        top_ips = list(
            AuditLog.objects.filter(ip_address__isnull=False)
            .values('ip_address')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        # Eventos críticos recentes
        recent_critical_events = AuditLog.objects.filter(
            severity='CRITICAL',
            timestamp__gte=week_ago
        ).order_by('-timestamp')[:10]
        
        # Eventos de segurança recentes
        recent_security_events = SecurityEvent.objects.filter(
            timestamp__gte=week_ago
        ).order_by('-timestamp')[:10]
        
        stats_data = {
            'total_events': total_events,
            'events_today': events_today,
            'events_this_week': events_this_week,
            'events_this_month': events_this_month,
            'security_events_total': security_events_total,
            'security_events_unresolved': security_events_unresolved,
            'events_by_type': events_by_type,
            'events_by_severity': events_by_severity,
            'events_by_user': events_by_user,
            'top_users': top_users,
            'top_ips': top_ips,
            'recent_critical_events': recent_critical_events,
            'recent_security_events': recent_security_events,
        }
        
        serializer = AuditStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Gera relatório de auditoria personalizado"""
        serializer = AuditReportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        queryset = self.get_queryset()
        
        # Aplicar filtros
        queryset = queryset.filter(
            timestamp__gte=data['start_date'],
            timestamp__lte=data['end_date']
        )
        
        if data.get('event_types'):
            queryset = queryset.filter(event_type__in=data['event_types'])
        
        if data.get('users'):
            queryset = queryset.filter(user__id__in=data['users'])
        
        if data.get('severity_levels'):
            queryset = queryset.filter(severity__in=data['severity_levels'])
        
        if data.get('modules'):
            queryset = queryset.filter(module__in=data['modules'])
        
        if data.get('ip_addresses'):
            queryset = queryset.filter(ip_address__in=data['ip_addresses'])
        
        # Gerar relatório no formato solicitado
        report_format = data.get('format', 'json')
        
        if report_format == 'csv':
            return self._generate_csv_report(queryset, data['include_details'])
        elif report_format == 'json':
            return self._generate_json_report(queryset, data['include_details'])
        else:
            return Response(
                {'error': 'Formato não suportado'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _generate_csv_report(self, queryset, include_details=False):
        """Gera relatório em formato CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="audit_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Header
        headers = [
            'Data/Hora', 'Tipo de Evento', 'Severidade', 'Usuário', 
            'IP', 'Módulo', 'Descrição'
        ]
        if include_details:
            headers.extend(['Detalhes', 'Valores Anteriores', 'Novos Valores'])
        
        writer.writerow(headers)
        
        # Dados
        for log in queryset:
            row = [
                log.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
                log.get_event_type_display(),
                log.get_severity_display(),
                log.user.username if log.user else '',
                log.ip_address or '',
                log.module or '',
                log.description
            ]
            
            if include_details:
                row.extend([
                    json.dumps(log.details, indent=2) if log.details else '',
                    json.dumps(log.old_values, indent=2) if log.old_values else '',
                    json.dumps(log.new_values, indent=2) if log.new_values else ''
                ])
            
            writer.writerow(row)
        
        return response
    
    def _generate_json_report(self, queryset, include_details=False):
        """Gera relatório em formato JSON"""
        serializer_class = AuditLogSerializer if include_details else AuditLogSummarySerializer
        serializer = serializer_class(queryset, many=True)
        
        return Response({
            'report_generated_at': timezone.now(),
            'total_records': queryset.count(),
            'data': serializer.data
        })

class SecurityEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet para eventos de segurança
    
    Permissions:
    - Lista, detalhes e update: Apenas administradores
    - Create e delete: Não permitido (eventos são criados automaticamente)
    """
    
    queryset = SecurityEvent.objects.all()
    serializer_class = SecurityEventSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['event_type', 'resolved', 'user']
    search_fields = ['description', 'ip_address', 'user__username']
    ordering_fields = ['timestamp', 'event_type', 'resolved']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        return super().get_queryset().select_related('user', 'resolved_by')
    
    def create(self, request, *args, **kwargs):
        return Response(
            {'error': 'Eventos de segurança são criados automaticamente pelo sistema'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def destroy(self, request, *args, **kwargs):
        return Response(
            {'error': 'Eventos de segurança não podem ser deletados'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def update(self, request, *args, **kwargs):
        # Permitir apenas atualização dos campos de resolução
        instance = self.get_object()
        
        if 'resolved' in request.data and request.data['resolved']:
            instance.resolved = True
            instance.resolved_by = request.user
            instance.resolved_at = timezone.now()
            instance.save()
            
            # Log da resolução
            AuditLogger.log_event(
                event_type='SECURITY_EVENT',
                description=f'Evento de segurança resolvido: {instance.event_type}',
                user=request.user,
                content_object=instance,
                request=request,
                module='security'
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_resolve(self, request):
        """Resolve múltiplos eventos de segurança"""
        event_ids = request.data.get('event_ids', [])
        
        if not event_ids:
            return Response(
                {'error': 'event_ids é obrigatório'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated = SecurityEvent.objects.filter(
            id__in=event_ids,
            resolved=False
        ).update(
            resolved=True,
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        
        # Log da ação em lote
        AuditLogger.log_event(
            event_type='SECURITY_EVENT',
            description=f'Resolução em lote de {updated} eventos de segurança',
            user=request.user,
            details={'resolved_count': updated, 'event_ids': event_ids},
            request=request,
            module='security'
        )
        
        return Response({'resolved_count': updated})

class DataChangeHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para histórico de mudanças de dados"""
    
    queryset = DataChangeHistory.objects.all()
    serializer_class = DataChangeHistorySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['content_type', 'field_name', 'changed_by']
    search_fields = ['field_name', 'old_value', 'new_value']
    ordering_fields = ['timestamp', 'field_name']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        return super().get_queryset().select_related('content_type', 'changed_by', 'audit_log')

class AuditSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet para configurações de auditoria"""
    
    queryset = AuditSettings.objects.all()
    serializer_class = AuditSettingsSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_object(self):
        # Sempre retornar a configuração singleton
        return AuditSettings.get_settings()
    
    def list(self, request, *args, **kwargs):
        settings = self.get_object()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        return Response(
            {'error': 'Use PUT para atualizar as configurações'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def destroy(self, request, *args, **kwargs):
        return Response(
            {'error': 'Configurações não podem ser deletadas'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

class AuditReportsViewSet(viewsets.ViewSet):
    """ViewSet para relatórios de auditoria"""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def user_activity(self, request):
        """Relatório de atividade por usuário"""
        user_id = request.query_params.get('user_id')
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                users = [user]
            except User.DoesNotExist:
                return Response(
                    {'error': 'Usuário não encontrado'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Top 20 usuários mais ativos
            users = User.objects.filter(
                audit_logs__isnull=False
            ).annotate(
                event_count=Count('audit_logs')
            ).order_by('-event_count')[:20]
        
        activity_data = []
        
        for user in users:
            user_logs = AuditLog.objects.filter(user=user)
            
            # Estatísticas do usuário
            total_events = user_logs.count()
            last_activity = user_logs.first().timestamp if user_logs.exists() else None
            
            # Eventos por tipo
            events_by_type = dict(
                user_logs.values('event_type')
                .annotate(count=Count('id'))
                .values_list('event_type', 'count')
            )
            
            # Eventos recentes
            recent_events = user_logs.order_by('-timestamp')[:10]
            
            # Eventos de segurança
            security_events = SecurityEvent.objects.filter(user=user).count()
            failed_logins = SecurityEvent.objects.filter(
                user=user, 
                event_type='FAILED_LOGIN'
            ).count()
            
            # IPs únicos
            ip_addresses = list(
                user_logs.filter(ip_address__isnull=False)
                .values_list('ip_address', flat=True)
                .distinct()
            )
            
            # Último login (assumindo que existe um log de LOGIN)
            last_login_log = user_logs.filter(event_type='LOGIN').first()
            last_login = last_login_log.timestamp if last_login_log else None
            
            activity_data.append({
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'total_events': total_events,
                'last_activity': last_activity,
                'last_login': last_login,
                'events_by_type': events_by_type,
                'recent_events': recent_events,
                'security_events': security_events,
                'failed_logins': failed_logins,
                'ip_addresses': ip_addresses,
            })
        
        serializer = UserActivitySummarySerializer(activity_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def system_health(self, request):
        """Relatório de saúde do sistema de auditoria"""
        now = timezone.now()
        today = now.date()
        yesterday = now - timedelta(days=1)
        
        # Estatísticas básicas
        total_logs = AuditLog.objects.count()
        logs_today = AuditLog.objects.filter(timestamp__date=today).count()
        
        # Oldest and newest logs
        oldest_log = AuditLog.objects.order_by('timestamp').first()
        newest_log = AuditLog.objects.order_by('-timestamp').first()
        
        # Eventos críticos e de segurança
        critical_events_last_24h = AuditLog.objects.filter(
            severity='CRITICAL',
            timestamp__gte=yesterday
        ).count()
        
        security_events_last_24h = SecurityEvent.objects.filter(
            timestamp__gte=yesterday
        ).count()
        
        unresolved_security_events = SecurityEvent.objects.filter(
            resolved=False
        ).count()
        
        # Configurações de retenção
        settings = AuditSettings.get_settings()
        retention_cutoff = now - timedelta(days=settings.retention_days)
        old_logs_count = AuditLog.objects.filter(timestamp__lt=retention_cutoff).count()
        
        # Status geral
        alerts = []
        if unresolved_security_events > 0:
            alerts.append(f'{unresolved_security_events} eventos de segurança não resolvidos')
        
        if critical_events_last_24h > 10:
            alerts.append(f'{critical_events_last_24h} eventos críticos nas últimas 24h')
        
        if old_logs_count > 1000:
            alerts.append(f'{old_logs_count} logs antigos precisam ser arquivados')
        
        status_text = 'OK' if not alerts else 'ALERTA' if len(alerts) < 3 else 'CRÍTICO'
        
        # Métricas de performance (simuladas)
        performance_metrics = {
            'avg_response_time_ms': 150,  # Seria calculado de logs reais
            'db_size_mb': total_logs * 0.001,  # Estimativa
            'logs_per_minute': logs_today / (24 * 60) if logs_today > 0 else 0
        }
        
        health_data = {
            'status': status_text,
            'total_logs': total_logs,
            'logs_today': logs_today,
            'oldest_log': oldest_log.timestamp if oldest_log else None,
            'newest_log': newest_log.timestamp if newest_log else None,
            'disk_usage_mb': total_logs * 0.001,  # Estimativa
            'retention_policy_active': settings.retention_days > 0,
            'critical_events_last_24h': critical_events_last_24h,
            'security_events_last_24h': security_events_last_24h,
            'unresolved_security_events': unresolved_security_events,
            'performance_metrics': performance_metrics,
            'alerts': alerts
        }
        
        serializer = SystemHealthSerializer(health_data)
        return Response(serializer.data)
