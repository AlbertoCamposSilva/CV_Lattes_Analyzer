select distinct areas_conhecimento.id from public.areas_conhecimento 
inner join public.dados_gerais
	on areas_conhecimento.id = dados_gerais.id
inner join public.vinculos
	on areas_conhecimento.id = vinculos.id
inner join (
				SELECT id, CAST(MIN(ano) AS INTEGER) as ano_doutorado from public.indicadores
				where tipo = '@ANO-DE-CONCLUSAO DOUTORADO '
				group by id
				) as primeiro_ano_doutorado
				on areas_conhecimento.id = primeiro_ano_doutorado.id	

where 1=1
and area = 'Odontologia'
and dados_gerais.sexo = 'F'
and enquadramento like '%PROFESSOR%'
and vinculos.tipo like '%SERVIDOR%'
and ano_doutorado > 1980 
and ano_doutorado < 1990
and uf in ('ES', 'MG', 'RJ', 'SP')