update dados_gerais set sexo = CAST(substring(cod_sexo,1) AS char) from public.en_recurso_humano
where NOT public.en_recurso_humano.cod_sexo IS NULL
and UPPER(unaccent(dados_gerais.nome)) = UPPER(unaccent(public.en_recurso_humano.nme_rh))


insert into public.indicadores_pareamento select id from public.all_lattes where dt_atualizacao < '2020-01-01'




insert into public.indicadores_pareamento select id from public.all_lattes where dt_atualizacao < '2020-01-01'

update public.indicadores_pareamento set public.indicadores_pareamento.sexo = public.dados_gerais.sexo

select * from public.en_recurso_humano where nme_rh like 'Adail%'

select * from public.dados_gerais LIMIT 100