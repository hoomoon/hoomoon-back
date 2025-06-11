import threading
import time
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.urls import resolve
from django.utils import timezone
from .utils import AuditLogger
from .models import AuditEventType, AuditSeverity

User = get_user_model()

# Thread local storage para o usuário atual
_thread_local = threading.local()

def get_current_user():
    """Retorna o usuário atual do thread local"""
    return getattr(_thread_local, 'user', None)

def set_current_user(user):
    """Define o usuário atual no thread local"""
    _thread_local.user = user

class AuditMiddleware(MiddlewareMixin):
    """
    Middleware principal de auditoria que captura:
    - Todas as requisições HTTP
    - Usuário atual para uso em signals
    - Eventos de segurança
    - Performance de requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Processa o início da requisição"""
        # Armazenar timestamp para calcular tempo de resposta
        request._audit_start_time = time.time()
        
        # Armazenar usuário no thread local
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)
        else:
            set_current_user(None)
        
        # Detectar tentativas de ataques comuns
        self._detect_security_threats(request)
        
        return None
    
    def process_response(self, request, response):
        """Processa a resposta"""
        # Calcular tempo de resposta
        start_time = getattr(request, '_audit_start_time', None)
        if start_time:
            response_time = time.time() - start_time
            
            # Log apenas para requests importantes ou lentos
            if self._should_log_request(request, response, response_time):
                self._log_request(request, response, response_time)
        
        # Limpar thread local
        set_current_user(None)
        
        return response
    
    def process_exception(self, request, exception):
        """Processa exceções"""
        AuditLogger.log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            description=f"Exceção na requisição: {exception.__class__.__name__}: {str(exception)}",
            user=getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
            severity=AuditSeverity.HIGH,
            details={
                'exception_type': exception.__class__.__name__,
                'exception_message': str(exception),
                'path': request.path,
                'method': request.method
            },
            request=request,
            module='system'
        )
        
        return None
    
    def _should_log_request(self, request, response, response_time):
        """Determina se deve fazer log da requisição"""
        # Sempre logar requests com problemas
        if response.status_code >= 400:
            return True
        
        # Logar requests muito lentos
        if response_time > 5.0:  # mais de 5 segundos
            return True
        
        # Logar requests para endpoints críticos
        critical_paths = [
                    '/api/auth/',
        '/api/users/',
        '/api/investments/',
        '/api/payments/',
        '/api/financial/',
            '/admin/',
        ]
        
        if any(request.path.startswith(path) for path in critical_paths):
            return True
        
        # Logar requests POST, PUT, PATCH, DELETE
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return True
        
        return False
    
    def _log_request(self, request, response, response_time):
        """Registra log da requisição"""
        try:
            # Resolver view name
            try:
                resolver_match = resolve(request.path)
                view_name = resolver_match.view_name
            except:
                view_name = 'unknown'
            
            # Determinar severidade baseada no status code
            if response.status_code >= 500:
                severity = AuditSeverity.CRITICAL
            elif response.status_code >= 400:
                severity = AuditSeverity.HIGH
            elif response_time > 3.0:
                severity = AuditSeverity.MEDIUM
            else:
                severity = AuditSeverity.LOW
            
            description = f"Requisição HTTP: {request.method} {request.path} - Status: {response.status_code}"
            
            AuditLogger.log_event(
                event_type=AuditEventType.SECURITY_EVENT if response.status_code >= 400 else AuditEventType.CREATE,
                description=description,
                user=getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                severity=severity,
                details={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'view_name': view_name,
                    'content_type': response.get('Content-Type', ''),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
                },
                request=request,
                module='http'
            )
            
        except Exception as e:
            # Não falhar se o logging falhar
            pass
    
    def _detect_security_threats(self, request):
        """Detecta possíveis ameaças de segurança"""
        threats_detected = []
        
        # SQL Injection patterns
        sql_patterns = [
            'union select', 'drop table', 'insert into', 'update set',
            'delete from', 'create table', 'alter table', '--', ';--',
            'exec(', 'execute(', 'sp_', 'xp_'
        ]
        
        # XSS patterns
        xss_patterns = [
            '<script', 'javascript:', 'onload=', 'onerror=', 'onmouseover=',
            'onfocus=', 'onblur=', 'onchange=', 'onsubmit=', 'eval(',
            'alert(', 'confirm(', 'prompt('
        ]
        
        # Verificar parâmetros GET
        query_string = request.META.get('QUERY_STRING', '').lower()
        for pattern in sql_patterns:
            if pattern in query_string:
                threats_detected.append(('SQL_INJECTION', f'Pattern found in query string: {pattern}'))
                break
        
        for pattern in xss_patterns:
            if pattern in query_string:
                threats_detected.append(('XSS_ATTEMPT', f'Pattern found in query string: {pattern}'))
                break
        
        # Verificar POST data se existir
        if request.method == 'POST' and hasattr(request, 'body'):
            try:
                body = request.body.decode('utf-8', errors='ignore').lower()
                for pattern in sql_patterns:
                    if pattern in body:
                        threats_detected.append(('SQL_INJECTION', f'Pattern found in POST data: {pattern}'))
                        break
                
                for pattern in xss_patterns:
                    if pattern in body:
                        threats_detected.append(('XSS_ATTEMPT', f'Pattern found in POST data: {pattern}'))
                        break
            except:
                pass
        
        # Verificar User-Agent suspeito
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        suspicious_agents = ['sqlmap', 'nikto', 'burp', 'zap', 'nessus', 'nmap']
        for agent in suspicious_agents:
            if agent in user_agent:
                threats_detected.append(('SUSPICIOUS_ACTIVITY', f'Suspicious User-Agent: {agent}'))
                break
        
        # Verificar referer suspeito (possível CSRF)
        referer = request.META.get('HTTP_REFERER', '')
        if referer and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            from urllib.parse import urlparse
            try:
                referer_domain = urlparse(referer).netloc
                host = request.META.get('HTTP_HOST', '')
                if referer_domain and referer_domain != host:
                    threats_detected.append(('CSRF_ATTACK', f'Suspicious referer: {referer}'))
            except:
                pass
        
        # Registrar ameaças detectadas
        for threat_type, description in threats_detected:
            AuditLogger.log_security_event(
                event_type=threat_type,
                description=description,
                request=request,
                additional_data={
                    'path': request.path,
                    'method': request.method,
                    'query_string': request.META.get('QUERY_STRING', ''),
                    'referer': request.META.get('HTTP_REFERER', ''),
                }
            )

class RequestTimeMiddleware(MiddlewareMixin):
    """Middleware para medir tempo de resposta de requests"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            response_time = time.time() - request._start_time
            
            # Adicionar header com tempo de resposta
            response['X-Response-Time'] = f"{response_time:.3f}s"
            
            # Log requests muito lentos
            if response_time > 10.0:  # mais de 10 segundos
                AuditLogger.log_event(
                    event_type=AuditEventType.SECURITY_EVENT,
                    description=f"Request muito lento: {request.path} - {response_time:.2f}s",
                    user=getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                    severity=AuditSeverity.MEDIUM,
                    details={
                        'path': request.path,
                        'method': request.method,
                        'response_time': response_time,
                        'status_code': response.status_code
                    },
                    request=request,
                    module='performance'
                )
        
        return response

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware para adicionar headers de segurança"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_response(self, request, response):
        # Headers de segurança
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # CSP para APIs
        if request.path.startswith('/api/'):
            response['Content-Security-Policy'] = "default-src 'none'; script-src 'none'; object-src 'none';"
        
        return response 