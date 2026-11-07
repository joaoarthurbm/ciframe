# Proposta — Sequências de Acordes Customizadas

## Abordagem escolhida

### Algoritmo de matching
Para sequências cadastradas pelo usuário (sem tag pré-computada), o matching será calculado **em tempo real**. Definição precisa:

- **Fonte da sequência da música:** usar `musica.cifra` (lista processada por `limpa_cifra` em `main.py:11-23`, mantida em `Musica.cifra`, `musica.py:17`) — preserva ordem de aparição dos acordes após limpeza/filtragem. `musica.acordes` (`list(set(cifra))`) não preserva ordem e remove duplicados, portanto não é adequado para "sequência aparece".
- **Representação da sequência consultada:** lista ordenada de acordes fornecida (pode vir como lista separada por vírgulas no parâmetro `sequencia`, ou como lista ordenada na API de cadastro). Normalizar removendo espaços em branco e comparando com a notação de acorde preservada (**case-sensitive**, pois `C` e `c` representam acordes diferentes). Manter notação de acorde tal como aparece (ex. `Bm`, `C#m`, `F#/Bb`, `7`, `m7`).
- **Regra de "aparece":** a **sequência ordenada** de acordes consultada deve aparecer como uma **subsequência na ordem** dentro de `musica.cifra` da música (subsequência não necessariamente contígua).
  - **Ordem importa.**
  - **Repetições dentro da música importam na medida em que a subsequência ordenada é encontrada ao percorrer a lista na ordem** (não colapsamos repetições da cifra).
  - **Não exigimos correspondência exata de todo o encadeamento** — basta que a sequência consultada apareça em ordem em algum ponto da cifra da música.
- **Compatibilidade com as 6 originais:** as 6 sequências hardcoded em `main.py:40-45` continuarão usando o mecanismo existente via `seqs_famosas` (tags pré-computadas no CSV). O endpoint `/similares?sequencia=...` deve manter o comportamento atual para essas chaves, produzindo os mesmos resultados. Para sequências **não** presentes no mapeamento hardcoded (sequências customizadas cadastradas), usar o matching em tempo real por subsequência ordenada sobre `musica.cifra`.

### Banco de dados
**Tecnologia:** **SQLite** via módulo padrão `sqlite3` (Python 3.9).
- Embutido, sem serviço externo, cabe no container Docker único e local-only.
- Arquivo persistido no filesystem (ex. `data/sequencias.db` ou caminho configurável). Persistência entre reinícios do container exige que o arquivo resida em local gravável e, conforme necessário, montado como volume no `docker run` (sem alterar a premissa de "container único").
- Apenas o **catálogo de sequências** vai para o banco. Catálogo de **músicas e gêneros** continua vindo do CSV carregado em memória como hoje (`main.py:49-98`, `AGENTS.md:9-11`).

### Esquema de dados (alto nível)
Tabela única (mínima) para o catálogo:
- `sequences` (ou equivalente):
  - `id` (PK, autoincrement)
  - `chords` (string) — tokens normalizados separados por vírgula (ex. `Bm,G,D,A`)
  - `chords_key` (string) — chave canônica delimitada por espaço (ex. `Bm G D A`), unívoca e usada para lookup/duplicidade; linhas antigas com chave concatenada continuam sendo lidas para compatibilidade
  - `created_at` (timestamp, opcional)

Regras: catálogo aberto e anônimo; permitir cadastrar novas sequências. Tratar duplicados (mesma sequência canônica) de forma a não criar entradas redundantes. Sequências idênticas às seis originais são rejeitadas como duplicadas do catálogo original (o caminho de busca original é preservado).

### API
Manter compatibilidade com comportamento existente:
- **GET /similares?sequencia=...** continua funcionando para as 6 sequências hardcoded (via `seqs_famosas`). Para sequências cadastradas/customizadas não mapeadas no hardcoded, resolver via banco + matching em tempo real por subsequência ordenada em `musica.cifra`. Respostas continuam via `json.dumps(...)` (string), sem `jsonify` (`AGENTS.md:46`).
- **Novos endpoints (propostos):**
  - `GET /sequencias` — listar catálogo completo (6 originais + cadastradas) com identificação suficiente para o frontend exibi-las e usá-las na busca (formato a ser compatível com o que o frontend precisa).
  - `POST /sequencias` — cadastrar nova sequência (lista ordenada de acordes). Aberto e anônimo, sem login. Validar formato/básico; em caso de duplicado, retornar representação consistente (sem quebrar uso).

Formato de entrada/saída será JSON serializado via `json.dumps` como hoje.

### Frontend
Em `#/porsequencia` (`static/templates/sequencia.html`, `static/assets/js/controllers/sequencia.js`):
- **Catálogo dinâmico:** buscar catálogo real do backend (via novo endpoint) ao invés de manter apenas as 4 sequências hardcoded em `sequencia.js`. Exibir todas as sequências disponíveis (as 6 originais + cadastradas). Resolver o fato atual de frontend ter 4 vs backend 6.
- **Cadastro:** permitir cadastrar nova sequência de acordes (interface para montar/fornecer lista ordenada). Após cadastro bem-sucedido, atualizar catálogo e permitir busca imediatamente.
- **Busca:** manter fluxo existente — ao clicar/selecionar uma sequência, chamar `/similares?sequencia=...` com a forma que o backend espera; deve funcionar para sequências antigas e novas da mesma forma.

## Alternativas consideradas e descartadas
- **Usar `musica.acordes` (conjunto único, sem ordem) para matching de sequências customizadas:** descartado porque `musica.acordes = list(set(cifra))` em `musica.py:17` não preserva ordem nem repetições; não permite representar "sequência". Incompatível com noção de sequência ordenada.
- **Persistir sequências em arquivo JSON simples sem SGBD:** descartado como "banco de dados" formalmente (requisito pede persistência em banco de dados). SQLite embutido é mais alinhado ao requisito e ainda cabe em container único sem serviço externo.
- **Migrar músicas/gêneros para banco:** descartado explicitamente pelo enunciado ("Catálogo de músicas e gêneros continua vindo do CSV, carregado em memória como hoje. Não migre músicas/gêneros para o banco. Só o catálogo de sequências precisa de persistência.").
- **Adicionar serviço externo (Postgres/MySQL):** descartado por violar "container único, sem serviços externos adicionais" e "local-only" conforme ADR 0001.

## Escopo explícito

**Dentro do escopo:**
- Persistir catálogo de sequências em banco de dados (SQLite embutido) sobrevivendo a reinícios.
- Suportar cadastro anônimo de novas sequências e busca por elas via `/similares?sequencia=...`.
- Tornar catálogo de sequências dinâmico no frontend `#/porsequencia` (refletir catálogo real do backend) e adicionar cadastro.
- Manter comportamento e resultados das 6 sequências hardcoded originais inalterados (regressão obrigatória).

**Fora do escopo (e por quê):**
- Alterar carregamento/migração de músicas/gêneros do CSV (ficam em memória como hoje — explícito no enunciado).
- Modernizar stack frontend/backend além do necessário para esta feature.
- Autenticação/login para cadastro (catálogo aberto e anônimo).
- Mudar formato de retorno dos endpoints para `jsonify` (deve continuar `json.dumps`).
