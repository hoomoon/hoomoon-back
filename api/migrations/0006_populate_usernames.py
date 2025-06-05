# api/migrations/0006_populate_usernames.py
from django.db import migrations
import uuid
import re
import random
import string

def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))

def generate_unique_username(user_instance, UserHistorical):
    """
    Tenta gerar um username único. Usa base do email/ID. Se colidir,
    usa uma base curta + alfanumérico aleatório de 8 dígitos.
    """
    user_email = getattr(user_instance, 'email', None)
    username_base = None

    if user_email:
        local_part = user_email.split('@')[0].lower()
        username_base = re.sub(r'[^a-z0-9]', '', local_part)
        if not username_base or len(username_base) < 3:
            username_base = f"user{user_instance.id}"
    else:
        username_base = f"user{user_instance.id}"

    # Limita o tamanho da base inicial
    username_base = username_base[:20] 

    username_candidate = username_base
    
    # Verifica se a sugestão inicial já existe para OUTRO usuário
    if not username_candidate or UserHistorical.objects.filter(username=username_candidate).exclude(pk=user_instance.pk).exists():
        # Se existe ou a base é vazia, parte para a geração com sufixo aleatório
        prefix = username_base[:10] if len(username_base) > 3 else "u" # Usa um prefixo curto
        
        loop_count = 0 # Para evitar loop infinito em caso extremo
        while True:
            loop_count +=1
            random_suffix = get_random_alphanumeric_string(8) # Gera 8 dígitos alfanuméricos
            username_candidate = f"{prefix}_{random_suffix}"
            
            # Garante que não excede o max_length do username (150 para AbstractUser)
            if len(username_candidate) > 150:
                username_candidate = username_candidate[:150]

            if not UserHistorical.objects.filter(username=username_candidate).exclude(pk=user_instance.pk).exists():
                break # Encontrou um username único
            
            if loop_count > 50: # Limite de segurança muito alto, improvável de atingir
                username_candidate = f"user_{uuid.uuid4().hex[:25]}" # Fallback ultra-seguro
                # Se este ainda colidir, há algo muito estranho.
                # Para simplicidade, vamos assumir que este será único.
                if UserHistorical.objects.filter(username=username_candidate).exclude(pk=user_instance.pk).exists():
                     username_candidate = f"user_{uuid.uuid4().hex[:25]}" # Tenta de novo
                break 
    
    return username_candidate

# A função populate_usernames_for_existing_users permanece a mesma da mensagem anterior,
# pois a lógica de quando atualizar e chamar generate_unique_username está correta.
# Apenas a própria generate_unique_username foi aprimorada.

def populate_usernames_for_existing_users(apps, schema_editor):
    UserHistorical = apps.get_model('api', 'User')
    
    users_to_update = []

    for user_obj in UserHistorical.objects.all():
        current_username = getattr(user_obj, 'username', None)
        # O username no AbstractUser pode ser uma string vazia por padrão em algumas criações antigas
        # ou se foi explicitamente definido como tal antes de unique=True ser aplicado consistentemente.
        # Também pode ser None se o campo foi adicionado como null=True na migração 0005.

        user_email_for_log = getattr(user_obj, 'email', '[sem email]')
        
        needs_new_username = False
        reason = ""

        # Se não há username ou é uma string vazia
        if not current_username: # Cobre None e string vazia ''
            needs_new_username = True
            reason = "username vazio ou nulo"
        # Se o username atual já existe para OUTRO usuário
        elif UserHistorical.objects.filter(username=current_username).exclude(pk=user_obj.pk).exists():
            needs_new_username = True
            reason = f"username '{current_username}' duplicado, gerando novo"
        # Opcional: Se quiser forçar a regeneração de usernames que são iguais ao email
        elif current_username == user_email_for_log and user_email_for_log != '[sem email]':
             needs_new_username = True
             reason = f"username '{current_username}' é igual ao email, padronizando"


        if needs_new_username:
            new_username = generate_unique_username(user_obj, UserHistorical)
            # Só atualiza se o novo username for de facto diferente do atual (ou se o atual era None/vazio)
            if new_username != current_username:
                print(f"  Atualizando username para ID {user_obj.id} ({user_email_for_log}). Razão: {reason}. De: '{current_username}' -> Para: '{new_username}'")
                user_obj.username = new_username
                users_to_update.append(user_obj)
        # else:
        #    print(f"  Username para ID {user_obj.id} ('{current_username}') está OK e único.")

    if users_to_update:
        # O Django >= 3.2 suporta update_fields em bulk_update, mas UserHistorical.objects.bulk_update não existe.
        # Salvar individualmente é mais seguro e simples para migrações de dados.
        for user_to_save in users_to_update:
            user_to_save.save(update_fields=['username'])
    else:
        print("  Nenhum username precisou de atualização.")


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_user_username_alter_user_email'), # Mantenha a sua dependência correta aqui
    ]

    operations = [
        migrations.RunPython(populate_usernames_for_existing_users),
    ]