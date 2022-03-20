from tkinter import NONE
from Lattes import Lattes
from Carga import Carga
from Database import Database
import psycopg2
import pandas, os
import statsmodels.api as sm
from urllib.parse import urlencode
from psycopg2.extensions import AsIs

class Regressao:

    def __init__ (self, 
                data_atualização = '2020-01-01', 
                path='d:/Lattes/Linnear Regression Models/', 
                indicador = None, 
                programa=None, 
                CA=None, 
                área=None, 
                chamada=None,
                ano_início = 2014,
                ano_fim = 2019,
                ):
        self.tipo_indicador = indicador
        self.ano_início = ano_início
        self.ano_fim = ano_fim
        self.data_atualização=data_atualização
        self.path=path
        self.programa=programa
        self.select_programa = True
        self.CA=CA
        self.select_CA = False
        self.área=área
        self.select_área = False
        self.chamada=chamada
        self.select_chamada = True
        self.include = []
        self.média_investimento = None
        self.total_investido = None
        self.lista_indicadores = []
        self.lista_cas = []
        self.lista_chamadas = []
        self.lista_programas = []
        self.est2 = None

        self.db = Database('CNPq')

    def gera_sql (  self, 
                    ignore_filters = False
                    ):        
        sql_select = f'''
        select indicadores.id 
            ,indicadores_nomes.nome as tipo
            ,pgtos'''
        for ano in range(self.ano_início, self.ano_fim + 1):
            sql_select+=f'\n            ,sum(qty) FILTER (WHERE ano <= {ano}) AS qty_{ano}'

        sql_from = '''
        from demanda_bruta
        left join
                (select "Processo" as processo, sum("Valor Pago") as pgtos from pagamentos
                where "Processo" in (select "Processo" from demanda_bruta)
                group by "Processo") AS pgtos
            on demanda_bruta."Processo" = pgtos.processo
        left join indicadores
            on CAST(demanda_bruta.id as bigint) = indicadores.id
        inner join all_lattes
            on CAST(demanda_bruta.id as bigint) = all_lattes.id
        inner join indicadores_nomes
            on indicadores.tipo = indicadores_nomes.tipo
        '''

        sql_where = f"""
        WHERE
            all_lattes.dt_atualizacao > '{self.data_atualização}'"""
        
        sql_group_by = '''
        GROUP BY
            indicadores.id 
            ,indicadores_nomes.nome
            ,demanda_bruta."Processo"
            ,demanda_bruta."Chamada"
            ,pgtos.pgtos'''
        
        if not self.tipo_indicador == None:
            if not ignore_filters:
                sql_where += f"\n            and indicadores_nomes.nome  = '{self.tipo_indicador}'"
        if not self.chamada == None:
            if not ignore_filters:
                sql_where += f'\n            and demanda_bruta.\"Chamada\" = \'{self.chamada}\''
        if not self.programa == None:
            self.select_programa = True
            if not ignore_filters:
                sql_where += f'\n            and demanda_bruta."Programa" = \'{self.programa}\''
        if not self.CA == None:
            self.select_CA = True
            if not ignore_filters:
                sql_where += f'\n            and demanda_bruta."CA" = \'{self.CA}\''
        if not self.área == None:
            self.select_área = True
            sql_from += '''
                        inner join areas_conhecimento
                            on CAST(demanda_bruta.id as bigint) = areas_conhecimento.id'''
            if not ignore_filters:
                sql_where += f"\n            and areas_conhecimento.area = \'{self.área}\'"
            

        if self.select_chamada:
            sql_select += '\n            ,"Chamada" as chamada'
        if self.select_área:
            sql_select += '\n            ,areas_conhecimento.area'
            sql_group_by += '\n            ,areas_conhecimento.area'
        if self.select_programa:
            sql_select += '\n            ,demanda_bruta."Programa" AS programa'
            sql_group_by += '\n            ,demanda_bruta."Programa"'
        if self.select_CA:
            sql_select += '\n            ,demanda_bruta."CA" AS ca'
            sql_group_by += '\n            ,demanda_bruta."CA"'

        self.sql = sql_select + sql_from + sql_where + sql_group_by

    def get_parâmetros(self):
        parâmetros = {
            'chamada': self.chamada,
            'programa': self.programa,
            'CA': self.CA,
            'área': self.área,
            'indicador': self.tipo_indicador,
            'data': self.data_atualização,
            }
        return parâmetros

    def grava_resultados (self):
        if not self.est2 == None:
            filename = self.path + urlencode(self.get_parâmetros(), doseq=True) + ".pickle"   
            self.est2.save(filename)
            resultado = {
                        'chamada': self.chamada,
                        'programa': self.programa,
                        'indicador': self.tipo_indicador,
                        'data': self.data_atualização,
                        'ca': self.CA,
                        'area': self.área,
                        'total_investido': self.total_investido,
                        'media_investimento': self.média_investimento,
                        'f_total': self.est2.f_pvalue,
                        'f_pagtos': self.est2.pvalues.get('pgtos'),
                        'parametro_pgtos': self.est2.params.get('pgtos'),
                        'f_qty_i': self.est2.pvalues.get('qty_' + str(self.ano_início)),
                        'parametro_qty_i': self.est2.params.get('qty_' + str(self.ano_início)),
                        'f_const': self.est2.pvalues.get('const'),
                        'parametro_const': self.est2.params.get('const'),
                        'r2': self.est2.rsquared,
                        'num_observacoes': self.est2.nobs,
                        }
        else:
            resultado = {
                        'chamada': self.chamada,
                        'programa': self.programa,
                        'indicador': self.tipo_indicador,
                        'data': self.data_atualização,
                        'ca': self.CA,
                        'area': self.área,
                        'total_investido': self.total_investido,
                        'media_investimento': self.média_investimento,
                        'f_total': None,
                        'f_pagtos': None,
                        'parametro_pgtos': None,
                        'f_qty_i': None,
                        'parametro_qty_i': None,
                        'f_const': None,
                        'parametro_const': None,
                        'r2': None,
                        'num_observacoes': None,
                        }

        for key in resultado.keys():
            if pandas.isnull(resultado[key]):
                resultado[key] = None
                

        self.db.insert_dict(column_name='resultados_regressao_linear', dict = resultado, on_conflict = ["chamada", "programa", "indicador"])
        self.db.commit()


    def já_feita(self):
        # filename = self.path + urlencode(self.get_parâmetros(), doseq=True)
        # if os.path.isfile(filename):
        #     return True
        existe = False
        SQL = '''
                SELECT count(*) 
                FROM resultados_regressao_linear
                WHERE
                    chamada = %s and
                    programa = %s and
                    indicador = %s and
                    data = %s
                ''' 
        data = (self.chamada, self.programa, self.tipo_indicador, self.data_atualização)
        num_indicadores = self.db.query(SQL, data)
        if int(num_indicadores[0][0]) > 0:
            existe = True
        return existe

    def get_pd (self, chamada = None, ignore_filters = False):
        if not chamada == None:
            self.chamada = chamada
        self.gera_sql(ignore_filters = ignore_filters)
        #print(SQL)
        engine = Carga.db_engine()
        self.pd = pandas.read_sql(self.sql, engine)
        self.pd['pgtos'] = pandas.to_numeric(self.pd['pgtos'].fillna(0))
        for ano in range(self.ano_início, self.ano_fim + 1):
            self.pd['qty_' + str(ano)] = pandas.to_numeric(self.pd['qty_' + str(ano)].fillna(0))
        self.pd.dropna(subset = ["id"], inplace=True)


    def fit (self, refaz = False):
        data = self.pd
        if refaz or not self.já_feita():
            if not self.tipo_indicador == None:
                data = data[data.tipo == self.tipo_indicador]
            if not self.chamada == None:
                data = data[data.chamada == self.chamada]
            if not self.programa == None:
                data = data[data.programa == self.programa]
            if not self.CA == None:
                data = data [data.ca == self.CA]
            if not self.área == None:
                data = data [data.area == self.área]
            X = data[['pgtos', 'qty_' + str(self.ano_início)]]
            y = pandas.DataFrame(data, columns=['qty_' + str(self.ano_fim)])
            self.média_investimento = float(data[data['pgtos']!=0].pgtos.mean())
            self.total_investido = float(data[data['pgtos']!=0].pgtos.sum())
            try:
                print('Começando estimativa...')
                X2 = sm.add_constant(X)
                est = sm.OLS(y, X2)
                self.est2 = est.fit()
                print('Regressão realizada. Gravando resultados.')
                self.grava_resultados ()       
                return self.est2.summary()
            except Exception as e:
                self.est2 = None
                self.grava_resultados () 
                return 'Erro na regressão: ' + str(e)                
        else:
            return 'Regressão já realizada - não será feita novamente.'

    def pega_lista_indicadores (self):
        if self.lista_indicadores == []:
            SQL = '''
                    select distinct nome from indicadores_nomes
                    ''' 
            self.lista_indicadores = [x[0] for x in self.db.query(SQL)]
        return self.lista_indicadores

    def pega_lista_programas (self):
        if self.lista_programas == []:
            SQL = '''
                    select distinct "Programa" from demanda_bruta
                    ''' 
            self.lista_programas = [x[0] for x in self.db.query(SQL)]
        return self.lista_programas

    def pega_lista_chamadas (self):
        if self.lista_chamadas == []:
            SQL = '''
                    select distinct "Chamada" from demanda_bruta
                    ''' 
            self.lista_chamadas = [x[0] for x in self.db.query(SQL)]
        return self.lista_chamadas

    def pega_lista_cas (self):
        if self.lista_cas == []:
            SQL = '''
                    select distinct "CA" from demanda_bruta
                    ''' 
            self.lista_cas = [x[0] for x in self.db.query(SQL)]
        return self.lista_cas

    def faz_regressoes (self, 
            atualiza_listas = True, 
            data_atualização = '2020-01-01', 
            refaz = False):
        self.data_atualização = data_atualização
        if atualiza_listas:
            print('Pegando listas de regressões:')
            self.pega_lista_chamadas()
            self.pega_lista_programas()
            self.pega_lista_indicadores()
            print('Pegando lista de indicadores no BD')
            self.select_chamada = True
            self.select_programa = True
            self.get_pd(ignore_filters = True)        
        print('Começando a regressão.')
        num_chamada = 0
        num_programa = 0
        num_indicador = 0
        for self.chamada in self.lista_chamadas:

            num_chamada += 1
            num_programa = 0
            for self.programa in self.lista_programas:
                num_programa += 1
                num_indicador = 0
                for self.tipo_indicador in self.lista_indicadores:
                    num_indicador +=1
                    self.est = None
                    print (f'''
Regressão Linear:
Chamada {num_chamada} / {len(self.lista_chamadas)}: {self.chamada}   
Programa {num_programa} / {len(self.lista_programas)}: {self.programa}                 
Indicador {num_indicador} / {len(self.lista_indicadores)}: {self.tipo_indicador}''')
                    resultado = self.fit(refaz = refaz)
                    #os.system('cls')
                    print(f'''
Resultado:
{resultado}

___
'''                    )
        self.db.close()