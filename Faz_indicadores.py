from Lattes import Lattes
import pandas
import psycopg2


indicadores = pandas.DataFrame


SQL = '''select * from indicadores where id in
    (select distinct id 
    from all_lattes 
    natural join carga_dados_pessoais 
    where all_lattes.dt_atualizacao > %s)
    '''
conn = None
try:
    params = Database.config_db_connection()
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    ids = cur.execute(SQL, data)
    indicadores = cur.fetchall()
    conn.commit()
    cur.close()
    print("Banco de dados atualizado. XML inserted.")
    #return ids
except (Exception, psycopg2.DatabaseError) as error:
    print("Erro ao Inserir Currículo no BD: ", error)
    #return (error)
finally:
    if conn is not None:
        conn.close()

