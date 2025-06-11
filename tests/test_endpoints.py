#!/usr/bin/env python
"""
Script para testar endpoints do app investments
"""
import os
import sys
import django
import requests

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_endpoints():
    """
    Testa endpoints básicos do sistema
    """
    base_url = "http://localhost:8000"
    
    endpoints = [
        "/api/system/health/",
        "/api/system/config/", 
                    "/api/investments/plans/",
    ]
    
    print("🔍 Testando endpoints do HooMoon...")
    
    for endpoint in endpoints:
        url = base_url + endpoint
        try:
            response = requests.get(url, timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {endpoint} - Status: {response.status_code}")
            
            if response.status_code == 200 and endpoint.endswith("health/"):
                print(f"   Resposta: {response.json()}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Erro: {e}")
    
    print("\n🎯 Teste concluído!")

if __name__ == '__main__':
    test_endpoints() 