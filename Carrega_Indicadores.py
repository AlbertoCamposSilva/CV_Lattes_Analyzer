from datetime import datetime
import os
from Lattes import Lattes
from Indicadores import Indicadores
from Database import Database
from pandas import pandas as pd
print('Importações Iniciais')
print('Início em: ', datetime.now())
print('Fim das importações: ', datetime.now())


def faz_carga(pasta):
    print('Carregando Pastas')
    caminhos = [os.path.join(pasta, nome) for nome in os.listdir(pasta)]
    print('Carergando aquivos')
    arquivos = [arq for arq in caminhos if os.path.isfile(arq)]
    print('Fazendo lista de arquivos a importar')
    zips = [arq for arq in arquivos if arq.lower().endswith(".zip")]
    número = 0
    for zip in zips:
        if os.path.basename(zip)[0:7] == 'Lattes_':
            número += 1
            id = os.path.basename(zip)[7:-4]
            print(f'{número}: Recuperando dados do Currículo: {id}')
            lattes = Lattes()
            lattes.id = id

            if lattes.read_zip_from_disk():
                lattes.get_xml()
                lattes.save_json_to_disk(path='d:/Lattes_JSON/')
                lattes.save_xml_to_disk(path='d:/Lattes_XML/')
                lattes.get_indicadores()
                lattes.update_indicadores_bd()
            else:
                print('Erro ao carregar arquivo:', lattes.id)


class Carga:
    # Apenas um exemplo de como usar a função map em uma classe - desconsiderar

    def __init__(self, pasta=r'C:\Downloads'):
        self.pasta = pasta
        self.indicadores = []
        self.indicadores = list(
            map(self.get_indicators, self.pega_lista_zips()))

    def pega_lista_zips(self, pasta=None):
        # Pega Lista de Totos os Indicadores
        if not pasta == None:
            self.pasta = pasta
        caminhos = [os.path.join(self.pasta, nome)
                    for nome in os.listdir(self.pasta)]
        arquivos = [arq for arq in caminhos if os.path.isfile(arq)]
        zips = [arq for arq in arquivos if arq.lower().endswith(".zip")]
        return zips

    def get_indicators(self, arq):
        print(f'calling get with arq {arq}')
        # Com a lista de indicadores, coloca todos na variável da classe Indicadores.Indicadores
        número = 0
        if os.path.basename(arq)[0:7] == 'Lattes_':
            número += 1
            id = os.path.basename(arq)[7:-4]
            print(f'{número}: Recuperando dados do Currículo: {id}')
            lattes = Lattes()
            lattes.id = id
            lattes.read_zip_from_disk()
            indicadores = Indicadores(lattes.xml, id=id)
            indicadores.get_indicadores()
            return indicadores.indicadores


def carrega_lista_ids(ids_para_importar=[],
                      ano_início=2014,
                      ano_fim=2020,
                      nível_início=0,
                      nível_fim=0,
                      novos=True,):
    print('Carregando indicadores na memória. Início em: ', datetime.now())

    db = Database('CNPq')
    engine = db.db_engine()

    sql = "select all_lattes.id from all_lattes"
    if novos:
        sql += """
    left join dados_gerais
        on all_lattes.id = dados_gerais.id
    where dados_gerais.dt_importacao is null
        and not all_lattes.erro = True
    """
    if ano_início > 0:
        sql += f"and all_lattes.dt_atualizacao > '01/01/{ano_início}'\n"
    if ano_fim > 0:
        sql += f"and all_lattes.dt_atualizacao < '31/12/{ano_fim}'\n"
    if nível_início > 0:
        sql += f"and all_lattes.cod_nivel > {nível_início}\n"
    if nível_fim > 0:
        sql += f"and all_lattes.cod_nivel < {nível_fim}\n"

    print()
    print("Executando a consulta:")
    print(sql)
    dt = pd.read_sql(sql, engine)
    print(f'dt.size: {dt.size}')
    if len(ids_para_importar) > 0:
        dt = dt.loc[dt.id.astype(str).str[0].isin(ids_para_importar)]
    print('Término em: ', datetime.now())

    return dt


def carrega_os_indicadores_pelo_zip(dt, verbose=True, mostra_a_cada=1000):
    número_ids_total = dt.size
    número_ids_já_feitos = 0
    tempo_início = datetime.now()
    if verbose:
        print(f'Iniciado em {tempo_início}.')
    num_imortacoes = -1
    pular_no_início = 0

    for id in dt.iterrows():
        if número_ids_já_feitos < pular_no_início:
            número_ids_já_feitos += 1
            continue
        if verbose and not número_ids_já_feitos == 0:
            porcentagem_já_feita = (número_ids_já_feitos/número_ids_total)
            tempo_passado = datetime.now() - tempo_início
            tempo_por_id = tempo_passado / número_ids_já_feitos
            tempo_restante = (número_ids_total - número_ids_já_feitos) * tempo_por_id
            tempo_em_que_vai_acabar = datetime.now() + tempo_restante
            if número_ids_já_feitos % mostra_a_cada == 0:
                print(f'{número_ids_já_feitos}/{número_ids_total}. {porcentagem_já_feita * 100}% feitos. Fazendo id: {id}. Acabará em {tempo_em_que_vai_acabar}. O Último demorou: {datetime.now() - tempo_último}.')
        else:
            if verbose and número_ids_já_feitos % mostra_a_cada == 0:
                print(f'{número_ids_já_feitos}/{número_ids_total}. Fazendo id: {id}.')
        tempo_último = datetime.now()

        indicador = Indicadores(id=str(int(id[1])))
        indicador.show_messages = False
        indicador.show_sql = False
        indicador.atualiza()
        número_ids_já_feitos += 1
        if num_imortacoes > 0 and número_ids_já_feitos > num_imortacoes:
            break
    if verbose:
        print(f'Último atualizado. {número_ids_já_feitos} / {número_ids_total} realizados.')
