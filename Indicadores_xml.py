#Funções que não foram adiante.

class Indicadores_xml ():
        def get_all_indicadores(self, xml = None, nivel = 0):
        dado={}
        if xml == None:
            xml = self.xml
            if xml == None:
                return None
        if not (
                type(xml) == BeautifulSoup or
                type(xml) == Tag ):
            xml = BeautifulSoup(xml, "xml")
 
        if not xml.find('CURRICULO-VITAE') == None:
            xml = xml.find('CURRICULO-VITAE')

        nome_indicador = xml.name


        # Verifica se os filhos não são detalhamentos do pai
        detalhamento = False
        for child in xml.children:
            child_name = child.name
            if (not child_name == None and 
                    (child_name[0:14] == 'DADOS-BASICOS' or
                    child_name[0:13] == 'DETALHAMENTO-' or
                    child_name == 'AUTORES' or
                    child_name == "PALAVRAS-CHAVE" or
                    child_name == "AREAS-DO-CONHECIMENTO" or
                    child_name == "SETORES-DE-ATIVIDADE" or
                    child_name == "INFORMACOES-ADICIONAIS" or
                    child_name == 'INFORMACOES-ADICIONAIS' or
                    child_name == 'INFORMACOES-ADICIONAIS-INSTITUICOES' or
                    child_name == 'INFORMACOES-ADICIONAIS-CURSOS' 
                    )):
                detalhamento = True
                continue

        #Se houver detalhamento, pega.
        if detalhamento:
            #1. Pegar autores, se existirem
            autores = []
            num_autores = 0
            posicao_autor = 0
            for autor in xml.find_all('AUTORES'):
                num_autores += 1
                if autor.get("NRO-ID-CNPQ") == self.id:
                    posicao_autor = num_autores
                for (key, value) in xml.attrs.items():
                    try:
                        dado[key.lower()].append(value)
                    except:
                        dado[key.lower()] = [value]
                        # if key.lower() in dado:
                        #     dado[key.lower()] = [dado[key.lower()]]
                        #     dado[key.lower()].append(value)
                        # else:
                        #     dado[key.lower()] = value
                autores.append(list(autor.attrs.items()))
            if len(autores) > 0:
                dado['numero-autores'] = [num_autores]
                dado['posicao-autor'] = [posicao_autor]
                dado['autores'] = autores
            
            #2 Pegar palavras-chave, se existirem.
            palavras_chaves = []
            for palavra in xml.find_all('PALAVRAS-CHAVE'):
                palavras_chaves.append(list(palavra.attrs.values()))
            if len(palavras_chaves) > 0:
                dado['palavras-chave'] = palavras_chaves
                
            #3 Pegar áreas de atuação, se existirem
            areas = []
            for area in xml.find_all('AREAS-DO-CONHECIMENTO'):
                for a in area.children:
                    area_ga = a.find('NOME-GRANDE-AREA-DO-CONHECIMENTO')
                    area_a = a.find('NOME-DA-AREA-DO-CONHECIMENTO')
                    area_sa = a.find('NOME-DA-SUB-AREA-DO-CONHECIMENTO')
                    area_e = a.find('NOME-DA-ESPECIALIDADE')
                    areas.append ((area_ga, area_a, area_sa, area_e))
            if len(areas) > 0:
                dado['areas-do-conhecimento'] = areas
                        
            #4 Setores de Atividade
            setores = []
            for setor in xml.find_all('SETORES-DE-ATIVIDADE'):
                setores.append(list(setor.attrs.values()))
            if len(setores) > 0:
                    dado['setores-de-atividade'] = setores
                    
            #5 Informações adicionais
            informacoes = []
            for palavra in xml.find_all('INFORMACOES-ADICIONAIS'):
                informacoes.append(list(palavra.attrs.values()))
            if len(informacoes) > 0:
                    dado['informacoes-adicionais'] = informacoes
                    
            #6 Pegar outras informações
            for child in xml.children:
                child_name = child.name
                if child_name in [
                        'AUTORES',
                        'PALAVRAS-CHAVE',
                        'AREAS-DO-CONHECIMENTO',
                        'SETORES-DE-ATIVIDADE',
                        'INFORMACOES-ADICIONAIS',
                        'INFORMACOES-ADICIONAIS-INSTITUICOES',
                        'INFORMACOES-ADICIONAIS-CURSOS',
                        'SISTEMA-ORIGEM-XML',
                        '[document] - '
                        ]:
                    continue
                try:
                    for (key, value) in child.attrs.items():
                        try:
                            dado[key.lower()].append(value)
                        except:
                            dado[key.lower()] = [value]
                            # if key.lower() in dado:
                            #     dado[key.lower()] = [dado[key.lower()]]
                            #     dado[key.lower()].append(value)
                            # else:
                            #     if key in ('AUTORES',
                            #         'PALAVRAS-CHAVE',
                            #         'AREAS-DO-CONHECIMENTO',
                            #         'SETORES-DE-ATIVIDADE',):
                            #         dado[key.lower()] = [value]
                            #     else:
                            #         dado[key.lower()] = value
                    try:
                        for child2 in child.children:
                            child_name = child2.name
                            if child_name in [
                                    'AUTORES',
                                    'PALAVRAS-CHAVE',
                                    'AREAS-DO-CONHECIMENTO',
                                    'SETORES-DE-ATIVIDADE',
                                    'INFORMACOES-ADICIONAIS',
                                    ]:
                                continue
                            for (key, value) in child2.attrs.items():
                                try:
                                    dado[key.lower()].append(value)
                                except:
                                    dado[key.lower()] = [value]
                    except:
                        pass
                except:
                    pass

        #Pega outros atributos do XML
        for (key, value) in xml.attrs.items():
                dado[key.lower()] = [value]

        #Pega o ano, se houver           
        try:
            if not dado.get('ano') == None:
                ano = dado.get('ano')[0]
            elif not dado.get('ano-de-conclusao') == None:
                ano = dado.get('ano-de-conclusao')[0]
            elif not dado.get('ano-da-obra-de-referencia') == None:
                ano = dado.get('ano-da-obra-de-referencia')[0]
            elif not dado.get('ano-de-obtencao-do-titulo') ==None:
                ano = dado.get('ano-de-obtencao-do-titulo')[0]
            elif not dado.get('ano-fim') == None:
                ano = dado.get('ano-fim')[0]
            elif not dado.get('ano-de-realizacao') == None:
                ano = dado.get('ano-de-realizacao')[0]
            elif not dado.get('ano-do-artigo') == None:
                ano = dado.get('ano-do-artigo')[0]
            elif not dado.get('ano-do-texto') == None:
                ano = dado.get('ano-do-texto')[0]
            elif not dado.get('ano-desenvolvimento') == None:
                ano = dado.get('ano-desenvolvimento')[0]
            elif not dado.get('ano-solicitacao') == None:
                ano = dado.get('ano-solicitacao')[0]
            elif not dado.get('ano-da-obra') == None:
                ano = dado.get('ano-da-obra') [0]
            else:
                ano = None
            if not ano==None and int(ano) > 0:
                dado['ano'] = [int(ano)]
                
                self.indicadores_append(nome_indicador, 1, ano)
                if not dado.get('numero-autores') == None:
                    self.indicadores_append(nome_indicador + ' - INVERSO-DE-AUTORES', (1/int(dado.get('numero-autores')[0])), ano)
                if not dado.get('posicao-autor') == None:
                    self.indicadores_append(nome_indicador + ' - POSIÇÃO-AUTOR', dado.get('posicao-autor')[0], ano)                    
        except:
            pass
        #coloca o tipo de indicador nos dados
        parent = xml.parent
        pais = xml.name
        while not parent == None:
            if not pais == '':
                pais = parent.name + ', ' + pais 
            else:
                pais = parent.name
            parent = parent.parent
        
        dado['tipo-indicador'] = [pais]

        #atualiza a variável Indicador.lattes, exceto se só houver o 'tipo-indicador' nos dados
        if len(dado) > 1:
            try:
                self.lattes[nome_indicador].append(dado)
            except:
                self.lattes[nome_indicador] = [dado]
                # if nome_indicador in self.lattes:
                #     self.lattes[nome_indicador] = [self.lattes[nome_indicador]]
                #     self.lattes[nome_indicador].append(dado)
                # else:
                #     self.lattes[nome_indicador] = dado
                
        #Continua, exceto para detalhamentos, que já devem ter sido pegos        
        if not detalhamento:

            for child in xml.children:
                self.get_all_indicadores(child, nivel + 1)
                    



    def indicadores_append (self, descricao, qty, ano):
        if ano == None or ano == '': 
            ano = 0
        existe = False
        for item in self.indicadores:
            if (item['id'] == self.id and
                item['tipo'] == self.get_lista_indicadores(descricao) and
                item['ano'] == int(ano)
                ):
                item['qty'] += 1
                existe = True
        if not existe:
            mydict = {
                'id': self.id,
                'tipo': self.get_lista_indicadores(descricao),
                'ano': int(ano),
                'qty': qty,
            }
            self.indicadores.append(mydict)

            