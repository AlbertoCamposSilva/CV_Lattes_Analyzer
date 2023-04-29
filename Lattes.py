from distutils.log import ERROR
import os, time, zeep, pytz, socket, html
import xmltodict, json
from zipfile import ZipFile
import io
import pathlib
from datetime import datetime
from collections import OrderedDict
from bs4 import BeautifulSoup, Tag

from Database import Database

class Lattes:

    def __init__ (self, 
                id = '1600461423386842',
                wsdl = 'http://servicosweb.cnpq.br/srvcurriculo/WSCurriculo?wsdl',
                auto_save_json_to_bd = True,
                path = None):
        self.id = id
        self.auto_save_json_to_bd = auto_save_json_to_bd
        self.update_errors_on_bd = False
        self.nome = None
        self.CPF = None
        self.data_nascimento = None
        self.wsdl = wsdl
        self.bd = Database('CNPq')
        self.path = path
        self.ocorrencia = None
        self.zip = None
        self.xml = None
        self.soup = None
        self.json = None
        self.dt_atualizacao = None
        self.bd_dt_atualizacao = None
        self.palavras_chave = []
        self.dados_gerais = ({
            'id': self.id,
            'nome': None,
            'cpf': None,
            'email': None,
            'telefone': None,
            'sexo': None,
            'regiao': None,
            'nomes_citacao': None,
            'dt_atualizacao': None, 
            'nacionalidade': None, 
            'pais_nascimento': None, 
            'uf_nascimento': None, 
            'cidade_nascimento': None, 
            'data_nascimento': None,
            'data_falecimento': None,
            'sigla_pais_nacionalidade': None, 
            'raca_cor': None, 
            'orcid': None, 
            'codigo_instituicao_empresa':None,
            'nome_instituicao_empresa':None,
            'codigo_orgao':None,
            'nome_orgao':None,
            'codigo_unidade':None,
            'nome_unidade':None,
            'logradouro_complemento':None,
            'pais':None,
            'uf':None,
            'cep':None,
            'cidade':None,
            'bairro':None,
            'ddd':None,
            'ramal':None,
            'fax':None,
            'caixa_postal':None,
            'home_page':None,
            'e_mail':None,
            'dt_importacao':None,

        })
        if socket.gethostbyname(socket.gethostname()) == '10.10.2.1':
            self.can_get_soap = True
            if self.path == None: self.path = 'c:/Lattes'
        else:
            self.can_get_soap = False
            if self.path == None: self.path = 'd:/Lattes'
            
        self.get_lattes()


#       ___           ___           ___           ___   
#      /\__\         /\  \         /\  \         /\  \  
#     /:/ _/_       /::\  \       /::\  \       /::\  \ 
#    /:/ /\  \     /:/\:\  \     /:/\:\  \     /:/\:\__\
#   /:/ /::\  \   /:/  \:\  \   /:/ /::\  \   /:/ /:/  /
#  /:/_/:/\:\__\ /:/__/ \:\__\ /:/_/:/\:\__\ /:/_/:/  / 
#  \:\/:/ /:/  / \:\  \ /:/  / \:\/:/  \/__/ \:\/:/  /  
#   \::/ /:/  /   \:\  /:/  /   \::/__/       \::/__/   
#    \/_/:/  /     \:\/:/  /     \:\  \        \:\  \   
#      /:/  /       \::/  /       \:\__\        \:\__\  
#      \/__/         \/__/         \/__/         \/__/  


#       ___           ___           ___           ___     
#      /\__\         /\  \         /\  \         /\__\    
#     /:/ _/_        \:\  \        \:\  \       /:/  /    
#    /:/ /\__\        \:\  \        \:\  \     /:/  /     
#   /:/ /:/  /    ___  \:\  \   _____\:\  \   /:/  /  ___ 
#  /:/_/:/  /    /\  \  \:\__\ /::::::::\__\ /:/__/  /\__\
#  \:\/:/  /     \:\  \ /:/  / \:\~~\~~\/__/ \:\  \ /:/  /
#   \::/__/       \:\  /:/  /   \:\  \        \:\  /:/  / 
#    \:\  \        \:\/:/  /     \:\  \        \:\/:/  /  
#     \:\__\        \::/  /       \:\__\        \::/  /   
#      \/__/         \/__/         \/__/         \/__/    


    def get_zip_from_SOAP(self, id=None, set_auto_save=True, num_errors = 0, path = None):
        if path == None:
            path = self.path
        self.ocorrencia = None
        self.zip = None
        if not id == None:
            self.id = id
        if self.can_get_soap:
            print (f'Tentando recuperar Lattes compactado {self.id} via SOAP')
            try:
                client = zeep.Client(wsdl=self.wsdl)
                self.zip = client.service.getCurriculoCompactado(self.id)
                self.ocorrencia = client.service.getOcorrenciaCV(self.id)
            except Exception as e:
                if self.ocorrencia == None:
                    self.ocorrencia = str(e)
            if not self.ocorrencia == "Curriculo recuperado com sucesso!" and num_errors < 3:
                num_errors += 1
                print (f'Erro {num_errors}: "{self.ocorrencia}".')
                if self.ocorrencia == 'Nenhum curriculo encontrado!' or self.ocorrencia == 'Mais de um curriculo atende ao criterio informado!' or self.ocorrencia == 'Nenhum curriculo encontrado!':
                    if self.update_errors_on_bd:
                        sql = "UPDATE public.all_lattes SET erro = True WHERE id = %s"
                        self.bd.execute(sql, (self.id,))
                    return self.ocorrencia
                tempo_a_dormir = (num_errors*4)**2
                print(f'Esperando {tempo_a_dormir} segundos.')
                time.sleep(tempo_a_dormir)
                print(f'Tentando novamente.')
                self.get_zip_from_SOAP(id = self.id, set_auto_save = set_auto_save, num_errors = num_errors)
            if self.ocorrencia == "Curriculo recuperado com sucesso!" and not self.zip == None:
                print('Lattes compactado recuperado via SOAP')
                if set_auto_save:
                    self.save_zip_to_disk(path)
                    print('Lattes salvo no disco.')
                if self.auto_save_json_to_bd and not self.json == None:
                    self.insert_json()
                return self.ocorrencia
            elif num_errors >= 3:
                return self.ocorrencia
            else:
                return (self.ocorrencia + ' - Erro ao recuperar zip.')
        else:
            return "Wrong IP number. Can't get zipped Lattes from this IP number."

    def get_atualizacao_SOAP (self, id=None):
        if not id == None:
            self.id = id
        if self.can_get_soap:
            client = zeep.Client(wsdl=self.wsdl)
            self.dt_atualizacao = client.service.getDataAtualizacaoCV(self.id)
            if self.dt_atualizacao == None:
                raise ValueError('Invalid ID')
            else:
                self.dt_atualizacao = datetime.strptime(self.dt_atualizacao, '%d/%m/%Y %H:%M:%S').replace(tzinfo=pytz.UTC)
                return True
        else:
            return False

    def get_id (self, CPF = "69045542153", nome="Alberto de Campos e Silva", data_nascimento="10/05/1976"):
        self.CPF = CPF
        self.nome = nome
        self.data_nascimento = data_nascimento
        client = zeep.Client(wsdl=self.wsdl)
        self.id = client.service.getIdentificadorCNPq(self.CPF, self.nome, self.data_nascimento)
        if self.id == None:
            raise ValueError('Invalid CPF, Name or DateBirth informed.')
        return True

    def get_atualizacao_JSON (self):
        return datetime.strptime(self.json['CURRICULO-VITAE']['@DATA-ATUALIZACAO'] + self.json['CURRICULO-VITAE']['@HORA-ATUALIZACAO'], '%d%m%Y%H%M%S').replace(tzinfo=pytz.UTC)

#  _____ _   _  _____ ___________ _____ 
# |_   _| \ | |/  ___|  ___| ___ \_   _|
#   | | |  \| |\ `--.| |__ | |_/ / | |  
#   | | | . ` | `--. \  __||    /  | |  
#  _| |_| |\  |/\__/ / |___| |\ \  | |  
#  \___/\_| \_/\____/\____/\_| \_| \_/  

 
# ______ _   _ _   _ _____ 
# |  ___| | | | \ | /  __ \
# | |_  | | | |  \| | /  \/
# |  _| | | | | . ` | |    
# | |   | |_| | |\  | \__/\
# \_|    \___/\_| \_/\____/


    def insert_xml(self):
        if self.id == None or self.xml == None:
            raise Exception('No id or xml to insert.')
        sql = """INSERT INTO public."lattes_xml"(
            id, xml)
            VALUES(%s, %s::xml)
            ON CONFLICT (id)
            DO
            UPDATE SET
            xml = EXCLUDED.xml,
            ;
            """
        data = (self.id,
                self.xml,
                )
        self.bd.execute(sql, data)

    def insert_json(self):
        if self.id == None or self.json == None:
            raise Exception('No id or json to insert.')
        sql = """INSERT INTO public."lattes_json"(
            id, json)
            VALUES(%s, %s::json)
            ON CONFLICT (id)
            DO
            UPDATE SET
            json = EXCLUDED.json
            ;
            """
        data = (self.id,
                json.dumps(self.json)
               )
        self.bd.execute(sql, data)

    def insert_lattes_atualizacao_bd(self):
        if self.id == None or self.dt_atualizacao == None:
            raise Exception('No id or dt_atualizacao to insert.')
        sql = """INSERT INTO public."lattes_atualizacao"(
            id, last_updated)
            VALUES(%s, TIMESTAMP %s)
            ON CONFLICT (id)
            DO
            UPDATE SET
            last_updated = EXCLUDED.last_updated,
            created_at = now()
            ;
            """
        data = (self.id,
                self.dt_atualizacao.strftime('%Y-%m-%dT%H:%M:%S.%f'))
        self.bd.execute(sql, data)

    def insert_palavras_chave_no_bd (self, data):
        sql = 'INSERT INTO public."palavras_chave"(id, palavra) VALUES(%(id)s, %(palavra)s);'
        data = ({'id': self.id, 'palavra': palavra} for palavra in self.palavras_chave)
        self.bd.execute(sql, data)

    def insere_dados_gerais_no_bd(self, on_conflict = True):
        sql = '''
            INSERT INTO public."dados_gerais"
               (id, nome, cpf, email, telefone, sexo, regiao, nomes_citacao, dt_atualizacao, 
               nacionalidade, pais_nascimento, uf_nascimento, cidade_nascimento, data_nascimento, 
               data_falecimento, sigla_pais_nacionalidade, raca_cor, orcid, 
               codigo_instituicao_empresa, nome_instituicao_empresa, codigo_orgao, 
               nome_orgao, codigo_unidade, nome_unidade, logradouro_complemento, pais, uf, cep, 
               cidade, bairro, ddd, ramal, fax, caixa_postal, home_page, e_mail)
            VALUES
                (%(id)s, %(nome)s, %(cpf)s, %(email)s, %(telefone)s, %(sexo)s, %(regiao)s, %(nomes_citacao)s, %(dt_atualizacao)s,
                %(nacionalidade)s, %(pais_nascimento)s, %(uf_nascimento)s, %(cidade_nascimento)s, %(data_nascimento)s,
                %(data_falecimento)s, %(sigla_pais_nacionalidade)s, %(raca_cor)s, %(orcid)s,
                %(codigo_instituicao_empresa)s, %(nome_instituicao_empresa)s, %(codigo_orgao)s,
                %(nome_orgao)s, %(codigo_unidade)s, %(nome_unidade)s, %(logradouro_complemento)s, %(pais)s, %(uf)s, %(cep)s,
                %(cidade)s, %(bairro)s, %(ddd)s, %(ramal)s, %(fax)s, %(caixa_postal)s, %(home_page)s, %(e_mail)s)
           
            '''
        if on_conflict:
            sql += '''
            ON CONFLICT (id) DO UPDATE SET
                nome = excluded.nome,
                cpf = excluded.cpf,
                email = excluded.email,
                telefone = excluded.telefone,
                sexo = excluded.sexo,
                regiao = excluded.regiao,
                nomes_citacao = excluded.nomes_citacao,
                dt_atualizacao  = excluded.dt_atualizacao ,
                nacionalidade  = excluded.nacionalidade ,
                pais_nascimento  = excluded.pais_nascimento ,
                uf_nascimento  = excluded.uf_nascimento ,
                cidade_nascimento  = excluded.cidade_nascimento ,
                data_nascimento = excluded.data_nascimento,
                data_falecimento = excluded.data_falecimento,
                sigla_pais_nacionalidade  = excluded.sigla_pais_nacionalidade ,
                raca_cor  = excluded.raca_cor ,
                orcid  = excluded.orcid ,
                codigo_instituicao_empresa = excluded.codigo_instituicao_empresa,
                nome_instituicao_empresa = excluded.nome_instituicao_empresa,
                codigo_orgao = excluded.codigo_orgao,
                nome_orgao = excluded.nome_orgao,
                codigo_unidade = excluded.codigo_unidade,
                nome_unidade = excluded.nome_unidade,
                logradouro_complemento = excluded.logradouro_complemento,
                pais = excluded.pais,
                uf = excluded.uf,
                cep = excluded.cep,
                cidade = excluded.cidade,
                bairro = excluded.bairro,
                ddd = excluded.ddd,
                ramal = excluded.ramal,
                fax = excluded.fax,
                caixa_postal = excluded.caixa_postal,
                home_page = excluded.home_page,
                e_mail = excluded.e_mail
            '''
        else:
            sql += '''
            ON CONFLICT DO NOTHING
            '''
        sql +=';'
        self.bd.execute(sql, self.dados_gerais)


#  _____  _____ _____
# |  __ \|  ___|_   _|
# | |  \/| |__   | |
# | | __ |  __|  | |
# | |_\ \| |___  | |
#  \____/\____/  \_/


# ______ _   _ _   _ _____
# |  ___| | | | \ | /  __ \
# | |_  | | | |  \| | /  \/
# |  _| | | | | . ` | |
# | |   | |_| | |\  | \__/\
# \_|    \___/\_| \_/\____/


    def get_xml_bd(self):
        sql = """SELECT xml from public."lattes_xml"
        where id = %s;
        """
        data = (self.id,)
        resultado = self.bd.query(sql, data, many=False)
        if not resultado == None:
            self.xml = resultado[0]
            return True
        return False

    def get_json_bd(self):
        sql = """SELECT json from public."lattes_json"
        where id = %s;
        """
        data = (self.id,)
        resultado = self.bd.query(sql, data, many=False)
        if not resultado == None:
            self.json = resultado[0]
            return True
        return False

    def get_atualizacao_SOAP(self):
        sql = """SELECT 
            dt_atualizacao as created_at, 
            dt_importacao as last_updated
        from public.dados_gerais
        where id = %s;
        """
        data = (self.id,)
        resultado = self.bd.query(sql, data, many=False)
        if not resultado == None:
            self.bd_dt_atualizacao = resultado[0].replace(tzinfo=pytz.UTC)
            self.bd_created_at = resultado[1].replace(tzinfo=pytz.UTC)
            return True
        return False



# d8888b.      d888888b      .d8888.      db   dD
# 88  `8D        `88'        88'  YP      88 ,8P'
# 88   88         88         `8bo.        88,8P
# 88   88         88           `Y8b.      88`8b
# 88  .8D        .88.        db   8D      88 `88.
# Y8888D'      Y888888P      `8888Y'      YP   YD


# d88888b db    db d8b   db  .o88b. d888888b d888888b  .d88b.  d8b   db .d8888.
# 88'     88    88 888o  88 d8P  Y8 `~~88~~'   `88'   .8P  Y8. 888o  88 88'  YP
# 88ooo   88    88 88V8o 88 8P         88       88    88    88 88V8o 88 `8bo.
# 88~~~   88    88 88 V8o88 8b         88       88    88    88 88 V8o88   `Y8b.
# 88      88b  d88 88  V888 Y8b  d8    88      .88.   `8b  d8' 88  V888 db   8D
# YP      ~Y8888P' VP   V8P  `Y88P'    YP    Y888888P  `Y88P'  VP   V8P `8888Y'


    def get_lattes (self):
        conseguiu = True
        if not self.read_zip_from_disk ():
            conseguiu = self.get_zip_from_SOAP()
        if conseguiu:
            conseguiu = self.get_xml()
            self.get_dados_gerais_by_xml()
        return conseguiu

    @staticmethod
    def get_saving_path(type, path, id, create_path_if_new = False):
        filename = "Lattes_" + id + "." + type
        path_name = os.path.join(path, 'Lattes_' + type.upper())
        if type=="zip":
            full_path =  os.path.join(path_name, id[0], id[1])
        else:
            full_path = os.path.join(path_name, id[0], id[1], id[2], id[3], id[4])
        if create_path_if_new:
            pathlib.Path(full_path).mkdir(parents=True, exist_ok=True)
        return os.path.join(full_path, filename)

    def read_zip_from_disk(self, filename = None, path = None, get_from_SOAP_if_not_exists = True):
        if path == None:
            path = self.path
        if filename == None:
            filename = Lattes.get_saving_path(type = "zip", path = path, id = self.id)
        try:
            with open(filename, 'rb') as f:
                self.zip = f.read()
            if self.zip == None:
                if get_from_SOAP_if_not_exists and self.can_get_soap:
                    return self.get_zip_from_SOAP()
                else: return False

        except:
            return False
        return True

    def read_xml_from_disk (self, filename = None, path = None):
        if path == None:
            path = self.path
        if filename == None:
            filename = Lattes.get_saving_path("xml", path = path, id = self.id)
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.xml = f.read()
            if not self.xml == None:
                return True
            else:
                return False
        except:
            return False

    def read_json_from_disk(self, filename = None, path = None):
        if path == None:
            path = self.path
        if filename == None:
            filename = Lattes.get_saving_path("JSON", path = path, id = self.id)
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.json = json.load(f)
            if not self.json == None:
                return True
            else:
                return False
        except:
            return False

    def read_from_disk (self, path = None):
        if path == None:
            path = self.path
        if not path == None:
            self.path = path
        resposta = True
        if not self.read_zip_from_disk(): resposta = False
        if not self.read_xml_from_disk(): resposta = False
        if not self.read_json_from_disk(): resposta = False
        return resposta

    def save_xml_to_disk (self, filename = None, path = None, replace = False):
        if path == None:
            path = self.path
        if filename == None:
            filename = Lattes.get_saving_path("xml", path = path, id = self.id, create_path_if_new = True)
        if replace or not os.path.isfile(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.xml)
            return True
        return False

    def save_json_to_disk (self, filename = None, path = None, replace = False):
        if path == None:
            path = self.path
        if filename == None:
            filename = Lattes.get_saving_path("JSON", path = path, id = self.id, create_path_if_new = True)
        if replace or not os.path.isfile(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.json, f, indent=4)
            return True
        return False

    def save_zip_to_disk (self, path = None, filename = None, replace = False):
        if path == None:
            path = self.path
        if filename == None:
            filename = Lattes.get_saving_path("zip", path = path, id = self.id, create_path_if_new = True)
        if replace or not os.path.isfile(filename):
            with open(filename, 'wb') as f:
                f.write(self.zip)
            return True
        return False

    def save_to_disk (self, path = None, replace = False):
        if not path == None:
            self.path = path
        resposta = True
        if not self.save_zip_to_disk(replace = replace): resposta = False
        if not self.save_xml_to_disk(replace = replace): resposta = False
        if not self.save_json_to_disk(replace = replace): resposta = False
        return resposta



#  dP""b8    dP"Yb    88b 88   Yb    dP   888888   88""Yb   888888
# dP   `"   dP   Yb   88Yb88    Yb  dP    88__     88__dP     88
# Yb        Yb   dP   88 Y88     YbdP     88""     88"Yb      88
#  YboodP    YbodP    88  Y8      YP      888888   88  Yb     88

#  888888   88   88   88b 88    dP""b8   888888   88    dP"Yb    88b 88   .dP"Y8
# 88__     88   88   88Yb88   dP   `"     88     88   dP   Yb   88Yb88   `Ybo."
# 88""     Y8   8P   88 Y88   Yb          88     88   Yb   dP   88 Y88   o.`Y8b
# 88       `YbodP'   88  Y8    YboodP     88     88    YbodP    88  Y8   8bodP'



    def recorre_sobre_todo_json(self, d, path=None):
            if not path: path = []
            for k, v in d.items():
                if isinstance(v, dict) or isinstance(v, OrderedDict):
                    self.recorre_sobre_todo_json(v, path + [k])
                elif isinstance(v, list):
                    num = 0
                    for item in v:
                        self.recorre_sobre_todo_json(item, path + [k] + [num])
                        num +=1
                else:
                    if not v == None:
                        d[k] = html.unescape(v)
                    else:
                        pass
            return d

    def get_xml(self):
        if self.zip == None:
            return False
        try:
            with ZipFile(io.BytesIO(self.zip)) as myzip:
                with myzip.open(myzip.namelist()[0]) as myfile:
                    self.xml = myfile.read()
                self.json = xmltodict.parse(self.xml)
                self.json = self.recorre_sobre_todo_json(self.json)
                self.xml = self.xml.decode('iso-8859-1').replace('encoding="ISO-8859-1" ', '')
            if self.auto_save_json_to_bd:
                self.insert_json()
            return True
        except:
            if self.update_errors_on_bd:
                sql = "UPDATE public.all_lattes SET erro = True WHERE id = %s"
                self.bd.execute(sql, (self.id,))
            return False


    def get_dados_gerais_by_xml (self):
        if self.xml == None: return None
        if not (
                type(self.soup) == BeautifulSoup or
                type(self.soup) == Tag ):
            self.soup = BeautifulSoup(self.xml, "xml")
        id = self.soup.find('CURRICULO-VITAE').get('NUMERO-IDENTIFICADOR')
        if id == None:
            self.dados_gerais['id'] = self.id
        data = self.soup.find('CURRICULO-VITAE').get('DATA-ATUALIZACAO')
        hora = self.soup.find('CURRICULO-VITAE').get('HORA-ATUALIZACAO')
        try:
            self.dados_gerais['dt_atualizacao'] = datetime.strptime(data + hora, '%d%m%Y%H%M%S')
        except:
            self.dados_gerais['dt_atualizacao'] = None
        self.dados_gerais['nome'] = self.soup.find('DADOS-GERAIS').get('NOME-COMPLETO')
        self.dados_gerais['nacionalidade'] = self.soup.find('DADOS-GERAIS').get('PAIS-DE-NACIONALIDADE')
        self.dados_gerais['nomes_citacao'] = self.soup.find('DADOS-GERAIS').get('NOME-EM-CITACOES-BIBLIOGRAFICAS')
        self.dados_gerais['pais_nascimento'] = self.soup.find('DADOS-GERAIS').get('PAIS-DE-NASCIMENTO')
        self.dados_gerais['uf_nascimento'] = self.soup.find('DADOS-GERAIS').get('UF-NASCIMENTO')
        self.dados_gerais['cidade_nascimento'] = self.soup.find('DADOS-GERAIS').get('CIDADE-NASCIMENTO')
        self.dados_gerais['data_nascimento'] = self.soup.find('DADOS-GERAIS').get('DATA-NASCIMENTO')
        self.dados_gerais['cidade_nascimento'] = self.soup.find('DADOS-GERAIS').get('CIDADE-NASCIMENTO')
        self.dados_gerais['sexo'] = self.soup.find('DADOS-GERAIS').get('SEXO')
        self.dados_gerais['data_falecimento'] = self.soup.find('DADOS-GERAIS').get('DATA-FALECIMENTO')
        self.dados_gerais['sigla_pais_nacionalidade'] = self.soup.find('DADOS-GERAIS').get('SIGLA-PAIS-NACIONALIDADE')
        self.dados_gerais['nacionalidade'] = self.soup.find('DADOS-GERAIS').get('PAIS-DE-NACIONALIDADE')
        self.dados_gerais['raca_cor'] = self.soup.find('DADOS-GERAIS').get('RACA-OU-COR')
        self.dados_gerais['orcid'] = self.soup.find('DADOS-GERAIS').get('ORCID-ID')
        self.dados_gerais['cidade_nascimento'] = self.soup.find('DADOS-GERAIS').get('CIDADE-NASCIMENTO')
        if not self.soup.find('ENDERECO-PROFISSIONAL') == None:
            self.dados_gerais['codigo_instituicao_empresa'] = self.soup.find('ENDERECO-PROFISSIONAL').get('CODIGO-INSTITUICAO-EMPRESA')
            self.dados_gerais['codigo_orgao'] = self.soup.find('ENDERECO-PROFISSIONAL').get('CODIGO-ORGAO')
            self.dados_gerais['nome_orgao'] = self.soup.find('ENDERECO-PROFISSIONAL').get('NOME-ORGAO')
            self.dados_gerais['codigo_unidade'] = self.soup.find('ENDERECO-PROFISSIONAL').get('CODIGO-UNIDADE')
            self.dados_gerais['nome_unidade'] = self.soup.find('ENDERECO-PROFISSIONAL').get('NOME-UNIDADE')
            self.dados_gerais['logradouro_complemento'] = self.soup.find('ENDERECO-PROFISSIONAL').get('LOGRADOURO-COMPLEMENTO')
            self.dados_gerais['pais'] = self.soup.find('ENDERECO-PROFISSIONAL').get('PAIS')
            self.dados_gerais['uf'] = self.soup.find('ENDERECO-PROFISSIONAL').get('UF')
            self.dados_gerais['cep'] = self.soup.find('ENDERECO-PROFISSIONAL').get('CEP')
            self.dados_gerais['cidade'] = self.soup.find('ENDERECO-PROFISSIONAL').get('CIDADE')
            self.dados_gerais['bairro'] = self.soup.find('ENDERECO-PROFISSIONAL').get('BAIRRO')
            self.dados_gerais['ddd'] = self.soup.find('ENDERECO-PROFISSIONAL').get('DDD')
            self.dados_gerais['telefone'] = self.soup.find('ENDERECO-PROFISSIONAL').get('TELEFONE')
            self.dados_gerais['ramal'] = self.soup.find('ENDERECO-PROFISSIONAL').get('RAMAL')
            self.dados_gerais['fax'] = self.soup.find('ENDERECO-PROFISSIONAL').get('FAX')
            self.dados_gerais['caixa_postal'] = self.soup.find('ENDERECO-PROFISSIONAL').get('CAIXA-POSTAL')
            self.dados_gerais['e_mail'] = self.soup.find('ENDERECO-PROFISSIONAL').get('E-MAIL')
            self.dados_gerais['home_page'] = self.soup.find('ENDERECO-PROFISSIONAL').get('HOME-PAGE')
        self.dados_gerais['dt_importacao'] = datetime.now()
