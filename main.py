# coding: utf-8
import json
from flask import Flask, request
import sys
from musica import *
from collections import OrderedDict
import unicodedata
import time
import custom_sequences

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024

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

# colunas do csv
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

genero_musicas = {}
generos = set()
acordes = set()
sequencias = {'BmGDA' : 0,
        'CGAmF' : 1,
        'EmG' : 2,
        'CA7DmG7' : 3,
        'GmF' : 4,
        'CC7FFm' : 5}

musicas_dict = {}

INICIO = time.perf_counter()
f = open('data/top/dataset_final.csv')
f.readline()

for line in f:
    line = line.replace('"', '').replace('NA', '')[:-1]

    musica = line.split(',')
    musica[POPULARIDADE] = int(musica[POPULARIDADE].replace('.', ''))

    if musica[CIFRA] != '':
        musica[CIFRA] = limpa_cifra(musica[CIFRA].split(';'))
    else:
        musica[CIFRA] = []

    musica[SEQ_FAMOSA] = musica[SEQ_FAMOSA].split(";")

    # conjunto único de gêneros
    generos.add(musica[GENERO])

    # inclui música no dict de músicas
    musica_obj = Musica(musica[ARTISTA_ID], musica[ARTISTA],
            musica[MUSICA_ID], musica[MUSICA], musica[GENERO],
            int(musica[POPULARIDADE]), musica[SEQ_FAMOSA],
            musica[TOM], musica[CIFRA])

    musicas_dict[musica_obj.id_unico_musica] = musica_obj

    # conjunto único de acordes
    for acorde in musica_obj.acordes:
        acordes.add(acorde)

    # constrói dict mapeando gênero para músicas
    # deve ser usado para melhorar o desempenho das buscas
    if musica_obj.genero in genero_musicas:
        genero_musicas[musica_obj.genero].append(musica_obj)
    else:
        genero_musicas[musica_obj.genero] = [musica_obj]

# dicionário de músicas cujos valores são ordenados por popularidade
musicas = OrderedDict(sorted(musicas_dict.items(),
    key=lambda x: x[1].popularidade, reverse = True))

# para trabalhar melhor com json
generos = list(generos)
ACORDES_VOCABULARIO = acordes

# ordena genero_musicas por popularidade
for k,v in genero_musicas.items():
    genero_musicas[k].sort(key = lambda x : x.popularidade, reverse = True)

f.close()
TEMPO_CSV = time.perf_counter() - INICIO

# catálogo de sequências (as 6 originais + as cadastradas em runtime) vive
# em SQLite; músicas e gêneros continuam exclusivamente no CSV em memória.
DB_PATH = custom_sequences.resolve_db_path(app)
INICIO_DB = time.perf_counter()
DB_INFO = custom_sequences.init_db(DB_PATH)
TEMPO_DB = time.perf_counter() - INICIO_DB
INICIO_INDICE = time.perf_counter()
MATCHING_INDEX = custom_sequences.MatchingIndex(musicas)
TEMPO_INDICE = time.perf_counter() - INICIO_INDICE
app.logger.info(
    "Startup: csv=%.2fs banco=%.3fs indice=%.3fs total=%.2fs; "
    "banco=%s versão=%s seed=%s total=%s índice=%s músicas",
    TEMPO_CSV,
    TEMPO_DB,
    TEMPO_INDICE,
    time.perf_counter() - INICIO,
    DB_PATH,
    DB_INFO["version"],
    DB_INFO["seeded"],
    DB_INFO["total"],
    len(MATCHING_INDEX.cifra_index),
)


@app.route('/')
def index():
    return app.send_static_file('index.html')
''' Busca por músicas que possuem no título ou no nome do artista o argumento passado por key.
params: key e generos (opcional). Caso generos não sejam definidos, a busca não irá filtrar por gênero.
exemplo 1: /search?key=no dia em que eu saí de casa
exemplo 2: /search?key=no dia em que eu saí de casa&generos=Rock,Samba '''

@app.route('/<path:path>')
def static_proxy(path):
  # send_static_file will guess the correct MIME type
  return app.send_static_file(path)

@app.route('/search')
def busca():
    generos_tag = request.args.get('generos', [])
    pagina_tag = request.args.get('pagina','1')
    keys = request.args.get('key').lower()
    keys = remover_combinantes(keys).split(' ')

    generos_key = generos
    if generos_tag:
        generos_key = generos_tag.split(',')

    collection = apply_filtro(musicas.values(), generos_key)
    out = []

    for musica in collection:
        text = '%s %s' % (musica.nome_artista.lower(), musica.nome_musica.lower())
        text_list = remover_combinantes(text).split(' ')
        if all(key in text_list for key in keys):
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
@app.route('/musicas')
def get_musicas():
    return json.dumps([v.__dict__ for v in musicas.values()])

@app.route('/generos')
def get_generos():
    return json.dumps(generos)

@app.route('/acordes')
def get_acordes():
    return json.dumps(list(acordes))

@app.route('/sequencias')
def listar_sequencias():
    return json.dumps(custom_sequences.list_sequences(DB_PATH))

@app.errorhandler(413)
def corpo_muito_grande(error):
    return json.dumps({'erro': 'corpo da requisição muito grande'}), 413

@app.route('/sequencias', methods=['POST'])
def criar_sequencia():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return json.dumps({'erro': 'corpo JSON inválido'}), 400

    try:
        nome, acordes_validos = custom_sequences.validate_sequence(
            payload.get('nome'),
            payload.get('acordes'),
            ACORDES_VOCABULARIO,
        )
    except custom_sequences.ValidationError as exc:
        app.logger.warning('POST /sequencias recusado: %s', exc)
        return json.dumps({'erro': str(exc)}), 400

    try:
        sequencia = custom_sequences.create_sequence(
            DB_PATH, nome, acordes_validos
        )
    except custom_sequences.DuplicateSequence as exc:
        app.logger.info('POST /sequencias duplicado: %s', exc.existing_id)
        return json.dumps({
            'erro': str(exc),
            'id': exc.existing_id,
        }), 409

    app.logger.info('POST /sequencias criado: %s', sequencia['id'])
    return json.dumps(custom_sequences.to_public(sequencia)), 201

@app.route('/musica/<m_id>/')
def get_musica(m_id):
    return json.dumps(musicas[m_id].__dict__)

@app.route('/similares')
def get_similares():
    # tratando request
    acordes_tag = request.args.get('acordes')
    id_musica_tag = request.args.get('id_unico_musica')
    sequencia_id_tag = request.args.get('sequencia_id')
    sequencia_tag = request.args.get('sequencia')
    pagina_tag = request.args.get('pagina','1')

    # se não existir, filtra por todos.
    generos_tag = request.args.get('generos')
    generos_key = generos
    if generos_tag:
        generos_key = generos_tag.split(',')

    acordes = []
    if acordes_tag:
        acordes = acordes_tag.split(',')
    elif id_musica_tag:
        musica = musicas[id_musica_tag]
        acordes = musica.acordes
    elif sequencia_id_tag:
        sequencia = custom_sequences.get_sequence(DB_PATH, sequencia_id_tag)
        similares = []
        if sequencia:
            if sequencia['matching_mode'] == 'legacy_tag':
                similares = get_pagina(
                    get_similares_por_sequencia(
                        sequencia['legacy_tag'], generos_key
                    ),
                    pagina_tag,
                )
            else:
                similares = get_similares_por_sequencia_custom(
                    sequencia, generos_key, pagina_tag
                )
        return json.dumps(similares)
    elif sequencia_tag:
        acordes = sequencia_tag.replace(',','')
        similares = []

        if acordes in sequencias:
            id_seq = sequencias[acordes]
            similares = get_pagina(get_similares_por_sequencia(id_seq, generos_key), pagina_tag)
        return json.dumps(similares)

    similares = get_similares(acordes, generos_key, id_musica_tag)

    return json.dumps(get_pagina(similares, pagina_tag))

def get_similares_por_sequencia(id_seq, generos_key):
    # filtra para melhor desempenho
    collection = apply_filtro(musicas.values(), generos_key)

    similares = []
    for musica in collection:
        if str(id_seq) in musica.seqs_famosas:
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


def get_similares_por_sequencia_custom(sequencia, generos_key, pagina_tag):
    permitidos = set(generos_key)
    ids = [
        song_id
        for song_id in MATCHING_INDEX.matches(
            sequencia['id'], sequencia['acordes']
        )
        if musicas[song_id].genero in permitidos
    ]

    similares = []
    for song_id in get_pagina(ids, pagina_tag):
        musica = musicas[song_id]
        similares.append({
            'id_unico_musica' : musica.id_unico_musica,
            'id_artista' : musica.id_artista,
            'id_musica' : musica.id_musica,
            'nome_artista' : musica.nome_artista,
            'nome_musica' : musica.nome_musica,
            'popularidade' : musica.popularidade,
            'acordes' : musica.acordes,
            'genero' : musica.genero,
            'url' : musica.url,
        })

    return similares


def get_pagina(colecao, pagina_tag):
    sl = (int(pagina_tag) - 1)*TAM_PAGINA
    return colecao[sl:sl+TAM_PAGINA]

def get_similares(acordes, generos_key, id_musica = None):

    # filtra para melhor desempenho
    collection = apply_filtro(musicas.values(), generos_key)

    similares = []
    for musica in collection:

        if musica.id_unico_musica != id_musica:

            inter = set(acordes).intersection(set(musica.acordes))
            diff = set(musica.acordes) - set(acordes)

            # somente as que tiverem interseção e as que forem
            # dos generos solicitados.
            if len(inter) > 0:
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

## Filtra a coleção de músicas por gênero.
def apply_filtro(musicas, generos_key):
    # filtra para melhor desempenho
    collection = []
    for genero in generos_key:
        if genero in generos:
            collection += genero_musicas[genero]
    return collection

@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == '__main__':
    app.run(debug=True)
