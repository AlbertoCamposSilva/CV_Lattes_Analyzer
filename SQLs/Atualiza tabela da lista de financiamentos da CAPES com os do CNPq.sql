update financiamentos 
set cnpq = pagamentos.pagtos
from (
	select id, sum("Valor Pago") AS pagtos from pagamentos, dados_gerais
	where pagamentos."Beneficiário" = dados_gerais.nome
		and "Ano Referência" >= 2014
		and "Ano Referência" < 2019
		and (
			"Modalidade" = 'GD - Doutorado'
			or "Modalidade" = 'GDE - Doutorado no Exterior'
			or "Modalidade" = 'SWE - Doutorado Sanduíche no Exterior'
			or "Modalidade" = 'SWI - Doutorado-Sanduiche Empresarial'
			or "Modalidade" = 'SWP - Doutorado-Sanduiche no Pais')
	Group by id
	) AS pagamentos
where financiamentos.id = pagamentos.id