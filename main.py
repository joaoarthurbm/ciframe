# coding: utf-8
import json
from flask import Flask, request
import sys
from musica import *
from collections import OrderedDict
import unicodedata
import sqlite3
import os
import re
from datetime import datetime, timezone

app = Flask(__name__)

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
SEQUENCIAS_ORIGINAIS = OrderedDict([
    ('BmGDA', ['Bm', 'G', 'D', 'A']),
    ('CGAmF', ['C', 'G', 'Am', 'F']),
    ('EmG', ['Em', 'G']),
    ('CA7DmG7', ['C', 'A7', 'Dm', 'G7']),
    ('GmF', ['Gm', 'F']),
    ('CC7FFm', ['C', 'C7', 'F', 'Fm']),
])
sequencias = {key: index for index, key in enumerate(SEQUENCIAS_ORIGINAIS)}

DB_PATH = os.environ.get('SEQUENCIAS_DB_PATH') or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'data', 'sequencias.db')


def init_db():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL')
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS sequences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chords TEXT NOT NULL,
        chords_key TEXT NOT NULL UNIQUE,
        created_at TEXT
    )""")
    conn.commit()
    conn.close()


init_db()

musicas_dict = {}

f = open('data/top/dataset_final.csv', encoding='utf-8', errors='replace')
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


CHORD_RE = re.compile(r'^[A-Ga-g][A-Za-z0-9#b/°+\-().]*$')
MAX_CHORDS_PER_SEQUENCE = 32
MAX_CHORD_LENGTH = 20


def _normalize_chord_token(ch):
    if ch is None:
        return ''
    return ''.join(str(ch).split())


def _normalize_chords_list(chords):
    return [t for t in (_normalize_chord_token(c) for c in chords) if t]


def _legacy_chords_key(chords_normalized):
    return ''.join(chords_normalized)


def _chords_key(chords_normalized):
    return ' '.join(chords_normalized)


def _validar_chords(chords_list):
    if not chords_list:
        return 'empty'
    if len(chords_list) > MAX_CHORDS_PER_SEQUENCE:
        return 'too_many_chords'
    for chord in chords_list:
        if len(chord) > MAX_CHORD_LENGTH or not CHORD_RE.match(chord):
            return 'invalid_chord'
    return None


def _get_db_conn():
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.execute('PRAGMA busy_timeout=5000')
    conn.row_factory = sqlite3.Row
    return conn


def _parse_stored_chords(c):
    if c.strip().startswith('['):
        return json.loads(c)
    if ',' in c:
        return [x.strip() for x in c.split(',') if x.strip()]
    return [c.strip()] if c.strip() else []


def _buscar_sequencia_custom(*keys, concat=None):
    conn = _get_db_conn()
    try:
        cur = conn.cursor()
        for key in keys:
            if not key:
                continue
            cur.execute('SELECT chords FROM sequences WHERE chords_key = ?', (key,))
            row = cur.fetchone()
            if row:
                try:
                    return _parse_stored_chords(row['chords'])
                except Exception:
                    return None
        if concat:
            cur.execute(
                "SELECT chords FROM sequences WHERE REPLACE(chords_key, ' ', '') = ? ORDER BY id LIMIT 1",
                (concat,))
            row = cur.fetchone()
            if row:
                try:
                    return _parse_stored_chords(row['chords'])
                except Exception:
                    return None
    finally:
        conn.close()
    return None


def listar_sequencias_catalogo():
    res = [
        {'chords': list(chords), 'chords_key': key, 'origem': 'original'}
        for key, chords in SEQUENCIAS_ORIGINAIS.items()
    ]
    conn = _get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, chords, chords_key, created_at FROM sequences ORDER BY id ASC')
        for row in cur.fetchall():
            try:
                chords_list = _parse_stored_chords(row['chords'])
            except Exception:
                chords_list = row['chords']
            res.append({
                'id': row['id'],
                'chords': chords_list,
                'chords_key': row['chords_key'],
                'created_at': row['created_at'],
                'origem': 'custom',
            })
    finally:
        conn.close()
    return res


# dicionário de músicas cujos valores são ordenados por popularidade
musicas = OrderedDict(sorted(musicas_dict.items(),
    key=lambda x: x[1].popularidade, reverse = True))

# para trabalhar melhor com json
generos = list(generos)

# ordena genero_musicas por popularidade
for k,v in genero_musicas.items():
    genero_musicas[k].sort(key = lambda x : x.popularidade, reverse = True)

f.close()


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

@app.route('/sequencias', methods=['GET'])
def get_sequencias():
    return json.dumps(listar_sequencias_catalogo())


@app.route('/sequencias', methods=['POST'])
def post_sequencias():
    conn = None
    try:
        data = request.get_json(silent=True)
        if data is None:
            data = request.form

        chords = None
        if isinstance(data, list):
            chords = data
        elif hasattr(data, 'get'):
            for field in ('chords', 'sequencia', 'sequence'):
                if field in data:
                    chords = data[field]
                    break
        if chords is None and request.data:
            try:
                data2 = json.loads(request.data)
            except Exception:
                data2 = None
            if isinstance(data2, list):
                chords = data2
            elif isinstance(data2, dict):
                chords = data2.get('chords') or data2.get('sequencia')

        if isinstance(chords, str):
            chords_list = _normalize_chords_list(chords.split(','))
        elif isinstance(chords, list):
            chords_list = _normalize_chords_list(chords)
        else:
            return json.dumps({'error': 'invalid'}), 400

        erro = _validar_chords(chords_list)
        if erro:
            return json.dumps({'error': erro}), 400

        if chords_list in [list(v) for v in SEQUENCIAS_ORIGINAIS.values()]:
            return json.dumps({
                'chords': chords_list,
                'chords_key': _legacy_chords_key(chords_list),
                'duplicado': True,
                'origem': 'original',
            })

        chords_key = _chords_key(chords_list)
        chords_store = ','.join(chords_list)
        conn = _get_db_conn()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO sequences (chords, chords_key, created_at) VALUES (?,?,?)',
                        (chords_store, chords_key, datetime.now(timezone.utc).isoformat()))
            conn.commit()
            row_id = cur.lastrowid
        except sqlite3.IntegrityError:
            return json.dumps({'chords': chords_list, 'chords_key': chords_key, 'duplicado': True})
        return json.dumps({'id': row_id, 'chords': chords_list, 'chords_key': chords_key})
    except Exception:
        return json.dumps({'error': 'invalid'}), 400
    finally:
        if conn is not None:
            conn.close()


@app.route('/musicas')
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
        generos_key = generos_tag.split(',')

    acordes = []
    if acordes_tag:
        acordes = acordes_tag.split(',')
    elif id_musica_tag:
        musica = musicas[id_musica_tag]
        acordes = musica.acordes
    elif sequencia_tag:
        # try hardcoded first - must remain unchanged
        acordes_concat = sequencia_tag.replace(',', '')
        if acordes_concat in sequencias and (
            ',' not in sequencia_tag
            or _normalize_chords_list(sequencia_tag.split(','))
                == list(SEQUENCIAS_ORIGINAIS[acordes_concat])
        ):
            id_seq = sequencias[acordes_concat]
            similares = get_pagina(get_similares_por_sequencia(id_seq, generos_key), pagina_tag)
            return json.dumps(similares)

        seq_list = _normalize_chords_list(sequencia_tag.split(','))
        key_cand = _chords_key(seq_list)
        key_cand_legacy = _legacy_chords_key(seq_list)
        concat = ''.join(acordes_concat.split()) if ',' not in sequencia_tag else None
        seq_cand = _buscar_sequencia_custom(key_cand, key_cand_legacy, concat=concat)
        if not seq_cand:
            return json.dumps([])
        seq_cand_norm = _normalize_chords_list(seq_cand)
        if not seq_cand_norm:
            return json.dumps([])
        similares = get_similares_por_sequencia_custom(seq_cand_norm, generos_key)
        return json.dumps(get_pagina(similares, pagina_tag))

    similares = get_similares(acordes, generos_key, id_musica_tag)

    return json.dumps(get_pagina(similares, pagina_tag))


def get_similares_por_sequencia_custom(seq_cand, generos_key):
    collection = apply_filtro(musicas.values(), generos_key)
    similares = []
    seq_cand_norm = _normalize_chords_list(seq_cand) if seq_cand else []
    if not seq_cand_norm:
        return similares

    total = len(seq_cand_norm)
    for musica in collection:
        cifra = getattr(musica, 'cifra', None) or []
        if total > len(cifra):
            continue
        j = 0
        for chord in cifra:
            if chord == seq_cand_norm[j]:
                j += 1
                if j == total:
                    break
        if j == total:
            similar = {
                'id_unico_musica': musica.id_unico_musica,
                'id_artista': musica.id_artista,
                'id_musica': musica.id_musica,
                'nome_artista': musica.nome_artista,
                'nome_musica': musica.nome_musica,
                'popularidade': musica.popularidade,
                'acordes': musica.acordes,
                'genero': musica.genero,
                'url': musica.url,
            }
            similares.append(similar)
    return similares


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
