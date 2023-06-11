/*create tablespace tmp_huge location 'D:\PostgreSQL';
alter database "CNPq" set temp_tablespaces = tmp_huge ;
GRANT ALL ON TABLESPACE tmp_huge to lattes_user;*/

/*copy (*/


/*DROP TABLE IF EXISTS public.indicadores_pareamento;*/

create table indicadores_pareamento as
	SELECT indicadores.id 
				,indicadores_nomes.grupo as grupo
				,pgtos
				,sexo
				,uf
				,sum(qty) FILTER (WHERE ano <= 2012) AS qty_2012
				,sum(qty) FILTER (WHERE ano <= 2013) AS qty_2013
				,sum(qty) FILTER (WHERE ano <= 2014) AS qty_2014
				,sum(qty) FILTER (WHERE ano <= 2015) AS qty_2015
				,sum(qty) FILTER (WHERE ano <= 2016) AS qty_2016
				,sum(qty) FILTER (WHERE ano <= 2017) AS qty_2017
				,sum(qty) FILTER (WHERE ano <= 2018) AS qty_2018
				,sum(qty) FILTER (WHERE ano <= 2019) AS qty_2019
				,"Chamada" as chamada
				,demanda_bruta."Programa" AS programa
				,demanda_bruta."Área do Conhecimento" AS area_demanda_bruta
				,areas_conhecimento
				,instituicoes
				,num_anos AS num_anos_na_instituicao
				,enquadramentos AS enquadramento_vinculo
				,tipos AS tipos_vinculo
				,ano_doutorado
			from all_lattes
			left join demanda_bruta
				on all_lattes.id = CAST(demanda_bruta.id as bigint)
			left join
					(select "Processo" as processo, sum("Valor Pago") as pgtos from pagamentos
					where "Processo" in (select "Processo" from demanda_bruta)
					group by "Processo") AS pgtos
				on demanda_bruta."Processo" = pgtos.processo
			left join indicadores
				on all_lattes.id = indicadores.id
			inner join indicadores_nomes
				on indicadores.tipo = indicadores_nomes.tipo
			left join public.dados_gerais
				on public.dados_gerais.id = public.all_lattes.id
			left join (
				select id, string_agg(area, ', ') AS areas_conhecimento
				from public.areas_conhecimento 
				group by id
				) AS areas
				on areas.id = all_lattes.id
			left join (
				SELECT id, 
					string_agg(instituicao, ', ') AS instituicoes
					,string_agg(CAST(num_anos AS TEXT), ', ') AS num_anos
					,string_agg(enquadramento, ', ') AS enquadramentos
					,string_agg(tipo, ', ') AS tipos
				FROM vinculos
				WHERE atual = true
				GROUP BY id) AS tbl_vinculos
				on tbl_vinculos.id = all_lattes.id
			left join (
				SELECT id, MIN(ano) as ano_doutorado from public.indicadores
				where tipo = '@ANO-DE-CONCLUSAO DOUTORADO '
				group by id
				) as primeiro_ano_doutorado
				on all_lattes.id = primeiro_ano_doutorado.id
			WHERE
				all_lattes.dt_atualizacao > '2020-01-01'
				/*and not ano_doutorado is null*/
				and not indicadores_nomes.grupo IS NULL
				/*and all_lattes.id = 1600461423386842*/
			GROUP BY
				indicadores.id 
				,indicadores_nomes.grupo
				,demanda_bruta."Processo"
				,demanda_bruta."Chamada"
				,pgtos.pgtos
				,demanda_bruta."Programa"
				,dados_gerais.sexo
				,dados_gerais.uf
				,demanda_bruta."Área do Conhecimento" 
				,areas_conhecimento
				,instituicoes
				,num_anos 
				,enquadramentos 
				,tipos
				,ano_doutorado
			/*LIMIT 200*/

/*) to 'D:\Lattes\indicadores_para_regressao.csv' with csv*/
;

copy public.indicadores_pareamento to 'D:\Lattes\indicadores_para_regressao.csv' with csv
