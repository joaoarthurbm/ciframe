# Plano — Sequências de Acordes Customizadas

## Passos

### 1) Criar e inicializar o banco SQLite com persistência compatível com Docker
- [x] **1.1. Definir caminho do banco.** Escolher caminho gravável (ex. `data/sequencias.db`). Garantir diretório existe. Compatível com container único; documentar que para persistência entre reinícios pode ser necessário volume, sem adicionar serviços externos.
- [x] **1.2. Criar schema.** Criar tabela `sequences` com `id` (PK autoincrement), `chords` (string canônica), `chords_key` (string normalizada/concatenada para lookup), `created_at` (timestamp). Garantir unicidade em `chords_key`/representação canônica.
- [x] **1.3. Inicialização no startup.** Adicionar inicialização do SQLite em `main.py` (import e criação/conexão + criação de tabela se não existir), sem migrar músicas/gêneros (continuam em CSV em memória).
- [x] **1.4. Verificação.** Após inicialização, arquivo `data/sequencias.db` criado; tabela `sequences` existe. App sobe normalmente.

**Arquivos envolvidos:** `main.py`, `data/` (novo arquivo `.db`), possivelmente `Dockerfile` (apenas se necessário para garantir path - sem mudanças obrigatórias).
**Verificação:** rodar app localmente; inspecionar arquivo SQLite (`sqlite3 data/sequencias.db ".schema"`).

### 2) Cadastrar e listar sequências pela API, com validação
- [x] **2.1. Endpoint GET /sequencias.** Listar catálogo completo (incluir as 6 originais + cadastradas). Retornar via `json.dumps` (string), sem `jsonify`. Formato deve ser utilizável pelo frontend.
- [x] **2.2. Endpoint POST /sequencias.** Cadastrar nova sequência (lista ordenada de acordes). Aberto e anônimo. Validar entrada (não vazia, acordes válidos/formato esperado). Normalizar para forma canônica e `chords_key`. Tratar duplicados (não criar entrada redundante, retornar representação consistente).
- [x] **2.3. Verificação.** Cadastrar via POST retorna sucesso/representação; GET lista inclui nova sequência. Duplicado tratado sem erro quebrando uso.

**Arquivos envolvidos:** `main.py`
**Verificação:** `curl` para GET/POST; inspecionar respostas e banco.

### 3) Adaptar `/similares?sequencia=...` para sequências customizadas, preservando resultados das seis originais
- [x] **3.1. Preservar comportamento atual.** Manter lookup no dict hardcoded `sequencias` (`main.py:40-45`) para as 6 chaves originais (`BmGDA`, `CGAmF`, `EmG`, `CA7DmG7`, `GmF`, `CC7FFm`), usando fluxo via `get_similares_por_sequencia` com `seqs_famosas`. **Não alterar** esse caminho.
- [x] **3.2. Suportar sequências customizadas.** Se sequência não estiver no hardcoded, buscar no banco por `chords_key`/canônica. Se encontrada, obter lista ordenada de acordes da sequência cadastrada.
- [x] **3.3. Implementar matching em tempo real.** Para sequência customizada, filtrar por gênero via `apply_filtro`, buscar músicas onde a sequência ordenada aparece como **subsequência ordenada** em `musica.cifra` (preservar ordem; não usar `musica.acordes` por ser `set`). Aplicar paginação. Manter retorno via `json.dumps`.
- [x] **3.4. Teste de regressão.** Verificar as 6 sequências originais retornam os mesmos resultados que hoje (mesmo conjunto antes da paginação/filtros).
- [x] **3.5. Verificação.** Testar cada uma das 6 originais e ao menos uma sequência customizada recém-cadastrada.

**Arquivos envolvidos:** `main.py`, `musica.py` (apenas se necessário para acesso a `cifra` - já existe)
**Verificação:** comparar respostas para as 6 chaves originais antes/depois (via curl); testar sequência customizada.

### 4) Tornar `#/porsequencia` dinâmico e permitir cadastrar sequências
- [x] **4.1. Carregar catálogo do backend.** Remover/atualizar lista hardcoded em `static/assets/js/controllers/sequencia.js` (atualmente 4 sequências). Carregar via `GET /sequencias` na inicialização do controller.
- [x] **4.2. Exibir catálogo dinâmico.** Adaptar `static/templates/sequencia.html` para renderizar catálogo vindo do backend (manter uso de `df-hex` para exibir acordes).
- [x] **4.3. Permitir cadastro.** Adicionar UI para cadastrar nova sequência (montar lista ordenada de acordes ou input). Chamar `POST /sequencias`. Após sucesso, recarregar catálogo e permitir busca.
- [x] **4.4. Garantir busca funciona para antigas e novas.** Manter fluxo de busca via `/similares?sequencia=...` existente.
- [x] **4.5. Verificação.** Página carrega catálogo dinâmico (6+ cadastradas), cadastro funciona, busca por nova sequência funciona.

**Arquivos envolvidos:** `static/assets/js/controllers/sequencia.js`, `static/templates/sequencia.html`
**Verificação:** testar no navegador.

### 5) Criar testes automatizados, incluindo testes de regressão das seis sequências originais
- [x] **5.1. Criar suite de testes.** Adicionar testes (pytest ou unittest) cobrindo: inicialização do banco, GET/POST /sequencias, validação, duplicados, `/similares?sequencia=` para sequências customizadas, e regressão das 6 originais.
- [x] **5.2. Teste de regressão obrigatório.** Para cada uma das 6 sequências (`BmGDA`,`CGAmF`,`EmG`,`CA7DmG7`,`GmF`,`CC7FFm`), comparar conjunto de resultados (antes/padrão esperado pelo mecanismo atual) com resultados após mudanças.
- [x] **5.3. Verificação.** Todos os testes passam.

**Arquivos envolvidos:** novo arquivo de testes (ex. `tests/test_sequencias_customizadas.py` ou similar), possivelmente `requirements.txt` (apenas se adicionar dependências necessárias - preferir stdlib)
**Verificação:** `python -m unittest discover -s tests -v` executando com sucesso.

### 6) Executar a aplicação e verificar o fluxo completo no navegador
- [ ] **6.1. Build/run.** Usando Docker conforme `AGENTS.md` (`docker build -t ciframe . && docker run -p 8080:8080 -v "$(pwd)/data:/app/data" ciframe`) ou virtualenv. Verificar app sobe.
- [ ] **6.2. Verificação via curl.** Testar `/generos`, `/sequencias`, `/similares?sequencia=` para originais e customizadas.
- [ ] **6.3. Verificação no navegador.** Acessar `#/porsequencia`, verificar catálogo dinâmico, cadastrar nova sequência, buscar por ela e por originais.
- [ ] **6.4. Verificação.** Fluxo completo funcionando.

**Arquivos envolvidos:** nenhum (verificação)
**Verificação:** respostas corretas e UI funcional.

### 7) Registrar os resultados no relatório final de testes
- [x] **7.1. Preencher `04-test-report.md`.** Documentar cobertura, testes automatizados, teste de regressão das 6 originais (resultados), testes manuais no navegador, e eventuais issues.
- [x] **7.2. Verificação.** Relatório completo e objetivo.

**Arquivos envolvidos:** `docs/features/sequencias-customizadas/04-test-report.md`
**Verificação:** arquivo preenchido sem instruções em bloco de citação.

## Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `main.py` | Adicionar SQLite (init/schema), endpoints `GET/POST /sequencias`, estender `/similares?sequencia=...` para customizadas com matching por subsequência em `musica.cifra` (preservando caminho hardcoded para 6 originais) |
| `musica.py` | Sem alteração obrigatória (já possui `cifra` e `acordes`); apenas garantir uso de `cifra` para matching |
| `static/assets/js/controllers/sequencia.js` | Remover hardcode, carregar catálogo via `GET /sequencias`, adicionar lógica de cadastro, manter busca |
| `static/templates/sequencia.html` | Adaptar para catálogo dinâmico e UI de cadastro |
| `data/sequencias.db` (novo) | Banco SQLite persistido (gitignored; persiste via volume Docker) |
| `tests/test_sequencias_customizadas.py` (novo) | 17 testes automatizados incluindo regressão das 6 originais, usando banco temporário |
| `.gitignore` / `.dockerignore` | Ignoram o banco de runtime e artefatos WAL |
| `AGENTS.md` / `docs/adr/0002-...` | Documentam volume Docker e `SEQUENCIAS_DB_PATH` |

## Riscos e mitigação

| Risco | Como perceber | Mitigação |
|---|---|---|
| Quebrar resultados das 6 originais | Teste de regressão falha | Preservar caminho hardcoded em `/similares?sequencia=` exatamente como hoje; testar cada uma das 6 antes/depois |
| Usar `musica.acordes` (set) ao invés de `musica.cifra` | Matching incorreto | Usar `musica.cifra` para subsequência ordenada; documentar e testar |
| Banco não persiste no Docker | Arquivo perdido ao reiniciar container | Usar caminho em diretório montável/gravável (ex. `data/`), instruir volume `-v "$(pwd)/data:/app/data"` sem adicionar serviços externos |


## Revisão pós-implementação (Fase 4)

- Banco: `data/sequencias.db` (SQLite) inicializado em `main.py:init_db()`, criado em `data/`. Persistente em arquivo no filesystem do container; para sobrevivência entre recriações do container é necessário montar volume apontando para `data/` (não adiciona serviços externos). Atende proposta/ADR. Caminho pode ser sobrescrito por `SEQUENCIAS_DB_PATH`.
- Cadastro duplicado: `POST /sequencias` trata `sqlite3.IntegrityError` retornando `json.dumps({...duplicado: True...})` com status 200 (sem quebrar uso). Sequências idênticas às originais retornam `duplicado: True` com `origem: original` e não são gravadas. Comportamento documentado.
- Chave canônica: `chords_key` usa tokens normalizados separados por espaço (evita colisões como `['A','C']` vs `['AC']`); chaves concatenadas antigas continuam sendo lidas para compatibilidade. Entrada validada: até 32 acordes, até 20 caracteres por acorde, notação iniciando em `A`-`G`.
- Matching: para customizadas busca subsequência ordenada em `musica.cifra` (ordem respeitada). Entradas vazias retornam lista vazia. Caminho hardcoded das 6 originais preservado; formas ambíguas (ex. `E,mG`) não caem no catálogo original.
- Regressão: comparada via test client após alterações - `BmGDA 100, CGAmF 100, EmG 4, CA7DmG7 5, GmF 7, CC7FFm 3` (mesmos valores obtidos).
- Frontend: `#/porsequencia` carrega catálogo via `GET /sequencias`, permite cadastro via `POST /sequencias`, exibe mensagem de status/erro e aviso quando o catálogo não carrega.
- Testes: criados em `tests/test_sequencias_customizadas.py` (17 casos) usando `unittest` e banco SQLite temporário (`SEQUENCIAS_DB_PATH`), sem tocar em `data/sequencias.db`. Comando executado: `python -m unittest discover -s tests -v`. Resultado: 17 testes, todos OK (4.2s).
