select distinct id from demanda_bruta inner join pagamentos on demanda_bruta."Processo" = pagamentos."Processo"

13.104

select count (distinct id) from pareamentos

10.217


select count (distinct id) from demanda_bruta inner join pagamentos
on demanda_bruta."Processo" = pagamentos."Processo"
where not CAST(id AS BIGINT) IN (select distinct id from pareamentos);

2.887