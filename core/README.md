# App Core - Funcionalidades Base

O app `core` é a base do sistema modular de investimentos. Ele contém todas as funcionalidades reutilizáveis que podem ser utilizadas por outros apps.

## Estrutura do App

```
core/
├── models.py          # Modelos abstratos e FeatureFlagModel
├── views.py           # Views base (SystemConfigView, HealthCheckView)
├── utils.py           # Utilitários (APIResponseHandler, FeatureToggle, etc.)
├── middleware.py      # Middlewares customizados
├── permissions.py     # Permissões reutilizáveis
├── admin.py          # Admin para FeatureFlags
├── urls.py           # URLs do core
└── apps.py           # Configuração do app
```

## Principais Funcionalidades

### 1. Sistema de Respostas Padronizadas (APIResponseHandler)

```python
from core.utils import APIResponseHandler

# Resposta de sucesso
return APIResponseHandler.success(
    data={"user": "john"},
    message="Usuário obtido com sucesso"
)

# Resposta de erro
return APIResponseHandler.error(
    message="Usuário não encontrado",
    error_code="USER_NOT_FOUND",
    status_code=404
)

# Resposta paginada
return APIResponseHandler.paginated(
    data=users_data,
    page=1,
    total_pages=5,
    total_items=50,
    page_size=10
)
```

### 2. Sistema de Feature Flags (FeatureToggle)

```python
from core.utils import FeatureToggle

# Verificar se uma feature está habilitada
if FeatureToggle.is_enabled('REFERRAL_SYSTEM'):
    # Código para sistema de referência
    pass

# Decorator para views que precisam de uma feature
@FeatureToggle.require_feature('PIX_PAYMENTS')
def pix_payment_view(request):
    pass
```

### 3. Configurações Dinâmicas do Sistema (SystemConfig)

```python
from core.utils import SystemConfig

# Obter informações do sistema
system_info = SystemConfig.get_system_info()

# Obter métodos de pagamento habilitados
payment_methods = SystemConfig.get_payment_methods()

# Obter prefixo para códigos de indicação
prefix = SystemConfig.get_referral_code_prefix()
```

### 4. Modelos Abstratos Reutilizáveis

```python
from core.models import TimestampedModel, StatusModelMixin, MoneyFieldMixin

class MinhaTransacao(TimestampedModel, MoneyFieldMixin, StatusModelMixin):
    # Herda automaticamente:
    # - created_at, updated_at (TimestampedModel)
    # - amount (MoneyFieldMixin)
    # - status (StatusModelMixin)
    description = models.CharField(max_length=200)
```

### 5. Permissões Customizadas

```python
from core.permissions import IsOwnerOrReadOnly, RequireFeature, IsAdminOrOwner

class MinhaViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    # Ou usar decorator
    @require_feature('ADVANCED_FEATURES')
    def advanced_action(self, request):
        pass
```

### 6. Middlewares

#### DynamicHeadersMiddleware
Adiciona headers automáticos com informações do sistema:
```http
X-System-Name: Investment Platform
X-System-Version: 1.0.0
X-Features-Enabled: REFERRAL_SYSTEM,PIX_PAYMENTS
X-Default-Currency: USD
X-API-Version: v2
```

#### FeatureToggleMiddleware
Bloqueia automaticamente acesso a endpoints de funcionalidades desabilitadas.

#### RequestLoggingMiddleware
Log detalhado de requests da API em modo debug.

## Endpoints Disponíveis

### Configuração do Sistema
```http
GET /api/system/config/
```
Retorna todas as configurações que o frontend precisa para se adaptar.

### Health Check
```http
GET /api/system/health/
```
Endpoint para verificar a saúde do sistema.

## Feature Flags no Banco de Dados

O modelo `FeatureFlagModel` permite controlar features via admin do Django:

```python
# Via admin ou programaticamente
feature = FeatureFlagModel.objects.create(
    name='NEW_FEATURE',
    description='Nova funcionalidade experimental',
    is_enabled=True
)
```

## Como Usar em Outros Apps

### 1. Importar Utilitários
```python
from core.utils import APIResponseHandler, FeatureToggle
from core.permissions import IsOwnerOrReadOnly
from core.models import TimestampedModel
```

### 2. Herdar de Modelos Base
```python
from core.models import TimestampedModel, StatusModelMixin

class MeuModelo(TimestampedModel, StatusModelMixin):
    nome = models.CharField(max_length=100)
```

### 3. Usar Permissões
```python
from core.permissions import IsAdminOrOwner

class MinhaView(APIView):
    permission_classes = [IsAdminOrOwner]
```

### 4. Verificar Features
```python
from core.utils import FeatureToggle

def minha_funcao():
    if FeatureToggle.is_enabled('MINHA_FEATURE'):
        # Fazer algo
        pass
```

## Configurações Necessárias

No `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'core',  # Deve vir antes de outros apps customizados
    # ...
]

# Configurações do sistema
SYSTEM_NAME = 'Meu Sistema'
FEATURES = {
    'REFERRAL_SYSTEM': True,
    'PIX_PAYMENTS': True,
}
BUSINESS_RULES = {
    'MIN_DEPOSIT_AMOUNT': 10.00,
}
```

## Benefícios

1. **Padronização**: Todas as APIs seguem o mesmo formato de resposta
2. **Flexibilidade**: Features podem ser ligadas/desligadas facilmente
3. **Reutilização**: Modelos e permissões podem ser reutilizados
4. **Manutenibilidade**: Código centralizado em um local
5. **Escalabilidade**: Base sólida para novos apps

## Próximos Passos

Com o app `core` pronto, podemos agora:

1. Criar app `users` para gestão de usuários
2. Criar app `investments` para lógica de investimentos  
3. Criar app `payments` para processamento de pagamentos
4. Migrar gradualmente funcionalidades do app `api`

O `core` fornece a base sólida para que todos os outros apps sejam consistentes e reutilizáveis. 