#!/usr/bin/env python
"""
Teste rápido do sistema HooMoon - Demonstração básica
"""
import os
import sys
import requests
import json
from datetime import datetime

# Adicionar o diretório pai ao Python path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_endpoints():
    """Teste rápido dos endpoints principais"""
    print("🚀 TESTE RÁPIDO DO HOOMOON")
    print("="*40)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:8000"
    
    # Lista de endpoints para testar
    endpoints = [
        ("/api/system/health/", "Saúde do Sistema"),
        ("/api/system/config/", "Configuração do Sistema"),
        ("/api/investments/plans/", "Planos de Investimento"),
        ("/api/users/check/username/test_user/", "Verificar Username"),
        ("/api/docs/", "Documentação da API"),
    ]
    
    results = []
    
    for endpoint, description in endpoints:
        print(f"\n🔍 Testando: {description}")
        print(f"   URL: {base_url}{endpoint}")
        
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Status: {response.status_code} (OK)")
                
                # Tentar mostrar dados JSON se disponível
                try:
                    if 'application/json' in response.headers.get('content-type', ''):
                        data = response.json()
                        if isinstance(data, dict) and 'success' in data:
                            print(f"   📊 Sucesso: {data.get('success')}")
                        
                        # Mostrar dados específicos por endpoint
                        if endpoint.endswith('plans/') and 'data' in data:
                            plans_count = len(data['data']) if isinstance(data['data'], list) else 0
                            print(f"   📋 Planos encontrados: {plans_count}")
                        elif endpoint.endswith('config/') and 'data' in data:
                            system_name = data.get('data', {}).get('name', 'N/A')
                            print(f"   🏷️ Sistema: {system_name}")
                        elif endpoint.endswith('health/') and 'data' in data:
                            status_info = data.get('data', {}).get('status', 'N/A')
                            print(f"   💚 Status: {status_info}")
                            
                except json.JSONDecodeError:
                    # Para endpoints que retornam HTML (como /api/docs/)
                    if 'text/html' in response.headers.get('content-type', ''):
                        print(f"   📄 HTML retornado ({len(response.text)} chars)")
                
                results.append(True)
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   📝 Resposta: {response.text[:100]}...")
                results.append(False)
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Erro: Servidor não está rodando")
            print(f"   💡 Execute: python manage.py runserver 0.0.0.0:8000")
            results.append(False)
        except requests.exceptions.Timeout:
            print(f"   ❌ Erro: Timeout na requisição")
            results.append(False)
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            results.append(False)
    
    # Resumo
    print("\n" + "="*40)
    print("📊 RESUMO DO TESTE RÁPIDO")
    print("="*40)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passou: {passed}/{total}")
    print(f"❌ Falhou: {total-passed}/{total}")
    print(f"📈 Taxa de sucesso: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("🚀 Sistema HooMoon está funcionando!")
    elif passed > 0:
        print(f"\n⚠️ Sistema parcialmente funcional")
        print(f"🔧 {total-passed} endpoint(s) com problema")
    else:
        print(f"\n❌ Sistema não está funcionando")
        print(f"💡 Verifique se o servidor está rodando")
    
    print("\n💡 PRÓXIMOS PASSOS:")
    if passed > 0:
        print("   📚 Acesse a documentação: http://localhost:8000/api/docs/")
        print("   🔧 Acesse o admin: http://localhost:8000/admin/")
        print("   🧪 Execute testes completos: python run_all_tests.py")
    else:
        print("   🔄 Inicie o servidor: python manage.py runserver 0.0.0.0:8000")
        print("   📦 Crie dados de teste: python create_test_data.py")
    
    print("="*40)
    
    return passed == total

if __name__ == '__main__':
    try:
        success = test_basic_endpoints()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erro durante os testes: {str(e)}")
        sys.exit(1) 