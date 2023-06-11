select distinct (id) from pagamentos, dados_gerais
	where "Linha de Fomento" = 'Bolsas de Doutorado' 
		and UPPER(pagamentos."Beneficiário") = UPPER(dados_gerais.nome)
		and SUBSTRING("Processo",8,4) = '2014'

	
select distinct (id) from pagamentos, dados_gerais
	where "Linha de Fomento" = 'Bolsas de Doutorado' 
		and UPPER(pagamentos."Beneficiário") = UPPER(dados_gerais.nome)
		and "Ano Referência" >= 2014 and "Ano Referência" < 2020	