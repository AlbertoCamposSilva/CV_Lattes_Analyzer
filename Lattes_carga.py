import os
os.system('cls')
print("Carregando os módulos necessários.")
from Lattes import Lattes
print('Começando a carga.')
Lattes.load_carga(
    linhas_a_pular=0,
    tempo_a_esperar_em_horário_de_pico = 0,
    de_dados_pessoais = False,
    de_carga = True,
    insere_no_bd = False,
    num_imports_skip_before_log = 100,
    show_import_messages = False,
    path = 'C:/Lattes/'
    )
