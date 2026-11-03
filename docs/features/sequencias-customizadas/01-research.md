# Pesquisa — Sequências de Acordes Customizadas

## Resumo

Hoje a busca por "sequência famosa" é inteiramente baseada em uma coluna pré-calculada do CSV: `main.py:40-45` define seis sequências com ids inteiros, e `GET /similares?sequencia=...` apenas verifica se o id está na lista `Musica.seqs_famosas` (`main.py:190-197`, `main.py:203-223`). Não existe cálculo em tempo real a partir da cifra, nem endpoint de escrita de sequências; o frontend oferece outras quatro sequências, hardcoded em `static/assets/js/controllers/sequencia.js:2-37`. O CSV `data/top/dataset_final.csv` não tem cabeçalho e `main.py:50` descarta a primeira linha de dados, de modo que 67.585 das 67.586 músicas ficam em memória. O rótulo `SEQ_FAMOSA` não significa "a sequência aparece na música": o gerador `scripts/generate_data_set.py:7-24` exige ao mesmo tempo que a sequência inteira ocorra contiguamente e que a música não use nenhum acorde fora dela. O repositório não contém banco de dados, testes automatizados nem configuração de CI.

## Perguntas que você precisa responder

1. **Algoritmo de matching**: hoje, as 6 sequências hardcoded em `main.py` (linhas
   40-45) são comparadas contra músicas via uma tag pré-computada
   (`SEQ_FAMOSA`/`seqs_famosas`, vinda do CSV). Sequências cadastradas pelo usuário
   não têm essa tag — o matching precisa ser calculado em tempo real a partir da
   lista de acordes de cada música (`musica.acordes`/`musica.cifra`). O que vai
   definir "a sequência X aparece na música Y"? A ordem dos acordes importa?
   Repetições de acorde dentro da música importam? É preciso normalizar (ex.:
   maiúsculas/minúsculas, variações de escrita do mesmo acorde)?
2. **Validação da hipótese**: rode o algoritmo que você está considerando contra os
   dados reais em `data/top/dataset_final.csv`, para as 6 sequências hoje
   hardcoded, e confirme (ou refute) que ele reproduz os mesmos matches que o
   código atual produz via `seqs_famosas`. Esse é o bar mínimo de correção que
   você vai usar na fase de testes.
3. **Banco de dados**: quais bancos embarcados (sem serviço externo adicional) são
   viáveis dentro do container Docker único e local-only já documentado em
   `docs/adr/0001-local-only-docker-deploy.md`? O que cada opção implica para o
   `Dockerfile` atual e para a persistência dos dados entre reinícios do
   container?
4. **Frontend existente**: o que a página `#/porsequencia`
   (`static/templates/sequencia.html` +
   `static/assets/js/controllers/sequencia.js`) já faz? Repare que ela tem hoje uma
   lista *hardcoded no JavaScript* de 4 sequências (`sequencia1`..`sequencia4`),
   diferente das 6 que existem no backend — um detalhe real e pré-existente do
   código, não um erro seu, que vale entender antes de decidir o que precisa
   mudar.

## Registro das descobertas

### 1. Algoritmo de matching

#### 1.1 O caminho do `GET /similares?sequencia=...`

A rota está em `main.py:170-201`. Os parâmetros lidos são `acordes`,
`id_unico_musica`, `sequencia` e `pagina` (`main.py:173-176`) e, opcionalmente,
`generos` (`main.py:179-182`). O trecho que trata sequência é `main.py:190-197`:

- `acordes = sequencia_tag.replace(',', '')` remove as vírgulas do valor recebido
  (`main.py:191`), transformando `Bm,G,D,A` em `BmGDA`.
- A string resultante é usada como chave do dicionário `sequencias`
  (`main.py:40-45`): `{'BmGDA': 0, 'CGAmF': 1, 'EmG': 2, 'CA7DmG7': 3, 'GmF': 4,
  'CC7FFm': 5}`. A comparação é exata e sensível a maiúsculas/minúsculas: foi
  verificado que `sequencia=emg` devolve `[]`, `sequencia=Em,G` devolve 4
  resultados e `sequencia=Em, G` (com espaço) devolve `[]`.
- Se a chave existir, chama `get_similares_por_sequencia(id_seq, generos_key)` e
  pagina o resultado (`main.py:194-196`). Se não existir, `similares` permanece
  `[]` e a resposta é `[]` (`main.py:192-197`).
- O filtro por gênero é aplicado antes da varredura, via `apply_filtro`
  (`main.py:205`, `main.py:266-272`).
- A resposta é `json.dumps(...)` (string), com `Content-Type: text/html;
  charset=utf-8` (verificado com o test client do Flask), não `jsonify`.

`get_similares_por_sequencia` (`main.py:203-223`) percorre a coleção filtrada e
inclui a música quando `str(id_seq) in musica.seqs_famosas` (`main.py:209`). Cada
item devolvido contém `id_unico_musica`, `id_artista`, `id_musica`,
`nome_artista`, `nome_musica`, `popularidade`, `acordes`, `genero` e `url`
(`main.py:210-220`). Não há `diferenca` nem `intersecao` nesse caminho.

A paginação é `TAM_PAGINA = 100` (`main.py:35`) e o corte é
`(int(pagina_tag) - 1) * 100` (`main.py:226-228`). Por isso, das 199 músicas com a
tag `0`, a página 1 devolve 100 e a página 2 devolve 99; das 296 com a tag `1`, as
páginas 1 e 2 devolvem 100 cada e a página 3 devolve 96. Valores não inteiros de
`pagina` causam `ValueError`/HTTP 500 (verificado com `pagina=abc`).

O dicionário `sequencias` é independente de `data/mapeamento_sequencias_famosas.txt`
(`data/mapeamento_sequencias_famosas.txt:1-6`): esse arquivo lista os mesmos ids e
nomes, mas não é lido por nenhum código Python, JavaScript, R ou shell do
repositório (busca por `mapeamento_sequencias` não retorna referências).

#### 1.2 De onde vem `SEQ_FAMOSA`/`seqs_famosas`

- A coluna 7 do CSV é lida como `SEQ_FAMOSA` (`main.py:33`).
- Na carga, `musica[SEQ_FAMOSA] = musica[SEQ_FAMOSA].split(";")` (`main.py:63`).
  Para músicas sem tag, o campo `NA` já foi removido em `main.py:53`, o `split`
  produz `['']` e a lista fica `['']` (confirmado em
  `/musica/14-bis_adoraveis-criaturas/`).
- `Musica.__init__` apenas guarda essa lista em `self.seqs_famosas`
  (`musica.py:18`). Nada no backend calcula a tag em tempo de request.

A coluna foi gerada por `scripts/generate_data_set.py:7-24`. A função
`get_famosas` (linhas 7-24):

1. baixa a caixa da cifra (`acorde = acorde.lower()`, linha 12);
2. exige que a sequência inteira, com separadores `;`, apareça como substring
   contígua da cifra: `if s in acorde:` (linha 13);
3. exige que **todos** os acordes da música estejam entre os acordes da sequência:
   o laço das linhas 16-20 percorre `acorde.split(';')` e marca `achou = False` no
   primeiro acorde que não estiver em `s.split(';')`;
4. se as duas condições valerem, acrescenta o índice da sequência (linha 22).

O resultado é concatenado sem separador (`famosas = ''.join(get_famosas(str_notas))`,
linha 88) e escrito na coluna 7 (`scripts/generate_data_set.py:84-89`). Como todas
as tags presentes no CSV atual têm um único dígito (ver 1.3 e seção 2), a
concatenação não produz valores com mais de um dígito nesse arquivo.

Definição operacional que o código atual usa, portanto: uma música recebe a tag da
sequência `i` quando (a) a sequência completa ocorre de forma contígua, na ordem,
na cifra da música (após baixar a caixa) **e** (b) a música não usa nenhum acorde
que não pertença ao conjunto de acordes da sequência. A ordem importa para a
condição (a); repetições só importam enquanto afetam a ocorrência contígua;
maiúsculas/minúsculas são normalizadas apenas por `lower()`; não há normalização de
enarmonia ou de variações de escrita (`C` e `C7` são acordes distintos, como
mostra `scripts/generate_data_set.py:8`).

#### 1.3 O que o código atual não tem

- Não há cálculo de matching de sequência a partir de `musica.cifra` nem de
  `musica.acordes`: o caminho de sequência só consulta `seqs_famosas`
  (`main.py:203-223`).
- `musica.acordes` é `list(set(cifra))` (`musica.py:17`), ou seja, perde ordem e
  repetições. `musica.cifra` preserva a ordem (`musica.py:16`).
- O único tokenizador de cifra é `limpa_cifra` (`main.py:11-23`): descarta tokens
  vazios, para linhas com `|` pega o texto antes do primeiro `|` e o primeiro
  token, e para as demais separa por espaços. Ele não baixa caixa nem normaliza
  acordes.
- A rota `GET /similares` também atende busca por acordes avulsos e por música.
  Nesses dois caminhos, `get_similares` (`main.py:230-263`) faz interseção e
  diferença de conjuntos (`main.py:240-241`) e devolve `diferenca` e `intersecao`
  (`main.py:246-258`), ordenando por `(len(diferenca), -len(intersecao))`
  (`main.py:263`) — apesar de o comentário em `main.py:262` citar popularidade, ela
  não entra na chave de ordenação.
- Não existe rota de escrita. O mapa de rotas (`main.py:101-172`) contém apenas
  `GET` em `/`, `/<path:path>`, `/search`, `/musicas`, `/generos`, `/acordes`,
  `/musica/<m_id>/` e `/similares`; não há `POST`, `PUT` ou `DELETE`.
- Detalhe de implementação: a função da rota chama-se `get_similares`
  (`main.py:170-171`) e, mais abaixo, o helper também se chama `get_similares`
  (`main.py:230`). O Flask registrou o primeiro objeto no mapa de rotas; em tempo
  de execução, o nome global resolve para o helper de 3 argumentos, que é o que a
  linha `main.py:199` chama. Verificado com o test client: a rota continua
  respondendo e `main.app.view_functions['get_similares']` tem 0 argumentos,
  enquanto `main.get_similares` tem 3.

### 2. Validação com os dados

#### 2.1 Estado do arquivo

- `data/top/dataset_final.csv` tem 67.586 linhas e 15.866.887 bytes; a primeira
  linha já é um registro de dados
  (`14-bis,a-qualquer-tempo,14 Bis,A Qualquer Tempo,MPB,...`), não um cabeçalho.
- `main.py:50` executa `f.readline()` assumindo cabeçalho e descarta essa primeira
  música. Resultado: `GET /musicas` devolve 67.585 objetos (verificado), e
  `/musica/14-bis_a-qualquer-tempo/` devolve HTTP 500 por `KeyError`
  (`main.py:168`).
- Todas as 67.585 linhas restantes têm 9 campos após a limpeza de `main.py:53-55`.
- 8.141 linhas têm `CIFRA = NA`; após `main.py:53` e `main.py:58-61`, ficam com
  `cifra = []` e `acordes = []`.
- 514 linhas têm alguma tag em `SEQ_FAMOSA`: 199 com `0`, 296 com `1`, 4 com `2`,
  5 com `3`, 7 com `4` e 3 com `5`. As outras 67.071 ficam com `['']`.
- A coluna de tag só assume os valores `''`, `'0'`, `'1'`, `'2'`, `'3'`, `'4'` e
  `'5'` (7 valores distintos).

#### 2.2 Reprodução do rótulo atual

Reimplementando exatamente as duas condições de `scripts/generate_data_set.py:7-24`
sobre as 67.585 linhas carregadas, a coluna `SEQ_FAMOSA` foi reproduzida com **0
divergências**. Isso confirma que a tag atual não é "a sequência aparece na
música", e sim a conjunção "sequência contígua presente" + "nenhum acorde fora da
sequência".

Contagens medidas sobre o CSV (script de pesquisa, sem alterar o repositório):

| Sequência | id | tag atual (`seqs_famosas`) | contígua (tokens), caixa exata | substring, sem diferenciar caixa | só "acordes dentro da sequência" | as duas condições (reproduz a tag) |
|---|---|---:|---:|---:|---:|---:|
| Bm–G–D–A | 0 | 199 | 866 | 972 | 873 | 199 |
| C–G–Am–F | 1 | 296 | 1.216 | 1.246 | 958 | 296 |
| Em–G | 2 | 4 | 3.110 | 3.704 | 24 | 4 |
| C–A7–Dm–G7 | 3 | 5 | 96 | 96 | 53 | 5 |
| Gm–F | 4 | 7 | 1.039 | 1.522 | 18 | 7 |
| C–C7–F–Fm | 5 | 3 | 132 | 144 | 57 | 3 |

A coluna "contígua (tokens), caixa exata" é o teste de subsequência contígua
comparando os tokens da cifra como estão escritos no CSV, com limites de token. A
coluna "substring, sem diferenciar caixa" usa `lower()` e busca a sequência como
substring, sem exigir limites de token; por isso `em;g` também casa prefixos como
`g5` e os números são maiores. A implementação usa a primeira regra. A coluna "só
acordes dentro da sequência" aplica apenas a condição das linhas 16-20. A última
coluna aplica as duas e coincide exatamente com a coluna do CSV.

O caso citado no rascunho anterior se confirma com os dados: a linha
`14-bis,linda-juventude,14 Bis,Linda Juventude,...,NA,...` não tem tag, embora sua
cifra contenha `Em;G` em várias posições. Já a linha
`flavio-venturini,linda-juventude,Flávio Venturini,Linda Juventude,...` começa com
`Em;G` mas usa acordes como `A9`, `B4`, `C`, `D`, `Bm7` etc., então também não
recebe a tag `2`. As duas linhas foram inspecionadas diretamente no CSV.

Observação sobre a consulta: como a comparação no endpoint é feita por igualdade
de string após remover vírgulas (`main.py:191-194`), a ordem e a grafia enviadas
pelo cliente têm de coincidir com as chaves de `main.py:40-45`. `Em,G` funciona;
`emg`, `Em, G` e `G,Em` não funcionam (verificado).

### 3. Banco de dados

O estado atual do repositório é: **não há banco de dados**.

- `requirements.txt:4-5` declara somente `Flask==3.1.3` e `gunicorn==23.0.0`.
- Não há `import sqlite3`, SQLAlchemy, TinyDB, DuckDB, PyMongo ou equivalente em
  nenhum `.py` do projeto (busca em `main.py`, `musica.py` e `scripts/*.py`).
- Todo o estado é construído uma vez na importação do módulo, a partir do CSV
  (`main.py:49-98`): `musicas_dict`, `musicas`, `genero_musicas`, `generos` e
  `acordes`. Não há camada de persistência, migration, schema ou arquivo de dados
  gerado em runtime.
- O `Dockerfile` (`Dockerfile:1-12`) não declara `VOLUME` e o comando documentado
  de execução não monta volume (`README.md:15-18`, `AGENTS.md:22-25`:
  `docker run -p 8080:8080 ciframe`). O processo roda via
  `gunicorn --bind 0.0.0.0:8080 main:app` (`Dockerfile:12`); localmente,
  `python main.py` sobe em `:5000` com `debug=True` (`main.py:279-280`).
- `docs/adr/0002-persist-custom-sequences.md` é um template não preenchido: contém
  as instruções em bloco de citação e o marcador `[seu texto aqui]`
  (`docs/adr/0002-persist-custom-sequences.md:1-8`). Não há decisão registrada
  sobre banco.
- O enunciado da tarefa exige persistência apenas para o catálogo de sequências,
  mantendo músicas/gêneros no CSV em memória, dentro de um único container local
  (`docs/features/sequencias-customizadas/00-enunciado.md:38-40`,
  `00-enunciado.md:52-55`, `00-enunciado.md:60-65`). Isso é a especificação da
  tarefa, não código existente.

Sobre as tecnologias citadas na pergunta, o que o repositório atual permite afirmar:

| Opção | Presente no repo? | Dependência adicional | Onde os dados ficariam |
|---|---|---|---|
| SQLite | não | nenhuma: o módulo `sqlite3` faz parte da biblioteca padrão do CPython | arquivo local; para sobreviver à remoção do container precisaria de um volume, e nenhum volume está declarado no `Dockerfile` nem no comando documentado |
| TinyDB | não | precisaria ser acrescentado a `requirements.txt` | arquivo/JSON local; mesma questão de volume |
| DuckDB | não | precisaria ser acrescentado a `requirements.txt` | arquivo local; mesma questão de volume |
| JSON em arquivo | não | nenhuma | arquivo local; exigiria código de leitura/escrita, que hoje não existe; mesma questão de volume |

O único dado persistido hoje é o próprio `data/top/dataset_final.csv`, versionado
no repositório e copiado para a imagem em `Dockerfile:8`; ele é lido a cada início
de processo, não a cada request (`main.py:49-98`).

### 4. Frontend existente

#### 4.1 Rota, controller e template

- A rota `#/porsequencia` está em `static/assets/js/routes.js:17-21` e aponta para
  `templates/sequencia.html` com `SequenciaController` e `controllerAs:
  "Sequencia"`.
- O controller está em `static/assets/js/controllers/sequencia.js:1-105`.
- O template está em `static/templates/sequencia.html:1-63`.
- A página é incluída em `static/index.html:123` (`ng-view`) e os scripts são
  carregados em `static/index.html:125-147`; AngularJS 1.4.9 e jQuery 1.11.3 vêm de
  CDN (`static/index.html:126-134`).

#### 4.2 As quatro sequências hardcoded

`static/assets/js/controllers/sequencia.js:2-37` define quatro objetos e os
empilha em `vm.sequenciasFamosas`:

| Objeto JS | Linhas | Acordes | String enviada | Chave no backend | Tag |
|---|---|---|---|---:|---:|
| `sequencia1` | 2-9 | `Bm, G, D, A` | `BmGDA` | `main.py:40` | 0 |
| `sequencia2` | 10-17 | `C, G, Am, F` | `CGAmF` | `main.py:41` | 1 |
| `sequencia3` | 18-23 | `Gm, F` | `GmF` | `main.py:44` | 4 |
| `sequencia4` | 24-31 | `C, C7, F, Fm` | `CC7FFm` | `main.py:45` | 5 |
| — | — | `Em, G` | `EmG` | `main.py:42` | 2 |
| — | — | `C, A7, Dm, G7` | `CA7DmG7` | `main.py:43` | 3 |

As duas últimas linhas existem no backend, mas não aparecem na página. Os objetos
têm um campo `index` fixo em `1` (`sequencia.js:3`, `11`, `19`, `25`) que não é
usado no template.

#### 4.3 O que a página faz

- O painel esquerdo lista as quatro sequências; o `ng-click` está no contêiner de
  cada sequência (`static/templates/sequencia.html:6`), e cada acorde é desenhado
  pela diretiva `df-hex` (`static/templates/sequencia.html:7`,
  `static/assets/js/directives/df-hex.js:1-12`).
- Ao clicar, `pesquisarPorSequencia` (`sequencia.js:63-90`) monta
  `similares?sequencia=<acordes separados por vírgula>` (`sequencia.js:73`),
  opcionalmente com `&generos=<um gênero>` (`sequencia.js:74-76`), e faz
  `$http.get` (`sequencia.js:77-89`). `createChordsString`
  (`sequencia.js:55-61`) remove a última vírgula.
- O seletor de gênero é um `select` único (`static/templates/sequencia.html:24-30`);
  só permite um gênero por vez. A lista `GENEROS` está hardcoded em
  `static/assets/js/app.js:6-58` com 51 nomes. O backend tem 52 gêneros: o CSV
  contém `R&B;` (303 músicas), que não está na lista do JavaScript (comparação
  feita entre `app.js` e a coluna 4 do CSV).
- O filtro de gênero e a lista de acordes da sequência selecionada só aparecem
  depois de uma seleção (`static/templates/sequencia.html:19`). Clicar em qualquer
  acorde da sequência selecionada chama `limparPesquisa`
  (`static/templates/sequencia.html:34`, `sequencia.js:92-95`).
- Os resultados são exibidos em cartões (`static/templates/sequencia.html:40-58`);
  cada cartão mostra `nome_musica`, `nome_artista` e `genero`, e o clique abre
  `music.url` em nova janela (`sequencia.js:97-99`). O template usa
  `ng-hide="music.diferenca.length"` (`static/templates/sequencia.html:43`), mas o
  caminho de sequência não devolve `diferenca` (`main.py:210-220`); a expressão
  Angular avalia `undefined.length` sem erro.
- Não há formulário, botão ou chamada para cadastrar sequência. Também não há
  controle de paginação: `pagina` nunca é enviado, então só a primeira página de
  100 resultados é exibida.
- A constante `RESTAPI` (`static/assets/js/app.js:3-5`, valor
  `http://localhost:5003`) não é injetada em nenhum controller. Os controllers de
  acordes, música e sequência usam `apiUrl = ""` (`acordes.js:91`,
  `musica.js:12`, `sequencia.js:72`), de modo que as requisições são relativas à
  mesma origem.
- A tela de busca por música usa `uib-typeahead` com `typeahead-min-length="3"` e
  `typeahead-wait-ms="1000"` (`static/templates/musica.html:8-18`), chamando
  `search?key=<valor>` (`musica.js:14-20`); ao selecionar, chama
  `similares?id_unico_musica=<id>` (`musica.js:43-70`). Os métodos `addAcorde` e
  `temAcorde` de `musica.js:22-33` referenciam `vm.meusAcordes`, que não é
  inicializado nesse controller e não é usado no template.

### 5. Carregamento do CSV e estruturas em memória

A carga ocorre na importação do módulo e é o único ponto que lê o CSV
(`main.py:49-98`):

1. `f = open('data/top/dataset_final.csv')` (`main.py:49`) e `f.readline()`
   (`main.py:50`). Como não há cabeçalho, a primeira música é descartada.
2. Para cada linha: `line.replace('"', '').replace('NA', '')[:-1]` (`main.py:53`).
   Isso remove todas as aspas, remove **toda** ocorrência da substring `NA` e
   descarta o último caractere (o `\n`). Efeitos observados no CSV atual:
   - 18 linhas contêm aspas; por exemplo
     `data/top/dataset_final.csv:8381` (`"3"` vira `3`),
     `data/top/dataset_final.csv:9543` (`"Vamo" Comer` vira `Vamo Comer`) e
     `data/top/dataset_final.csv:26276` (`O Grande "Eu Sou"`).
   - 7 títulos/artistas contêm `NA` e são alterados; por exemplo
     `data/top/dataset_final.csv:25631` (`DNA` vira `D`),
     `data/top/dataset_final.csv:37719` (`CABANA` vira `CABA`) e
     `data/top/dataset_final.csv:45099` (`She's Got Style (Versão ORIGINAL)` vira
     `... ORIGIL`).
3. `musica = line.split(',')` (`main.py:55`) e os índices fixos de
   `main.py:25-34`: `0` artista_id, `1` musica_id, `2` artista, `3` musica, `4`
   genero, `5` popularidade, `6` tom, `7` seq_famosa, `8` cifra.
4. Popularidade: `int(musica[POPULARIDADE].replace('.', ''))` (`main.py:56`).
5. Cifra: se não vazia, `limpa_cifra(musica[CIFRA].split(';'))` (`main.py:58-59`);
   senão `[]` (`main.py:60-61`). `limpa_cifra` (`main.py:11-23`) descarta tokens
   vazios, para tokens com `|` pega o texto antes do `|` e o primeiro token, e para
   os demais separa por espaços.
6. Sequências: `split(";")` (`main.py:63`).
7. Constrói `Musica` com os nove campos (`main.py:69-72`) e guarda em
   `musicas_dict[id_unico_musica]` (`main.py:74`). `id_unico_musica` é
   `'%s_%s' % (id_artista, id_musica)` (`musica.py:20`) e `url` é
   `http://www.cifraclub.com.br/<id_artista>/<id_musica>` (`musica.py:22`).
8. Acumula gêneros em um `set` (`main.py:66`) e acordes em outro `set`
   (`main.py:77-78`, a partir de `musica_obj.acordes`). Indexa as músicas por
   gênero em `genero_musicas` (`main.py:82-85`).
9. Cria `musicas` como `OrderedDict` ordenado por popularidade decrescente
   (`main.py:88-89`), converte `generos` para lista (`main.py:92`) e ordena cada
   lista de `genero_musicas` por popularidade decrescente (`main.py:95-96`).

Números observados após a carga: 67.585 músicas, 52 gêneros, 6.653 acordes
distintos e tempo de importação de aproximadamente 1,7 s no ambiente desta
pesquisa. `AGENTS.md:41` também registra que o startup pode demorar enquanto o CSV
é parseado.

Consequências observáveis dos `set`:

- `generos` é `list(set)` (`main.py:38`, `main.py:92`); a ordem de `GET /generos`
  muda entre processos. Em duas execuções separadas, as listas começaram com
  `['Samba Enredo', 'Disco', 'Regional', ...]` e
  `['Sertanejo', 'Reggae', 'Disco', ...]`.
- `Musica.acordes` é `list(set(cifra))` (`musica.py:17`); a ordem dos acordes no
  JSON também muda entre processos. Para `capital-inicial_a-sua-maneira`, foram
  observadas `['D', 'G', 'Bm', 'A']` e `['G', 'A', 'D', 'Bm']` em execuções
  diferentes.
- Como `apply_filtro` concatena as listas na ordem de `generos_key`
  (`main.py:266-272`), a ordem dos resultados de `/similares` sem filtro de gênero
  acompanha essa ordem não determinística. O caminho de sequência não reordena o
  resultado (`main.py:203-223`).

Outros endpoints e comportamentos observados:

- `GET /musicas` (`main.py:154-156`) devolve todos os 67.585 objetos
  (`__dict__`), incluindo `cifra`, `acordes`, `seqs_famosas`, `tom` e `url`. O
  comentário em `main.py:149-153` fala em paginação, mas o código não pagina.
- `GET /musica/<m_id>/` (`main.py:166-168`) devolve o objeto completo; id
  inexistente gera HTTP 500 (`KeyError`). A rota exige a barra final: sem ela, o
  Flask responde 308 redirecionando para a versão com barra.
- `GET /search` (`main.py:114-142`) exige `key`; sem ela, `request.args.get('key')`
  é `None` e a rota responde HTTP 500 (`main.py:118`). A busca remove acentos com
  `remover_combinantes` (`main.py:145-147`), compara tokens exatos de
  `nome_artista` + `nome_musica` (`main.py:129-131`) e devolve
  `id_unico_musica`, `id_artista`, `id_musica`, `nome_artista`, `nome_musica`,
  `genero` e `url` (`main.py:132-140`), paginados (`main.py:142`). A rota também
  aceita `generos` (`main.py:116`, `main.py:121-125`) e `pagina` (`main.py:117`,
  `main.py:142`); o typeahead do frontend envia apenas `key` (`musica.js:16`).
- `GET /generos` (`main.py:158-160`) devolve os 52 gêneros; `GET /acordes`
  (`main.py:162-164`) devolve os 6.653 acordes em ordem arbitrária.
- `GET /` serve `static/index.html` (`main.py:101-103`); `/<path:path>` serve
  qualquer arquivo de `static/` (`main.py:109-112`), inclusive
  `/templates/home.html` e `/assets/js/app.js` (verificado com o test client). O
  Flask também registra a rota padrão `/static/<path:filename>`.
- `@app.after_request` adiciona `Access-Control-Allow-Origin: *` a todas as
  respostas (`main.py:274-277`).

### 6. Testes atuais

- Não há testes automatizados no repositório: nenhum arquivo de teste está
  versionado (`git ls-files` só encontra
  `docs/features/sequencias-customizadas/04-test-report.md`), não há `pytest`,
  `unittest` ou framework de testes em `requirements.txt:4-5`, e não existe
  diretório `.github/` nem configuração de CI.
- `docs/features/sequencias-customizadas/04-test-report.md:1-25` é o template da
  fase de testes, ainda não preenchido.
- O critério de regressão existe apenas como texto na especificação:
  `docs/features/sequencias-customizadas/00-enunciado.md:66-68` e
  `04-test-report.md:9-14` exigem que as 6 sequências originais continuem
  produzindo os mesmos resultados. Não há teste que verifique isso.
- A verificação manual documentada é `curl http://localhost:8080/generos`
  (`AGENTS.md:35-41`).

## Fluxo de dados entre componentes

1. **Startup**: `data/top/dataset_final.csv` é lido uma vez em `main.py:49-98`;
   cada linha vira um `Musica` (`musica.py:1-25`); os objetos vão para
   `musicas_dict` e depois para `musicas` (ordenado por popularidade), além de
   `genero_musicas`, `generos` e `acordes`.
2. **Busca por sequência**: `#/porsequencia` → `SequenciaController`
   (`sequencia.js:1-105`) → `createChordsString` (`sequencia.js:55-61`) →
   `GET /similares?sequencia=Bm,G,D,A` → `main.py:190-197` remove vírgulas →
   `sequencias['BmGDA'] = 0` (`main.py:40-45`) → `apply_filtro` (`main.py:266-272`)
   → varredura de `musica.seqs_famosas` (`main.py:203-223`) → `get_pagina`
   (`main.py:226-228`) → `json.dumps` → resposta consumida por
   `$http.get` (`sequencia.js:77-89`) → cartões em
   `static/templates/sequencia.html:40-58`.
3. **Busca por acordes**: `#/poracordes` → `AcordesController`
   (`acordes.js:84-115`) → `GET /similares?acordes=C,G` → `main.py:184-186` →
   `get_similares` (`main.py:230-263`) calcula `intersecao` e `diferenca` →
   `get_pagina` → `json.dumps` → template separa músicas tocáveis
   (`music.diferenca.length == 0`, `static/templates/acordes.html:41-58`) das que
   exigem acordes novos (`static/templates/acordes.html:64-91`).
4. **Busca por música**: `#/pormusica` → typeahead chama `GET /search?key=...`
   (`musica.js:14-20`, `main.py:114-142`) → seleção chama
   `GET /similares?id_unico_musica=...` (`musica.js:43-70`) → `main.py:187-189`
   usa os acordes da música → mesmo `get_similares` do item 3.
5. **Catálogo de sequências**: hoje só existe no backend (`main.py:40-45`) e,
   separadamente, no JavaScript (`sequencia.js:2-37`); não há chamada de API que
   devolva o catálogo nem endpoint que o altere.

## Trade-offs identificados

Características observáveis do estado atual (sem propor mudanças):

- **Matching por tag x matching por cifra**: a tag é mais restritiva que a
  ocorrência contígua. Medido no CSV: 866 músicas contêm `Bm;G;D;A` contiguamente
  com limites de token (3.110 para `Em;G`), mas apenas 199 (4 para `Em;G`)
  satisfazem também "nenhum acorde fora da sequência". A variante por substring dá
  972 e 3.704, mas casa prefixos e não é a regra adotada. As duas definições
  produzem conjuntos diferentes de músicas.
- **Catálogo de sequências**: as 6 sequências do backend estão em código
  (`main.py:40-45`) e as 4 do frontend estão em outro código
  (`sequencia.js:2-37`); não há fonte única nem endpoint de catálogo. `EmG` e
  `CA7DmG7` existem no backend mas não são alcançáveis pela página.
- **Persistência**: não há banco; o único dado persistido é o CSV versionado, lido
  a cada início de processo. O `Dockerfile` não declara volume e o comando
  documentado não monta volume, então nada gravado dentro do container em runtime
  sobrevive à remoção do container. O ADR 0002, que registraria essa decisão, está
  em branco (`docs/adr/0002-persist-custom-sequences.md:1-8`).
- **Carga do CSV**: a primeira linha de dados é sempre descartada
  (`main.py:50`), 8.141 músicas ficam sem cifra e 7 títulos são alterados pela
  remoção global de `NA` (`main.py:53`). O arquivo precisa ser relido por inteiro
  a cada restart (`AGENTS.md:45`).
- **Ordenação**: `generos` e `acordes` vêm de `set`, então a ordem de
  `GET /generos`, de `GET /acordes` e dos resultados de `/similares` sem filtro
  varia entre processos; o caminho de sequência não aplica ordenação própria.
- **Paginação**: todos os endpoints de busca cortam em 100 itens
  (`main.py:35`, `main.py:226-228`); o frontend nunca envia `pagina`, então só a
  primeira página é acessível pela UI.
