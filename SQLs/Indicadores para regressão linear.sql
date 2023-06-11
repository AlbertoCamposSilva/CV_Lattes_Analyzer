select indicadores.id, 
	indicadores.tipo, 
	lista_indicadores.descricao, 
	demanda_bruta."Processo", 
	"Chamada",
	sum("Valor Pago") FILTER (WHERE "Ano Referência" >= 2014 and "Ano Referência" < 2020) AS pagto,
	sum(qty) FILTER (WHERE ano <= 2014) AS qty_2014,
	sum(qty) FILTER (WHERE ano <= 2020) AS qty_2020
from indicadores inner join demanda_bruta 
	on indicadores.id = cast(demanda_bruta.id AS bigint)
inner join all_lattes 
	on cast(demanda_bruta.id AS bigint) = all_lattes.id
inner join areas_conhecimento
	on all_lattes.id = areas_conhecimento.id
inner join lista_indicadores
	on indicadores.tipo = lista_indicadores.id
left join pagamentos
	on demanda_bruta."Processo" = pagamentos."Processo"
where all_lattes.dt_atualizacao > '2020-01-01'
	and areas_conhecimento.area = 'Física'
	and indicadores.tipo=2
GROUP BY indicadores.id, indicadores.tipo, lista_indicadores.descricao, demanda_bruta."Processo", "Chamada"


