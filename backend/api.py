# coding: utf-8
import json
from flask import Flask, request
import sys
from musica import *
from collections import OrderedDict
import unicodedata

app = Flask(__name__)

ARTISTA_ID = 0
MUSICA_ID = 1
ARTISTA = 2
MUSICA = 3
GENERO = 4
POPULARIDADE = 5
TOM = 6
SEQ_FAMOSA = 7
CIFRA = 8
TAM_PAGINA = 100


def init():
    reload(sys)  
    sys.setdefaultencoding('utf8')
    
    f = open('../data/top/dataset_final.csv')
    f.readline()
    
    global generos
    global musicas
    global sequencias
    global acordes
    
    generos = set()
    acordes = set()
    sequencias = {'BmGDA' : 0,
            'CGAmF' : 1,
            'EmG' : 2,
            'CA7DmG7' : 3, 
            'GmF' : 4, 
            'CC7FFm' : 5}
    
    musicas_dict = {}
    for line in f:
        line = line.replace('"', '').replace('NA', '')[:-1]

        musica = line.split(',')
        musica[POPULARIDADE] = int(musica[POPULARIDADE].replace('.', ''))
        
        if musica[CIFRA] != '':
            musica[CIFRA] = limpa_cifra(musica[CIFRA].split(';'))
        else:
            musica[CIFRA] = []

        musica[SEQ_FAMOSA] = musica[SEQ_FAMOSA].split(";")
    
        generos.add(musica[GENERO])
        
        # inclui música no dict de músicas
        musica_obj = Musica(musica[ARTISTA_ID], musica[ARTISTA], musica[MUSICA_ID], musica[MUSICA],
                musica[GENERO], int(musica[POPULARIDADE]), musica[SEQ_FAMOSA], musica[TOM], musica[CIFRA])
        musicas_dict[musica_obj.id_unico_musica] = musica_obj

        for acorde in musica_obj.acordes:
            acordes.add(acorde)
    
    # dicionário cujos valores são ordenados por popularidade
    musicas = OrderedDict(sorted(musicas_dict.items(), key=lambda x: x[1].popularidade, reverse = True))
    
    # para trabalhar melhor com json
    generos = list(generos)
    
    f.close()

def limpa_cifra(raw_cifra):
    cifra = []
    for m in raw_cifra:
        if m.strip() != '':
            # filtra tablaturas
            if '|' in m:
                acorde = m.split('|')[0].split()[0]
                cifra.append(acorde)
            # lida com acordes separados por espaço
            else:
                tokens = [token for token in m.split()]
                cifra += tokens
    return cifra

''' Busca por músicas que possuem no título ou no nome do artista o argumento passado por key.
    params: key e generos (opcional). Caso generos não sejam definidos, a busca não irá filtrar por gênero.
    exemplo 1: /search?key=no dia em que eu saí de casa
    exemplo 2: /search?key=no dia em que eu saí de casa&generos=Rock,Samba '''
@app.route('/search')
def busca():
    generos_tag = request.args.get('generos', [])
    generos_key = generos
    if generos_tag:
        generos_key = generos_tag.encode('utf-8').split(',')

    pagina_tag = request.args.get('pagina','1')
    
    keys = request.args.get('key').lower()
    keys = remover_combinantes(keys).split(' ')
    
    out = []
    for musica in musicas.values():
        text = '%s %s' % (musica.nome_artista.lower(), musica.nome_musica.lower())
        text_list = remover_combinantes(unicode(text)).split(' ')
        if musica.genero in generos_key and all(key in text_list for key in keys):
            matches = {
                'id_unico_musica' : musica.id_unico_musica,
                'id_artista' : musica.id_artista,
                'id_musica' : musica.id_musica,
                'nome_artista' : musica.nome_artista,
                'nome_musica' : musica.nome_musica,
                'genero' : musica.genero,
                'url' : musica.url,
            }
            out.append(matches)
    return json.dumps(get_pagina(out, pagina_tag))

# cópia
def remover_combinantes(string):
    string = unicodedata.normalize('NFD', string)
    return u''.join(ch for ch in string if unicodedata.category(ch) != 'Mn')

''' Retorna as músicas armazenadas no sistema (ordenados por popularidade). 
    O serviço é paginado. Cada página tem tamanho 100, por default.
    params: pagina. Caso não seja definida a página, o valor default é 1.
    exemplo 1: /musica?pagina=2
    exemplo 2: /musica'''
@app.route('/musica')
def get_musicas():
    return json.dumps([v.__dict__ for v in musicas.values()])

@app.route('/generos')
def get_generos():
    return json.dumps(generos)

@app.route('/acordes')
def get_acordes():
    return json.dumps(list(acordes))

@app.route('/musica/<m_id>/')
def get_musica(m_id):
    return json.dumps(musicas[m_id].__dict__)

@app.route('/similares')
def get_similares():
    # tratando request
    acordes_tag = request.args.get('acordes')
    id_musica_tag = request.args.get('id_unico_musica')
    sequencia_tag = request.args.get('sequencia')
    pagina_tag = request.args.get('pagina','1')
    
    # se não existir, filtra por todos.
    generos_tag = request.args.get('generos')
    generos_key = generos
    if generos_tag:
        generos_key = generos_tag.encode('utf-8').split(',')
    
    acordes = []
    if acordes_tag:
        acordes = acordes_tag.encode('utf-8').split(',')
    elif id_musica_tag:
        musica = musicas[id_musica_tag]
        acordes = musica.acordes
    elif sequencia_tag:
        acordes = sequencia_tag.encode('utf-8').replace(',','')
        similares = []
        
        if acordes in sequencias:
            id_seq = sequencias[acordes]
            similares = get_pagina(get_similares_por_sequencia(id_seq, generos_key), pagina_tag)
        return json.dumps(similares)

    similares = get_similares(acordes, generos_key)

    return json.dumps(get_pagina(similares, pagina_tag))

def get_similares_por_sequencia(id_seq, generos_key):
    similares = []
    for musica in musicas.values():
        if str(id_seq) in musica.seqs_famosas and musica.genero in generos_key:
            similar = {
                'id_unico_musica' : musica.id_unico_musica,
                'id_artista' : musica.id_artista,
                'id_musica' : musica.id_musica,
                'nome_artista' : musica.nome_artista,
                'nome_musica' : musica.nome_musica,
                'popularidade' : musica.popularidade,
                'acordes' : musica.acordes,
                'genero' : musica.genero,
                'url' : musica.url,
            }
            similares.append(similar)

    return similares


def get_pagina(colecao, pagina_tag):
    sl = (int(pagina_tag) - 1)*TAM_PAGINA
    return colecao[sl:sl+TAM_PAGINA]

def get_similares(acordes, generos_key):
    similares = []
    for musica in musicas.values():
        inter = set(acordes).intersection(set(musica.acordes))
        diff = set(musica.acordes) - set(acordes)

        # somente as que tiverem interseção e as que forem 
        # dos generos solicitados.
        if len(inter) > 0 and musica.genero in generos_key:
            similar = {
                    'id_unico_musica' : musica.id_unico_musica,
                    'id_artista' : musica.id_artista,
                    'id_musica' : musica.id_musica,
                    'nome_artista' : musica.nome_artista,
                    'nome_musica' : musica.nome_musica,
                    'popularidade' : musica.popularidade,
                    'acordes' : musica.acordes,
                    'genero' : musica.genero,
                    'url' : musica.url,
                    'diferenca' : list(diff),
                    'intersecao' : list(inter)
            }
            
            similares.append(similar)

    # ordenados por menor diferença, maior interseção e maior popularidade.
    return sorted(similares, key=lambda x: (len(x['diferenca']), -len(x['intersecao'])))


@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == '__main__':
    init()
    app.run(debug=True)

