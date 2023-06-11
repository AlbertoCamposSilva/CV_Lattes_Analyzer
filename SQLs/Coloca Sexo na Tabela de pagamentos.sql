

/* ATUALIZANDO "Sexo" NA TABELA pagamentos*/

update public.pagamentos set "Sexo" = NULL;

update public.pagamentos
set "Sexo" = cod_sexo FROM
	public.en_recurso_humano
	WHERE UPPER(UNACCENT(public.en_recurso_humano.nme_rh)) = UPPER(UNACCENT(public.pagamentos."Beneficiário"));
	
update public.pagamentos
set "Sexo" = cod_sexo FROM
	public.en_recurso_humano
	where
		UPPER(unaccent(split_part(nme_rh,' ',1))) = UPPER(unaccent(split_part("Beneficiário", ' ', 1)))
		and UPPER(unaccent(split_part(nme_rh,' ',2))) = UPPER(unaccent(split_part("Beneficiário", ' ', 2)))
		and UPPER(unaccent(split_part(nme_rh,' ',3))) = UPPER(unaccent(split_part("Beneficiário", ' ', 3)))
		and UPPER(unaccent(split_part(nme_rh,' ',4))) = UPPER(unaccent(split_part("Beneficiário", ' ', 4)))
		and not cod_sexo IS NULL 
		and not "Sexo" IS NULL;
		
	
update public.pagamentos
set "Sexo" = cod_sexo FROM
	public.en_recurso_humano
	where
		UPPER(unaccent(split_part(nme_rh,' ',1))) = UPPER(unaccent(split_part("Beneficiário", ' ', 1)))
		and UPPER(unaccent(split_part(nme_rh,' ',2))) = UPPER(unaccent(split_part("Beneficiário", ' ', 2)))
		and UPPER(unaccent(split_part(nme_rh,' ',3))) = UPPER(unaccent(split_part("Beneficiário", ' ', 3)))
		and not cod_sexo IS NULL 
		and not "Sexo" IS NULL;
		
	
update public.pagamentos
set "Sexo" = cod_sexo FROM
	public.en_recurso_humano
	where
		UPPER(unaccent(split_part(nme_rh,' ',1))) = UPPER(unaccent(split_part("Beneficiário", ' ', 1)))
		and UPPER(unaccent(split_part(nme_rh,' ',2))) = UPPER(unaccent(split_part("Beneficiário", ' ', 2)))
		and not cod_sexo IS NULL 
		and not "Sexo" IS NULL;
		
	
update public.pagamentos
set "Sexo" = cod_sexo FROM
	public.en_recurso_humano
	where
		UPPER(unaccent(split_part(nme_rh,' ',1))) = UPPER(unaccent(split_part("Beneficiário", ' ', 1)))
		and not cod_sexo IS NULL 
		and not "Sexo" IS NULL;		

select count(*), "Sexo" from public.pagamentos group by "Sexo";

