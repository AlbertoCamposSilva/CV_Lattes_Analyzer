from datetime import datetime
from shutil import ExecError
import pytz, json, time
from collections import OrderedDict
from Lattes import Lattes
import psycopg2, requests, json
from Database import Database
from functools import wraps
import numpy as np


class Indicadores:

    def __init__ (self, 
                  id = None, 
                  json = None, 
                  filename = None, 
                  show_execution_time = False,
                  show_sql = False,
                  auto_save_json_to_bd = False,
                  on_conflic_update = True,
                  show_messages = False,
                  ):
        self.id = id
        self.erro = False
        self.filename = filename
        self.show_execution_time = show_execution_time
        self.show_messages = show_messages
        self.on_conflic_update = on_conflic_update
        self.show_sql = show_sql
        self.auto_save_json_to_bd = auto_save_json_to_bd
        self.db = Database('CNPq', show_sql = show_sql)
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
        self.dados_gerais = None
        self.publicações=[]

        #Pegando o Lattes
        
        if not self.id == None:
            self.lattes = Lattes(id, auto_save_json_to_bd = self.auto_save_json_to_bd)
            if self.lattes.get_lattes():
                self.get_dados_gerais()
            else:
                self.db.execute(f'update all_lattes set erro = true where id = {self.id}')
                self.erro = True
        elif not filename == None:
            load = False
            if filename[:-3].lower() =="zip":
                load = self.lattes.read_zip_from_disk(filename=filename)
                if load: 
                    self.lattes.get_lattes()
                    self.get_dados_gerais()
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
    def salva_indicadores_no_bd (self):
        if self.list_indicadores == None or len(self.list_indicadores) == 0: return False
        sql = ''

        #Apgando se for para atualizar
        if self.on_conflic_update:
            sql = f'delete from public."indicadores" where id = %s;'
            sql = self.db.cursor.mogrify(sql, [int(self.id)])
            if self.show_sql: print (sql)
            self.db.execute(sql)

        #Inserindo
        args_str = ','.join((self.db.cur.mogrify("(%s,%s,%s,%s,%s)", x).decode("utf-8")) for x in self.list_indicadores)
        sql = '''
                insert into public."indicadores"
                    (id, ano, path, tipo, qty)
                VALUES ''' + (args_str) + ';'
        sql = self.db.cursor.mogrify(sql)
        if self.show_sql: print (sql)
        return self.db.execute(sql)

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
                        procura_palavras_chave(json = item, path = path + [k] + [num], palavras_chave = palavras_chave)
                        num +=1
                else:
                    if not v == None:
                        if k[0:15] == '@PALAVRA-CHAVE-':
                            if (len(v) > 2):
                                if not v in palavras_chave:
                                    palavras_chave.append(v)
                    else:
                        pass
            return palavras_chave

        self.palavras_chave = procura_palavras_chave(json = json, path = path, palavras_chave=palavras_chave)
        return True

    @timing
    def salva_palavras_chave_no_bd (self):
        if self.palavras_chave == None or len(self.palavras_chave) == 0: return False
        if self.on_conflic_update:
            sql = "DELETE from palavras_chave WHERE id = %s;\n"
            sql = self.db.cursor.mogrify(sql, (self.id,)).decode("utf-8")
        else: sql = ''
        args_str = ','.join((self.db.cursor.mogrify("(" + str(self.id) + ",%s)", (x,)).decode("utf-8")) for x in self.palavras_chave)
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
    def salva_areas_do_conhecimento_no_bd (self):
        if self.areas_conhecimento == None or len(self.areas_conhecimento) == 0: return False
        sql = ''
        if self.on_conflic_update:
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
    def salva_publicações_no_bd(self):
        if self.lista_de_publicações == None or len(self.lista_de_publicações) == 0: return False
        sql = ''
        args_str = ','.join((self.db.cursor.mogrify("\n(%s, %s, %s, %s, %s, %s, %s)", x).decode("utf-8")) for x in self.lista_de_publicações)
        #print(args_str)
        if self.on_conflic_update:
            delete_sql = '''DELETE from publicacoes WHERE id = %s;\n'''
            sql+= self.db.cursor.mogrify(delete_sql, (self.id,)).decode("utf-8")
        sql += '''INSERT INTO publicacoes (id, doi, path, tipo, titulo, ano, natureza)
        VALUES ''' + args_str + ''';
        '''
        if self.show_sql: print (sql)
        self.db.execute(sql)
        return True

    @timing
    def get_dados_gerais(self):
        self.dados_gerais = self.lattes.dados_gerais
        self.get_sexo()
        return True

    @timing
    def salva_dados_gerais_no_bd (self):
        if self.dados_gerais == None or len(self.dados_gerais) == 0: return False
        self.db.insert_dict ('dados_gerais', self.dados_gerais, on_conflict = ['id'])
        return True

    @timing
    def get_vinculos (self):
        self.vinculos = []
        if self.lattes.json == None: return False
        atuações_profissionais = self.lattes.json['CURRICULO-VITAE']['DADOS-GERAIS'].get('ATUACOES-PROFISSIONAIS')
        if not atuações_profissionais == None:
            for lista_atuação in self.lattes.json['CURRICULO-VITAE']['DADOS-GERAIS']['ATUACOES-PROFISSIONAIS']:
                #print(lista_atuação)
                for atuacao in self.get_list(self.lattes.json['CURRICULO-VITAE']['DADOS-GERAIS']['ATUACOES-PROFISSIONAIS'][lista_atuação]):
                    if not atuacao.get('VINCULOS') == None:
                        anos = []
                        instituição = None
                        num_anos = None
                        atual = False
                        enquadramento = None
                        tipo = None
                        vinculos = atuacao['VINCULOS']
                        instituição = atuacao.get('@NOME-INSTITUICAO')
                        for vinculo in self.get_list(vinculos):
                            ano_fim = None
                            ano_inicio = None
                            #print('\n\n', vinculo)
                            ano_fim = self.inteiro(vinculo.get('@ANO-FIM'))
                            ano_inicio = self.inteiro(vinculo.get('@ANO-INICIO'))
                            if ano_fim == None and not ano_inicio == None and ano_inicio > 1800:
                                anos.extend([*range(ano_inicio, 2020, 1)])
                                atual = True
                                enquadramento = vinculo.get('@ENQUADRAMENTO-FUNCIONAL')
                                tipo = vinculo.get('@TIPO-DE-VINCULO')
                            elif not ano_inicio == None and ano_inicio > 1800:
                                anos.extend([*range(ano_inicio, ano_fim +1, 1)])
                        num_anos = len(np.unique(np.array(anos)))
                        self.vinculos.append(
                            {
                                'id': self.id,
                                'instituicao': instituição,
                                'num_anos': num_anos,
                                'atual': atual,
                                'enquadramento': enquadramento,
                                'tipo': tipo,
                            }
                        )
        return True

    @timing
    def salva_vinculos_no_bd (self):
        if not self.vinculos == None and len(self.vinculos) > 0:
            sql = '''
                INSERT INTO vinculos
                    (id, instituicao, num_anos, atual, enquadramento, tipo)
                VALUES
                    {params_list}
                '''
            if self.on_conflic_update:
                sql = 'DELETE FROM vinculos WHERE id = ' + str(self.id) + ';\n' + sql
            data = []
            for chave in self.vinculos:
                linha = []
                for k,v in enumerate(chave):
                    linha.append(chave[v])
                data.append(linha)
            self.db.insert_many(sql, data)

    @timing
    def get_sexo (self):
         
        if self.show_messages:
            print(f"Pegando o sexo do id {self.id} com o nome {self.lattes.dados_gerais['nome']}")
        
        #tabela en_recursos_humanos
        try:
            sexo = self.db.query(f'select cod_sexo from en_recurso_humano where id = {self.id}')
            sexo =  sexo[0][0]
        except:
            sexo = None
        if self.show_messages:
            print('Resultado da tentativa de pegar sexo na tabela en_recurso_humano por id:', sexo)

        #Tabela dados_gerais    
        if sexo == None:  
            if self.show_messages:
                print(f"Pegando o sexo do id {self.id} com o nome {self.lattes.dados_gerais['nome']}")
            try:
                sexo = self.db.query(f'select sexo from dados_gerais where id = {self.id}')
                sexo =  sexo[0][0]
            except:
                sexo = None
            if self.show_messages:
                print('Resultado da tentativa de pegar sexo na tabela dados_gerais:', sexo)
            
        
        if sexo == None:
            if len (self.dados_gerais['nome']) > 2:
                sql = f'''
                    select cod_sexo 
                    from public.en_recurso_humano 
                    where  UPPER(unaccent(split_part(nme_rh,' ',1))) = 
                            UPPER(unaccent(split_part('{self.dados_gerais['nome'].split(sep=" ", maxsplit=1)[0]}',' ',1)))
                    limit 1;
                    '''
                try:
                    sexo = self.db.query(sql)
                    sexo =  sexo[0][0]
                except:
                    sexo = None
            if self.show_messages:
                print('Resultado da tentativa de pegar sexo na tabela en_recurso_humano por nome:', sexo)
        if sexo == None:
            if len (self.dados_gerais['nome']) > 2:
                sexo = self.getGender (self.dados_gerais['nome'])[0][0][0].upper()
                if sexo == 'E': sexo = None
                if self.show_messages:
                    print('Resultado da tentativa de pegar sexo no site:', sexo)        
        self.lattes.dados_gerais['sexo'] = sexo
        self.dados_gerais['sexo'] = sexo
        if self.show_messages:
            print('Sexo encontrado:', sexo)
        return sexo

    @timing
    def getGender(self, names=None):
        if names == None:
            names = self.lattes.dados_gerais['nome']
        url = ""
        cnt = 0
        if not isinstance(names,list):
            names = [names,]
        
        for name in names:
            if url == "":
                url = "name[0]=" + name.split(sep=" ", maxsplit=1)[0]
            else:
                cnt += 1
                url = url + "&name[" + str(cnt) + "]=" + name.split(sep=" ", maxsplit=1)[0]
        url = "https://api.genderize.io?" + url    
        if self.show_messages: print (url)
        req = requests.get(url)
        results = json.loads(req.text)
        
        retrn = []
        for result in results:
            if self.show_messages: print(result)
            try:
                if result["gender"] is not None:
                    retrn.append((result["gender"], result["probability"], result["count"]))
                else:
                    retrn.append((u'None',u'0.0',0.0))
            except:
                retrn.append((u'Erro',u'0.0',0.0))
        return retrn

    @timing
    def atualiza (self, 
                indicadores = True, 
                palavras_chave = True, 
                areas_conhecimento = True, 
                publicações = True, 
                dados_gerais=True,
                vinculos = True,
                ):
        if self.erro == True:
            if self.show_messages: print ('ERRRO - Lattes não está carregado. ID:', self.id)
            return False
        if self.lattes == None:
            if self.show_messages: print ('ERRRO - Lattes não está carregado. ID:', self.id)
            return False
        if indicadores:
            if not self.get_indicadores():
                if self.show_messages: print ('ERRRO - Não foi possível carregar Indicadores. ID:', self.id)
            else:
                self.salva_indicadores_no_bd()
        if palavras_chave:
            if not self.get_palavras_chave():
                if self.show_messages: print ('ERRRO - Não foi possível carregar as Palavras Chaves. ID:', self.id)
            else:
                self.salva_palavras_chave_no_bd()
        if areas_conhecimento:
            if not self.get_areas_conhecimento():
                if self.show_messages: print ('ERRRO - Não foi possível carregar Áreas do Conhecimento. ID:', self.id)
            else:
                self.salva_areas_do_conhecimento_no_bd()
        if publicações:
            if not self.get_publicações():
                if self.show_messages: print ('ERRRO - Não foi possível carregar Publicações. ID:', self.id)
            else:
                self.salva_publicações_no_bd()
        if vinculos:
            if not self.get_vinculos():
                if self.show_messages: print ('ERRRO - Não foi possível carregar Vínculos. ID:', self.id)
            else:
                self.salva_vinculos_no_bd()
        if dados_gerais:
            if not self.get_dados_gerais():
                if self.show_messages: print ('ERRRO - Não foi possível carregar Dados Pessoais. ID:', self.id)
            else:
                self.salva_dados_gerais_no_bd()



