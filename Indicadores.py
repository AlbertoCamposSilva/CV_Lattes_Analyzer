from datetime import datetime
from shutil import ExecError
import pytz, json
from collections import OrderedDict
from Lattes import Lattes
import psycopg2
from Database import Database
from functools import wraps

class Indicadores:

    def __init__ (self, 
                  id = None, 
                  json = None, 
                  filename = None, 
                  show_execution_time = False,
                  show_sql = False
                  ):
        self.id = id
        self.filename = filename
        self.show_execution_time = show_execution_time
        self.show_sql = show_sql
        self.db = Database('CNPq')
        self.indicadores = []
        self.list_indicadores = []
        self.lista_de_publicações = []
        self.palavras_chave = []
        self.areas_conhecimento = []
        self.areas = {
            'grande_area': [],
            'area': [],
            'sub-area': [],
            'especialidade': []
        }
        self.dados_pessoais = None
        self.publicações=[]

        #Pegando o Lattes
        self.lattes = Lattes(id)
        if not id == None and json == None:
            self.lattes.get_lattes()
        elif not json == None:
            self.get_dados_pessoais()
        elif not filename == None:
            load = False
            if filename[:-3].lower() =="zip":
                load = self.lattes.read_zip_from_disk(filename=filename)
                if load: load = load and self.lattes.get_xml()
            elif filename[:-3].lower() =="json":
                load = load and self.lattes.read_json_from_disk(filename=filename)
            if not load:
                raise Exception ('Não foi possível recuperar o currículo do arquivo informado.')
        else:
            raise Exception ('Ao menos um deve ser especificado, id, json ou filename.')
        
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

    def get_list(self, d):
        if isinstance(d, list):
            return d
        return [d]

    def inteiro(self,n):
        if  type(n) == int: return n
        elif type(n) == float: return int(n)
        elif not type(n) == str: return None
        elif type(n) == str and len(n) > 0:
            for x in n:
                if not x in ['0','1','2','3','4','5','6','7','8','9']: 
                    return None
            return int(n)
        else: return None

    @timing
    def get_indicadores(self):
        if self.lattes == None or self.lattes.json == None: return False
        self.indicadores=[]

        def procura_todos_anos (d, path=None):
                if not path: path = []
                for k, v in d.items():
                    if isinstance(v, dict) or isinstance(v, OrderedDict):
                        procura_todos_anos(v, path + [k])
                    elif isinstance(v, list):
                        num = 0
                        for item in v:
                            procura_todos_anos(item, path + [k] + [num])
                            num +=1
                    else:
                        valor = self.inteiro(v)
                        if not valor == None:
                            if k[:4] == '@ANO':
                                nome_indicador = k + ' '
                                for num in range(-1,-len(path),-1):
                                    if not str(path[num]).isnumeric() and not str(path[num])[:5] == 'DADOS':
                                        nome_indicador += path[num] + ' '
                                        break
                                indicador = {
                                    'id': self.id,
                                    'ano': valor,
                                    'path': path + [k],
                                    'tipo': nome_indicador,
                                    'qty': 1
                                }
                                self.indicadores.append(indicador)
                                self.list_indicadores.append((self.id,valor,json.dumps(path + [k]),nome_indicador,1))
                        else:
                            pass
                return self.indicadores

        self.indicadores = procura_todos_anos(self.lattes.json)
        return True



    @timing
    def salva_indicadores_no_bd (self, on_conflic_update = True):
        if self.list_indicadores == None or len(self.list_indicadores) == 0: return False
        args_str = ','.join((self.db.cur.mogrify("(%s,%s,%s,%s,%s)", x).decode("utf-8")) for x in self.list_indicadores)
        sql = ''
        if on_conflic_update:
            sql += f'''
                delete from public."indicadores" where id = %s;'''
        sql += '''
                insert into public."indicadores"
                    (id, ano, path, tipo, qty)
                VALUES ''' + (args_str) + ';'
        if on_conflic_update:
            sql = self.db.cursor.mogrify(sql, [self.id])
            if self.show_sql: print (sql)
            self.db.execute(sql)
        else:
            if self.show_sql: print (sql)
            self.db.execute(sql)
        return True

    def return_first_element_of(self, x):
        if x == None : return None
        elif x == '' : return None
        elif isinstance(x, list): return x[0]
        elif isinstance(x, OrderedDict): return x[x.keys()[0]]
        elif isinstance(x, dict): 
            for key in x.keys():
                return x[key]
        else: return x

    @staticmethod
    @timing
    def get_lista_indicadores (indicador = None):
        if indicador == None or not indicador in Indicadores.lista_indicadores:
            sql = 'SELECT id, descricao from public."lista_indicadores"'
            conn = None
            try:
                params = Database.config_db_connection()
                conn = psycopg2.connect(**params)
                cur = conn.cursor()
                cur.execute(sql)
                result = cur.fetchall()
                cur.close()
                for k in result:
                    Indicadores.lista_indicadores[k[1]] = k[0]
            except (Exception, psycopg2.DatabaseError) as error:
                print("Não foi possível pegar os indicadores. Erro: ", error)
                return False
            finally:
                if conn is not None:
                    conn.close()
        if not indicador == None and not indicador in Indicadores.lista_indicadores:
            try:
                sql = 'insert into public."lista_indicadores" (descricao) VALUES (%s);'
                params = Database.config_db_connection()
                conn = psycopg2.connect(**params)
                cur = conn.cursor()
                cur.execute(sql, [indicador])
                conn.commit()
                sql = 'SELECT id, descricao from public."lista_indicadores"'
                cur.execute(sql)
                result = cur.fetchall()
                cur.close()
                for k in result:
                    Indicadores.lista_indicadores[k[1]] = k[0]
            except (Exception, psycopg2.DatabaseError) as error:
                print("Não foi possível pegar os indicadores. Erro: ", error)
                return False
            finally:
                if conn is not None:
                    conn.close()
        if indicador == None:
            return Indicadores.lista_indicadores
        else:
            return Indicadores.lista_indicadores[indicador]


    @timing
    def get_palavras_chave(self, json = None, path = None, palavras_chave = None):
        if palavras_chave == None:
            palavras_chave = self.palavras_chave
        if json == None: json = self.lattes.json
        if json == None: return False

        def procura_palavras_chave (json, path, palavras_chave):
            if not path: path = []
            for k, v in json.items():
                if isinstance(v, dict) or isinstance(v, OrderedDict):
                    procura_palavras_chave(json = v, path = path + [k], palavras_chave = palavras_chave)
                elif isinstance(v, list):
                    num = 0
                    for item in v:
                        #print("Unfolding List: ", v)
                        procura_palavras_chave(json = item, path = path + [k] + [num], palavras_chave = palavras_chave)
                        num +=1
                else:
                    if not v == None:
                        #print(k[0:14], path, v)
                        if k[0:15] == '@PALAVRA-CHAVE-':
                            if (len(v) > 2): 
                                if not v in palavras_chave:
                                    palavras_chave.append(v)
                        #print("{2} - {0} : {1}".format(k, html.unescape(v), path))
                    else:
                        #print("{2} - {0} : {1}".format(k, v, path))
                        pass
            return palavras_chave
        
        self.palavras_chave = procura_palavras_chave(json = json, path = path, palavras_chave=palavras_chave)
        return True

    @timing
    def salva_palavras_chave_no_bd (self, on_conflic_update = True):
        if self.palavras_chave == None or len(self.palavras_chave) == 0: return False
        if on_conflic_update:
            sql = "DELETE from palavras_chave WHERE id = %s;\n"
            sql = self.db.cursor.mogrify(sql, (self.id,)).decode("utf-8")
        else: sql = ''
        args_str = ','.join((self.db.cursor.mogrify("(" + self.id + ",%s)", (x,)).decode("utf-8")) for x in self.palavras_chave)
        sql += '''INSERT into palavras_chave (id, palavra)
        VALUES
            ''' + args_str
        if self.show_sql: print (sql)
        self.db.execute(sql)
        return True

    @timing
    def get_areas_conhecimento(self):
        if self.lattes.json == None or self.lattes.json.get("CURRICULO-VITAE") == None: return False
        áreas =  self.lattes.json.get("CURRICULO-VITAE")
        if not áreas == None:
            áreas = áreas.get("DADOS-GERAIS")
            if not áreas == None:
                áreas = áreas.get('AREAS-DE-ATUACAO')
                if not áreas == None:
                    for area in áreas:
                        areas2 = self.get_list(self.lattes.json["CURRICULO-VITAE"]["DADOS-GERAIS"]['AREAS-DE-ATUACAO'][area])
                        for area2 in areas2:
                            if area2.get('@NOME-GRANDE-AREA-DO-CONHECIMENTO') and len(area2['@NOME-GRANDE-AREA-DO-CONHECIMENTO']) > 1:
                                self.areas_conhecimento.append((
                                    self.id,
                                    "grande-area",
                                    area2['@NOME-GRANDE-AREA-DO-CONHECIMENTO'])
                                    )
                                self.areas['grande_area'].append(area2['@NOME-GRANDE-AREA-DO-CONHECIMENTO'])
                            if area2.get('@NOME-DA-AREA-DO-CONHECIMENTO') and len(area2['@NOME-DA-AREA-DO-CONHECIMENTO']) > 1:
                                self.areas_conhecimento.append((
                                    self.id,
                                    "area",
                                    area2['@NOME-DA-AREA-DO-CONHECIMENTO']))
                                self.areas['area'].append(area2['@NOME-DA-AREA-DO-CONHECIMENTO'])
                            if area2.get('@NOME-DA-SUB-AREA-DO-CONHECIMENTO') and len(area2['@NOME-DA-SUB-AREA-DO-CONHECIMENTO']) > 1:
                                self.areas_conhecimento.append((
                                    self.id,
                                    "sub-area",
                                    area2['@NOME-DA-SUB-AREA-DO-CONHECIMENTO']))
                                self.areas['sub-area'].append(area2['@NOME-DA-SUB-AREA-DO-CONHECIMENTO'])
                            if area2.get('@NOME-DA-ESPECIALIDADE') and len(area2['@NOME-DA-ESPECIALIDADE']) > 1:
                                self.areas_conhecimento.append((
                                    self.id,
                                    "especialidade",
                                    area2['@NOME-DA-ESPECIALIDADE']))
                                self.areas['especialidade'].append(area2['@NOME-DA-ESPECIALIDADE'])
        return True

    @timing
    def salva_areas_do_conhecimento_no_bd (self, on_conflic_update = False):
        if self.areas_conhecimento == None or len(self.areas_conhecimento) == 0: return False
        sql = ''
        if on_conflic_update:
            sql += self.db.cursor.mogrify('delete from public."areas_conhecimento" where id = %s;', (self.id,)).decode("utf-8")
        args_str = ','.join((self.db.cursor.mogrify("(%s,%s,%s)", x).decode("utf-8")) for x in self.areas_conhecimento)
        sql = '''
        insert into public."areas_conhecimento" (id, tipo, area) VALUES \n''' + args_str + '''
        ON CONFLICT (id, tipo, area) DO NOTHING'''
        sql = self.db.cursor.mogrify(sql)
        if self.show_sql: print (sql)
        self.db.execute(sql)
        return True

    @timing
    def get_publicações(self):
        if self.lattes.json == None: return False
        def procura_todos_DOIs (d, path=None):
            if not path: path = []
            for k, v in d.items():
                if isinstance(v, dict) or isinstance(v, OrderedDict):
                    procura_todos_DOIs (v, path + [k])
                elif isinstance(v, list):
                    num = 0
                    for item in v:
                        procura_todos_DOIs (item, path + [k] + [num])
                        num +=1
                else:
                    if not v == None:
                        if (k[:4] == '@DOI' 
                        # or k[:5] == '@ISBN' or k[:5] == '@ISSN'
                        ):
                            nome_indicador = k + ' '
                            for num in range(-1,-len(path),-1):
                                if not str(path[num]).isnumeric() and not str(path[num])[:5] == 'DADOS':
                                    nome_indicador += path[num] + ' '
                                    break
                            titulo = ''
                            ano = 0
                            natureza = ''
                            for o, p in d.items():
                                if o.find('TIT') > -1 and o.find('ING') == -1:
                                    titulo = p
                                if o[:4] == '@ANO' and not self.inteiro(p) == None and self.inteiro(p) > 0:
                                    ano = self.inteiro(p)
                                if o[:9] == '@NATUREZA':
                                    natureza = p
                            if len(titulo) > 0:
                                publicação = {
                                    'id': self.id,
                                    'DOI': v,
                                    'path': path + [k],
                                    'tipo': nome_indicador,
                                    'titulo':titulo,
                                    'ano': ano,
                                    'natureza': natureza,
                                }
                                self.publicações.append(publicação)
                                self.lista_de_publicações.append((self.id,v,json.dumps(path + [k]),nome_indicador,titulo, ano, natureza))
                    else:
                        pass

        procura_todos_DOIs (self.lattes.json)
        return True

    @timing
    def salva_publicações_no_bd(self, on_conflic_update = True):
        if self.lista_de_publicações == None or len(self.lista_de_publicações) == 0: return False
        sql = ''
        args_str = ','.join((self.db.cursor.mogrify("\n(%s, %s, %s, %s, %s, %s, %s)", x).decode("utf-8")) for x in self.lista_de_publicações)
        #print(args_str)
        if on_conflic_update:
            delete_sql = '''DELETE from publicacoes WHERE id = %s;\n'''
            sql+= self.db.cursor.mogrify(delete_sql, (self.id,)).decode("utf-8")
        sql += '''INSERT INTO publicacoes (id, doi, path, tipo, titulo, ano, natureza)
        VALUES ''' + args_str + ''';
        '''
        if self.show_sql: print (sql)
        self.db.execute(sql)
        return True

    @timing
    def get_dados_pessoais(self):
        if self.lattes.json == None: return False
        id = self.lattes.json['CURRICULO-VITAE'].get('@NUMERO-IDENTIFICADOR')
        if not self.inteiro(id) == None and len(id) == 16:
            id = self.inteiro(id)
            if not self.id == None and not int(self.id) == id:
                print('ERRO. ID da classe não é o mesmo do ID do Lattes. ID Lattes: ', id, '. ID Classe: ', self.id, '.')
            self.id = id
        elif self.inteiro(id) == None or not len(id) == 16:
            if not self.id == None:
                id = self.id
        else:
            return False
        data =  self.lattes.json['CURRICULO-VITAE'].get('@DATA-ATUALIZACAO')
        hora =  self.lattes.json['CURRICULO-VITAE'].get('@HORA-ATUALIZACAO')
        self.lattes.data_atualizacao = datetime.strptime(data + hora, '%d%m%Y%H%M%S')

        self.dados_pessoais = {
            'id': id,
            'nome': self.lattes.json['CURRICULO-VITAE']['DADOS-GERAIS'].get('@NOME-COMPLETO'),
            'nacionalidade': self.lattes.json['CURRICULO-VITAE']['DADOS-GERAIS'].get('@PAIS-DE-NACIONALIDADE'),
            'nomes_citacao': self.lattes.json['CURRICULO-VITAE']['DADOS-GERAIS'].get('@NOME-EM-CITACOES-BIBLIOGRAFICAS'),
            'orcid': self.lattes.json['CURRICULO-VITAE']['DADOS-GERAIS'].get('@ORCID-ID'),
        }
        return True

    @timing
    def salva_dados_pessoais_no_bd (self, on_conflic_update = False):
        if self.dados_pessoais == None or len(self.dados_pessoais) == 0: return False
        sql = '''INSERT INTO dados_pessoais (id, nome, nacionalidade, nomes_citacao, orcid) VALUES (%s,%s,%s,%s,%s) '''
        if on_conflic_update:
            sql += '''ON CONFLICT (id) DO
                        UPDATE SET
                        nome = EXCLUDED.nome,
                        nacionalidade = EXCLUDED.nacionalidade,
                        nomes_citacao = EXCLUDED.nomes_citacao,
                        orcid = EXCLUDED.orcid
                        ;'''
        else:
            sql += 'ON CONFLICT (id) DO NOTHING;'
        sql = self.db.cursor.mogrify(sql, [self.dados_pessoais[k] for k in self.dados_pessoais.keys()])
        if self.show_sql: print(sql)
        self.db.execute(sql)
        return True

    @timing
    def atualiza (self, 
                indicadores = True, 
                palavras_chave = True, 
                areas_conhecimento = True, 
                publicações = True, 
                dados_pessoais=True,
                on_conflic_update = True):
        if self.lattes == None or self.lattes.json == None:
            print ('ERRRO - Lattes não está carregado. ID:', self.id)
            return False
        if indicadores:
            if not self.get_indicadores():
                print ('ERRRO - Não foi possível carregar Indicadores. ID:', self.id)
                return False
            else:
                self.salva_indicadores_no_bd(on_conflic_update = on_conflic_update)
        if palavras_chave:
            if not self.get_palavras_chave():
                print ('ERRRO - Não foi possível carregar Indicadores. ID:', self.id)
            else:
                self.salva_palavras_chave_no_bd(on_conflic_update = on_conflic_update)
        if areas_conhecimento:
            if not self.get_areas_conhecimento():
                print ('ERRRO - Não foi possível carregar Áreas do Conhecimento. ID:', self.id)
            else:
                self.salva_areas_do_conhecimento_no_bd(on_conflic_update = on_conflic_update)
        if publicações:
            if not self.get_publicações():
                print ('ERRRO - Não foi possível carregar Publicações. ID:', self.id)
            else:
                self.salva_publicações_no_bd(on_conflic_update = on_conflic_update)
        if dados_pessoais:
            if not self.get_dados_pessoais():
                print ('ERRRO - Não foi possível carregar Dados Pessoais. ID:', self.id)
                return False
            else:
                self.salva_dados_pessoais_no_bd(on_conflic_update = on_conflic_update)