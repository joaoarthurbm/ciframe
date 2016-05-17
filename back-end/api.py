# coding: utf-8
import json
from flask import Flask, request
import sys
from musica import *
from collections import OrderedDict

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

generos = set()

def init():
    reload(sys)  
    sys.setdefaultencoding('utf8')
    
    f = open('../data/top/dataset_final.csv')
    f.readline()
    
    musicas_dict = {}
    global generos
    global musicas

    for line in f:
        line = line.replace('"', '').replace('NA', '')[:-1]

        musica = line.split(',')
        musica[POPULARIDADE] = int(musica[POPULARIDADE].replace('.', ''))
        musica[CIFRA] = list(musica[CIFRA].split(';')) if musica[CIFRA] != '' else list()
        musica[SEQ_FAMOSA] = musica[SEQ_FAMOSA].split(";")
    
        if musica[GENERO] != '' :
            generos.add(musica[GENERO])
        
        musica_obj = Musica(musica[ARTISTA_ID], musica[ARTISTA], musica[MUSICA_ID], musica[MUSICA],
                musica[GENERO], int(musica[POPULARIDADE]), musica[SEQ_FAMOSA], musica[TOM], musica[CIFRA])
        musicas_dict[musica_obj.id_unico_musica] = musica_obj

    # dictionary sorted by popularity
    musicas = OrderedDict(sorted(musicas_dict.items(), key=lambda x: x[1].popularidade, reverse = True))
    generos = list(generos)
    
    f.close()
    

def apply_filtro(nome_filtro, colecao, coluna):
    filtro = request.args.get(nome_filtro, '[]')
    filtro = set(json.loads(filtro))

    return filter(lambda x: x[coluna] in filtro, colecao) if len(filtro) > 0 else colecao

def pagina(colecao):
    inicio = (int(request.args.get('pagina', 1))-1) * TAM_PAGINA
    return colecao[inicio:inicio+TAM__PAGINA]

def metodo_mestre(acordes):
    answer = applyFiltro('filtro-artistas', musicas, ARTISTA)
    answer = applyFiltro('filtro-generos', answer, GENERO)

    answer = [{
        'artista': m[ARTISTA],
        'musica': m[MUSICA],
        'genero': m[GENERO],
        'artista_id': m[ARTISTA_ID],
        'musica_id': m[MUSICA_ID],
        'facilidade': 1.0 * len(m[CIFRA] & acordes) / len(m[CIFRA]),
        'diferenca': list(m[CIFRA] - acordes)
    } for m in answer]

    minimo = float(request.args.get('min', 0))/ 100
    maximo = float(request.args.get('max', 100))/ 100

    answer = filter(lambda x: minimo <= x['facilidade'] <= maximo, answer)

    answer.sort(key = lambda x: -x['facilidade'])
    return json.dumps(pagina(answer))

@app.route('/busca')
def busca():
    key = request.args.get('musica').lower()
    filtered = filter(lambda x: key in x[MUSICA].lower(), musicas)
    return json.dumps([{
	    'artista': m[ARTISTA],
	    'musica': m[MUSICA],
	    'genero': m[GENERO],
    } for m in filtered])
	
@app.route('/musica')
def get_musicas():
    return json.dumps([v.__dict__ for v in musicas.values()])

@app.route('/genero')
def get_generos():
    return json.dumps(list(generos))

@app.route('/musica/<m_id>/')
def get_musica(m_id):
    return json.dumps(musicas[m_id].__dict__)

@app.route('/similares')
def get_similares():
    # tratando request
    acordes_tag = request.args.get('acordes')
    id_musica_tag = request.args.get('id_musica')
    sequencia_tag = request.args.get('sequencias')
    pagina_tag = request.args.get('pagina','1')
    
    # se não existir, filtra por todos.
    generos_tag = request.args.get('generos')
    generos_key = generos
    if generos_tag:
        generos_key = generos_tag.encode('utf-8').split(',')
    
    acordes = []
    is_sequencia = False
    if acordes_tag:
        acordes = acordes_tag.encode('utf-8').split(',')
    elif id_musica_tag:
        musica = musicas[id_musica_tag]
        acordes = musica.acordes
    elif sequencia_tag:
        acordes = sequencia_tag.encode('utf-8').split(',')
        is_sequencia = True

    similares = get_similares(acordes, generos_key, is_sequencia)
    sl = (int(pagina_tag) - 1)*TAM_PAGINA

    return json.dumps(similares[sl:sl+TAM_PAGINA])


def get_similares(acordes, generos_key, is_sequencia):
    similares = []
    for musica in musicas.values():
        inter = set(acordes).intersection(set(musica.acordes))
        diff = set(musica.acordes) - set(acordes)

        # somente as que tiverem interseção e as que forem dos generos solicitados
        if len(inter) > 0 and musica.genero in generos_key:
            similar = {
                    'id_unico_musica' : musica.id_unico_musica,
                    'id_artista' : musica.id_artista,
                    'id_musica' : musica.id_musica,
                    'nome_artista' : musica.nome_artista,
                    'nome_musica' : musica.nome_musica,
                    'genero' : musica.genero,
                    'popularidade' : musica.popularidade,
                    'acordes' : musica.acordes,
                    'genero' : musica.genero,
                    'url' : musica.url,
                    'diferenca' : list(diff),
                    'intersecao' : list(inter)
            }
            
            similares.append(similar)

    # ordenados por menor diferença e maior interseção
    return sorted(similares, key=lambda x: (len(x['diferenca']), -len(x['intersecao'])))


@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == '__main__':
    init()
    app.run(debug=True)
