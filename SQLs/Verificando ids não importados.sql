select distinct(enquadramento) as enquadramento, count(distinct demanda_bruta.id) as qty from demanda_bruta
inner join pagamentos
	on demanda_bruta."Processo" = pagamentos."Processo"
inner join vinculos
	on cast(demanda_bruta.id AS BIGINT) = vinculos.id
group by enquadramento

select count(*) from demanda_bruta
inner join pagamentos
	on demanda_bruta."Processo" = pagamentos."Processo"
inner join all_lattes
	on all_lattes.id = cast(demanda_bruta.id as bigint)
where dt_atualizacao >= '2020-01-01'

Menor -> 870
Maior oi igual -> 22.439

select distinct demanda_bruta.id from demanda_bruta
inner join pagamentos
	on demanda_bruta."Processo" = pagamentos."Processo"
inner join all_lattes
	on all_lattes.id = cast(demanda_bruta.id as bigint)
where dt_atualizacao >= '2020-01-01'	
and cast(demanda_bruta.id as bigint) not in (select distinct id from indicadores_pareamento)

select id from public.indicadores_pareamento where id = 9012359647335296