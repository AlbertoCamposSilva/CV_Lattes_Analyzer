/*create tablespace tmp_huge location 'D:\PostgreSQL';
alter database "CNPq" set temp_tablespaces = tmp_huge ;
GRANT ALL ON TABLESPACE tmp_huge to lattes_user;*/


DROP TABLE IF EXISTS public.indicadores_doutorado;

create table indicadores_doutorado as
	SELECT indicadores.id 
				,indicadores.tipo AS indicador_tipo
				,indicadores_nomes.grupo AS indicador_grupo
				,indicadores_nomes.nome AS indicador
				,sum(qty) FILTER (WHERE ano <= 2012) AS qty_2012
				,sum(qty) FILTER (WHERE ano <= 2013) AS qty_2013
				,sum(qty) FILTER (WHERE ano <= 2014) AS qty_2014
				,sum(qty) FILTER (WHERE ano <= 2015) AS qty_2015
				,sum(qty) FILTER (WHERE ano <= 2016) AS qty_2016
				,sum(qty) FILTER (WHERE ano <= 2017) AS qty_2017
				,sum(qty) FILTER (WHERE ano <= 2018) AS qty_2018
				,sum(qty) FILTER (WHERE ano <= 2019) AS qty_2019
			from all_lattes
			left join indicadores
				on all_lattes.id = indicadores.id
			left join indicadores_nomes
				on indicadores.tipo = indicadores_nomes.tipo
			WHERE
				all_lattes.dt_atualizacao > '2020-01-01'
				and all_lattes.id in (select id from public.ids_doutorandos_inicio_em_2014)
			GROUP BY
				indicadores.id 
				,indicadores.tipo
				,indicadores_nomes.grupo
				,indicadores_nomes.nome


/*copy public.indicadores_doutorado to 'D:\Lattes\indicadores_para_regressao_doutorado_2014.csv' with csv*/
