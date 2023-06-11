drop table if exists ids_doutorandos_inicio_em_2014;

CREATE TABLE ids_doutorandos_inicio_em_2014 AS
	SELECT distinct(id) FROM indicadores AS ind_a where 
	 tipo = '@ANO-DE-INICIO DOUTORADO ' AND
	 ano = 2014	 and
	 (
		SELECT min(ano) from indicadores AS ind_b
		 where tipo = '@ANO-DE-INICIO DOUTORADO '
		 and ind_b.id = ind_a.id
	 ) = 2014;

select * from ids_doutorandos_inicio_em_2014;