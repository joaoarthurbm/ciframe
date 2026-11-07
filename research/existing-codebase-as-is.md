# Research: existing codebase as-is

## High-level summary (3-6 sentences)

The codebase is "deciframe/ciframe" (song-discovery): Flask 3.1 backend in a single file `main.py` loads `data/top/dataset_final.csv` once at import time into in-memory structures (`musicas_dict`/`musicas` OrderedDict by popularity, `genero_musicas` grouped by genre sorted by popularity, `generos` list, `acordes` set). Data is modeled by `musica.Musica` (sets `acordes = list(set(cifra))`, builds `id_unico_musica`, `url` to CifraClub). All API responses are produced via `json.dumps(...)` returned as plain strings (intentionally `Content-Type: text/html`). The AngularJS 1.4.9 frontend (no build step) calls the API from `RESTAPI.url: 'http://localhost:5003'` (configured in `static/assets/js/app.js`) and has routes for `/`, `/poracordes`, `/pormusica`, `/porsequencia`, `/sobre`. "Sequências famosas" search is hardcoded in both backend and frontend today: `main.py` has a dict `sequencias = {'BmGDA':0,...,'CC7FFm':5}` and `/similares` routes `sequencia_tag` to `get_similares_por_sequencia(id_seq, generos_key)` matching songs where `str(id_seq) in musica.seqs_famosas` (from CSV `SEQ_FAMOSA` split by `;`). Frontend `#/porsequencia` hardcodes 4 sequences in `static/assets/js/controllers/sequencia.js` and renders them in `static/templates/sequencia.html`.

## Backend (`main.py`)

### Imports and setup
- `main.py:1-9`: `json`, `Flask`, `request`, `sys`, `from musica import *`, `OrderedDict`, `unicodedata`. App created at `main.py:9`.

### Chord/cipher cleaning
- `main.py:11-23` `limpa_cifra(raw_cifra)`: for each line/token in `raw_cifra`; if empty skipped; if `'|'` in string, takes `acorde = m.split('|')[0].split()[0]` (tablature filtering); else splits by whitespace and appends tokens. Returns flattened list.

### Constants and in-memory structures
- Column indices: `ARTISTA_ID:26`, `MUSICA_ID:27`, `ARTISTA:28`, `MUSICA:29`, `GENERO:30`, `POPULARIDADE:31`, `TOM:32`, `SEQ_FAMOSA:33`, `CIFRA:34`. `TAM_PAGINA:35`.
- Globals initialized: `genero_musicas = {}` (`37`), `generos = set()` (`38`), `acordes = set()` (`39`), `sequencias = {...}` hardcoded 6 entries (`40-45`), `musicas_dict = {}` (`47`).

### CSV loading (at import)
- `main.py:49-98`: opens `'data/top/dataset_final.csv'`, reads header (`49-50`), iterates lines. For each line: `line.replace('"','').replace('NA','')[:-1]` (`53`); split by comma into `musica` list (`55`). `POPULARIDADE` converted to int after removing dots (`56`). If `musica[CIFRA] != ''` sets `musica[CIFRA] = limpa_cifra(musica[CIFRA].split(';'))` else `[]` (`58-61`). `musica[SEQ_FAMOSA]` split by `";"` (`63`). Adds to `generos` set (`66`). Creates `Musica(...)` and stores in `musicas_dict[musica_obj.id_unico_musica] = musica_obj` (`69-74`). Adds each chord in `musica_obj.acordes` to `acordes` set (`77-78`). Appends to `genero_musicas[genero]` (`82-85`). After loop builds `musicas = OrderedDict(sorted(musicas_dict.items(), key=lambda x: x[1].popularidade, reverse=True))` (`88-89`), converts `generos` to list (`92`), sorts each genre bucket by popularity desc (`95-96`), closes file (`98`).

### Routes
- `@app.route('/')` -> `app.send_static_file('index.html')` (`101-103`).
- `@app.route('/<path:path>')` static proxy via `send_static_file` (`109-112`).
- `@app.route('/search')` (`114-142`): reads `generos` (default `[]`), `pagina` (default `'1'`), `key` (lowercased). Normalizes keys via `remover_combinantes(keys).split(' ')` (`118-119`). Determines `generos_key = generos` or split of `generos_tag` (`121-123`). Calls `collection = apply_filtro(musicas.values(), generos_key)` (`125`). For each musica builds `text = '%s %s' % (musica.nome_artista.lower(), musica.nome_musica.lower())` and checks `all(key in text_list for key in keys)` where `text_list = remover_combinantes(text).split(' ')` (`128-131`); builds dict with `id_unico_musica,id_artista,id_musica,nome_artista,nome_musica,genero,url` and appends (`132-141`). Returns `json.dumps(get_pagina(out, pagina_tag))` (`142`).
- `remover_combinantes` (`145-147`): NFD normalize and drop combining marks.
- `@app.route('/musicas')` (`154-156`): returns `json.dumps([v.__dict__ for v in musicas.values()])`.
- `@app.route('/generos')` (`158-160`): `json.dumps(generos)`.
- `@app.route('/acordes')` (`162-164`): `json.dumps(list(acordes))`.
- `@app.route('/musica/<m_id>/')` (`166-168`): `json.dumps(musicas[m_id].__dict__)`.
- `@app.route('/similares')` (`170-201`): reads `acordes_tag`, `id_musica_tag`, `sequencia_tag`, `pagina_tag` default `'1'`. Reads `generos_tag` -> `generos_key` (all if not set). If `sequencia_tag` present: sets `acordes = sequencia_tag.replace(',','')`, checks if `acordes in sequencias` (`194-197`): gets `id_seq = sequencias[acordes]`, calls `get_similares_por_sequencia(id_seq, generos_key)`, paginates with `get_pagina`, returns `json.dumps(similares)`. If `acordes_tag` provided sets `acordes = acordes_tag.split(',')`; elif `id_musica_tag` sets `acordes = musicas[id_musica_tag].acordes`. Calls `get_similares(acordes, generos_key, id_musica_tag)` and returns `json.dumps(get_pagina(similares, pagina_tag))` (`199-201`).
- `get_similares_por_sequencia(id_seq, generos_key)` (`203-223`): filters collection via `apply_filtro(musicas.values(), generos_key)`, iterates; if `str(id_seq) in musica.seqs_famosas` builds dict with fields including `popularidade`, `acordes`, `genero`, `url` and appends.
- `get_pagina(colecao, pagina_tag)` (`226-227`): slices `(int(pagina_tag)-1)*TAM_PAGINA : sl+TAM_PAGINA`.
- `get_similares(acordes, generos_key, id_musica=None)` (`230-263`): filters collection; for each musica where `musica.id_unico_musica != id_musica` computes `inter = set(acordes).intersection(set(musica.acordes))`, `diff = set(musica.acordes) - set(acordes)`. If `len(inter) > 0` appends dict with `diferenca` (list(diff)) and `intersecao` (list(inter)); returns sorted by `(len(x['diferenca']), -len(x['intersecao']))` (`262-263`).
- `apply_filtro(musicas, generos_key)` (`266-272`): builds collection by iterating generos_key and concatenating `genero_musicas[genero]` if `genero` in `generos`.
- `@app.after_request` adds CORS header (`274-277`). `app.run(debug=True)` under `__main__` (`279-280`).

## Model (`musica.py`)
- `Musica.__init__(self, id_artista, nome_artista, id_musica, nome_musica, genero, popularidade, seqs_famosas, tom, cifra)` (`1-19`): sets attributes, `self.acordes = list(set(cifra))` (unique chords from cifra list), `self.seqs_famosas = seqs_famosas` (list from CSV split by `;`), `self.id_unico_musica = '%s_%s' % (id_artista, id_musica)`, `self.url = 'http://www.cifraclub.com.br/%s/%s' % (id_artista, id_musica)`. `__str__` returns `id_unico_musica,genero,popularidade` (`24-25`).

## Frontend (`static/`)
- `static/index.html`: loads Angular 1.4.9, ngRoute, ngAnimate, ui-bootstrap, ngprogress, app.js/routes.js/controllers.
- `static/assets/js/app.js:2-56`: module `deciframeApp` with deps; `.constant('RESTAPI', { url: 'http://localhost:5003' })`; large `GENEROS` constant.
- `static/assets/js/routes.js:1-29`: routes to home/acordes/musica/sequencia/sobre.
- `static/assets/js/controllers/sequencia.js:1-220`: hardcodes 4 sequences `sequencia1-4`; `vm.sequenciasFamosas` built from them. `createChordsString` joins with commas. `vm.pesquisarPorSequencia` GETs `similares?sequencia=...` with optional `&generos=`.
- `static/assets/js/controllers/acordes.js:1-180`: chord sets hardcoded; searches via `similares?acordes=...`.
- `static/assets/js/controllers/musica.js:1-150`: typeahead uses `search?key=`; similar via `similares?id_unico_musica=...`.
- `static/assets/js/controllers/search.js:1-30`: placeholder logic.
- `static/templates/sequencia.html`: renders famous sequences, genre filter, results grid filtered by `ng-hide="music.diferenca.length"` ordered by `-popularidade`.

## Notes
- CSV loaded once at import; changes require restart. All endpoints return `json.dumps(...)` as plain strings. Deploy local-only via Docker.
