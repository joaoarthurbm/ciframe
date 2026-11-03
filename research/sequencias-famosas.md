# Research: o estado atual das "sequências famosas" do deciframe

## Resumo

O deciframe atual não calcula se uma sequência de acordes aparece em uma música. O
backend mantém seis sequências fixas com ids inteiros (`main.py:40-45`) e
`GET /similares?sequencia=...` apenas verifica se o id está na lista
`Musica.seqs_famosas` (`main.py:190-197`, `main.py:203-223`), que vem da coluna 7
(`SEQ_FAMOSA`) de `data/top/dataset_final.csv` (`main.py:33`, `main.py:63`,
`musica.py:18`). Essa coluna foi gerada offline por
`scripts/generate_data_set.py:7-24`: uma música recebe a tag quando a sequência
inteira ocorre contiguamente na cifra **e** a música não usa nenhum acorde fora da
sequência. O CSV não tem cabeçalho e `main.py:50` descarta a primeira linha de
dados, então 67.585 das 67.586 músicas ficam em memória. A página `#/porsequencia`
tem quatro sequências hardcoded em JavaScript (`sequencia.js:2-37`), diferentes das
seis do backend, e não oferece cadastro. O repositório não tem banco de dados,
testes automatizados nem CI; a persistência existente é o próprio CSV versionado,
lido a cada início de processo.

## Escopo e método

Este documento registra apenas o comportamento do código no estado atual. As
evidências vieram de leitura integral dos arquivos do repositório, de inspeção do
CSV e de requisições feitas com o test client do Flask (`main.app.test_client()`)
usando um virtualenv temporário com `Flask==3.1.3`. Nenhum arquivo de aplicação foi
alterado.

## 1. Dados: CSV e geração offline

### 1.1 O arquivo

- `data/top/dataset_final.csv` tem 67.586 linhas, 15.866.887 bytes e 9 colunas por
  linha.
- A primeira linha é um registro de dados, não um cabeçalho:
  `14-bis,a-qualquer-tempo,14 Bis,A Qualquer Tempo,MPB,70115,B,NA,E;F#;...`.
- As colunas, na ordem fixada em `main.py:25-34`, são: `ARTISTA_ID`, `MUSICA_ID`,
  `ARTISTA`, `MUSICA`, `GENERO`, `POPULARIDADE`, `TOM`, `SEQ_FAMOSA`, `CIFRA`.
- 8.141 linhas têm `CIFRA = NA` e 67.072 têm `SEQ_FAMOSA = NA`.
- 303 linhas têm o gênero `R&B;` (o ponto e vírgula faz parte do valor da coluna).
- 18 linhas contêm aspas duplas; exemplos em `data/top/dataset_final.csv:8381`,
  `:9543`, `:26276`.

### 1.2 Como a coluna `SEQ_FAMOSA` foi produzida

`scripts/generate_data_set.py:7-24` define `get_famosas(acorde)` com uma lista fixa
de seis sequências (linha 8). Para cada sequência `i`:

1. a cifra e a sequência são comparadas em minúsculas (`acorde = acorde.lower()`,
   linha 12);
2. a sequência completa precisa aparecer como substring contígua da cifra
   (`if s in acorde:`, linha 13);
3. todos os acordes da música precisam pertencer ao conjunto de acordes da
   sequência; o primeiro acorde fora do conjunto zera `achou` (linhas 16-20);
4. se as duas condições valerem, o índice `i` é acrescentado (linha 22).

O resultado é concatenado sem separador (linha 88) e escrito na coluna 7
(`scripts/generate_data_set.py:84-89`). No CSV atual todas as tags têm um único
dígito, então não existem valores concatenados com mais de um dígito.

Consequência: a tag não representa "a sequência aparece em algum ponto da música".
Ela representa "a sequência inteira aparece contiguamente e a música só usa acordes
dessa sequência". Ordem importa para a ocorrência contígua; repetições só importam
enquanto afetam essa ocorrência; a única normalização é `lower()`; não há
normalização de enarmonia ou de grafia (`C` e `C7` são tokens distintos, linha 8).

### 1.3 O arquivo de mapeamento

`data/mapeamento_sequencias_famosas.txt:1-6` lista os mesmos ids e nomes das seis
sequências, mas não é lido por nenhum código Python, JavaScript, R ou shell do
repositório. O catálogo efetivo do backend é o dicionário `main.py:40-45`.

## 2. Backend: carga do CSV e estruturas em memória

Toda a leitura acontece uma vez, na importação do módulo (`main.py:49-98`):

1. `open('data/top/dataset_final.csv')` (`main.py:49`) e `f.readline()`
   (`main.py:50`). Como o arquivo não tem cabeçalho, a música
   `14-bis/a-qualquer-tempo` é descartada. `GET /musicas` devolve 67.585 objetos e
   `/musica/14-bis_a-qualquer-tempo/` responde HTTP 500 (`KeyError` em
   `main.py:168`).
2. Limpeza por linha: `line.replace('"', '').replace('NA', '')[:-1]`
   (`main.py:53`). Toda ocorrência da substring `NA` é removida, não só o campo
   `NA`. Efeitos observados:
   - 7 títulos são alterados: `DNA` vira `D`
     (`data/top/dataset_final.csv:25631`), `CABANA` vira `CABA` (`:37719`),
     `JULIANA` vira `JULIA` (`:56713`), entre outros;
   - 18 linhas perdem aspas, por exemplo `"Vamo" Comer` vira `Vamo Comer`
     (`:9543`).
3. `line.split(',')` (`main.py:55`) e os índices fixos de `main.py:25-34`.
4. Popularidade convertida para inteiro (`main.py:56`).
5. Cifra tokenizada por `limpa_cifra` (`main.py:11-23`) sobre `split(';')`
   (`main.py:58-59`) ou `[]` quando vazia (`main.py:60-61`). `limpa_cifra`
   descarta tokens vazios; para tokens com `|`, pega o texto antes do `|` e o
   primeiro token; para os demais, separa por espaços. Não há normalização de
   caixa nem de grafia.
6. `SEQ_FAMOSA` é dividida por `;` (`main.py:63`); músicas sem tag ficam com
   `['']`.
7. Cada linha vira um `Musica` (`main.py:69-72`, `musica.py:1-25`):
   `id_unico_musica = '<id_artista>_<id_musica>'` (`musica.py:20`),
   `url = 'http://www.cifraclub.com.br/<id_artista>/<id_musica>'` (`musica.py:22`),
   `acordes = list(set(cifra))` (`musica.py:17`) e `seqs_famosas` (`musica.py:18`).
8. `musicas_dict` indexa por `id_unico_musica` (`main.py:74`); `generos` e
   `acordes` são `set`s (`main.py:38-39`, `main.py:66`, `main.py:77-78`);
   `genero_musicas` indexa listas por gênero (`main.py:82-85`).
9. `musicas` é um `OrderedDict` ordenado por popularidade decrescente
   (`main.py:88-89`); `generos` vira lista (`main.py:92`); cada lista de
   `genero_musicas` é ordenada por popularidade (`main.py:95-96`).

Números observados: 67.585 músicas, 52 gêneros, 6.653 acordes distintos e
aproximadamente 1,7 s de importação no ambiente desta pesquisa. `AGENTS.md:41`
registra que o startup pode demorar enquanto o CSV é parseado.

Como `generos` e `acordes` vêm de `set`, a ordem varia entre processos:

- `GET /generos` começou com `['Samba Enredo', 'Disco', 'Regional', ...]` em uma
  execução e `['Sertanejo', 'Reggae', 'Disco', ...]` em outra;
- `capital-inicial_a-sua-maneira.acordes` apareceu como `['D', 'G', 'Bm', 'A']`
  e `['G', 'A', 'D', 'Bm']` em execuções diferentes;
- os resultados de `/similares` sem filtro de gênero seguem a ordem de
  `apply_filtro` (`main.py:266-272`), que percorre `generos_key` nessa ordem.

## 3. API: `GET /similares` e a semântica de matching

### 3.1 Rota e precedência de parâmetros

Rota em `main.py:170-201`. Parâmetros: `acordes`, `id_unico_musica`, `sequencia`,
`pagina` (`main.py:173-176`) e `generos` (`main.py:179-182`). A precedência é
`acordes` > `id_unico_musica` > `sequencia` (`main.py:184-197`).

Caminho de sequência (`main.py:190-197`):

1. `acordes = sequencia_tag.replace(',', '')` (`main.py:191`), portanto
   `Bm,G,D,A` vira `BmGDA`;
2. a string é buscada por igualdade no dicionário `sequencias` (`main.py:40-45`):
   `BmGDA=0`, `CGAmF=1`, `EmG=2`, `CA7DmG7=3`, `GmF=4`, `CC7FFm=5`;
3. se existir, `get_similares_por_sequencia(id_seq, generos_key)` (`main.py:196`,
   `main.py:203-223`) e paginação; se não existir, a resposta é `[]`
   (`main.py:192-197`).

A comparação é sensível a caixa e a espaços. Verificado com o test client:
`sequencia=EmG` e `sequencia=Em,G` devolvem 4 resultados; `emg`, `G,Em` e
`Em, G` devolvem `[]`.

### 3.2 O matching efetivo

`get_similares_por_sequencia` filtra a coleção por gênero (`main.py:205`) e inclui
a música quando `str(id_seq) in musica.seqs_famosas` (`main.py:209`). O item
devolvido tem `id_unico_musica`, `id_artista`, `id_musica`, `nome_artista`,
`nome_musica`, `popularidade`, `acordes`, `genero` e `url` (`main.py:210-220`);
não tem `diferenca` nem `intersecao`.

Não há uso de `musica.cifra` nem de `musica.acordes` nesse caminho. Não há cálculo
em tempo real de ocorrência de sequência em nenhum ponto do backend.

### 3.3 Paginação e filtros

- `TAM_PAGINA = 100` (`main.py:35`); o corte é
  `(int(pagina_tag) - 1) * 100` (`main.py:226-228`).
- Totais por sequência: 199, 296, 4, 5, 7 e 3. Via API, a sequência 0 devolve
  100 + 99 nas páginas 1 e 2; a sequência 1 devolve 100 + 100 + 96; `pagina=abc`
  gera HTTP 500 (`ValueError` em `main.py:227`).
- `generos` aceita uma lista separada por vírgulas, mas o frontend envia um único
  gênero. Gêneros desconhecidos são ignorados por `apply_filtro` (`main.py:266-272`).

### 3.4 O outro caminho: acordes e música

Quando `acordes` é enviado (lista separada por vírgulas) ou quando
`id_unico_musica` é enviado, o backend usa `get_similares`
(`main.py:230-263`). Ele calcula `intersecao` e `diferenca` de conjuntos
(`main.py:240-241`), exige interseção não vazia (`main.py:245`), devolve os dois
campos (`main.py:246-258`) e ordena por `(len(diferenca), -len(intersecao))`
(`main.py:263`). O comentário de `main.py:262` cita popularidade, mas ela não entra
na chave de ordenação. Esse caminho é usado pelo frontend nas páginas
`#/poracordes` e `#/pormusica`.

### 3.5 Detalhes de implementação observados

- A função de rota e o helper têm o mesmo nome `get_similares`
  (`main.py:170-171`, `main.py:230`). O Flask registrou a rota no decorator; em
  tempo de execução, o nome global aponta para o helper de 3 argumentos, chamado em
  `main.py:199`. A rota funciona normalmente.
- Todos os endpoints usam `json.dumps(...)`, não `jsonify`; o `Content-Type`
  observado é `text/html; charset=utf-8` e `Access-Control-Allow-Origin: *` é
  adicionado em `main.py:274-277`.
- `GET /search` (`main.py:114-142`) exige `key` (sem ela, HTTP 500 em
  `main.py:118`), remove acentos (`main.py:145-147`), compara tokens exatos de
  artista + título (`main.py:129-131`) e devolve 7 campos (`main.py:132-140`),
  paginados (`main.py:142`).
- `GET /musicas` (`main.py:154-156`) devolve todos os objetos, apesar de o
  comentário `main.py:149-153` falar em paginação.
- `GET /musica/<m_id>/` (`main.py:166-168`) devolve o objeto completo; id
  inexistente gera HTTP 500. Sem a barra final, o Flask responde 308.
- `GET /generos` (`main.py:158-160`) devolve 52 gêneros; `GET /acordes`
  (`main.py:162-164`) devolve 6.653 acordes em ordem arbitrária.
- `GET /` serve `static/index.html` (`main.py:101-103`); `/<path:path>` serve
  qualquer arquivo de `static/` (`main.py:109-112`); o Flask também registra
  `/static/<path:filename>`.
- Localmente, `python main.py` sobe em `:5000` com `debug=True`
  (`main.py:279-280`); no Docker, `gunicorn --bind 0.0.0.0:8080 main:app`
  (`Dockerfile:12`).

## 4. Frontend: `#/porsequencia`

### 4.1 Rota e arquivos

- Rota em `static/assets/js/routes.js:17-21`:
  `templateUrl: "templates/sequencia.html"`, `controller: "SequenciaController"`,
  `controllerAs: "Sequencia"`.
- Controller em `static/assets/js/controllers/sequencia.js:1-105`.
- Template em `static/templates/sequencia.html:1-63`.
- Inclusão em `static/index.html:123` (`ng-view`) e scripts em
  `static/index.html:125-147` (AngularJS 1.4.9 e jQuery 1.11.3 via CDN, bootstrap
  3.3.6, `app.js`, `routes.js`, controllers e diretivas).

### 4.2 Catálogo hardcoded

`sequencia.js:2-37` define e empilha quatro sequências em
`vm.sequenciasFamosas`:

| Objeto | Linhas | Acordes | String | Chave backend | Tag |
|---|---|---|---:|---:|---:|
| `sequencia1` | 2-9 | Bm, G, D, A | `BmGDA` | `main.py:40` | 0 |
| `sequencia2` | 10-17 | C, G, Am, F | `CGAmF` | `main.py:41` | 1 |
| `sequencia3` | 18-23 | Gm, F | `GmF` | `main.py:44` | 4 |
| `sequencia4` | 24-31 | C, C7, F, Fm | `CC7FFm` | `main.py:45` | 5 |

`EmG` (id 2, `main.py:42`) e `CA7DmG7` (id 3, `main.py:43`) existem no backend mas
não aparecem na página. Cada objeto tem `index: 1` (`sequencia.js:3`, `11`, `19`,
`25`), campo não usado no template.

### 4.3 Comportamento da página

- A lista é renderizada em `static/templates/sequencia.html:6-8`; o clique está no
  contêiner de cada sequência (`:6`), e cada acorde é um `df-hex`
  (`:7`, `static/assets/js/directives/df-hex.js:1-12`).
- Ao clicar, `pesquisarPorSequencia` (`sequencia.js:63-90`) monta
  `similares?sequencia=<acordes com vírgulas>` (`:73`), opcionalmente com
  `&generos=<um gênero>` (`:74-76`), e faz `$http.get` (`:77-89`).
  `createChordsString` (`:55-61`) remove a vírgula final.
- O seletor de gênero é único (`static/templates/sequencia.html:24-30`) e usa a
  lista `GENEROS` hardcoded em `static/assets/js/app.js:6-58` com 51 nomes. O
  backend tem 52, incluindo `R&B;`, ausente no JavaScript.
- A área de resultados só aparece depois de uma seleção
  (`static/templates/sequencia.html:19`); clicar em um acorde da sequência
  selecionada limpa a busca (`:34`, `sequencia.js:92-95`).
- Os cartões (`static/templates/sequencia.html:40-58`) mostram título, artista e
  gênero; o clique abre `music.url` em nova janela (`sequencia.js:97-99`). O
  template usa `ng-hide="music.diferenca.length"` (`:43`), mas o caminho de
  sequência não devolve `diferenca`; o Angular avalia `undefined.length` sem erro.
- Não há formulário, botão, `POST` ou chamada para cadastrar sequência, nem
  controle de paginação. `pagina` nunca é enviado, então só a primeira página de
  100 resultados é acessível pela UI.
- A constante `RESTAPI` (`static/assets/js/app.js:3-5`,
  `http://localhost:5003`) não é injetada em nenhum controller. Os controllers
  usam `apiUrl = ""` (`acordes.js:91`, `musica.js:12`, `sequencia.js:72`), então as
  requisições são relativas à mesma origem.
- Em `#/pormusica`, o typeahead usa `search?key=<valor>` (`musica.js:14-20`,
  `static/templates/musica.html:8-18`) e a seleção usa
  `similares?id_unico_musica=<id>` (`musica.js:43-70`). Os métodos
  `addAcorde`/`temAcorde` de `musica.js:22-33` referenciam `vm.meusAcordes`, que
  não é inicializado nesse controller e não é usado no template.

## 5. Persistência, deploy e testes

### 5.1 Persistência

- Não há banco de dados. `requirements.txt:4-5` lista apenas
  `Flask==3.1.3` e `gunicorn==23.0.0`; não há `import sqlite3`, SQLAlchemy, TinyDB,
  DuckDB ou equivalente em nenhum `.py`.
- Todo o estado é construído em memória na importação, a partir do CSV
  (`main.py:49-98`).
- O `Dockerfile:1-12` não declara `VOLUME`; o comando documentado
  `docker run -p 8080:8080 ciframe` (`README.md:15-18`, `AGENTS.md:22-25`) não
  monta volume. Nada gravado dentro do container em runtime sobrevive à remoção do
  container.
- `docs/adr/0002-persist-custom-sequences.md:1-8` é um template não preenchido
  (bloco de instruções + `[seu texto aqui]`); não há decisão de banco registrada.
- O enunciado da tarefa (`docs/features/sequencias-customizadas/00-enunciado.md:38-40`,
  `:52-55`, `:60-65`) pede persistência apenas para o catálogo de sequências,
  mantendo músicas/gêneros no CSV em memória e a aplicação em um container único
  local. Isso é especificação da tarefa, não implementação existente.
- Opções citadas na pergunta e o que existe no repo: SQLite, TinyDB, DuckDB e JSON
  não estão presentes. SQLite não exigiria dependência adicional porque `sqlite3`
  integra a biblioteca padrão do CPython; TinyDB e DuckDB exigiriam inclusão em
  `requirements.txt`; JSON exigiria código de leitura/escrita, que não existe.
  Qualquer armazenamento em arquivo dependeria de um volume para sobreviver à
  remoção do container, e nenhum volume está declarado no `Dockerfile` ou no
  comando documentado.

### 5.2 Testes e verificação

- Não há testes automatizados versionados: `git ls-files` só encontra
  `docs/features/sequencias-customizadas/04-test-report.md`, que é um template não
  preenchido (`04-test-report.md:1-25`). Não há `pytest`/`unittest` em
  `requirements.txt` nem configuração de CI (`.github/` não existe).
- O critério de regressão aparece apenas como texto em
  `docs/features/sequencias-customizadas/00-enunciado.md:66-68` e
  `04-test-report.md:9-14`.
- A verificação manual documentada é `curl http://localhost:8080/generos`
  (`AGENTS.md:35-41`).

## 6. Fluxos de dados entre componentes

### 6.1 Startup

```
data/top/dataset_final.csv
  -> main.py:49-98 (parse, limpeza, limpa_cifra, split SEQ_FAMOSA)
  -> Musica objects (musica.py:1-25)
  -> musicas_dict -> musicas (OrderedDict por popularidade)
     + genero_musicas (listas por gênero, ordenadas por popularidade)
     + generos (list) + acordes (set)
```

### 6.2 Busca por sequência

```
#/porsequencia (routes.js:17-21)
  -> SequenciaController.pesquisarPorSequencia (sequencia.js:63-90)
  -> createChordsString (sequencia.js:55-61): "Bm,G,D,A"
  -> GET /similares?sequencia=Bm,G,D,A[&generos=X]
  -> main.py:191 substitui "," -> "BmGDA"
  -> sequencias["BmGDA"] = 0 (main.py:40-45)
  -> apply_filtro(musicas.values(), generos_key) (main.py:205, 266-272)
  -> scan de musica.seqs_famosas (main.py:203-223)
  -> get_pagina (main.py:226-228)
  -> json.dumps (main.py:197)
  -> $http.get success/error (sequencia.js:77-89)
  -> cartões em sequencia.html:40-58
```

### 6.3 Busca por acordes e por música

```
#/poracordes -> AcordesController (acordes.js:84-115)
  -> GET /similares?acordes=C,G[&generos=X]
  -> main.py:184-186
  -> get_similares(acordes, generos_key) (main.py:230-263)
  -> interseção/diferença + ordenação (main.py:240-263)
  -> resposta com "diferenca"/"intersecao"
  -> acordes.html:41-58 (tocáveis) e :64-91 (faltam acordes)

#/pormusica -> MusicaController (musica.js:1-80)
  -> typeahead GET /search?key=... (musica.js:14-20, main.py:114-142)
  -> seleção GET /similares?id_unico_musica=... (musica.js:43-70, main.py:187-189)
  -> mesmo get_similares do caminho de acordes
```

### 6.4 Catálogo de sequências

Hoje há duas fontes independentes e nenhuma API de catálogo:

- backend: dicionário `main.py:40-45`;
- frontend: array `sequencia.js:2-37`;
- arquivo auxiliar não lido por código:
  `data/mapeamento_sequencias_famosas.txt:1-6`.

Não há endpoint que devolva o catálogo nem endpoint que cadastre/altere
sequências.

## 7. Medições de matching sobre o CSV

Todas as contagens abaixo foram feitas sobre as 67.585 linhas carregadas, com a
mesma limpeza de `main.py:53-55`. "Contígua exata" compara os tokens como estão
escritos; "contígua lower" aplica `lower()` antes, como
`scripts/generate_data_set.py:12`; "só acordes da sequência" aplica apenas as
linhas 16-20 do gerador; a última coluna aplica as duas condições e reproduz a
coluna do CSV com 0 divergências.

| Sequência | id | tag atual | contígua exata | contígua lower | só acordes da seq. | ambas |
|---|---|---:|---:|---:|---:|---:|
| Bm–G–D–A | 0 | 199 | 866 | 972 | 873 | 199 |
| C–G–Am–F | 1 | 296 | 1.216 | 1.246 | 958 | 296 |
| Em–G | 2 | 4 | 3.110 | 3.704 | 24 | 4 |
| C–A7–Dm–G7 | 3 | 5 | 96 | 96 | 53 | 5 |
| Gm–F | 4 | 7 | 1.039 | 1.522 | 18 | 7 |
| C–C7–F–Fm | 5 | 3 | 132 | 144 | 57 | 3 |

O caso `Linda Juventude` ilustra a diferença: a versão do 14 Bis tem cifra com
trechos `Em;G` mas usa muitos outros acordes e não tem tag; a versão de Flávio
Venturini começa com `Em;G` mas também usa `A9`, `B4`, `C`, `D`, `Bm7` etc. e
também não tem tag 2.

## 8. Observações factuais adicionais

- `musicas` é ordenado globalmente por popularidade (`main.py:88-89`), mas
  `apply_filtro` devolve as listas por gênero concatenadas; a ordenação global não
  é reaplicada em `get_similares_por_sequencia`.
- `Musica.acordes` perde ordem e repetição (`musica.py:17`); `Musica.cifra`
  preserva (`musica.py:16`).
- Músicas com cifra vazia (8.141) têm `acordes = []` e nunca entram em resultados
  de `/similares` por acordes ou por música; continuam acessíveis em `/musicas`,
  `/search` e `/musica/<id>/`.
- O `id_unico_musica` é usado como chave de `musicas` (`main.py:74`), então ids
  repetidos no CSV sobrescreveriam a entrada anterior; no CSV atual não há
  duplicatas (67.585 pares `(ARTISTA_ID, MUSICA_ID)` distintos).
- O CSV é lido sem `encoding` explícito (`main.py:49`); o arquivo contém
  caracteres não ASCII (por exemplo `Adoráveis Criaturas`, `Muié`), servidos
  corretamente no ambiente de teste.
