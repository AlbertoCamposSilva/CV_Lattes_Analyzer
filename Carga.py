from distutils.log import ERROR
import os, sys, time, zeep, pytz,  html, glob
import shutil, pandas, json, csv, psycopg2
from re import S
from tkinter import EXCEPTION

from configparser import ConfigParser
from datetime import datetime
from collections import OrderedDict
from sqlalchemy import create_engine, false
from bs4 import BeautifulSoup, Tag
from Lattes import Lattes
from Database import Database
from Indicadores import Indicadores
from Database import Database
import threading 
from functools import wraps



class Carga:
    lista_indicadores = {}
    bd_lista_ids = []
    indicadores = pandas.DataFrame()
    carga_dados_pessoais = pandas.DataFrame()

    def __init__(self,
                 path = None,
                 carga = 'C:/Users/albertos/CNPq/Lattes/Planilhas/R358737.csv',
                 show_execution_time = False,
                 ) :
        self.path = path
        self.show_execution_time = show_execution_time
        self.bd_lista_ids = None
        self.indicadores = []
        self.publicações = []
        self.palavras_chave = []
        self.carga = carga
        self.erros_anteriores = []
        self.arquivos_no_HD = []
        self.emails = None
        self.telefones = None
        self.chamada = None
        self.regiao = None
        self.nomes_citação = None
        self.nome_completo = None
        self.nacionalidade = None
        self.CPF = None
        self.data_nascimento = None
        self.sexo = None
        self.areas_do_conhecimento = [('Grande Área', 'Área', 'Sub-Área', 'Especialidade')]
        self.bd = Database('CNPq')
        self.lattes = Lattes()
        self.db = Database()


    def timing(f):
        @wraps(f)
        def wrap(*args, **kw):
            if args[0].show_execution_time: ts = datetime.now()
            result = f(*args, **kw)
            if args[0].show_execution_time:
                te = datetime.now()
                print ('func:%r took: %2.4f sec' % \
                    (f.__name__, (te-ts).total_seconds()))
            return result
        return wrap
        
    @timing
    def get_list_ids_dados_pessoais_data (self, data):
        sql = '''
            select distinct "carga_dados_pessoais".id from "carga_dados_pessoais" join "all_lattes"
            on CAST ("carga_dados_pessoais".id as BIGINT) = "all_lattes".id
            WHERE "all_lattes".dt_atualizacao > %s
            '''
        ids = self.bd.query(sql, data)
        return ids

#  .d8b.  db    db d888888b  .d88b.  .88b  d88.  .d8b.  d888888b d88888b        
# d8' `8b 88    88 `~~88~~' .8P  Y8. 88'YbdP`88 d8' `8b `~~88~~' 88'            
# 88ooo88 88    88    88    88    88 88  88  88 88ooo88    88    88ooooo        
# 88~~~88 88    88    88    88    88 88  88  88 88~~~88    88    88~~~~~        
# 88   88 88b  d88    88    `8b  d8' 88  88  88 88   88    88    88.            
# YP   YP ~Y8888P'    YP     `Y88P'  YP  YP  YP YP   YP    YP    Y88888P        
                                                                              
                                                                              
# d88888b db    db d8b   db  .o88b. d888888b d888888b  .d88b.  d8b   db .d8888. 
# 88'     88    88 888o  88 d8P  Y8 `~~88~~'   `88'   .8P  Y8. 888o  88 88'  YP 
# 88ooo   88    88 88V8o 88 8P         88       88    88    88 88V8o 88 `8bo.   
# 88~~~   88    88 88 V8o88 8b         88       88    88    88 88 V8o88   `Y8b. 
# 88      88b  d88 88  V888 Y8b  d8    88      .88.   `8b  d8' 88  V888 db   8D 
# YP      ~Y8888P' VP   V8P  `Y88P'    YP    Y888888P  `Y88P'  VP   V8P `8888Y' 

    @timing
    def get_xml_auto_source(self, id=None, pegar_data_pelos_indicadores = True):
        '''Pega o xml de um Currículo Lattes, sendo que verifica a necessidade antes.

        Será usado a seguinte ordem de prioridade:
        1. Banco de Dados Postgree
        2. Arquivo ZIP
        3. SOAP do Extrator Lattes

        Parâmetros:
        id (str): define o id do Lattes a ser pego.
        '''
        if not id == None:
            self.lattes.id = id
        if self.lattes.bd_data_atualizacao == None:
            self.lattes.get_lattes_atualizacao_bd()
            if not self.lattes.bd_data_atualizacao == None:
                if self.lattes.data_atualizacao == None:
                    self.lattes.get_atualizacao_SOAP()
                    if self.lattes.data_atualizacao == None:
                        pegar_data_pelos_indicadores = True
        if self.lattes.bd_data_atualizacao == None or self.lattes.data_atualizacao == None or (
            self.lattes.data_atualizacao > self.lattes.bd_data_atualizacao):
            self.lattes.get_zip_from_SOAP()
        else:
            print('Não é necessário atualizar o currículo.')
        if pegar_data_pelos_indicadores:
            self.lattes.data_atualizacao = self.lattes.get_atualizacao_JSON()
            print('Data de atualização do Lattes pega pelo XML: ', self.lattes.data_atualizacao)

        if self.lattes.xml == None:
            self.lattes.get_xml()


# d888888b .88b  d88. d8888b.  .d88b.  d8888b. d888888b                          
#   `88'   88'YbdP`88 88  `8D .8P  Y8. 88  `8D `~~88~~'                          
#    88    88  88  88 88oodD' 88    88 88oobY'    88                             
#    88    88  88  88 88~~~   88    88 88`8b      88                             
#   .88.   88  88  88 88      `8b  d8' 88 `88.    88                             
# Y888888P YP  YP  YP 88       `Y88P'  88   YD    YP                             
                                                                               
                                                                               
#  .d8b.  db      db           db       .d8b.  d888888b d888888b d88888b .d8888. 
# d8' `8b 88      88           88      d8' `8b `~~88~~' `~~88~~' 88'     88'  YP 
# 88ooo88 88      88           88      88ooo88    88       88    88ooooo `8bo.   
# 88~~~88 88      88           88      88~~~88    88       88    88~~~~~   `Y8b. 
# 88   88 88booo. 88booo.      88booo. 88   88    88       88    88.     db   8D 
# YP   YP Y88888P Y88888P      Y88888P YP   YP    YP       YP    Y88888P `8888Y' 

    @staticmethod
    def import_demanda_bruta_para_bd(pasta = 'C:/Users/silva/CNPq/Lattes/carga/'):
        files = os.listdir(pasta)
        files_xls = [f for f in files if f[-3:] == 'xls' or f[-4:] == 'xlsx']
        df = pandas.DataFrame()
        for f in files_xls:
            pd = pandas.read_excel(os.path.join(pasta,f), header=3)
            if f[-3:] == 'xls':
                pd['Chamada'] = f[:-4]
            elif f[-4:] == 'xlsx':
                pd['Chamada'] = f[:-5]            
            pd['id'] = None
            df = df.append(pd)
        engine = Carga.db_engine()
        df.to_sql('demanda_bruta', engine, if_exists='append', index = False)
        # query = text(f""" INSERT INTO test_db VALUES {','.join([str(i) for i in list(df0.to_records(index=False))])} ON CONFLICT ON CONSTRAINT test_db_pkey DO NOTHING""")
        # self.engine.connect().execute(query)

    @staticmethod
    def import_carga_para_bd(arquivo= 'C:/Users/silva/CNPq/Lattes/Planilhas/R358737.csv'):
        def insere_carga_no_bd(data):
            sql = '''
                INSERT INTO public."all_lattes" 
                    (id, sgl_pais, dt_atualizacao, cod_area, cod_nivel, dta_carga) 
                    VALUES
                    (%(id)s, %(sgl_pais)s, %(dt_atualizacao)s, %(cod_area)s, %(cod_nivel)s, %(dta_carga)s)
                    ON CONFLICT (id)
                    DO
                    UPDATE SET
                    id = EXCLUDED.id,
                    sgl_pais = EXCLUDED.sgl_pais,
                    dt_atualizacao = EXCLUDED.dt_atualizacao,
                    cod_area = EXCLUDED.cod_area,
                    cod_nivel = EXCLUDED.cod_nivel,
                    dta_carga = EXCLUDED.dta_carga;


                '''

            conn = None
            try:
                params = Database.config_db_connection()
                conn = psycopg2.connect(**params)
                cur = conn.cursor()
                cur.executemany(sql, data)
                conn.commit()
                cur.close()
                print("Banco de dados atualizado.")
                return("Data inserted.")
            except (Exception, psycopg2.DatabaseError) as error:
                print("Erro ao Inserir Dados PEssoais no BD: ", error)
                return (error)
            finally:
                if conn is not None:
                        conn.close()
        dados = []
        with open(arquivo, 'r') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            next(csv_reader)
            num_lines = 0
            for row in csv_reader:
                if row[0].isnumeric():
                    num_lines += 1
                    for index, r in enumerate(row):
                        if r == '': row[index] = None
                        elif r.isnumeric(): row[index] = int(r)
                        elif len(r) < 2: row[index] = None
                    data = {
                        'id': row[0],
                        'sgl_pais': row[1],
                        'dt_atualizacao': row[2],
                        'cod_area': row[3],
                        'cod_nivel': row[4],
                        'dta_carga': row[5]
                    }
                    dados.append(data)

        insere_carga_no_bd(dados)

    @staticmethod
    def importa_tabela_en_recursos_humanos_para_bd():
        file = 'D:/Lattes/rh.csv'
        dados = []
        with open(file, encoding='utf8') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            numlines = 0
            next(spamreader)
            for row in spamreader:
                #print(row)
                for k,v in enumerate(row):
                    if v == '': row[k] = None
                numlines += 1
                dado = {
                    'COD_RH': int(row[0]), 
                    'SGL_UF_CART_IDENT': row[1], 
                    'SGL_PAIS_NASC': row[2], 
                    'COD_NIVEL_FORM': row[3], 
                    'id': row[4], 
                    'CPF_RH': row[5], 
                    'NME_RH': row[6], 
                    'NME_RH_FILTRO': row[7], 
                    'TPO_NACIONALIDADE': row[8], 
                    'NRO_PASSAPORTE': row[9], 
                    'COD_SEXO': row[10], 
                    'DTA_NASC': row[11], 
                    'NME_CITACAO_BIBLIOG': row[12], 
                    'TXT_LOCAL_NASC_RH': row[13], 
                    'COD_ESTADO_CIVIL': row[14], 
                    'SGL_UF_NASC': row[15], 
                    'TXT_SITUACAO_LOCAL': row[16], 
                    'TXT_SITUACAO_CNPQ': row[17], 
                    'DTA_ENVIO_SIAFI': row[18], 
                    'TXT_USERNAME_ULT_ATUALIZ': row[19], 
                    'NME_CITACAO_BIBLIOG_FILTRO': row[20], 
                    'TPO_DOC_ATUALIZ_CURRIC': row[21], 
                    'COD_VERSAO_DOC_ATUALIZ_CURRIC': row[22], 
                    'TXT_USERNAME_APLIC_ATUALIZ': row[23], 
                    'STA_EXIBICAO_EMAIL': row[24], 
                    'DTA_FALECIMENTO': row[25], 
                    'NRO_ID_RACA_COR': row[26], 
                    'SGL_PAIS_NACIONALIDADE': row[27]
                }
                dados.append(dado)
        sql = '''
            INSERT INTO public."en_recurso_humano" 
                    (
                    COD_RH, 
                    SGL_UF_CART_IDENT, 
                    SGL_PAIS_NASC, 
                    COD_NIVEL_FORM, 
                    id, 
                    CPF_RH, 
                    NME_RH, 
                    NME_RH_FILTRO, 
                    TPO_NACIONALIDADE, 
                    NRO_PASSAPORTE, 
                    COD_SEXO, 
                    DTA_NASC, 
                    NME_CITACAO_BIBLIOG, 
                    TXT_LOCAL_NASC_RH, 
                    COD_ESTADO_CIVIL, 
                    SGL_UF_NASC, 
                    TXT_SITUACAO_LOCAL, 
                    TXT_SITUACAO_CNPQ, 
                    DTA_ENVIO_SIAFI, 
                    TXT_USERNAME_ULT_ATUALIZ, 
                    NME_CITACAO_BIBLIOG_FILTRO, 
                    TPO_DOC_ATUALIZ_CURRIC, 
                    COD_VERSAO_DOC_ATUALIZ_CURRIC, 
                    TXT_USERNAME_APLIC_ATUALIZ, 
                    STA_EXIBICAO_EMAIL, 
                    DTA_FALECIMENTO, 
                    NRO_ID_RACA_COR, 
                    SGL_PAIS_NACIONALIDADE
                    )
                VALUES
                    (
                    %(COD_RH)s, 
                    %(SGL_UF_CART_IDENT)s, 
                    %(SGL_PAIS_NASC)s, 
                    %(COD_NIVEL_FORM)s, 
                    %(id)s, 
                    %(CPF_RH)s, 
                    %(NME_RH)s, 
                    %(NME_RH_FILTRO)s, 
                    %(TPO_NACIONALIDADE)s, 
                    %(NRO_PASSAPORTE)s, 
                    %(COD_SEXO)s, 
                    %(DTA_NASC)s, 
                    %(NME_CITACAO_BIBLIOG)s, 
                    %(TXT_LOCAL_NASC_RH)s, 
                    %(COD_ESTADO_CIVIL)s, 
                    %(SGL_UF_NASC)s, 
                    %(TXT_SITUACAO_LOCAL)s, 
                    %(TXT_SITUACAO_CNPQ)s, 
                    %(DTA_ENVIO_SIAFI)s, 
                    %(TXT_USERNAME_ULT_ATUALIZ)s, 
                    %(NME_CITACAO_BIBLIOG_FILTRO)s, 
                    %(TPO_DOC_ATUALIZ_CURRIC)s, 
                    %(COD_VERSAO_DOC_ATUALIZ_CURRIC)s, 
                    %(TXT_USERNAME_APLIC_ATUALIZ)s, 
                    %(STA_EXIBICAO_EMAIL)s, 
                    %(DTA_FALECIMENTO)s, 
                    %(NRO_ID_RACA_COR)s, 
                    %(SGL_PAIS_NACIONALIDADE)s
                    )
                ON CONFLICT (COD_RH)
                DO
                UPDATE SET
                    COD_RH = EXCLUDED.COD_RH,
                    SGL_UF_CART_IDENT = EXCLUDED.SGL_UF_CART_IDENT,
                    SGL_PAIS_NASC = EXCLUDED.SGL_PAIS_NASC,
                    COD_NIVEL_FORM = EXCLUDED.COD_NIVEL_FORM,
                    id = EXCLUDED.id,
                    CPF_RH = EXCLUDED.CPF_RH,
                    NME_RH = EXCLUDED.NME_RH,
                    NME_RH_FILTRO = EXCLUDED.NME_RH_FILTRO,
                    TPO_NACIONALIDADE = EXCLUDED.TPO_NACIONALIDADE,
                    NRO_PASSAPORTE = EXCLUDED.NRO_PASSAPORTE,
                    COD_SEXO = EXCLUDED.COD_SEXO,
                    DTA_NASC = EXCLUDED.DTA_NASC,
                    NME_CITACAO_BIBLIOG = EXCLUDED.NME_CITACAO_BIBLIOG,
                    TXT_LOCAL_NASC_RH = EXCLUDED.TXT_LOCAL_NASC_RH,
                    COD_ESTADO_CIVIL = EXCLUDED.COD_ESTADO_CIVIL,
                    SGL_UF_NASC = EXCLUDED.SGL_UF_NASC,
                    TXT_SITUACAO_LOCAL = EXCLUDED.TXT_SITUACAO_LOCAL,
                    TXT_SITUACAO_CNPQ = EXCLUDED.TXT_SITUACAO_CNPQ,
                    DTA_ENVIO_SIAFI = EXCLUDED.DTA_ENVIO_SIAFI,
                    TXT_USERNAME_ULT_ATUALIZ = EXCLUDED.TXT_USERNAME_ULT_ATUALIZ,
                    NME_CITACAO_BIBLIOG_FILTRO = EXCLUDED.NME_CITACAO_BIBLIOG_FILTRO,
                    TPO_DOC_ATUALIZ_CURRIC = EXCLUDED.TPO_DOC_ATUALIZ_CURRIC,
                    COD_VERSAO_DOC_ATUALIZ_CURRIC = EXCLUDED.COD_VERSAO_DOC_ATUALIZ_CURRIC,
                    TXT_USERNAME_APLIC_ATUALIZ = EXCLUDED.TXT_USERNAME_APLIC_ATUALIZ,
                    STA_EXIBICAO_EMAIL = EXCLUDED.STA_EXIBICAO_EMAIL,
                    DTA_FALECIMENTO = EXCLUDED.DTA_FALECIMENTO,
                    NRO_ID_RACA_COR = EXCLUDED.NRO_ID_RACA_COR,
                    SGL_PAIS_NACIONALIDADE = EXCLUDED.SGL_PAIS_NACIONALIDADE;
            '''

        conn = None
        try:
            params = Database.config_db_connection()
            conn = psycopg2.connect(**params)
            cur = conn.cursor()
            cur.executemany(sql, dados)
            conn.commit()
            cur.close()
            print("Banco de dados atualizado.")
        except (Exception, psycopg2.DatabaseError) as error:
            print("Erro ao Inserir Dados PEssoais no BD: ", error)
        finally:
            if conn is not None:
                    conn.close()


    def lista_arquivos_no_HD (self, níveis=True):
        print("Pegando lista de ids já salvos no HD.")
        if níveis:
            ids_já_carregados = {}
        else:
            ids_já_carregados = []
        if níveis:
            for x0 in range(10):
                ids_já_carregados[str(x0)] ={}
                for x1 in range(10):
                    ids_já_carregados[str(x0)][str(x1)] = {}
                    for x2 in range(10):
                        ids_já_carregados[str(x0)][str(x1)][str(x2)] = {}
                        for x3 in range(10):
                            ids_já_carregados[str(x0)][str(x1)][str(x2)][str(x3)] = {}
                            for x4 in range(10):
                                ids_já_carregados[str(x0)][str(x1)][str(x2)][str(x3)][str(x4)] = []
        diretórios_lidos = 0
        for x in os.walk(self.path):
            diretórios_lidos +=1
            print(f'    {round(diretórios_lidos/1.11,1)}% completos.\r', end="", flush=True)
            for y in glob.glob(os.path.join(x[0], '*.zip')):
                id = y[-20:-4]
                if id.isnumeric():
                    try:
                        if níveis:
                            ids_já_carregados[id[0]][id[1]][id[2]][id[3]][id[4]].append(id)
                        else:
                            ids_já_carregados.append(id)
                    except:
                        print (id)
                        raise Exception
                else:
                    print (f'\n\nErro! {id} não é um número.')
        self.arquivos_no_HD = ids_já_carregados
        return ids_já_carregados
        
    @staticmethod
    def db_engine ():
        params = Database.config_db_connection()
        username = params['user']
        password = params['password']
        ipaddress = params['host']
        port = int(params['port'])
        dbname = params['database']
        return f'postgresql://{username}:{password}@{ipaddress}:{port}/{dbname}'

    @staticmethod
    def carrega_dados_pessoais (
        path = 'C:/Users/silva/CNPq/Lattes/Python/Carga/Dados Pessoais de Beneficiários',
        insert_bd = True, 
        ):
        print('Carregando tabela atual.')
        engine = Carga.db_engine()
        Carga.carga_dados_pessoais = pandas.read_sql('carga_dados_pessoais', engine)
        print('Pegando lista de arquivos para baixar:')
        files = [y for x in os.walk(path) for y in glob.glob(os.path.join(x[0], '*.xlsx'))]
        for file in files:
            print(f'Carregando arquivo: {file}')
            excel_file = pandas.ExcelFile(file)
            for x in range(len(excel_file.sheet_names)):
                if x == 0: 
                    dt = pandas.read_excel(excel_file, x, header = 4)
                    column_names = list(dt)
                else: 
                    dt = pandas.read_excel(excel_file, x, header = None, names=column_names)
                nome_arquivo = str(file).replace('\\', '/').split('/')[-1].split('.')[0]
                dt['chamada'] = nome_arquivo                
                dt.Lattes = dt.Lattes.str[-16:]
                columns = {}
                for column in dt.columns:
                    if column[:7] == 'Unnamed':
                        del dt[column]
                    else:
                        if column == 'Lattes':
                            columns['Lattes'] = 'id'
                        else:
                            columns[column] = column.lower()
                dt = dt.rename(columns = columns)
                dt.id = pandas.to_numeric(dt.id)
                Carga.carga_dados_pessoais = pandas.concat([dt,Carga.carga_dados_pessoais], ignore_index=True)
        print('Eliminando duplicatas.')
        Carga.carga_dados_pessoais = Carga.carga_dados_pessoais.drop_duplicates()
        if insert_bd:
            print('Inserindo no Banco de Dados.')
            Carga.carga_dados_pessoais.to_sql('carga_dados_pessoais', engine, if_exists='replace')
        return Carga.carga_dados_pessoais

    @staticmethod
    def atualiza_id_em_demanda_bruta ():
        SQL = '''
            update demanda_bruta set 
                id = carga_dados_pessoais.id 
            FROM carga_dados_pessoais
            WHERE lower(unaccent(demanda_bruta."Proponente")) = 
                  lower(unaccent(carga_dados_pessoais.nome))        
        '''
        try:
            params = Database.config_db_connection()
            conn = psycopg2.connect(**params)
            cur = conn.cursor()
            cur.execute(SQL)
            conn.commit()
            cur.close()
            print("Banco de dados atualizado.")
            return("IDs da Demanda Bruta atualizados")
        except (Exception, psycopg2.DatabaseError) as error:
            print("Erro ao atualizar os IDs: ", error)
            return (error)
        finally:
            if conn is not None:
                conn.close()

    
    def carrega_erros_anteriores (self, log_file = 'C:/Users/albertos/CNPq/Lattes/log.txt'):
        print('Carregando erros anteriores.')
        erros = []
        if os.path.exists(log_file):
            with open(log_file) as file:
                json_erros = json.load(file) 
            for erro in json_erros:
                if isinstance(erro, dict) or isinstance(erro, OrderedDict):
                    erros.append(erro['id'])
                elif isinstance(erro, list):
                    for err in erro:
                        erros.append(err)
            del json_erros
        self.erros_anteriores = erros
        return erros

    @staticmethod
    def show_progress(tempo_inicio, num_imports_skip_before_log, linhas_totais, linhas_lidas, num_erros):

        if linhas_lidas % num_imports_skip_before_log == 0:
            os.system('cls')
            segundos_por_linha = (datetime.now() - tempo_inicio)/num_imports_skip_before_log
            tempo_para_fim = (linhas_totais - linhas_lidas) * segundos_por_linha
            porcentagem = round(100 * (linhas_lidas/linhas_totais), 1)
            segundos_por_linha_total = (datetime.now() - tempo_inicio)/(linhas_lidas)
            acabará_em_total = (tempo_inicio + (linhas_totais - linhas_lidas) * segundos_por_linha_total).strftime("%d/%m/%Y, %H:%M:%S")
            resposta = (f'Importação iniciada em {tempo_inicio.strftime("%d/%m/%Y, %H:%M:%S")}')
            resposta += (f'\n{porcentagem}% importados.\n')
            if not segundos_por_linha_total.total_seconds() == 0:
                resposta += (f'\nLinhas por segundo lidas (total): {round(1/segundos_por_linha_total.total_seconds(), 1)}')
            resposta +=  ('\n{:,} de {:,}'.format(linhas_lidas, linhas_totais))
            resposta +=  ('\n{:,} erros.\n'.format(num_erros))
            resposta += (f'\nAcabará em:')
            resposta += (f'\n    Cálculo considerando desde o início: {acabará_em_total}\n\n')
            return resposta
        else:
            return ''


    @staticmethod
    def faz_dimensões ():
        variável = {}
        for x0 in range(10):
            variável[str(x0)] = {}
            for x1 in range(10):
                variável[str(x0)][str(x1)] = {}
                for x2 in range(10):
                    variável[str(x0)][str(x1)][str(x2)] = {}
                    for x3 in range(10):
                        variável[str(x0)][str(x1)][str(x2)][str(x3)] = {}
                        for x4 in range(10):
                            variável[str(x0)][str(x1)][str(x2)][str(x3)][str(x4)] = []
        return variável

    def carrega_lista_ids_bd (self, tabela = "indicadores", níveis = True, data=None, nível_mínimo = None):
        ids_no_bd = []
        if data == None:
            sql = f'SELECT distinct id from public."{tabela}";'
            if not nível_mínimo == None:
                sql += f'''
                join "all_lattes"
                on CAST ("{tabela}".id as BIGINT) = "all_lattes".id
                WHERE "all_lattes".cod_nivel >= {nível_mínimo}
                '''
        elif tabela=='all_lattes':
            sql = f'SELECT distinct "{tabela}".id from public."{tabela}"'
            sql += f'\nWHERE "{tabela}".dt_atualizacao > \'{data}\''
            if not nível_mínimo == None:
                sql += f' and cod_nivel >= {nível_mínimo}'
        else:
            sql = f'SELECT distinct "{tabela}".id from public."{tabela}"'
            sql += f'''
                join "all_lattes"
                on CAST ("{tabela}".id as BIGINT) = "all_lattes".id
                WHERE "all_lattes".dt_atualizacao > '{data}'
                '''
            if not nível_mínimo == None:
                sql += f' and cod_nivel >= {nível_mínimo}'

        
        bd_lista_ids = self.bd.query(sql)
        if níveis: ids_no_bd = Lattes.faz_dimensões()
        for bd_id in bd_lista_ids:
            id = str(bd_id[0])
            while len(id) < 16:
                id = '0' + id
            if níveis: 
                ids_no_bd[id[0]][id[1]][id[2]][id[3]][id[4]].append(id)
            else: 
                ids_no_bd.append(id)
        return ids_no_bd

    @staticmethod
    def move_files_temp_to_path (path = 'c:/Downloads/', temp_path = None):
        if temp_path == None:
            temp_path = path[:-1] + '_temp' + '/'
        print('Movendo arquivos do diretório temporário para o diretório permanente.')
        files = [y for x in os.walk(temp_path) for y in glob.glob(os.path.join(x[0], '*.zip'))]
        num_files = 0
        for file in files:
            shutil.move(file, file.replace('\\','/').replace(temp_path, path))
            num_files += 1
        print(f'Foram movidos {num_files} arquivos.')



    def load_carga (self,
                    carga = 'C:/Users/albertos/CNPq/Lattes/Planilhas/R358737.csv', 
                    max=-1, 
                    data_mínima_de_atualização=-1, 
                    path = 'C:/Lattes/',
                    log_file = 'C:/Users/albertos/CNPq/Lattes/log.txt',
                    linhas_a_pular = 0,
                    tempo_a_esperar_em_horário_de_pico = 0.5,
                    insere_no_bd = False,
                    temp_path = None,
                    num_imports_skip_before_log = 100,
                    show_import_messages = False,
                    pula_erros = True,
                    pula_bd_indicadores = True,
                    pula_bd_lattes = True,
                    pula_hd = False,
                    de_bd_demanda_bruta = True,
                    de_bd_carga_dados_pessoais = True,
                    de_carga_dados_pessoais = False, 
                    de_carga = True,
                    começando_com = [str(x) for x in range(10)]
                    ):
        """Salva todos os currículos Lattes np HD do computador. Pode ser chamada sem inicialização.

        Exemplo de chamamento da função:
        from Lattes import Lattes
        Lattes.load_carga()

        Parâmetros:
        carga (str): caminho completo de onde se pode achar o arquivo com a carga a ser carregada.
            O arquivo pode ser baixado no seguinte endereço: http://memoria.cnpq.br/web/portal-lattes/extracoes-de-dados
        max (int): número máximo de arquivos a importar. Se negativo serão importados todos os arquivos.

        Returns:
        nothing

        """
        print(r'''
_______  _        ______   _______  _______ _________ _______ 
(  ___  )( \      (  ___ \ (  ____ \(  ____ )\__   __/(  ___  )
| (   ) || (      | (   ) )| (    \/| (    )|   ) (   | (   ) |
| (___) || |      | (__/ / | (__    | (____)|   | |   | |   | |
|  ___  || |      |  __ (  |  __)   |     __)   | |   | |   | |
| (   ) || |      | (  \ \ | (      | (\ (      | |   | |   | |
| )   ( || (____/\| )___) )| (____/\| ) \ \__   | |   | (___) |
|/     \|(_______/|/ \___/ (_______/|/   \__/   )_(   (_______)


 _______  _______  _______  _______  _______  _______ 
(  ____ \(  ___  )(       )(  ____ )(  ___  )(  ____ \
| (    \/| (   ) || () () || (    )|| (   ) || (    \/
| |      | (___) || || || || (____)|| |   | || (_____ 
| |      |  ___  || |(_)| ||  _____)| |   | |(_____  )
| |      | (   ) || |   | || (      | |   | |      ) |
| (____/\| )   ( || )   ( || )      | (___) |/\____) |
(_______/|/     \||/     \||/       (_______)\_______)



 _____     ___    ______    _____     ___  
/  __ \   / _ \   | ___ \  |  __ \   / _ \ 
| /  \/  / /_\ \  | |_/ /  | |  \/  / /_\ \
| |      |  _  |  |    /   | | __   |  _  |
| \__/\  | | | |  | |\ \   | |_\ \  | | | |
 \____/  \_| |_/  \_| \_|   \____/  \_| |_/

        ''')


        #Inicializando Variáveis
        if temp_path == None:
            temp_path = path[:-1] + '_temp' + '/'
        erros = {}
        if data_mínima_de_atualização > 0:
            data_mínima_de_atualização = datetime.strptime(data_mínima_de_atualização, '%d/%m/%Y')
        fim=''
        linhas_totais = 0
        lista_de_ids = []
        ids_para_pular = []
        ids_para_atualizar = []
        ids_para_pular_níveis = Lattes.faz_dimensões()
        linhas_lidas = 0

        # Creating Subdirectorys, if they don't exixsts
        print('Criando diretórios temporários, se não existirem.')
        if not os.path.isdir(temp_path):
            os.makedirs(temp_path)
            #print("Created folder : ", temp_path)
        for x in range (10):
            file_path1 = os.path.join(temp_path, str(x))
            for y in range(10):
                file_path2 = os.path.join(file_path1, str(y))
                CHECK_FOLDER = os.path.isdir(file_path2)
                # If folder doesn't exist, then create it.
                if not CHECK_FOLDER:
                    os.makedirs(file_path2)
                   #print("Created folder : ", file_path2)
                else:
                    #print(file_path2, "folder already exists.")
                    pass
        
        #Listando IDs a Excluir
        if pula_erros:
            print('\nPegando lista de erros.')
            ids_para_pular.extend(self.carrega_erros_anteriores(log_file))
            num_erros = len(ids_para_pular)
        if pula_bd_indicadores:
            ids_para_pular_níveis.extend(Lattes.carrega_lista_ids_bd(tabela='indicadores', níveis=True))
        if pula_bd_lattes:
            print('\nCarregando lista de indicadores já na tabela Lattes do BD')
            ids_para_pular_níveis.extend(Lattes.carrega_lista_ids_bd(tabela='lattes', níveis=True))
        if pula_hd:
            print('Gerando lista de ids a atualizar indicadores')
            ids_para_pular_níveis.extend(Lattes.lista_arquivos_no_HD (path, níveis=True))

        #Listando IDs a Incluir
        if de_bd_demanda_bruta:
            print('\nCarregando lista de indicadores já na tabela Latdemanda_bruta do BD')
            ids_para_atualizar.extend(Lattes.carrega_lista_ids_bd(tabela='demanda_bruta', níveis=False))
        if de_bd_carga_dados_pessoais:
            print('\nCarregando lista de indicadores já na tabela Latdemanda_bruta do BD')
            ids_para_atualizar.extend(Lattes.carrega_lista_ids_bd(tabela='carga_dados_pessoais', níveis=False))
        if de_carga_dados_pessoais == True:
            print ('Carregando lista de IDs a importar pela carga de dados pessoais do Relatórios do CNPq')
            ids_para_atualizar.extend(Lattes.carrega_dados_pessoais())
        if de_carga == True:
            print ('\n\nCarregando lista de IDs a importar pela carga de ids no SOAP')
            with open(carga) as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                print('Pulando primeiras linhas.')
                while linhas_lidas <= linhas_a_pular:
                    linhas_lidas += 1
                    next(spamreader)
                print('Carregando ids a ler.')
                for row in spamreader:
                    linhas_lidas += 1
                    id = row[0]
                    if len(id) == 16:
                        data_atualizado = datetime.strptime(row[2], '%d/%m/%Y')
                        if (
                                data_mínima_de_atualização < 0 or 
                                data_atualizado >= data_mínima_de_atualização
                                ):
                            ids_para_atualizar.extend(id)
                    else:
                        print (f'Erro na linha {linhas_lidas}: {row}')

        

        print('\nRetirando ids a exluir...')
        ids_para_atualizar = [id for id in ids_para_atualizar if id not in ids_para_pular and id[0] in [str(f) for f in começando_com]]
        for k,v in enumerate(ids_para_atualizar):
            if v in ids_para_pular_níveis[v[0]][v[1]][v[2]][v[3]][v[4]]:
                del ids_para_atualizar[k]


        print('Limpando memória.')
        del ids_já_carregados
        del ids_no_bd

        print('Começando importação.')
        start_time = datetime.now()
        tempo_inicio = datetime.now()
        linhas_lidas = 0
        linhas_totais = len(lista_de_ids)
        print(f'\n\n Há {linhas_totais} arquivos a importar.\n\n')
        for id in ids_para_atualizar:
            linhas_lidas += 1
            print(f'Importando {id}. -> Salvando arquivo compactado no disco.                              \r', end="", flush=True)
            if linhas_lidas % num_imports_skip_before_log == 0:
                Lattes.move_files_temp_to_path(path)
            #os.system('cls')
            print(Lattes.show_progress(tempo_inicio, num_imports_skip_before_log, linhas_totais, linhas_lidas, num_erros))
            if not show_import_messages:
                old_stdout = sys.stdout # backup current stdout -> https://stackoverflow.com/questions/8447185/to-prevent-a-function-from-printing-in-the-batch-console-in-python
                sys.stdout = open(os.devnull, "w")
            lattes = Lattes(id = id, path = temp_path)
            resposta = lattes.get_zip_from_SOAP()
            # print(resposta, insere_no_bd, resposta == True and insere_no_bd == True)
            if resposta == "Curriculo recuperado com sucesso!" and insere_no_bd == True:
                print(f'Importando {id}. -> Inserindo no Banco de Dados.                              \r', end="", flush=True)
                lattes.get_xml()
                lattes.insert_json()
            elif not resposta == "Curriculo recuperado com sucesso!":
                erro =  {
                    'data': datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
                    'id': id,
                    'erro': resposta
                }
                erros.append(erro)
                with open(log_file, 'w') as log:
                    json.dump(erros, log, indent=4)
            if not show_import_messages:
                sys.stdout = old_stdout # reset old stdout
            horas_agora = int(datetime.now().time().strftime("%H"))
            if (tempo_a_esperar_em_horário_de_pico > 0 and
                datetime.today().weekday() < 5 and
                horas_agora >= 8 and
                horas_agora <= 18
                ):
                print(f'Importando {id}. -> Esperando para não sobrecarregar o BD do CNPq.    \r', end="", flush=True)
                time.sleep(tempo_a_esperar_em_horário_de_pico)

            if max > 0 and linhas_lidas > max:
                print ('Erros:' ,erros)
                break
        print ('Erros:' ,erros)

            
    @staticmethod
    def grava_arquivo_json (
                    max=-1,
                    path = 'C:/Downloads/',
                    log_file = 'C:/Users/albertos/CNPq/Lattes/log_save_json.txt',
                    show_import_messages = False,
                    num_imports_skip_before_log = 100):
        """Salva todos os currículos Lattes np HD do computador. Pode ser chamada sem inicialização.

        Exemplo de chamamento da função:
        from Lattes import Lattes
        Lattes.load_carga()

        Parâmetros:
        carga (str): caminho completo de onde se pode achar o arquivo com a carga a ser carregada.
            O arquivo pode ser baixado no seguinte endereço: http://memoria.cnpq.br/web/portal-lattes/extracoes-de-dados
        max (int): número máximo de arquivos a importar. Se negativo serão importados todos os arquivos.

        Returns:
        nothing

        """

        print(r'''
 _______  _        ______   _______  _______ _________ _______ 
(  ___  )( \      (  ___ \ (  ____ \(  ____ )\__   __/(  ___  )
| (   ) || (      | (   ) )| (    \/| (    )|   ) (   | (   ) |
| (___) || |      | (__/ / | (__    | (____)|   | |   | |   | |
|  ___  || |      |  __ (  |  __)   |     __)   | |   | |   | |
| (   ) || |      | (  \ \ | (      | (\ (      | |   | |   | |
| )   ( || (____/\| )___) )| (____/\| ) \ \__   | |   | (___) |
|/     \|(_______/|/ \___/ (_______/|/   \__/   )_(   (_______)


 _______  _______  _______  _______  _______  _______ 
(  ____ \(  ___  )(       )(  ____ )(  ___  )(  ____ \
| (    \/| (   ) || () () || (    )|| (   ) || (    \/
| |      | (___) || || || || (____)|| |   | || (_____ 
| |      |  ___  || |(_)| ||  _____)| |   | |(_____  )
| |      | (   ) || |   | || (      | |   | |      ) |
| (____/\| )   ( || )   ( || )      | (___) |/\____) |
(_______/|/     \||/     \||/       (_______)\_______)



   ___  _____  _____  _   _                                  ______ ______ 
  |_  |/  ___||  _  || \ | |                                 | ___ \|  _  \
    | |\ `--. | | | ||  \| |    _ __    __ _  _ __   __ _    | |_/ /| | | |
    | | `--. \| | | || . ` |   | '_ \  / _` || '__| / _` |   | ___ \| | | |
/\__/ //\__/ /\ \_/ /| |\  |   | |_) || (_| || |   | (_| |   | |_/ /| |/ / 
\____/ \____/  \___/ \_| \_/   | .__/  \__,_||_|    \__,_|   \____/ |___/  

        ''')
        erros = []
        fim=''
        linhas_lidas = 0

        print('\n\nPegando lista de arquivos zip a importar.')
        ids_em_zip = [y[y.find('Lattes_')+7:-4] for x in os.walk(path) for y in glob.glob(os.path.join(x[0], '*.zip'))]
        ids_no_bd = Lattes.carrega_lista_ids_bd(tabela='lattes', níveis=False)

        print('\nGerando lista de arquivos a transformar em JSON')

        arquivos = [id for id in ids_em_zip if id not in ids_no_bd[id[0]][id[1]][id[2]][id[3]][id[4]]]
        linhas_totais = len(arquivos)
        print("Linhas a ler: ", linhas_totais)

        print("Apagando itens desnecessários da memória")
        del ids_no_bd
        del ids_em_zip

        num_erros = len(erros)

        print('Começando importação.')
        tempo_inicio = datetime.now()
        for id in arquivos:
            linhas_lidas += 1
            os.system('cls')
            print(Lattes.show_progress(tempo_inicio, num_imports_skip_before_log, linhas_totais, linhas_lidas, num_erros))

            print(f"Importing id {id}.\r", end="", flush=True)
            try:
                if not show_import_messages:
                    old_stdout = sys.stdout # backup current stdout -> https://stackoverflow.com/questions/8447185/to-prevent-a-function-from-printing-in-the-batch-console-in-python
                    sys.stdout = open(os.devnull, "w")
                lattes = Lattes(id = id)
                lattes.path = path
                lattes.read_xml_from_zip()
                print(id + ': ' + lattes.insert_json() + '\r')
                if not show_import_messages:
                    sys.stdout = old_stdout # reset old stdout
            except EXCEPTION as e:
                erro =  {
                    'data': datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
                    'id': id,
                    'erro': str(e)
                }
                erros.append(erro)
                with open(log_file, 'w') as log:
                    json.dump(erros, log, indent=4)

            if max > 0 and linhas_lidas > max:
                break


# _________ _______  _______  _______  _______ _________
# \__   __/(       )(  ____ )(  ___  )(  ____ )\__   __/
#    ) (   | () () || (    )|| (   ) || (    )|   ) (   
#    | |   | || || || (____)|| |   | || (____)|   | |   
#    | |   | |(_)| ||  _____)| |   | ||     __)   | |   
#    | |   | |   | || (      | |   | || (\ (      | |   
# ___) (___| )   ( || )      | (___) || ) \ \__   | |   
# \_______/|/     \||/       (_______)|/   \__/   )_(   




# _________ _        ______  _________ _______  _______  ______   _______ 
# \__   __/( (    /|(  __  \ \__   __/(  ____ \(  ___  )(  __  \ (  ___  )
#    ) (   |  \  ( || (  \  )   ) (   | (    \/| (   ) || (  \  )| (   ) |
#    | |   |   \ | || |   ) |   | |   | |      | (___) || |   ) || |   | |
#    | |   | (\ \) || |   | |   | |   | |      |  ___  || |   | || |   | |
#    | |   | | \   || |   ) |   | |   | |      | (   ) || |   ) || |   | |
# ___) (___| )  \  || (__/  )___) (___| (____/\| )   ( || (__/  )| (___) |
# \_______/|/    )_)(______/ \_______/(_______/|/     \|(______/ (_______)
                                                                        
#  _______  _______  _______ 
# (  ____ )(  ____ \(  ____ \
# | (    )|| (    \/| (    \/
# | (____)|| (__    | (_____ 
# |     __)|  __)   (_____  )
# | (\ (   | (            ) |
# | ) \ \__| (____/\/\____) |
# |/   \__/(_______/\_______)

    def set_approach(a,b):
        return list(set(a)-set(b))


    def atualiza_todos_os_indicadores (self,
            path = None,
            log_file = 'd:/indicadores.log',
            max = -1,
            de_hd = False,
            de_bd_lattes = False,
            de_all_lattes = False,
            de_bd_demanda_bruta = True,
            de_carga_dados_pessoais = True,
            pula_bd_indicadores = False,
            pula_erros = False,
            data_mínima_atualização_lattes = '2020-01-01',
            show_import_messages = False,
            num_imports_skip_before_log = 10,
            começando_com = list(range(10)),
            on_conflic_update = False,
            nível_mínimo = None
            ):
        ids_para_atualizar = []
        ids_para_pular = []
        num_erros = 0

        if pula_erros:
            print('\nPegando lista de erros.')
            ids_para_pular.extend(self.carrega_erros_anteriores(log_file))
            num_erros = len(ids_para_pular)
        if pula_bd_indicadores:
            print('\nCarregando lista de Ids da tabela indicadores para pular')
            ids_para_pular.extend(self.carrega_lista_ids_bd(tabela='indicadores', níveis=False))
        if de_bd_lattes:
            print('\nCarregando lista de indicadores para importar da tabela Lattes do BD')
            ids_para_atualizar.extend(self.carrega_lista_ids_bd(tabela='lattes', níveis=False, data = data_mínima_atualização_lattes))
        if de_all_lattes:
            print('\nCarregando lista de indicadores para importar da tabela Lattes do BD')
            ids_para_atualizar.extend(self.carrega_lista_ids_bd(tabela='all_lattes', níveis=False, data = data_mínima_atualização_lattes, nível_mínimo = nível_mínimo))
        if de_bd_demanda_bruta:
            print('\nCarregando lista de indicadores para importar da tabela demanda_bruta do BD')
            ids_para_atualizar.extend(self.carrega_lista_ids_bd(tabela='demanda_bruta', níveis=False, data = data_mínima_atualização_lattes))
        if de_carga_dados_pessoais:
            print('\nCarregando lista de indicadores para importar da tabela carga_dados_pessoais do BD')
            ids_para_atualizar.extend(self.carrega_lista_ids_bd(tabela='carga_dados_pessoais', níveis=False, data = data_mínima_atualização_lattes))
        if de_hd:
            print('Carregando lista de indicadores para importar dos Lattes baixados no HD')
            ids_para_atualizar.extend(self.lista_arquivos_no_HD (path, níveis=False))

        print('\nRetirando ids a exluir...')
        ids_para_atualizar = list(set(ids_para_atualizar)-set(ids_para_pular))

        print('Iniciando Importação.')
        os.system('cls')
        tempo_inicio = datetime.now()
        num_imports_skip_before_log = 100
        linhas_totais = len(ids_para_atualizar)
        num = 0
        list_threads = []

        def atualiza_indicador (id, on_conflic_update = False):
            ind = Indicadores (id = id)
            ind.atualiza(on_conflic_update=on_conflic_update)
            del ind

        for id in ids_para_atualizar:
            if not int(id[0]) in começando_com:
                continue
            num+=1
            print(f'{num} / {linhas_totais}. Importing id {id}.\r', end="", flush=True)
            # t = threading.Thread(group=None, target=atualiza_indicador, 
            #                 name='atualiza_indicador', 
            #                 kwargs={
            #                     'id': '1600461423386842',
            #                     'on_conflic_update': True,
            #                     })
            # t.start()
            # list_threads.append(t)
            # if len(list_threads) % 10 == 0:
            #     for t in list_threads:
            #         t.join()
            #     list_threads = []
            atualiza_indicador (id, on_conflic_update = on_conflic_update)
            if num%num_imports_skip_before_log == 0:
                segundos_por_linha = (datetime.now() - tempo_inicio)/num_imports_skip_before_log
                tempo_para_fim = (linhas_totais - num) * segundos_por_linha
                porcentagem = round(100 * (num/linhas_totais), 1)
                segundos_por_linha_total = (datetime.now() - tempo_inicio)/(num)
                acabará_em_total = (tempo_inicio + (linhas_totais - num) * segundos_por_linha_total).strftime("%d/%m/%Y, %H:%M:%S")
                resposta = (f'Importação iniciada em {tempo_inicio.strftime("%d/%m/%Y, %H:%M:%S")}')
                resposta += (f'\n{porcentagem}% importados.\n')
                if not segundos_por_linha_total.total_seconds() == 0:
                    resposta += (f'\nLinhas por segundo lidas (total): {round(1/segundos_por_linha_total.total_seconds(), 1)}')
                resposta +=  ('\n{:,} de {:,}'.format(num, linhas_totais))
                resposta += (f'\nAcabará em:')
                resposta += (f'\n    Cálculo considerando desde o início: {acabará_em_total}\n\n')
                os.system('cls')
                print(resposta)