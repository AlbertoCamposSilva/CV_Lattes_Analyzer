insert into ids_que_faltam_fazer

select distinct demanda_bruta.id from demanda_bruta
inner join pagamentos
	on demanda_bruta."Processo" = pagamentos."Processo"
inner join indicadores 
	on indicadores.id = CAST(demanda_bruta.id AS BIGINT)