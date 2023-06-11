select indicador, 
	/*f_pagtos, */
	ROUND(sum(parametro_pgtos * total_investido),0) as impacto 
from resultados_regressao_linear
where chamada like '%Universal 2014%'
and f_total < 0.05
and f_pagtos < 0.05
/*and programa like '%EDUCACAO'*/
and (parametro_pgtos * total_investido > 1
	or parametro_pgtos * total_investido < -1)
group by indicador
	/*,f_pagtos*/
order by indica desc


/*TOTAL INVESTIDO NA CHAMADA*/
select sum("Valor Pago")  
from pagamentos, demanda_bruta
where pagamentos."Processo" = demanda_bruta."Processo"
and demanda_bruta."Chamada" like 'Universal 2014 - Faixa %'



/*IMPACTO POR GRAU DE CONFIANÇA COM IMPACTO DE DIFERENÇA EM DIFERENÇAS*/
select indicador,
	ROUND(sum(parametro_pgtos * total_investido)  FILTER 
		(WHERE f_pagtos < 0.01 and 
		 	f_total < 0.01 
				)) as impacto_99,
	ROUND(sum(parametro_pgtos * total_investido)  FILTER 
		(WHERE f_pagtos < 0.05 and 
		 	f_total < 0.05 
				)) as impacto_95,
	ROUND(sum(parametro_pgtos * total_investido)  FILTER 
		(WHERE f_pagtos < 0.1 and 
		 	f_total < 0.1 
				)) as impacto_90,
	ROUND(sum(parametro_pgtos * total_investido)  FILTER 
		(WHERE f_pagtos < 0.3 and 
		 	f_total < 0.3 
				)) as impacto_80,
	ROUND(sum(parametro_pgtos * total_investido)  FILTER 
		(WHERE f_pagtos < 0.3 and 
		 	f_total < 0.3 
				)) as impacto_70,	
	ROUND(sum(parametro_pgtos * total_investido)  FILTER 
		(WHERE f_pagtos < 0.4 and 
		 	f_total < 0.4 
				)) as impacto_60,
	ROUND(sum(resultados_diferenca_em_diferencas.impacto),0) as impacto_medio
from resultados_regressao_linear
inner join resultados_diferenca_em_diferencas
	on resultados_regressao_linear.chamada  =  resultados_diferenca_em_diferencas.chamada
		and resultados_regressao_linear.programa  =  resultados_diferenca_em_diferencas.programa
		and resultados_regressao_linear.indicador  =  resultados_diferenca_em_diferencas.indicador
group by indicador
order by impacto_95 desc



/*TOTAL DE PAGAMENTO A UM PROGRAMA*/
select sum("Valor Pago")  
from pagamentos, demanda_bruta
where pagamentos."Processo" = demanda_bruta."Processo"
and "Programa" = 'PROGRAMA BASICO DE FISICA'


/* INDICADORES DE DIFERENÇA EM DIFERENÇAS */
select indicador, 
	ROUND(sum(impacto),0) as impacto
from public.resultados_diferenca_em_diferencas
where (impacto > 1
	or impacto < -1)
	and chamada = 'Universal 2014 Faixa A.'
	and programa = 'PROGRAMA BASICO DE FISICA'
	AND indicador = 'Artigos Publicados'
group by indicador
order by impacto desc 