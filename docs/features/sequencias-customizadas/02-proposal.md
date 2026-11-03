# Proposta — Sequências de Acordes Customizadas

## Abordagem escolhida

**Proposta 1 — SQLite com dois modos de matching.** O catálogo de sequências (as 6
originais + as novas) passa a viver em um banco SQLite embarcado, e a busca por
sequência ganha um caminho novo por `sequencia_id`. As 6 originais continuam usando
a tag `SEQ_FAMOSA` exatamente como hoje; as novas usam uma regra de ocorrência
contígua ordenada sobre `musica.cifra`. A escolha preserva o critério de regressão
por construção, mantém o CSV de músicas/gêneros em memória e não adiciona
dependência de runtime.

### Algoritmo de matching

**As 6 originais (modo `legacy_tag`).** Nada muda no caminho atual: a música entra no
resultado quando `str(legacy_tag) in musica.seqs_famosas` (`main.py:209`), onde a
lista vem da coluna `SEQ_FAMOSA` (`main.py:63`, `musica.py:18`). A pesquisa mostrou
que essa tag significa, ao mesmo tempo, "a sequência completa aparece contiguamente
na cifra" **e** "a música não usa nenhum acorde fora da sequência"
(`scripts/generate_data_set.py:7-24`; `01-research.md`, seções 1.2 e 2.2). Manter
esse caminho é a forma de menor risco de garantir os mesmos resultados de hoje.

**As novas (modo `ordered`).** Seja `S = [s1, …, sk]` a lista ordenada cadastrada e
`C = musica.cifra` a lista ordenada de acordes da música (`musica.py:16`). A música é
compatível se existe `i` tal que `C[i+j].lower() == s(j).lower()` para todo
`j` de `0` a `k-1`. Em outras palavras: a sequência precisa ocorrer **contígua e na
ordem**, e a música pode ter outros acordes antes ou depois. Repetições dentro da
música são permitidas e podem gerar mais de uma ocorrência; repetições dentro da
sequência precisam ser respeitadas. `musica.acordes` não é usado porque perde ordem e
repetição (`musica.py:17`).

Normalização e validação propostas:

- comparação em minúsculas (`lower()`), sem normalização enarmônica: `C#` e `Db`
  continuam acordes diferentes;
- cada acorde é validado contra o vocabulário de `GET /acordes` (6.653 tokens na
  carga atual, `01-research.md` seção 5) usando um índice case-insensitive; o valor
  canônico é o que fica salvo;
- 1 a 16 acordes por sequência, nome de 1 a 80 caracteres; `;` é rejeitado dentro de
  um acorde porque o índice de busca usa `;` como separador;
- a string normalizada (`;` + acordes em minúsculas + `;`) é única: duplicata
  retorna 409, inclusive se colidir com uma das 6 originais.

**Por que não aplicar a regra legada às novas.** A regra da tag é um artefato da
geração do CSV e é bem mais restritiva que "a sequência aparece na música". A
pesquisa mediu, por exemplo, 199 músicas para Bm–G–D–A pela tag contra 866 pela
ocorrência contígua com limites de token, e 4 para Em–G contra 3.110
(`01-research.md`, seção 2.2). A variante por substring daria 972 e 3.704, mas casa
prefixos como `G5`; não é a regra escolhida. Aplicar
a regra legada às sequências de usuário faria a maior parte dos cadastros retornar
quase nada, contrariando o objetivo da feature. A divergência é deliberada e fica
restrita às 6 originais, que são justamente as que têm requisito de compatibilidade.

**Implementação e custo.** Para não comparar listas token a token em 67.585 músicas a
cada request, a carga pode montar um índice `cifra_busca[id_unico_musica]` com
`';' + ';'.join(acorde.lower() for acorde in cifra) + ';'`. A busca vira um
`in` de string com as bordas `;`, que é exatamente a ocorrência contígua de tokens.
Esse índice fica em um dicionário à parte, **não** em `Musica.__dict__`, para não
vazar em `/musicas` e `/musica/<id>/` (`main.py:154-168`). O resultado por sequência
customizada é calculado uma vez (no POST ou na primeira busca após um restart) e
guardado em memória; como não há edição/exclusão no escopo, não há invalidação. O
caminho das 6 originais continua sem índice e sem ordenação própria, como hoje
(`main.py:203-223`). O caminho novo ordena por popularidade decrescente e
`id_unico_musica` para páginas determinísticas; o caminho antigo não é alterado.

### Banco de dados

SQLite via módulo `sqlite3` da biblioteca padrão do Python 3.9, em um único arquivo
`instance/sequences.db` (configurável por `SEQUENCES_DB`). O caminho fica fora de
`data/` de propósito: a imagem copia o repositório para `/app` (`Dockerfile:8`) e o
CSV é lido de `data/top/dataset_final.csv` (`main.py:49`); um volume montado em
`/app/data` esconderia o CSV. O volume deve ser montado em `/app/instance`, por
exemplo `docker run -p 8080:8080 -v deciframe-instance:/app/instance ciframe`.
`instance/` entra em `.gitignore` e `.dockerignore` para não ir para a imagem nem
para o repositório.

Por quê SQLite: não adiciona dependência (diferente de TinyDB/DuckDB), tem
transações/ACID, lê e escreve em um arquivo único, cabe no container único e
local-only da ADR 0001 e não exige serviço externo. O catálogo é pequeno e as
escritas são raras; o volume de leitura continua sendo o CSV em memória. A conexão
deve ser curta (uma por request ou thread-local), com transações curtas e
`PRAGMA user_version` para evolução manual do schema; não é necessário Alembic nesta
escala.

O que **não** vai para o banco: `musicas`, `generos`, `musica.acordes`, tags ou
qualquer dado do CSV. A carga de `main.py:49-98` e o modelo `musica.py` permanecem
como estão. As respostas continuam sendo `json.dumps(...)`, inclusive os erros, com
o mesmo `Content-Type: text/html; charset=utf-8` e o CORS de `main.py:274-277`;
apenas o corpo JSON do `POST` é lido com `request.get_json`.

**Persistência no Docker.** O banco só sobrevive a remoção/recriação do container
se `/app/instance` estiver montado em um volume nomeado. Para não depender de o
operador lembrar do `-v`, o caminho padrão de execução passa a ser um
`docker-compose.yml` com um único serviço, `restart: unless-stopped` e o volume
nomeado `deciframe-instance:/app/instance`. O `Dockerfile` também declara
`VOLUME ["/app/instance"]` como proteção adicional: um `docker run` sem `-v` ganha
um volume anônimo e sobrevive a `stop/start`, mas remoção/recriação do container
continua exigindo o volume nomeado. `docker compose down` preserva o volume;
`docker compose down -v` é a operação destrutiva que apaga o catálogo. Containers
antigos criados sem volume ainda podem ser recuperados com `docker cp` antes de
serem removidos. Essa correção não adiciona serviço externo nem muda a arquitetura
local-only de um único container.

### Esquema de dados (alto nível)

Uma tabela `sequences`:

| Coluna | Tipo/conteúdo |
|---|---|
| `id` | `TEXT PRIMARY KEY`; as 6 originais usam as chaves atuais (`BmGDA`, `CGAmF`, `EmG`, `CA7DmG7`, `GmF`, `CC7FFm`); as novas usam UUID4 |
| `nome` | `TEXT NOT NULL`, 1–80 caracteres; nomes podem se repetir |
| `acordes` | `TEXT NOT NULL`, array JSON na ordem cadastrada |
| `acordes_norm` | `TEXT NOT NULL UNIQUE`, minúsculas unidas por `;`, para detectar duplicatas |
| `origem` | `TEXT NOT NULL`, `builtin` ou `custom` |
| `matching_mode` | `TEXT NOT NULL`, `legacy_tag` ou `ordered` |
| `legacy_tag` | `INTEGER NULL`; 0–5 apenas nas 6 originais |
| `created_at` | `TEXT NOT NULL`, UTC em ISO-8601 |

As 6 linhas são inseridas de forma idempotente no startup (`INSERT OR IGNORE`), com
os nomes de `data/mapeamento_sequencias_famosas.txt:1-6`; se o arquivo não estiver
disponível, usa-se um nome genérico. Não há tabela de usuários, de músicas ou de
gêneros. Não há migration destrutiva: o banco nasce vazio e é semeado.

### API

- `GET /sequencias` — devolve o catálogo inteiro, com as 6 originais e as novas,
  ordenado por `origem` (builtin primeiro) e depois por `nome`. Cada item tem `id`,
  `nome`, `acordes` e `origem`; o `matching_mode` fica interno. Resposta
  `json.dumps(lista)`.
- `POST /sequencias` — corpo JSON `{"nome": "...", "acordes": ["C", "G", "Am", "F"]}`.
  Valida nome, quantidade/tamanho dos acordes, vocabulário de `/acordes` e
  duplicata; devolve 201 com o objeto criado ou 400/409 com
  `json.dumps({"erro": "..."})`. É anônimo, sem login, como pede o enunciado.
- `GET /similares?sequencia_id=<id>` — novo parâmetro. O servidor consulta a linha;
  se `matching_mode = legacy_tag`, usa o caminho atual por `seqs_famosas`; se for
  `ordered`, usa o índice/cache de ocorrência contígua. Aplica `generos` e `pagina`
  como hoje (`main.py:179-182`, `main.py:226-228`) e devolve os mesmos campos do
  caminho de sequência (`main.py:210-220`), via `json.dumps`.
- Compatibilidade: `GET /similares?sequencia=BmGDA` continua funcionando sem
  alteração pelo dicionário `main.py:40-45`; não é removido. Precedência dos
  parâmetros: `acordes` > `id_unico_musica` > `sequencia_id` > `sequencia`. Id
  desconhecido devolve `[]` (mesmo comportamento de sequência desconhecida hoje,
  `main.py:192-197`).
- O restante (`/search`, `/musicas`, `/generos`, `/acordes`, `/musica/<id>/`,
  `/<path:path>`) não muda. Nenhuma resposta usa `jsonify`.

### Frontend

- `SequenciaController` passa a carregar `GET /sequencias` no início e a preencher
  `vm.sequenciasFamosas`; o array hardcoded `sequencia1`..`sequencia4`
  (`sequencia.js:2-37`) é removido. As 6 originais e as novas aparecem na mesma
  lista, corrigindo a divergência 4 × 6 apontada na pesquisa. Como a API devolve
  `acordes` como lista de strings, o controller converte cada item para o formato
  que o template já usa (`{acorde: 'Bm', cor: '#2E1C74'}`) ou o template/`df-hex`
  passa a receber strings; `temAcorde` e `createChordsString` precisam acompanhar
  essa representação.
- A página ganha um painel de cadastro: nome, campo de acordes com typeahead em
  `GET /acordes` (ou lista carregada uma vez), chips de acordes com remoção e botão
  "Cadastrar". O POST usa `$http.post` e, em sucesso, atualiza a lista e seleciona a
  sequência nova; 400/409 exibem a mensagem do backend. O layout existente de
  `df-hex` e dos cartões de música é mantido (`sequencia.html:19-58`).
- A busca passa a chamar `similares?sequencia_id=<id>` para qualquer sequência,
  mantendo `&generos=<um gênero>` e sem paginação na UI (o limite de 100 por página
  continua, `main.py:35`). A lista de gêneros hardcoded de `app.js:6-58` fica como
  está; a divergência `R&B;` já existente fica fora do escopo.
- Não há build step novo: continua AngularJS 1.4.9 + jQuery carregados no
  `index.html:125-147`, e o controller já está incluído em `index.html:145`.

### Riscos e validação

Riscos principais da escolha: (a) a existência de duas semânticas de matching pode
surpreender quem comparar uma sequência nova com uma das 6; (b) o volume precisa ser
montado em `/app/instance`, nunca em `/app/data`; (c) o catálogo é anônimo, então não
há como impedir spam além dos limites de tamanho e da unicidade; (d) o cache de
matches cresce com o número de sequências e é reconstruído após restart; (e) SQLite
exige transações curtas e uma conexão por request/thread; (f) a validação contra
`/acordes` precisa ser case-insensitive para não rejeitar variantes de grafia.

Estratégia de testes, partindo de uma suíte que hoje não existe:

- **Regressão das 6 (obrigatória):** antes da mudança, capturar `?sequencia=` para
  todas as páginas das 6 em um fixture (contagens atuais 199, 296, 4, 5, 7 e 3) e,
  depois, comparar o conjunto de ids e a contagem total; a ordem entre gêneros não é
  estável porque `generos` deriva de um `set`. Incluir o caminho novo
  `?sequencia_id=` para as mesmas 6.
- **Matching:** testes unitários com sequência de 1, 2 e 4 acordes; início/fim da
  cifra; repetições; ocorrência sobreposta; acorde que é prefixo de outro (`C` não
  pode casar dentro de `C7`); sequência não contígua (deve falhar); diferença de
  caixa; cifra vazia; sequência vazia/longa.
- **API:** `GET /sequencias`, `POST` válido (201 + persistido), duplicata (409),
  acorde fora de `/acordes` (400), corpo inválido (400), `sequencia_id` desconhecido
  (`[]`), filtro de gênero, paginação, precedência de parâmetros, e a garantia de que
  a resposta é uma string JSON com `Content-Type: text/html` e CORS `*`.
- **Persistência:** banco temporário por teste; restart do processo; seed
  idempotente; teste real com `docker run -v deciframe-instance:/app/instance`,
  criar, `docker restart`, buscar, remover o container e recriar com o mesmo volume.
- **Concorrência:** POSTs paralelos (ex.: 10 sequências distintas) sem erro de lock
  nem duplicata; teste com mais de um worker para documentar o limite.
- **Performance:** medir a primeira busca de uma sequência nova (cache frio) e a
  busca seguinte (cache quente); definir um limite aceitável (ex.: 2 s no frio) e
  medir memória do índice.
- **Frontend:** roteiro manual/e2e sem framework: abrir `#/porsequencia`, conferir as
  6, cadastrar uma nova, buscá-la, recarregar a página, reiniciar o backend e repetir;
  verificar estados de erro 400/409.

## Alternativas consideradas e descartadas

**Proposta 2 — TinyDB com semântica legada unificada.** O catálogo iria para um
arquivo TinyDB (`instance/sequences.json`), com a dependência `tinydb` adicionada a
`requirements.txt`, e **todas** as sequências usariam a regra exata da tag,
recalculada em runtime: minúsculas, sequência completa como substring contígua da
cifra e nenhum acorde da música fora da sequência. A pesquisa verificou que essa
recomputação reproduz a coluna `SEQ_FAMOSA` com 0 divergências nas 67.585 linhas
(`01-research.md`, seção 2.2); logo, as 6 originais continuariam idênticas. O
resultado por sequência seria pré-computado no startup e mantido em memória.

- **Vantagens:** uma única semântica para todo o catálogo, sem depender da coluna
  `SEQ_FAMOSA` para o matching; schema menos rígido (documentos JSON); arquivo
  legível e fácil de inspecionar; menor número de conceitos no código de busca.
- **Backend/frontend:** as rotas, o schema de resposta e a tela seriam os mesmos da
  Proposta 1; mudaria o módulo de persistência (TinyDB em vez de `sqlite3`) e o
  matching seria único, sem `matching_mode`. O frontend continuaria consumindo
  `GET /sequencias` e `?sequencia_id=`.
- **Desvantagens:** adiciona uma dependência de runtime; o TinyDB reescreve o
  arquivo inteiro a cada escrita e não tem transações/ACID; concorrência entre
  workers é frágil (o `Dockerfile:12` usa o default de 1 worker, mas isso vira uma
  restrição implícita); o startup fica O(músicas × sequências) e cresce com o
  catálogo; e, principalmente, a regra legada é muito restritiva para sequências
  novas (4 resultados para Em–G contra 3.110 pela ocorrência contígua com limites de
  token), o que
  esvaziaria a experiência de cadastro.
- **Validação necessária:** comparar a recomputação em runtime com
  `seqs_famosas` para as 6 em todas as músicas (0 divergências), testar o TinyDB
  com escritas concorrentes e restart, medir o startup com N sequências e verificar
  que o arquivo não é corrompido em escrita interrompida.
- **Perguntas em aberto:** a semântica restritiva é aceitável para o usuário? Vale
  manter a coluna `SEQ_FAMOSA` como oráculo de regressão? O deploy continuará com 1
  worker?

**Outras alternativas descartadas**

- **JSON em arquivo sem banco** (ex.: `instance/sequences.json` lido/escrito à mão):
  seria o menor código, mas o enunciado pede um banco de dados, não um arquivo; e
  reescrita total, concorrência e atomicidade seriam piores que SQLite/TinyDB.
- **Aplicar a ocorrência contígua também às 6 originais**: violaria o critério de
  regressão (Bm–G–D–A passaria de 199 para 866 resultados; Em–G de 4 para 3.110).
- **DuckDB**: é um banco analítico/colunar, adiciona dependência e complexidade
  desnecessárias para um catálogo de poucas dezenas de sequências.
- **Manter as 6 hardcoded e guardar só as novas em banco**: não cumpre "a página
  reflete o catálogo real" nem dá uma fonte única para a lista; também duplicaria a
  validação de duplicatas.

**Comparação**

| Critério | Proposta 1 (escolhida) | Proposta 2 |
|---|---|---|
| Persistência | SQLite, `sqlite3` da stdlib, ACID, um arquivo | TinyDB, dependência nova, JSON reescrito inteiro |
| Matching | legado por tag nas 6; contíguo ordenado nas novas | regra legada unificada, recalculada |
| 6 originais | idênticas por construção (mesmo código) | idênticas se a recomputação reproduzir a tag (0 divergência medida) |
| Sequências novas | resultado intuitivo, mais músicas encontradas | regra restritiva, poucos resultados |
| Dependências | nenhuma nova | `tinydb` em `requirements.txt` |
| Concorrência/durabilidade | transações, WAL, arquivo único | reescrita total, sem transações |
| Custo | seed + cache sob demanda | pré-computa tudo no startup |
| Backend | novo módulo SQLite, schema/seed, `?sequencia_id=`, cache | novo módulo TinyDB, seed, `?sequencia_id=`, índice no startup |
| Frontend | catálogo via API + formulário; busca por id | o mesmo catálogo/formulário; busca por id |
| Risco principal | duas semânticas; volume; spam anônimo | UX restritiva; concorrência; dependência |
| Adequação ao enunciado | alta | média |

**Decisão:** Proposta 1. SQLite é um banco de verdade sem dependência nova, cabe no
container único e resolve durabilidade/concorrência melhor que TinyDB. Manter o
caminho de tag nas 6 elimina o risco de regressão, e a ocorrência contígua nas novas
é a regra que corresponde ao que o usuário espera de "essa sequência aparece nessa
música". O custo aceito é a existência de dois modos de matching, documentada na ADR
e no teste de regressão.

## Escopo explícito

**Dentro do escopo:**

- criar o banco SQLite em `instance/sequences.db`, com criação idempotente da tabela
  e seed das 6 originais;
- manter o caminho `?sequencia=` e a tag `SEQ_FAMOSA` para as 6, sem alterar
  resultados nem ordenação;
- implementar o matching contíguo ordenado e o cache em memória para as novas;
- adicionar `GET /sequencias`, `POST /sequencias` e `?sequencia_id=` em
  `GET /similares`, todas com `json.dumps`;
- trocar o catálogo hardcoded do frontend por `GET /sequencias`, adicionar o
  formulário de cadastro e usar `sequencia_id` na busca;
- adicionar `instance/` a `.gitignore`/`.dockerignore` e documentar o volume em
  `README.md`/ADR;
- criar o teste de regressão das 6 e testes de API/matching/persistência.

**Fora do escopo (e por quê):**

- editar/excluir sequências, moderação, login ou rate limiting: o enunciado pede
  catálogo aberto e anônimo; controles de abuso são uma decisão separada;
- migrar músicas, gêneros ou a coluna `SEQ_FAMOSA` para o banco: o enunciado fixa o
  CSV em memória e só o catálogo de sequências é persistido;
- trocar `json.dumps` por `jsonify` ou mudar o `Content-Type`: é uma restrição
  explícita do projeto (`AGENTS.md:43-46`);
- paginação/contagem total na UI, normalização enarmônica (`C#`/`Db`), busca por
  subsequência não contígua e edição das 6 originais: decisões de produto que podem
  vir depois, sem bloquear a feature;
- trocar a lista hardcoded de gêneros por `GET /generos` e resolver `R&B;`: é uma
  divergência pré-existente, fora do objetivo desta feature;
- múltiplos workers/HA, deploy em nuvem e migração de schema com Alembic: a ADR 0001
  fixa o container único local-only; se isso mudar, a decisão de SQLite e do cache
  por processo precisa ser revisitada.
