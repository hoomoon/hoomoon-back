# api/management/commands/import_users.py

import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import User # Seu modelo User

# Define o número de espaços por nível de indentação no arquivo TXT
SPACES_PER_INDENT_LEVEL = 4

class Command(BaseCommand):
    help = 'Importa usuários de arquivos CSV (detalhes) e um arquivo TXT (hierarquia) para o banco de dados.'

    def add_arguments(self, parser):
        parser.add_argument('hierarchy_txt_file', type=str, help='O caminho para o arquivo TXT contendo a hierarquia de logins.')
        parser.add_argument('csv_files_path', nargs='+', type=str, help='O(s) caminho(s) para o(s) arquivo(s) CSV ou um diretório contendo os arquivos CSV com os detalhes dos usuários.')

    def _get_column_mapping(self, csv_fieldnames_from_file):
        """
        Mapeia nomes lógicos de colunas para os nomes reais encontrados no cabeçalho do CSV.
        Isso lida com sufixos como '(Click to sort Ascending)'.
        """
        # Nomes lógicos que o script usa internamente e os prefixos que esperamos encontrar
        # nos cabeçalhos dos arquivos CSV.
        # Note que para 'País', esperamos encontrar um cabeçalho que comece com 'PaÃs'.
        logical_names_to_csv_prefixes = {
            'Login': 'Login',
            'Nome': 'Nome',
            'Email': 'Email',
            'País': 'País'  # Chave lógica é 'País', mas procuramos o prefixo 'PaÃs' no CSV
        }
        
        actual_column_map = {} # Mapeia nome lógico para nome real encontrado no CSV
        missing_prefixes = []  # Armazena prefixos que não foram encontrados

        for logical_name, prefix_to_find in logical_names_to_csv_prefixes.items():
            found_actual_name_in_csv = None
            for header_in_csv_file in csv_fieldnames_from_file:
                if header_in_csv_file.startswith(prefix_to_find):
                    found_actual_name_in_csv = header_in_csv_file
                    break # Encontrou o cabeçalho correspondente
            
            if found_actual_name_in_csv:
                actual_column_map[logical_name] = found_actual_name_in_csv
            else:
                missing_prefixes.append(prefix_to_find) # Adiciona o prefixo que não foi encontrado
        
        return actual_column_map, missing_prefixes

    def _load_user_details_from_csvs(self, csv_paths):
        user_details_map = {}
        actual_csv_files = []

        # Coleta todos os caminhos de arquivos CSV, expandindo diretórios
        for path_arg in csv_paths:
            if os.path.isdir(path_arg):
                for filename in os.listdir(path_arg):
                    if filename.lower().endswith('.csv'):
                        actual_csv_files.append(os.path.join(path_arg, filename))
            elif os.path.isfile(path_arg) and path_arg.lower().endswith('.csv'):
                actual_csv_files.append(path_arg)
            else:
                self.stdout.write(self.style.WARNING(f'Caminho CSV ignorado (não é arquivo CSV nem diretório válido): {path_arg}'))
        
        if not actual_csv_files:
            raise CommandError('Nenhum arquivo CSV válido encontrado nos caminhos fornecidos.')

        # Processa cada arquivo CSV encontrado
        for csv_file_path in actual_csv_files:
            try:
                with open(csv_file_path, mode='r', encoding='utf-8-sig') as file: # utf-8-sig para BOM
                    reader = csv.DictReader(file)
                    if not reader.fieldnames: # Verifica se o CSV tem cabeçalho
                        self.stderr.write(self.style.ERROR(f'Arquivo CSV "{csv_file_path}" está vazio ou não tem cabeçalho. Pulando arquivo.'))
                        continue

                    # Obtém o mapeamento das colunas lógicas para as colunas reais do CSV
                    column_map, missing_cols_prefixes = self._get_column_mapping(reader.fieldnames)

                    if missing_cols_prefixes: # Se faltarem colunas essenciais
                        self.stderr.write(self.style.ERROR(f'Arquivo CSV "{csv_file_path}" não contém colunas começando com: {", ".join(missing_cols_prefixes)}. Pulando arquivo.'))
                        continue
                    
                    # Itera sobre as linhas do CSV
                    for row_number, row_data in enumerate(reader, 1):
                        # Usa os nomes mapeados para obter os dados das colunas corretas
                        login = row_data.get(column_map['Login'], '').strip()
                        if not login:
                            self.stdout.write(self.style.WARNING(f'Linha {row_number} sem valor na coluna "{column_map["Login"]}" no arquivo {csv_file_path}. Pulando.'))
                            continue
                        
                        user_details_map[login] = {
                            'name': row_data.get(column_map['Nome'], '').strip(),
                            'email': row_data.get(column_map['Email'], '').strip() or None,
                            'country': row_data.get(column_map['País'], '').strip() # Usa a chave lógica 'País'
                        }
                self.stdout.write(self.style.SUCCESS(f'Detalhes de usuários carregados de: {csv_file_path}'))
            except FileNotFoundError:
                self.stderr.write(self.style.ERROR(f'Arquivo CSV "{csv_file_path}" não encontrado.'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Erro ao ler o arquivo CSV "{csv_file_path}": {e}'))
        
        if not user_details_map: # Se nenhum dado foi carregado após processar todos os CSVs
            raise CommandError('Nenhum detalhe de usuário foi carregado dos arquivos CSV.')
            
        return user_details_map

    @transaction.atomic
    def handle(self, *args, **options):
        hierarchy_txt_file = options['hierarchy_txt_file']
        csv_files_paths = options['csv_files_path']

        self.stdout.write(self.style.SUCCESS('Iniciando importação de usuários...'))

        # 1. Carregar detalhes dos CSVs
        try:
            user_details_from_csvs = self._load_user_details_from_csvs(csv_files_paths)
            self.stdout.write(self.style.SUCCESS(f'{len(user_details_from_csvs)} registros de detalhes de usuários carregados dos CSVs.'))
        except CommandError as e: # Erro específico do nosso carregamento
            self.stderr.write(self.style.ERROR(f'Erro ao carregar dados CSV: {e}'))
            return
        except Exception as e: # Outros erros inesperados
            self.stderr.write(self.style.ERROR(f'Erro inesperado ao carregar dados CSV: {e}'))
            import traceback
            traceback.print_exc()
            return

        # 2. Processar hierarquia e criar usuários
        created_users_count = 0
        parents_stack = []  # Pilha para manter os pais atuais em cada nível

        try:
            with open(hierarchy_txt_file, mode='r', encoding='utf-8') as file:
                for line_number, raw_line in enumerate(file, 1):
                    line_content_for_login = raw_line.rstrip('\n\r')
                    if not line_content_for_login.strip(): # Pula linhas vazias
                        continue

                    # Calcula o nível pela indentação de espaços
                    leading_spaces = len(line_content_for_login) - len(line_content_for_login.lstrip(' '))
                    current_level = 0
                    if SPACES_PER_INDENT_LEVEL > 0:
                        current_level = leading_spaces // SPACES_PER_INDENT_LEVEL
                    
                    if SPACES_PER_INDENT_LEVEL > 0 and leading_spaces % SPACES_PER_INDENT_LEVEL != 0:
                        self.stdout.write(self.style.WARNING(f'Linha {line_number} ("{line_content_for_login.strip()}") no TXT tem indentação inconsistente ({leading_spaces} espaços). Tratando como nível {current_level}.'))

                    login_from_txt = line_content_for_login.lstrip(' ').strip() # Obtém o login

                    if not login_from_txt:
                        self.stdout.write(self.style.WARNING(f'Linha {line_number} no TXT sem login após remover espaços. Pulando.'))
                        continue

                    # Busca detalhes do usuário
                    details = user_details_from_csvs.get(login_from_txt)
                    if not details:
                        self.stdout.write(self.style.WARNING(f'Login "{login_from_txt}" (linha {line_number} do TXT) não encontrado nos arquivos CSV. Pulando usuário.'))
                        continue
                    
                    # Verifica se o usuário já existe
                    if User.objects.filter(username=login_from_txt).exists():
                        self.stdout.write(self.style.NOTICE(f'Usuário "{login_from_txt}" já existe. Pulando criação, mas ajustando pilha de pais.'))
                        try:
                            user_obj = User.objects.get(username=login_from_txt)
                            parents_stack = parents_stack[:current_level] # Ajusta a pilha para o nível atual
                            parents_stack.append(user_obj)
                        except User.DoesNotExist:
                             self.stderr.write(self.style.ERROR(f'Inconsistência: Usuário "{login_from_txt}" reportado como existente mas não encontrado no get().'))
                        continue

                    # Determina o sponsor (pai)
                    sponsor_obj = None
                    if current_level > 0: # Se não for um usuário raiz
                        if len(parents_stack) >= current_level:
                            sponsor_obj = parents_stack[current_level - 1] # O pai está no nível anterior da pilha
                        else:
                            self.stderr.write(self.style.ERROR(f'Hierarquia inconsistente para "{login_from_txt}" (nível {current_level}). Pai esperado não encontrado na pilha (tamanho da pilha: {len(parents_stack)}). Pulando usuário.'))
                            continue
                    
                    # Cria o usuário
                    try:
                        user_name = details.get('name')
                        if not user_name: # Fallback se o nome estiver vazio no CSV
                             self.stdout.write(self.style.WARNING(f'Login "{login_from_txt}" não possui "Nome" nos dados CSV. Usando o próprio login como nome.'))
                             user_name = login_from_txt
                        
                        # Geração da senha dinâmica
                        password = f"Hoo.{login_from_txt}@temp"

                        user = User.objects.create_user(
                            username=login_from_txt,
                            name=user_name,
                            email=details.get('email'),
                            password=password
                        )
                        user.country = details.get('country', '') # Adiciona país
                        
                        if sponsor_obj: # Define o sponsor se houver
                            user.sponsor = sponsor_obj
                        
                        user.save() 
                        created_users_count += 1

                        # Atualiza a pilha de pais
                        parents_stack = parents_stack[:current_level] # Remove pais de níveis mais profundos
                        parents_stack.append(user) # Adiciona usuário atual à pilha no seu nível
                        
                        if created_users_count > 0 and created_users_count % 50 == 0: # Feedback a cada 50 usuários
                            self.stdout.write(self.style.SUCCESS(f'{created_users_count} usuários criados...'))

                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f'Erro ao criar usuário "{login_from_txt}" (linha {line_number} TXT): {e}'))
                        import traceback
                        traceback.print_exc()

        except FileNotFoundError:
            raise CommandError(f'Arquivo de hierarquia TXT "{hierarchy_txt_file}" não encontrado.')
        except Exception as e: # Erro genérico no processamento da hierarquia
            self.stderr.write(self.style.ERROR(f'Um erro crítico ocorreu durante o processamento da hierarquia: {e}'))
            import traceback
            traceback.print_exc()
            raise CommandError(f'Importação falhou. Veja os logs de erro. Erro: {e}')

        # Feedback final
        if created_users_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Importação concluída! Total de {created_users_count} usuários criados.'))
        else:
            self.stdout.write(self.style.WARNING('Importação concluída, mas nenhum usuário novo foi criado. Verifique os logs e os arquivos de entrada.'))