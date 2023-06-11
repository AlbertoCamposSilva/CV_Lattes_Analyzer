

/* ATUALIZANDO SEXO NA TABELA dados_gerais*/

update public.dados_gerais set sexo = NULL;


update public.dados_gerais
set sexo = cod_sexo FROM
	public.en_recurso_humano
	WHERE UPPER(UNACCENT(public.en_recurso_humano.nme_rh)) = UPPER(UNACCENT(public.dados_gerais.nome));


update public.dados_gerais
set sexo = mode from
(
	select mode() within group (order by cod_sexo) FROM
		(select * from public.en_recurso_humano 
		where 
			UPPER(unaccent(split_part(nme_rh,' ',1))) = UPPER(unaccent(split_part('Rosana De Martin Ximenes', ' ', 1)))
			and UPPER(unaccent(split_part(nme_rh,' ',2))) = UPPER(unaccent(split_part('Rosana De Martin Ximenes', ' ', 2)))
			and UPPER(unaccent(split_part(nme_rh,' ',3))) = UPPER(unaccent(split_part('Rosana De Martin Ximenes', ' ', 3)))
		 	and UPPER(unaccent(split_part(nme_rh,' ',4))) = UPPER(unaccent(split_part('Rosana De Martin Ximenes', ' ', 4)))
			and not cod_sexo IS NULL 
		) AS teste
		/*group by UPPER(unaccent(split_part(cod_sexo,' ',1)))*/
) AS ver_sexo
where public.dados_gerais.sexo IS NULL;

update public.dados_gerais
set sexo = mode from
(
	select mode() within group (order by cod_sexo) FROM
		(select * from public.en_recurso_humano 
		where 
			UPPER(unaccent(split_part(nme_rh,' ',1))) = UPPER(unaccent(split_part('Rosana De Martin Ximenes', ' ', 1)))
			and UPPER(unaccent(split_part(nme_rh,' ',2))) = UPPER(unaccent(split_part('Rosana De Martin Ximenes', ' ', 2)))
			and UPPER(unaccent(split_part(nme_rh,' ',3))) = UPPER(unaccent(split_part('Rosana De Martin Ximenes', ' ', 3)))
			and not cod_sexo IS NULL 
		) AS teste
		/*group by UPPER(unaccent(split_part(cod_sexo,' ',1)))*/
) AS ver_sexo
where public.dados_gerais.sexo IS NULL;

update public.dados_gerais
set sexo = mode from
(
	select mode() within group (order by cod_sexo) FROM
		(select * from public.en_recurso_humano 
		where 
			UPPER(unaccent(split_part(nme_rh,' ',1))) = UPPER(unaccent(split_part('Rosana De Martin Ximenes', ' ', 1)))
			and UPPER(unaccent(split_part(nme_rh,' ',2))) = UPPER(unaccent(split_part('Rosana De Martin Ximenes', ' ', 2)))
			and not cod_sexo IS NULL 
		) AS teste
		/*group by UPPER(unaccent(split_part(cod_sexo,' ',1)))*/
) AS ver_sexo
where public.dados_gerais.sexo IS NULL;

update public.dados_gerais
set sexo = mode from
(
	select mode() within group (order by cod_sexo) FROM
		(select * from public.en_recurso_humano 
		where 
			UPPER(unaccent(split_part(nme_rh,' ',1))) = UPPER(unaccent(split_part('Rosana De Martin Ximenes', ' ', 1)))
			and not cod_sexo IS NULL 
		) AS teste
		/*group by UPPER(unaccent(split_part(cod_sexo,' ',1)))*/
) AS ver_sexo
where public.dados_gerais.sexo IS NULL;

select * from public.dados_gerais  where sexo is null LIMIT 100;