# coding: utf-8
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from flask import Flask, request
import sys
from musica import *
from collections import OrderedDict
import unicodedata

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

# Catálogo inicial, na ordem das tags que existiam na coluna SEQ_FAMOSA (0..5).
# Os nomes vêm de data/mapeamento_sequencias_famosas.txt, que até então nenhum
# código lia. Recebem ids 1..6 na primeira subida.
SEQUENCIAS_LEGADO = [
    {'nome': 'Sequência de Bm', 'acordes': ['Bm', 'G', 'D', 'A']},
    {'nome': 'Sequência de C', 'acordes': ['C', 'G', 'Am', 'F']},
    {'nome': 'Sequência Em', 'acordes': ['Em', 'G']},
    {'nome': 'Sequência de C (Samba)', 'acordes': ['C', 'A7', 'Dm', 'G7']},
    {'nome': 'Sequência de Gm', 'acordes': ['Gm', 'F']},
    {'nome': 'Sequência de C (Samba cont.)', 'acordes': ['C', 'C7', 'F', 'Fm']},
]


def normalizar_chave(acordes):
    """Forma canônica usada no matching e na detecção de duplicata.

    Preserva ordem e repetições: 'C;C7;F;Fm' != 'C;F;C7;Fm' e 'C;C' != 'C',
    porque a regra de matching é sobre a cifra, que também preserva repetições.
    """
    return ';'.join(acorde.strip().casefold() for acorde in acordes)


# Forma canônica de uma sequência: ';' + casefold, preservando ordem e repetições.
SCHEMA = """
CREATE TABLE IF NOT EXISTS sequencias (
    id        INTEGER PRIMARY KEY,
    nome      TEXT NOT NULL,
    acordes   TEXT NOT NULL,
    chave     TEXT NOT NULL UNIQUE,
    criado_em TEXT NOT NULL
)
"""


def criar_schema():
    with conexao() as conn:
        conn.executescript(SCHEMA)


def seed_sequencias_legado():
    """Insere as 6 sequências originais. Idempotente por `chave` (UNIQUE)."""
    agora = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    with conexao() as conn:
        for sequencia in SEQUENCIAS_LEGADO:
            conn.execute(
                'INSERT OR IGNORE INTO sequencias (nome, acordes, chave, criado_em)'
                ' VALUES (?, ?, ?, ?)',
                (
                    sequencia['nome'],
                    json.dumps(sequencia['acordes'], ensure_ascii=False),
                    normalizar_chave(sequencia['acordes']),
                    agora,
                ),
            )


def _registro(row):
    """Linha do banco -> dict do catálogo (acordes desserializados)."""
    return {
        'id': row['id'],
        'nome': row['nome'],
        'acordes': json.loads(row['acordes']),
        'chave': row['chave'],
        'criado_em': row['criado_em'],
    }


def listar_sequencias():
    with conexao() as conn:
        return [_registro(row) for row in
                conn.execute('SELECT * FROM sequencias ORDER BY id')]


def por_chave(chave):
    with conexao() as conn:
        row = conn.execute(
            'SELECT * FROM sequencias WHERE chave = ?', (chave,)).fetchone()
    return _registro(row) if row else None


def resolver_chave(sequencia_tag):
    """Resolve o parâmetro legado `?sequencia=` para uma chave do catálogo.

    Aceita as duas formas que já circularam: acordes separados por vírgula
    (`Bm,G,D,A`, o que o frontend envia) e a concatenação sem separador
    (`BmGDA`, forma antiga da chave do dict hardcoded).
    """
    chave = normalizar_chave(sequencia_tag.split(','))
    if por_chave(chave):
        return chave

    alvo = ''.join(sequencia_tag.split()).casefold()
    if not alvo:
        return None
    for registro in listar_sequencias():
        if ''.join(registro['acordes']).casefold() == alvo:
            return registro['chave']
    return None


musicas_dict = {}

# --- catálogo de sequências: banco de dados ---------------------------------------
# Só o catálogo de sequências vai para o banco; músicas e gêneros continuam vindo
# do CSV em memória. Ver docs/adr/0002-persist-custom-sequences.md.
# O arquivo fica fora de /app/data de propósito: aquele diretório contém o CSV, e
# um volume montado ali esconderia o dataset e derrubaria o import.
DB_PADRAO = '/var/lib/ciframe/ciframe.db'


def db_path():
    """Caminho do arquivo do banco. `CIFRAME_DB` permite isolar os testes."""
    return os.environ.get('CIFRAME_DB', DB_PADRAO)


@contextmanager
def conexao():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def prepara_diretorio_db():
    """Falha no boot, não na primeira requisição, se o volume não for gravável."""
    diretorio = os.path.dirname(os.path.abspath(db_path()))
    try:
        os.makedirs(diretorio, exist_ok=True)
    except OSError as erro:
        raise SystemExit(
            'não foi possível criar o diretório do banco (%s): %s. '
            'Aponte CIFRAME_DB para um diretório gravável ou monte o volume: '
            'docker run -v ciframe-data:/var/lib/ciframe ciframe' % (diretorio, erro)
        )
    if not os.access(diretorio, os.W_OK):
        raise SystemExit(
            'o diretório do banco (%s) não é gravável. '
            'Aponte CIFRAME_DB para um diretório gravável ou monte o volume: '
            'docker run -v ciframe-data:/var/lib/ciframe ciframe' % diretorio
        )

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

# ordena genero_musicas por popularidade
for k,v in genero_musicas.items():
    genero_musicas[k].sort(key = lambda x : x.popularidade, reverse = True)

f.close()

# valida o diretório do banco no boot: melhor não subir do que subir e não cadastrar
prepara_diretorio_db()
criar_schema()
seed_sequencias_legado()


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
        similares = []

        chave = resolver_chave(sequencia_tag)
        if chave:
            similares = get_pagina(get_similares_por_chave(chave, generos_key), pagina_tag)
        return json.dumps(similares)

    similares = get_similares(acordes, generos_key, id_musica_tag)

    return json.dumps(get_pagina(similares, pagina_tag))

def musica_contem_sequencia(musica, chave):
    """A sequência `chave` aparece nesta música?

    Reproduz exatamente a regra que gerava a coluna SEQ_FAMOSA
    (`scripts/generate_data_set.py`):

    1. **contiguidade** — `chave` é substring contígua da cifra normalizada;
    2. **vocabulário contido** — todo acorde usado na música está entre os
       acordes da sequência.

    As duas condições juntas é que dão o resultado atual (ver 01-research.md).
    Usa `musica.cifra` — ordenada e com repetições — e não `musica.acordes`, que
    é `list(set(cifra))` e perdeu a ordem.
    """
    if not musica.cifra:
        return False

    cifra = ';'.join(acorde.casefold() for acorde in musica.cifra)
    if chave not in cifra:
        return False

    return set(cifra.split(';')).issubset(chave.split(';'))


def get_similares_por_chave(chave, generos_key):
    # filtra por gênero para melhor desempenho
    collection = apply_filtro(musicas.values(), generos_key)

    similares = []
    for musica in collection:
        if musica_contem_sequencia(musica, chave):
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
