from ntpath import join
import psycopg2
from psycopg2.extensions import AsIs
from configparser import ConfigParser


class Database:
    def __init__(self, name = 'CNPq'):
        self.params = Database.config_db_connection()
        self.conn = psycopg2.connect(**self.params)
        self.cur = self.conn.cursor()

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
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))
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
        self.cursor.execute(sql, params or None)
        self.commit()
        self.close()

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def query(self, sql, params=None, many = True):
        if not params == None and (
                type(params) == str or
                type(params) == int or
                type(params) == float):
            params = [params]
        self.cursor.execute(sql, params or None)
        if many: retorno = self.fetchall()
        else: retorno = self.fetchone()
        self.close()
        return retorno 

    def insert_many (self, sql, params_list, params):
        args_str = ','.join((self.cur.mogrify("(%s,%s,%s)", x).decode("utf-8")) for x in params_list)
        sql = sql.replace('{params_list}', args_str)
        self.query(sql, params or None)
        self.close()

    def insert_dict (self, column_name, dict, on_conflict = [], on_conflict_do_nothing = False):
        '''Constrói um SQL a partir de um dicionário, com a opção de atualiar em caso de conflito.

Argumentos:

column: Nome da coluna a ser atualizada;
dict: O dicionário. Nome das chaves devo coincidir com o nome das colunas.
on_conflict: Uma lista com o nome das chaves primárias da tabela. 
on_conflict_do_nothing: Se False -> quando houver conflito nas chaves acima mencionadas, atualizará a tabela.
    Se true -> quandou houver conflito, não atualizará a tabela (DO NOTHING)

        '''
        sql = 'insert into ' + column_name
        #sql = self.cursor.mogrify(sql, (column_name,)).decode("utf-8")
        sql += '(%s) values %s'
        columns = dict.keys()
        if len(on_conflict) > 0:
            sql += f"\nON CONFLICT ({','.join(on_conflict)}) DO "
            if on_conflict_do_nothing: sql += 'NOTHING'
            else:
                sql +="UPDATE SET\n"
                for column in columns:
                    sql += (f'\n{column} = EXCLUDED.{column},')
                sql = sql[:-1]+';'
        values = [dict[column] for column in columns]
        new_sql = self.cursor.mogrify(sql, (AsIs(','.join(columns)), tuple(values)))
        self.execute(new_sql)
        self.close()