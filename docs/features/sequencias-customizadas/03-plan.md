# Plano — Sequências de Acordes Customizadas

## Contexto atual

- O backend é um único `main.py` Flask que carrega `data/top/dataset_final.csv` uma vez, em memória (`main.py:49-98`); não há banco, migration nem testes automatizados.
- As 6 sequências originais são um dicionário fixo em `main.py:40-45`; a busca só consulta a tag pré-computada `Musica.seqs_famosas` (`main.py:203-223`), sem calcular nada a partir da cifra.
- O frontend `#/porsequencia` tem 4 sequências hardcoded em `static/assets/js/controllers/sequencia.js:2-37`; `EmG` e `CA7DmG7` existem no backend mas não aparecem na tela.
- Não existe endpoint de catálogo nem de escrita de sequências; a página não reflete o backend e não permite cadastro (`static/templates/sequencia.html:1-63`).
- O CSV continua sendo a fonte de músicas/gêneros; só o catálogo de sequências será persistido. O deploy é o container único local da ADR 0001, e todas as respostas usam `json.dumps(...)`.

## Diagnóstico da persistência (2026-11-02)

- **Sintoma:** sequências customizadas desapareceram depois de reiniciar o
  computador e executar novamente o container.
- **Evidência dos containers:** `docker inspect` mostrou `Mounts=[]` e
  `HostConfig.Binds=null` nos dois containers `ciframe` existentes
  (`lucid_bell`, em execução, e `clever_almeida`, parado). O `docker diff`
  mostrou `A /app/instance/sequences.db`: o banco foi criado apenas na camada
  gravável do container, não em um volume.
- **Evidência do histórico:** o comando usado foi
  `docker run -p 8080:8080 ciframe`, sem `-v`; o volume nomeado
  `deciframe-instance` documentado no README não existia (`docker volume
  inspect deciframe-instance` retornou "no such volume").
- **Evidência da aplicação:** `init_db` usa `CREATE TABLE IF NOT EXISTS` e o
  seed usa `INSERT OR IGNORE`; não há `DROP`, `DELETE` nem recriação do banco.
  Parar e iniciar o mesmo container preserva a camada gravável; remover e
  executar `docker run` de novo cria uma camada nova e vazia.
- **Dados recuperáveis:** o banco do container parado `clever_almeida` contém
  duas sequências customizadas (`BmGDF` e `Alexandre Sequencia`); o banco do
  container em execução `lucid_bell`, verificado ao final, contém duas
  (`Sequencia de alexandre` e `Sequencia teste`) em 8 registros totais — ele
  continuou em uso durante a sessão. Backups consistentes foram salvos em
  `instance/recovery/` (ignorado pelo Git); nenhum container, volume ou banco
  foi removido durante o diagnóstico.
- **Causa raiz:** a execução não montou `/app/instance` em um volume nomeado.
  A aplicação está correta no nível do SQLite, mas o comando de execução tornava
  o banco efêmero. A documentação já citava o volume, mas não havia um caminho
  de execução padrão que o aplicasse nem uma verificação que detectasse a
  ausência dele.

## Premissas de escopo, restrições e tempo

- **Escopo:** catálogo SQLite, seed das 6, matching novo, API de catálogo/cadastro, busca por `sequencia_id`, frontend AngularJS, volume Docker, migration inicial e testes. Edição/exclusão, login, moderação, rate limiting e migração do CSV ficam fora.
- **Restrições fixas:** um único `Dockerfile`/container; músicas e gêneros continuam no CSV em memória; as 6 originais não podem mudar de resultado; respostas continuam `json.dumps` com `Content-Type: text/html`; sem dependência nova de runtime.
- **Timeline assumida:** 1 desenvolvedor, 6–8 h/dia, sem data limite externa; estimativa total de **6–7 dias úteis**. As estimativas são relativas e devem ser ajustadas se houver prazo de entrega.
- **Dependência crítica:** a Fase 0 (baseline) tem de ser concluída antes de qualquer alteração de código, porque o fixture de regressão precisa capturar o comportamento atual.

## Requisitos

### Funcionais

- Qualquer visitante pode cadastrar uma sequência (lista ordenada de acordes), sem login.
- `GET /sequencias` devolve o catálogo real, incluindo as 6 originais e as novas.
- A busca por qualquer sequência usa `GET /similares?sequencia_id=<id>` e devolve o mesmo formato de item do caminho atual.
- As 6 originais mantêm resultados e contagens atuais; a ordem relativa entre gêneros continua a do caminho legado (não determinística entre processos) e `GET /similares?sequencia=BmGDA` continua funcionando.
- `#/porsequencia` lista o catálogo do backend, permite cadastrar e pesquisar; as 6 ficam visíveis.
- O catálogo sobrevive a `docker restart` e à recriação do container com o volume.
- Músicas/gêneros continuam vindo do CSV; nenhum dado de música vai para o banco.

### Não funcionais

- Startup do app (CSV + banco + índice) abaixo de 3 s no ambiente local; primeira busca de sequência customizada abaixo de 2 s; buscas seguintes com cache abaixo de 300 ms.
- Índice de cifras com acréscimo de memória abaixo de 50 MB.
- SQLite com transações curtas, conexão por request/thread e `timeout` para concorrência; seed e criação idempotentes.
- Nenhuma dependência nova em `requirements.txt`; testes com `unittest` e o test client do Flask.
- Backend e frontend sem build step novo; AngularJS 1.4.9 e jQuery continuam via CDN.

## Decisões de design

### 1. Persistência: SQLite da stdlib

- Usar `sqlite3` em `instance/sequences.db`, configurável por `SEQUENCES_DB`, porque não adiciona dependência, tem ACID, cabe no container único e não exige serviço externo.
- O arquivo fica fora de `data/`: o CSV é copiado para `/app/data` (`Dockerfile:8`) e lido de `data/top/dataset_final.csv` (`main.py:49`); montar `/app/data` esconderia as músicas.
- O volume nomeado é `deciframe-instance:/app/instance`; `instance/` entra em `.gitignore` e `.dockerignore`. O caminho de execução padrão passa a ser `docker compose up -d --build`, com `restart: unless-stopped` e volume nomeado declarado no `docker-compose.yml`, para que o mesmo container/volume volte após reinício do host.
- O `Dockerfile` declara `VOLUME ["/app/instance"]` como proteção adicional: mesmo um `docker run` sem `-v` ganha um volume anônimo e sobrevive a `stop/start`; para remoção/recriação do container, o volume nomeado documentado continua obrigatório.
- Schema inicial versionado com `PRAGMA user_version`; `CREATE TABLE IF NOT EXISTS`; sem Alembic. Se `user_version` for maior que a versão suportada, falhar com log claro em vez de sobrescrever.

### 2. Matching: legado para as 6, contíguo ordenado para as novas

- As 6 continuam no caminho `str(legacy_tag) in musica.seqs_famosas` (`main.py:209`), preservando os resultados por construção.
- As novas usam `S = [s1..sk]` e `C = musica.cifra` (`musica.py:16`): a música casa se existe `i` com `C[i+j].lower() == s(j).lower()` para todo `j`. É contíguo, na ordem, sem normalização enarmônica; usa `cifra`, não `acordes` (`musica.py:17` perde ordem/repetição).
- Índice `cifra_busca[id_unico_musica] = ";" + ";".join(acorde.lower() for acorde in cifra) + ";"`; a busca é `";" + seq.lower() + ";" in cifra_busca[id]`, garantindo limites de token (`C` não casa dentro de `C7`).
- Cache em memória `id_sequencia -> [id_unico_musica]`, protegido por `threading.Lock`, calculado no POST ou na primeira busca após restart; sem invalidação porque não há edição/exclusão.
- Resultados customizados ordenados por `(-popularidade, id_unico_musica)` para páginas determinísticas; o caminho das 6 não é reordenado.

### 3. Catálogo e API

- `GET /sequencias` devolve os itens com `id`, `nome`, `acordes` (lista) e `origem` (`builtin`/`custom`), ordenados por origem e nome.
- `POST /sequencias` recebe `{"nome": "...", "acordes": ["C", "G", "Am", "F"]}`; valida, canonicaliza e devolve 201, 400 ou 409, sempre com `json.dumps`.
- O mapa case-insensitive de acordes deve partir de `sorted(main.acordes)` com `setdefault`, para que a forma canônica escolhida seja determinística entre processos.
- `GET /similares?sequencia_id=<id>` consulta o banco, escolhe o caminho legado ou o cache e reaplica `generos`/`pagina`; id desconhecido devolve `[]`.
- Precedência de parâmetros: `acordes` > `id_unico_musica` > `sequencia_id` > `sequencia`. O caminho `sequencia` e o dicionário `main.py:40-45` permanecem.
- Nomes das views novas devem ser únicos (ex.: `listar_sequencias`, `criar_sequencia`) para não repetir o shadowing de `get_similares` (`main.py:170` e `main.py:230`).

### 4. Frontend consome o catálogo real

- O controller remove o array hardcoded e carrega `GET /sequencias`; converte `acordes: ["Bm", ...]` para `[{acorde: "Bm", cor: "#2E1C74"}, ...]` para reutilizar `df-hex`, `temAcorde` e o layout atual.
- A busca passa a enviar `sequencia_id`; `createChordsString` deixa de ser necessária e pode ser removida.
- O cadastro usa `GET /acordes` uma vez (typeahead) e `POST /sequencias`; em sucesso, atualiza a lista e seleciona a nova sequência; 400/409 mostram a mensagem do backend.
- A lista de gêneros hardcoded (`app.js:6-58`) e a divergência `R&B;` ficam fora do escopo.

## Design técnico

### Componentes principais

- **`custom_sequences.py` (novo):** constantes/seed das 6, resolução do caminho do banco, conexão, schema, seed, CRUD, normalização/validação, índice de cifras e matching contíguo.
- **`main.py`:** inicializa o banco após a carga do CSV, monta o índice, registra as rotas, faz a ponte entre o catálogo e os caminhos de busca legado/custom. Mantém `musicas`, `generos` e `acordes` como estão.
- **`static/assets/js/controllers/sequencia.js`:** catálogo via API, formulário, validação de UI, POST e busca por id.
- **`static/templates/sequencia.html`:** lista real, painel de cadastro, chips, estados de erro/carregamento e cartões de resultado existentes.

### Modelo de dados (SQLite)

Tabela `sequences`:

| Coluna | Conteúdo |
|---|---|
| `id` | `TEXT PRIMARY KEY`; 6 originais usam as chaves atuais; novas usam UUID4 |
| `nome` | `TEXT NOT NULL`, 1–80 caracteres |
| `acordes` | `TEXT NOT NULL`, array JSON na ordem cadastrada |
| `acordes_norm` | `TEXT NOT NULL UNIQUE`, minúsculas unidas por `;`, para duplicatas |
| `origem` | `TEXT NOT NULL`, `builtin` ou `custom` |
| `matching_mode` | `TEXT NOT NULL`, `legacy_tag` ou `ordered` |
| `legacy_tag` | `INTEGER NULL`; 0–5 apenas nas 6 originais |
| `created_at` | `TEXT NOT NULL`, UTC em ISO-8601 |

Seed das 6 (nomes de `data/mapeamento_sequencias_famosas.txt:1-6`):

| id | tag | acordes |
|---|---:|---|
| `BmGDA` | 0 | Bm, G, D, A |
| `CGAmF` | 1 | C, G, Am, F |
| `EmG` | 2 | Em, G |
| `CA7DmG7` | 3 | C, A7, Dm, G7 |
| `GmF` | 4 | Gm, F |
| `CC7FFm` | 5 | C, C7, F, Fm |

### Pontos de integração e fluxos

- **Startup:** carregar CSV (`main.py:49-98`) → resolver `SEQUENCES_DB`/`instance/sequences.db` → `init_db` (schema/seed) → montar `cifra_busca` → app pronta.
- **Catálogo:** `GET /sequencias` → `SELECT` ordenado → decodificar `acordes` → `json.dumps`.
- **Cadastro:** `POST /sequencias` → validar/normalizar → canonicalizar acordes via `main.acordes` → `INSERT` → calcular matches em cache → 201.
- **Busca:** `GET /similares?sequencia_id=` → carregar linha → `legacy_tag`: caminho atual; `ordered`: cache/índice → filtrar gênero → `get_pagina` (`main.py:226-228`) → `json.dumps`.
- **Legado:** `GET /similares?sequencia=` continua no mesmo ramo e no mesmo helper (`main.py:190-197`, `main.py:203-223`).

### Contrato resumido da API

| Rota | Entrada | Saída/erros |
|---|---|---|
| `GET /sequencias` | — | 200, lista JSON string |
| `POST /sequencias` | `{"nome", "acordes"}` | 201 criado; 400 validação; 409 duplicata |
| `GET /similares?sequencia_id=` | id do catálogo, `generos`, `pagina` | 200 lista; id desconhecido → `[]` |
| `GET /similares?sequencia=` | chave legada | inalterado |

Todas as respostas usam `json.dumps(...)` e herdam o CORS de `main.py:274-277`.

### Migração e evolução

- Versão 1: criar `sequences`, definir `PRAGMA user_version = 1` e semear as 6 na mesma transação.
- Startup idempotente: `CREATE TABLE IF NOT EXISTS`; `INSERT OR IGNORE` para as 6; não sobrescrever customizações.
- Não há migração de músicas/gêneros nem da coluna `SEQ_FAMOSA`.
- Versões futuras: switch por `user_version` em `custom_sequences.py`; backup do arquivo antes de qualquer migração destrutiva.
- Rollback de código: a versão antiga ignora o banco; manter o volume para não perder o catálogo.

## Passos

Estimativas por fase (1 dev, 6–8 h/dia): Fase 0 = 0,5 dia; Fase 1 = 1 dia; Fase 2 = 1 dia; Fase 3 = 1 dia; Fase 4 = 1,5 dia; Fase 5 = 0,5 dia; Fase 6 = 1 dia. Total ≈ 6–7 dias úteis.

- [x] Fase 0 — baseline e fixture de regressão
- [x] Fase 1 — banco, schema, seed e migration inicial
- [x] Fase 2 — índice de cifras, matching e cache
- [x] Fase 3 — endpoints e integração com o caminho legado
- [x] Fase 4 — integração AngularJS
- [x] Fase 5 — Docker, volume, documentação e rollback
- [x] Fase 6 — regressão, testes e relatório
- [x] Fase 7 — correção da persistência Docker após perda de dados
- [x] Fase 8 — correção do alinhamento entre nome e acordes do catálogo

### Fase 0 — Baseline e fixture de regressão (0,5 dia)

- **Arquivos:** `tests/capture_baseline.py` (novo), `tests/fixtures/sequencias_baseline.json` (novo).
- **Alterações:** com o código atual, usar `main.app.test_client()` para capturar as 6 sequências via `?sequencia=` em todas as páginas, salvando ids e ordem; registrar as contagens 199, 296, 4, 5, 7 e 3.
- **Dependências:** nenhuma; executar antes de alterar `main.py` ou o frontend.
- **Conclusão:** fixture reproduzível, com 514 ids no total e hashes/contagens conferidos; o teste futuro compara conjunto de ids e contagem (as páginas ficam registradas para inspeção).

### Fase 1 — Banco, schema, seed e migration inicial (1 dia)

- **Arquivos:** `custom_sequences.py` (novo), `main.py`, `.gitignore`, `.dockerignore`.
- **Alterações:** implementar `resolve_db_path`, `connect`, `init_db`, `seed_builtins`, `list_sequences`, `get_sequence`, `create_sequence` e `find_by_acordes_norm`; criar `instance/` com `os.makedirs`; schema e `PRAGMA user_version = 1`; seed das 6 com ids, tags, modos e nomes; adicionar `instance/` aos ignores; inicializar o store no startup de `main.py`.
- **Dependências:** Fase 0.
- **Conclusão:** banco novo cria tabela e 6 linhas; segundo startup não duplica; `SELECT` confirma ids/tags/modos; app continua subindo sem rotas novas; nenhum acesso ao CSV além do já existente.

### Fase 2 — Índice de cifras, matching e cache (1 dia)

- **Arquivos:** `custom_sequences.py`, `main.py`.
- **Alterações:** `build_cifra_index(musicas)` com `;` e `lower()`; `match_ordered(seq, cifra_busca)`; cache `custom_matches` com lock; ordenação por popularidade/id; helpers de normalização e canonicalização; montar o índice depois de `musicas` (`main.py:88-89`), sem alterar `Musica.__dict__`.
- **Dependências:** Fase 1.
- **Conclusão:** índice cobre 67.585 músicas; `Em,G` (case-insensitive, com limites de token) encontra 3.110 músicas no teste de sanidade; `C` não casa dentro de `C7`; ocorrência não contígua falha; segunda busca usa cache; startup e memória dentro dos limites. A contagem de 3.704 da pesquisa usa busca por substring (`em;g` também casa prefixos como `g5`); a implementação adota limites de token e por isso o alvo correto é 3.110.

### Fase 3 — Endpoints e integração com o caminho legado (1 dia)

- **Arquivos:** `custom_sequences.py`, `main.py`.
- **Alterações:** adicionar `GET /sequencias`, `POST /sequencias` e o ramo `sequencia_id` em `GET /similares`; validação de nome (1–80), acordes (1–16), vocabulário de `/acordes`, `;` proibido, duplicata 409; respostas 201/400/409 com `json.dumps`; precedência de parâmetros; views com nomes únicos; manter `?sequencia=` e o helper legado intactos.
- **Dependências:** Fases 1–2.
- **Conclusão:** catálogo devolve as 6; POST válido persiste e aparece no GET; duplicata 409; acorde inválido/corpo malformado 400; `sequencia_id` de builtin reproduz o legado; id desconhecido `[]`; respostas seguem `text/html` e CORS `*`.

### Fase 4 — Integração AngularJS (1,5 dia)

- **Arquivos:** `static/assets/js/controllers/sequencia.js`, `static/templates/sequencia.html`.
- **Alterações:** remover `sequencia1`..`sequencia4`; carregar catálogo e `/acordes`; mapear acordes para `{acorde, cor}`; formulário com nome, typeahead, adicionar/remover chips e botão Cadastrar; estados de salvando/erro; POST e atualização da lista; busca por `sequencia_id`; manter `df-hex`, filtro de gênero e cartões.
- **Dependências:** Fase 3.
- **Conclusão:** as 6 aparecem; cadastro de uma sequência de teste (ex.: D–A–Bm–G) funciona; busca retorna resultados; reload mantém o catálogo; erros 400/409 aparecem na tela; o console não tem erros da aplicação (só o `og:image` externo do `index.html`); `grep` não encontra sequências hardcoded no controller.

### Fase 5 — Docker, volume, documentação e rollback (0,5 dia)

- **Arquivos:** `README.md`, `AGENTS.md`, `.dockerignore`, `.gitignore`; `Dockerfile` só se a verificação exigir (preferir não alterar).
- **Alterações:** documentar `docker run -p 8080:8080 -v deciframe-instance:/app/instance ciframe`; explicar que `docker restart` preserva o container, mas recriação exige volume; documentar backup com `sqlite3 .backup`/API (ou cópia de `sequences.db` + `-wal`/`-shm` com o app parado); confirmar que o app cria `/app/instance`; garantir que `instance/` não entra na imagem; registrar rollback (imagem anterior ignora o banco).
- **Dependências:** Fases 1–4.
- **Conclusão:** `docker build` funciona; app sobe com volume; criar sequência, `docker restart`, buscar; remover e recriar o container com o mesmo volume e confirmar persistência; sem volume, documentar a perda na recriação; `docker run` sem volume não quebra o CSV. **Ressalva:** a execução real que perdeu dados usou `docker run` sem `-v`; a correção e a verificação estão na Fase 7.

### Fase 6 — Regressão, testes e relatório (1 dia)

- **Arquivos:** `tests/test_sequencias_store.py`, `tests/test_matching.py`, `tests/test_sequencias_api.py`, `tests/test_regression_sequencias.py`, `tests/test_persistence.py`, `tests/helpers.py`, `docs/features/sequencias-customizadas/04-test-report.md`.
- **Alterações:** implementar testes unitários/integrados, rodar o fixture da Fase 0, testar volume/concorrência/performance e preencher o relatório de testes.
- **Dependências:** todas as fases anteriores.
- **Conclusão:** `python -m unittest discover -s tests -v` passa com 48 testes; as 6 batem em conjunto/contagem com o baseline (a ordem entre gêneros varia por processo, comportamento legado); cadastro/busca/persistência/erros/concorrência cobertos; `04-test-report.md` registra comandos, resultados e limitações.

### Fase 7 — Correção da persistência Docker (0,5 dia)

- **Arquivos:** `docker-compose.yml` (novo), `Dockerfile`, `README.md`, `AGENTS.md`, `docs/adr/0002-persist-custom-sequences.md`, `docs/features/sequencias-customizadas/02-proposal.md`, `docs/features/sequencias-customizadas/03-plan.md`, `docs/features/sequencias-customizadas/04-test-report.md`.
- **Alterações:**
  - adicionar `docker-compose.yml` com um único serviço, `restart: unless-stopped`, porta 8080 e volume nomeado `deciframe-instance:/app/instance`;
  - declarar `VOLUME ["/app/instance"]` no `Dockerfile` como proteção contra `docker run` sem `-v`;
  - documentar o caminho padrão via Compose, o equivalente com `docker run`, como verificar o mount, como parar sem apagar o volume e como recuperar bancos antigos de containers sem volume;
  - registrar explicitamente que `docker compose down -v` apaga o catálogo e que `docker compose down` o preserva;
  - atualizar a ADR/proposta para refletir a decisão de volume nomeado + Compose + `VOLUME`.
- **Dependências:** Fases 1–6 e diagnóstico acima.
- **Conclusão:** criar uma sequência, fazer `docker stop`/`docker start` no mesmo container, remover e recriar o container com o mesmo volume, e confirmar que a sequência continua no `GET /sequencias`; confirmar que o seed não duplica as 6 nem apaga as customizadas; executar novamente a suíte de 48 testes e registrar as evidências em `04-test-report.md`.

### Fase 8 — Correção do alinhamento do catálogo (0,25 dia)

- **Diagnóstico:** o template coloca o nome em um `<p>` fora do `.acordes-container`, e o container só contém `.acorde-wrapper` com `float: left`. Medição no Chrome headless (viewport 1200px): o `.acordes-container` tem `height: 0`; o nome do item 0 fica em `189.8–209.8`, seus hexágonos em `211.8–267.7`, e o nome do item 1 começa em `211.8`, sobrepondo os hexágonos do item 0. O padrão se repete nos 6 itens; por isso o último nome aparece visualmente associado à sequência anterior.
- **Arquivos:** `static/templates/sequencia.html`, `static/assets/css/app.css`, `docs/features/sequencias-customizadas/03-plan.md`, `docs/features/sequencias-customizadas/04-test-report.md`.
- **Alterações:**
  - envolver cada item do `ng-repeat` em um container próprio com nome + acordes;
  - usar Flexbox em coluna no item e em linha (com `flex-wrap`) na fileira de hexágonos, mantendo o `float` interno do hexágono contido pelo item Flexbox;
  - manter cores, tipografia, SVG e formato dos acordes;
  - permitir quebra de nomes longos e limitar a fileira à largura disponível (`max-width: 100%`).
- **Dependências:** Fase 4 (template/controller do catálogo).
- **Conclusão:** cada item contém nome e acordes; não há sobreposição entre itens com 1, 2, 4 ou mais acordes; nomes longos quebram dentro do painel; layout validado em viewport desktop e estreito; testes existentes continuam passando.

## Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `custom_sequences.py` | **novo**: store SQLite, schema/seed, validação, índice e matching |
| `main.py` | inicialização do banco/índice, rotas de catálogo/cadastro e ramo `sequencia_id`; caminho legado preservado |
| `static/assets/js/controllers/sequencia.js` | catálogo via API, cadastro e busca por id; remoção do hardcode |
| `static/templates/sequencia.html` | lista real, formulário, chips, erros e estados de carregamento; item do catálogo com nome + acordes no mesmo container |
| `static/assets/css/app.css` | layout Flexbox do item do catálogo; fileira de hexágonos com quebra e nomes longos |
| `.gitignore` | ignorar `instance/` |
| `.dockerignore` | não copiar `instance/` para a imagem |
| `README.md` | comando com volume, persistência, backup e rollback |
| `AGENTS.md` | atualizar o comando Docker e o gotcha de volume/banco |
| `docker-compose.yml` | **novo**: serviço único, volume nomeado e `restart: unless-stopped` |
| `Dockerfile` | declarar `VOLUME ["/app/instance"]` como proteção adicional |
| `docs/adr/0002-persist-custom-sequences.md` | registrar a decisão de persistência, volume, Compose e matching |
| `docs/features/sequencias-customizadas/02-proposal.md` | refletir o caminho padrão de execução persistente |
| `docs/features/sequencias-customizadas/03-plan.md` | diagnosticar a perda e registrar a correção |
| `tests/capture_baseline.py` | **novo**: captura do baseline das 6 |
| `tests/fixtures/sequencias_baseline.json` | **novo**: fixture de regressão |
| `tests/helpers.py` | **novo**: bootstrap de app/banco temporário |
| `tests/test_sequencias_store.py` | **novo**: schema, seed, CRUD e duplicatas |
| `tests/test_matching.py` | **novo**: matching contíguo, limites e normalização |
| `tests/test_sequencias_api.py` | **novo**: catálogo, POST, erros, CORS e json.dumps |
| `tests/test_regression_sequencias.py` | **novo**: comparação das 6 com o baseline |
| `tests/test_persistence.py` | **novo**: restart, seed idempotente e volume |
| `docs/features/sequencias-customizadas/04-test-report.md` | preencher na fase de testes |

**Sem alteração:** `musica.py`, `requirements.txt`, `static/index.html`, `static/assets/js/app.js`, `static/assets/js/routes.js`, `data/top/dataset_final.csv`, `data/mapeamento_sequencias_famosas.txt` e `docs/adr/0001-*`.

## Estratégia de testes

### Unitários

- Normalização/canonicalização de acordes, rejeição de `;`, nome vazio/longo, lista vazia, mais de 16 acordes.
- Matching: sequência de 1, 2 e 4 acordes; início/fim; repetições; sobreposição; `C` não casar em `C7`; não contíguo; caixa; cifra vazia.
- Store: schema, `user_version`, seed idempotente, `INSERT OR IGNORE`, duplicata por `acordes_norm`, leitura/decodificação de `acordes`.
- Validação de JSON e serialização dos erros.

### Integração

- `GET /sequencias` com as 6 e uma custom; ordem builtin/custom.
- `POST` válido (201, persistido), duplicata (409), acorde desconhecido (400), corpo ausente/inválido (400), nome inválido (400).
- `?sequencia_id=` para builtin e custom; id desconhecido `[]`; precedência de parâmetros; filtro de gênero e paginação.
- `?sequencia=` legado continua idêntico; resposta é string JSON, `Content-Type: text/html`, CORS `*`.
- Persistência: banco temporário, restart do processo e seed idempotente; teste Docker com volume.

### Regressão obrigatória

- Comparar as 6 com `tests/fixtures/sequencias_baseline.json` por conjunto de ids e contagem total; repetir via `?sequencia=` e `?sequencia_id=`. A ordem entre gêneros não é estável porque `generos` deriva de um `set`; a comparação exata de página a página seria falsa mesmo sem mudanças.
- Contagens esperadas: 199, 296, 4, 5, 7 e 3; páginas de 100 (`main.py:35`, `main.py:226-228`).

### Concorrência, performance e frontend

- POSTs paralelos (10 sequências distintas) sem lock error nem duplicata; documentar o limite de 1 worker.
- Medir cold/warm da busca customizada, tempo de startup e memória do índice; registrar no relatório.
- Roteiro manual/e2e: abrir `#/porsequencia`, ver as 6, cadastrar, buscar, filtrar por gênero, recarregar, reiniciar backend e repetir; verificar 400/409.

## Observabilidade

- `app.logger` no startup: caminho do banco, quantidade de builtins inseridos/mantidos, tempo de carga do CSV e do índice.
- Log em nível `INFO` para POST aceito e em `WARNING` para validação recusada; não logar corpo bruto.
- Log da duração da primeira busca customizada (cache frio) e de erros `sqlite3`.
- Sem métricas, dashboards ou alertas nesta fase: não há infraestrutura de observabilidade no projeto. Logs do gunicorn + `app.logger` bastam para o escopo local.

## Segurança

- Catálogo anônimo por requisito: sem login, sem autorização e sem rate limiting; risco de spam é aceito e documentado como limitação.
- SQL sempre parametrizado; nunca interpolar `nome`/`acordes` na query.
- Validar tamanho/tipo de nome e acordes; rejeitar `;` e caracteres de controle; limitar o corpo do POST para evitar payloads abusivos.
- AngularJS interpola texto com escape; não usar `ng-bind-html` para nomes de sequência.
- CORS `*` permanece; qualquer origem pode cadastrar. Isso é aceitável no container local-only, mas deve ser revisto antes de qualquer deploy público.
- Backup/volume: o arquivo do banco é público apenas para quem tem acesso ao host/volume; não há dados pessoais no catálogo.

## Rollout e migração

1. **Development:** implementar fases 1–4 em branch, com banco temporário e testes locais.
2. **Testes:** rodar baseline/regressão, API, matching, persistência, concorrência e performance.
3. **Docker local:** `docker compose up -d --build` (volume nomeado e `restart: unless-stopped`); equivalente com `docker run -v deciframe-instance:/app/instance`; criar, reiniciar e recriar sem perder o volume.
4. **Migração:** no primeiro start, criar schema v1 e semear; fazer backup com `sqlite3 .backup`/API do SQLite (ou copiar `sequences.db` + `-wal`/`-shm` com o app parado) antes de futuras migrações; não migrar CSV.
5. **Rollback:** voltar a imagem/código anterior; o código antigo ignora o banco; preservar o volume; se necessário, restaurar o backup do SQLite.
6. **Monitoring:** smoke test local (`/generos`, `#/porsequencia`, cadastro e busca); sem staging/produção nesta fase.

## Dependências

- **Runtime:** Python 3.9, `sqlite3` (stdlib), Flask 3.1.3 e gunicorn 23.0.0 já existentes; nenhuma linha nova em `requirements.txt`.
- **Desenvolvimento:** `unittest` (stdlib), test client do Flask, Docker; `sqlite3` CLI opcional para inspeção.
- **Frontend:** AngularJS 1.4.9, jQuery 1.11.3 e ui-bootstrap já carregados; sem npm/build.
- **Dados:** `data/mapeamento_sequencias_famosas.txt` para nomes do seed; `data/top/dataset_final.csv` para músicas/gêneros.

## Considerações futuras

- Edição/exclusão de sequências e invalidação do cache; moderação/rate limiting para o catálogo anônimo.
- Unificar a semântica das 6 com as novas (exigiria mudar resultados e uma decisão de produto).
- Normalização enarmônica (`C#`/`Db`), paginação/contagem na UI e busca por subsequência não contígua.
- Migrar a lista hardcoded de gêneros para `GET /generos` e corrigir `R&B;`.
- Múltiplos workers/HA, backup automático, deploy em nuvem e migração para um banco gerenciado.
- Testes de carga com catálogo grande e limites de abuso.

## Riscos e mitigação

| Risco | Como detectar | Mitigação |
|---|---|---|
| Regressão nas 6 | diff contra o fixture da Fase 0 | manter o caminho legado intacto; testar `?sequencia=` e `?sequencia_id=` |
| Volume esconde o CSV | app não encontra `data/top/dataset_final.csv` ou `/generos` falha | montar somente `/app/instance`; documentar; testar no Docker |
| Perda do catálogo ao recriar o container | sequência some após `docker rm`/novo `run` | volume nomeado; Compose com volume; `VOLUME` no Dockerfile; teste de recriação; README |
| Execução sem volume | `docker inspect` com `Mounts=[]`; banco em `docker diff` | caminho padrão `docker compose up`; verificação de mount documentada; aviso explícito sobre `docker run` sem `-v` |
| Remoção acidental do volume | `docker compose down -v`/`docker volume rm` | documentar que `down` preserva e `down -v` apaga; backup antes |
| SQLite lock/concorrência | `database is locked` nos logs/testes | transações curtas, `timeout`, conexão por request; 1 worker documentado |
| Cache de matching desatualizado | busca não reflete sequência criada | cache preenchido no POST/primeira busca; sem edição/exclusão; invalidar no futuro |
| POST inválido causa 500 | testes de API/corpo malformado | `get_json(silent=True)`, validação e respostas 400/409 |
| Duplicata por corrida | dois POSTs simultâneos | `UNIQUE(acordes_norm)` + tratamento de `IntegrityError` → 409 |
| Frontend quebra com `acordes` string | tela sem hex/cards ou erro no console | mapear para `{acorde, cor}`; teste manual |
| Primeira busca lenta | medição cold > 2 s | índice `;`-join, cache; otimizar/limitar se necessário |
| Banco local entra na imagem | imagem nova já contém sequências | `instance/` em `.dockerignore`; testar build limpo |
| Rollback perde dados novos | sequências criadas somem na versão antiga | documentar; backup do SQLite antes do rollback |

## Definição de pronto

- [x] `docker build -t ciframe .` conclui sem erro; app sobe com `-v deciframe-instance:/app/instance`.
- [x] O caminho padrão `docker compose up -d --build` usa volume nomeado e `restart: unless-stopped`; `docker inspect` mostra o mount em `/app/instance`.
- [x] Uma sequência customizada sobrevive a `docker stop/start` e à remoção/recriação do container com o mesmo volume nomeado. O reinício físico do host não foi executado no ambiente de teste; o volume está em `/var/lib/docker/volumes` (fora da camada do container) e `restart: unless-stopped` foi verificado — ver a ressalva no `04-test-report.md`.
- [x] O seed continua idempotente: reiniciar o app não duplica as 6 e não apaga as customizadas.
- [x] A execução sem volume está documentada como efêmera; containers antigos sem volume podem ser recuperados com `docker cp` antes de serem removidos.
- [x] `GET /generos` continua funcionando; CSV de músicas/gêneros não foi migrado nem alterado.
- [x] `GET /sequencias` devolve as 6 originais e as customizadas, com `id`, `nome`, `acordes` e `origem`.
- [x] `POST /sequencias` cadastra uma sequência anônima, persiste e ela aparece no catálogo.
- [x] `GET /similares?sequencia_id=<id>` busca por uma sequência cadastrada e devolve os mesmos campos do caminho atual.
- [x] As 6 originais continuam com os mesmos resultados e contagens; a ordem entre gêneros não é estável (comportamento legado) e o fixture de regressão passa.
- [x] `?sequencia=` legado continua funcionando; nenhuma resposta usa `jsonify`.
- [x] `#/porsequencia` mostra as 6, permite cadastrar e buscar; não há sequências hardcoded no controller.
- [x] O catálogo mantém nome e acordes no mesmo container visual, sem sobreposição para 1, 2, 4 ou mais acordes, incluindo nomes longos e viewport estreito.
- [x] O catálogo sobrevive a `docker restart` e à recriação do container com o volume; sem volume, a limitação está documentada.
- [x] Testes de matching, store, API, persistência, concorrência e regressão passam; `04-test-report.md` está preenchido.
- [x] `README.md`/`AGENTS.md` documentam volume, backup e rollback; `instance/` está nos ignores.

## Referências

- `docs/features/sequencias-customizadas/00-enunciado.md`
- `docs/features/sequencias-customizadas/01-research.md`
- `docs/features/sequencias-customizadas/02-proposal.md`
- `docs/adr/0001-local-only-docker-deploy.md`
- `docs/adr/0002-persist-custom-sequences.md`
- `AGENTS.md` e `README.md`
- Template de design doc do RePPIT: `~/reppit-framework/templates/design_doc_template.md`
