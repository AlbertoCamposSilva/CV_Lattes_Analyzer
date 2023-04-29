from ntpath import join
import psycopg2
from psycopg2.extensions import AsIs
from configparser import ConfigParser

# Fazendo psycopg2 conseguir trabalhar com NP
# https://stackoverflow.com/questions/39564755/programmingerror-psycopg2-programmingerror-cant-adapt-type-numpy-ndarray
import numpy as np
from psycopg2.extensions import register_adapter, AsIs


def addapt_numpy_float64(numpy_float64):
    return AsIs(numpy_float64)


def addapt_numpy_int64(numpy_int64):
    return AsIs(numpy_int64)


def addapt_numpy_float32(numpy_float32):
    return AsIs(numpy_float32)


def addapt_numpy_int32(numpy_int32):
    return AsIs(numpy_int32)


def addapt_numpy_array(numpy_array):
    return AsIs(tuple(numpy_array))


register_adapter(np.float64, addapt_numpy_float64)
register_adapter(np.int64, addapt_numpy_int64)
register_adapter(np.float32, addapt_numpy_float32)
register_adapter(np.int32, addapt_numpy_int32)
register_adapter(np.ndarray, addapt_numpy_array)


class Database:
    def __init__(self, name='CNPq', show_sql=False):
        self.params = Database.config_db_connection()
        self.conn = psycopg2.connect(**self.params)
        self.cur = self.conn.cursor()
        self.show_sql = show_sql
        self.rollback()

    @staticmethod
    def db_engine():
        params = Database.config_db_connection()
        username = params['user']
        password = params['password']
        ipaddress = params['host']
        port = int(params['port'])
        dbname = params['database']
        return f'postgresql://{username}:{password}@{ipaddress}:{port}/{dbname}'

    @staticmethod
    def engine():
        return Database.db_engine()

    @staticmethod
    def config_db_connection(filename='d:/Lattes/database.ini', section='postgresql'):
        parser = ConfigParser()
        parser.read(filename)
        db = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db[param[0]] = param[1]
        else:
            raise Exception(
                'Section {0} not found in the {1} file'.format(section, filename))
        return db

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def connection(self):
        return self.conn

    @property
    def cursor(self):
        return self.cur

    def commit(self):
        self.connection.commit()

    def rollback(self):
        if not self.connection.closed == 0:
            self.connection.rollback()

    def close(self, commit=True):
        if not self.connection.closed == 0:
            if commit:
                self.commit()
            self.cursor.close()
            self.connection.close()

    def execute(self, sql, params=None):
        if not params == None and (
                type(params) == str or
                type(params) == int or
                type(params) == float):
            params = [params]
        sql_to_execute = self.cursor.mogrify(sql, params or None)
        if self.show_sql:
            print(sql_to_execute)
        try:
            self.cursor.execute(sql_to_execute)
        except:
            pass
        self.commit()
        self.close()

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def query(self, sql, params=None, many=True):
        if not params == None and (
                type(params) == str or
                type(params) == int or
                type(params) == float):
            params = [params]
        sql_to_execute = self.cursor.mogrify(sql, params or None)
        if self.show_sql:
            print(sql_to_execute)
        try:
            self.cursor.execute(sql_to_execute)
        except:
            pass
        if many:
            retorno = self.fetchall()
        else:
            retorno = self.fetchone()
        self.close()
        return retorno

    def insert_many(self, sql, params_list: list or None = None, params=None):
        if not params_list == None or len(params_list) > 0:
            params_list_string = '(' + \
                ','.join(["%s" for _ in range(len(params_list[0]))]) + ')'
            args_str = ','.join(
                (self.cur.mogrify(params_list_string, x).decode("utf-8")) for x in params_list)
            sql = sql.replace('{params_list}', args_str)
        if self.show_sql:
            print(sql)
        self.execute(sql, params)
        self.close()

    def insert_dict(self, column_name, dict, on_conflict=[], on_conflict_do_nothing=False):
        '''Constrói um SQL a partir de um dicionário, com a opção de atualiar em caso de conflito.

Argumentos:

column: Nome da coluna a ser atualizada;
dict: O dicionário. Nome das chaves devo coincidir com o nome das colunas.
on_conflict: Uma lista com o nome das chaves primárias da tabela. 
on_conflict_do_nothing: Se False -> quando houver conflito nas chaves acima mencionadas, atualizará a tabela.
    Se true -> quandou houver conflito, não atualizará a tabela (DO NOTHING)

        '''
        sql = 'insert into ' + column_name
        # sql = self.cursor.mogrify(sql, (column_name,)).decode("utf-8")
        sql += '(%s) values %s'
        columns = dict.keys()
        if len(on_conflict) > 0:
            sql += f"\nON CONFLICT ({','.join(on_conflict)}) DO "
            if on_conflict_do_nothing:
                sql += 'NOTHING'
            else:
                sql += "UPDATE SET\n"
                for column in columns:
                    sql += (f'\n{column} = EXCLUDED.{column},')
                sql = sql[:-1]+';'
        values = [dict[column] for column in columns]
        new_sql = self.cursor.mogrify(
            sql, (AsIs(','.join(columns)), tuple(values)))
        if self.show_sql:
            print(new_sql)
        self.execute(new_sql)
        self.close()
