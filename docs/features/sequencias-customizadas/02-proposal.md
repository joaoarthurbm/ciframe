# Proposta — Sequências de Acordes Customizadas

> Fase **P** do RePPIT (`commands/make-proposals.md`), reduzida a **uma** proposta
> escolhida porque o enunciado fixa o alvo: o template pede "a abordagem
> escolhida" e "alternativas descartadas", e não duas propostas concorrentes. As
> alternativas reais consideradas estão na seção de descarte, com o motivo
> concreto de cada uma — nenhuma delas foi descartada por preferência estética.

## Abordagem escolhida

### Algoritmo de matching

Uma música `M`, com cifra ordenada `C = [c1..cm]` (com repetições, exatamente
como `limpa_cifra` a produz em `main.py:11-23`), é compatível com a sequência
`S = [s1..sn]` se, e somente se, **as duas** condições valerem:

1. **Contiguidade** — `";".join(S).casefold()` é substring contígua de
   `";".join(C).casefold()`.
2. **Vocabulário contido** — todo acorde presente em `C` está presente em `S`
   (comparação `casefold`, por token inteiro).

Músicas com cifra vazia (8.141 registros) nunca são compatíveis.

Consequências explícitas, para que ninguém as descubra em produção:

- **a ordem importa**: `Gm;F` ≠ `F;Gm`;
- **repetição importa**: `C;C` ≠ `C`, porque a condição (1) é sobre a cifra, que
  preserva repetições;
- **não há equivalência enarmônica** (`C#` ≠ `Db`), nem tolerância a
  transposição, nem comparação aproximada;
- o matching usa `musica.cifra` e **não** `musica.acordes`: o segundo é
  `list(set(cifra))` (`musica.py:17`), sem ordem, e torna a condição (1)
  irrealizável;
- a condição (2) é o que dá sentido ao produto: "músicas que você toca **só**
  com esses acordes", o mesmo princípio do `diferenca` que a busca por acordes já
  usa (`main.py:230-263`).

Por que exatamente essa regra e não uma mais generosa: é a regra que a tag
`SEQ_FAMOSA` já codifica, e foi validada sem divergência nas 6 sequências
(`01-research.md`, seção 2). Qualquer relaxamento (por exemplo, exigir só a
contiguidade) multiplicaria os resultados por ~5 — `CGAmF` passaria de 296 para
1.246 músicas — e violaria o critério de regressão obrigatório.

Custo: uma varredura completa por requisição, medida em **40–51 ms** sobre
67.585 músicas, sem índice e sem cache. Não há otimização a fazer antes de haver
evidência de que ela é necessária.

### Banco de dados

**SQLite**, via `sqlite3` da biblioteca padrão do Python 3.9, em um arquivo único.

- **Zero dependência nova**: `requirements.txt` continua com Flask e gunicorn.
  Num projeto cujo deploy é um `Dockerfile` de 12 linhas, adicionar um driver ou
  um ORM é custo sem retorno.
- **`UNIQUE` e transação de verdade**: é o que permite tratar "sequência
  duplicada" como restrição do banco, e não como uma checagem em Python que
  perde corrida sob concorrência.
- **Um único worker gunicorn** (padrão `sync`): não há escrita concorrente entre
  processos, então o modo de journaling padrão do SQLite basta. Cada requisição
  abre e fecha a própria conexão.

Caminho do arquivo: **`/var/lib/ciframe/ciframe.db`**, sobrescrevível pela
variável de ambiente `CIFRAME_DB` (usada pelos testes, que apontam para
`tmp_path`).

O diretório é declarado como `VOLUME` no `Dockerfile` e o comando documentado
passa a ser `docker run -p 8080:8080 -v ciframe-data:/var/lib/ciframe ciframe`.

**Por que não em `/app/data`**: esse diretório contém o `dataset_final.csv`, e um
volume montado ali esconderia o arquivo — `main.py:49` abriria um caminho
inexistente e a aplicação morreria no import. O diretório gravável precisa ser
separado do dado versionado. Isso está registrado em
[ADR-0002](../../adr/0002-persist-custom-sequences.md).

### Esquema de dados (alto nível)

Uma tabela, porque o domínio tem uma entidade:

```
sequencias
  id         INTEGER PRIMARY KEY      -- ordem de cadastro, 1..6 são as legadas
  nome       TEXT NOT NULL            -- exibição ("Sequência de Bm")
  acordes    TEXT NOT NULL            -- JSON array, caixa original: ["Bm","G","D","A"]
  chave      TEXT NOT NULL UNIQUE     -- ";".join(casefold(acorde)): "bm;g;d;a"
  criado_em  TEXT NOT NULL            -- ISO-8601 UTC
```

Duas colunas para a mesma lista, de propósito: `acordes` preserva a grafia que o
usuário digitou (exibição e fidelidade ao cifraclub) e `chave` é a forma
canônica usada no matching e na detecção de duplicata. Guardar só a chave
perderia a caixa; guardar só os acordes obrigaria a normalizar em toda consulta.

A normalização é `";".join(t.strip().casefold() for t in acordes)`, preservando
ordem e repetições.

**Seed**: na primeira subida, as 6 sequências legadas são inseridas com os nomes
de `data/mapeamento_sequencias_famosas.txt` (arquivo que hoje nenhum código lê) e
recebem os ids 1..6, na ordem das tags 0..5. O seed é idempotente por
`INSERT OR IGNORE` sobre `chave` — reiniciar o container não duplica nada. Ids
começam em 1, e não em 0, para que nenhum `if (id)` em JavaScript trate a
primeira sequência como ausente.

O catálogo de músicas e gêneros **continua no CSV, em memória**, conforme o
requisito. A coluna `SEQ_FAMOSA` deixa de ser lida pelo código e permanece
intacta no arquivo.

### API

Três superfícies, todas devolvendo `json.dumps(...)` como string — **nunca**
`jsonify`, preservando o `Content-Type: text/html` documentado em `AGENTS.md`.
Somente os endpoints novos usam códigos de status reais.

**`GET /sequencias`** → `200`

```json
[{"id": 1, "nome": "Sequência de Bm", "acordes": ["Bm","G","D","A"],
  "chave": "bm;g;d;a", "criado_em": "2026-11-01T12:00:00Z"}]
```

Ordenado por `id`, sem contagem de músicas (calcular a contagem de N sequências
custaria ~45 ms × N; vira inviável quando o catálogo cresce, que é justamente o
ponto da feature).

**`POST /sequencias`** → `201`

```json
{"acordes": ["Bm","G","D","A"], "nome": "opcional"}
```

Resposta `201` com o registro criado (mesmo shape acima). Erros:

| situação | status | corpo |
|---|---|---|
| corpo não é JSON / `acordes` ausente ou não-array | `400` | `{"erro": "...", "campo": "acordes"}` |
| menos de 2 ou mais de 12 acordes | `400` | `{"erro": "entre 2 e 12 acordes"}` |
| acorde fora do vocabulário (`/acordes`, case-insensitive) | `400` | `{"erro": "...", "acorde": "Xyz"}` |
| `nome` com mais de 80 caracteres | `400` | `{"erro": "...", "campo": "nome"}` |
| `chave` já cadastrada | `409` | `{"erro": "já cadastrada", "id": 1, "chave": "c;g;am;f"}` |

Quando `nome` é omitido, o servidor deriva `"Bm - G - D - A"`.

**`GET /similares?sequencia_id=<id>`** → `200` com a mesma lista de 9 campos que
o `?sequencia=` já devolve hoje (sem `diferenca`/`intersecao`, para não quebrar o
`ng-hide` de `sequencia.html:42-43`); `404` se o id não existir.

**`GET /similares?sequencia=<acordes>`** — comportamento legado **preservado**:
desconhecida devolve `[]` com `200`. Internamente deixa de consultar o `dict`
hardcoded e passa a procurar a `chave` no banco, o que produz os mesmos
resultados nas 6.

Precedência de `/similares`: `acordes` > `id_unico_musica` > `sequencia_id` >
`sequencia`, estendendo a ordem que já existe (`main.py:184-201`) sem reordenar
nada.

Validação de acorde é feita contra o vocabulário global que a aplicação já
carrega (`acordes`, `main.py:162-164`): catálogo aberto não é catálogo com lixo,
e rejeitar token desconhecido é o único guardrail que sai de graça. Sem rate
limit, sem autenticação, sem moderação — decisão consciente, registrada no
escopo.

### Frontend

Em `#/porsequencia` (`static/templates/sequencia.html` +
`static/assets/js/controllers/sequencia.js`):

- a lista de sequências deixa de ser hardcoded e passa a vir de `GET /sequencias`
  no início do controller — o catálogo real, com as 6 legadas **e** as novas, e
  portanto `EmG` e `CA7DmG7` passam a ser alcançáveis pela UI pela primeira vez;
- `temAcorde` (`sequencia.js:47-53`) deixa de comparar **identidade de objeto**
  (`indexOf`) e passa a comparar a string do acorde. Hoje o destaque verde dos
  hexágonos só funciona porque os objetos literais são reusados; com dados vindos
  do servidor essa premissa cai;
- formulário **inline** no painel esquerdo, acima da lista: campo de texto aceita
  `Bm G D A`, `Bm,G,D,A` ou `Bm;G;D;A`, mostra os hexágonos em tempo real e envia
  `POST /sequencias` com o array;
- ao receber `201`: a sequência entra na lista, é selecionada e **a busca dispara
  na mesma ação**;
- ao receber `409`: a sequência existente é selecionada, com aviso — o usuário
  queria buscar aquilo, não criar um duplicado;
- as buscas da UI passam a usar `sequencia_id`; `?sequencia=` continua existindo
  como API legada, coberta por teste.

Fica de fora, deliberadamente: paginação e contagem de resultados (hoje a UI
trunca em 100 sem avisar — dívida documentada, não corrigida aqui), seleção
múltipla de gênero, e o gênero `R&B;` que falta na constante `GENEROS` de
`app.js:6-58`.

## Alternativas consideradas e descartadas

**Matching só por contiguidade (sem a condição de vocabulário).** Descartada:
quebraria a regressão de forma mensurável — `BmGDA` passaria de 199 para 972
músicas, `EmG` de 4 para 3.704 — e o enunciado trata "as 6 continuam iguais"
como critério obrigatório. Não é uma questão de gosto: é o requisito.

**Matching por conjunto de acordes, ignorando ordem.** Descartada: 14.160
músicas para `EmG`. Deixaria de existir o conceito de "sequência" — viraria a
busca por acordes que o app já tem em `/similares?acordes=`.

**Persistir o catálogo escrevendo no próprio CSV.** Descartada: o arquivo é lido
uma vez no import (`AGENTS.md`), então cadastro exigiria restart; não há
unicidade nem escrita atômica; e o requisito pede explicitamente banco.
Além disso, o CSV é dado de entrada do projeto, não estado da aplicação.

**PostgreSQL ou Redis.** Descartada: exige segundo container ou serviço externo,
o que viola `docs/adr/0001-local-only-docker-deploy.md` ("container único, sem
serviços externos adicionais").

**TinyDB / arquivo JSON.** Descartada: dependência nova (ou escrita manual não
atômica) sem `UNIQUE` real, para resolver um problema que o SQLite resolve na
biblioteca padrão.

**Manter a UI chamando `?sequencia=<acordes>` em vez de `sequencia_id`.**
Descartada: o parâmetro legado faz `replace(',','')` (`main.py:191`), então
`CG,Am,F` colide com `CGAmF`, e a string cresce linearmente com o número de
acordes. O contrato antigo fica por compatibilidade, não como caminho principal.

## Escopo explícito

**Dentro do escopo:**

- tabela `sequencias`, seed idempotente das 6 legadas, `UNIQUE` por `chave`;
- `VOLUME` no `Dockerfile` e comando `docker run -v` no `README.md`/`AGENTS.md`;
- matching em tempo real sobre `musica.cifra`, com a regra definida acima;
- `GET /sequencias`, `POST /sequencias`, `sequencia_id` em `/similares`;
- `?sequencia=` legado mantido, com resultados idênticos nas 6;
- `#/porsequencia` lendo o catálogo do backend, com formulário inline de cadastro;
- testes automatizados (unitários + integração via test client) e baseline golden
  das 6 sequências, gerada antes da mudança;
- `docs/adr/0002-persist-custom-sequences.md`.

**Fora do escopo (e por quê):**

- **editar e apagar sequências** — catálogo anônimo sem login não tem como
  autorizar ninguém; qualquer `DELETE` seria vandalismo trivial, e as 6 legadas
  são o próprio critério de regressão;
- **autenticação, moderação, rate limit** — o requisito é catálogo aberto e
  anônimo; rate limit em container único sem estado compartilhado é teatro;
- **enarmonia, transposição, matching aproximado** — mudaria os resultados das 6
  e quebraria a regressão; é uma feature de outra natureza;
- **paginação/contagem na UI, multi-gênero, `R&B;`** — dívidas pré-existentes,
  não requisitos desta tarefa;
- **migrar músicas/gêneros para o banco** — proibido pelo enunciado;
- **corrigir as 5 dívidas do `01-research.md`** (primeira linha do CSV
  descartada, `replace('NA','')`, ordem dependente de hash, `get_similares`
  duplicado, 500 em id inexistente) — mudariam resultados de endpoints que o
  requisito manda manter estáveis;
- **modernizar o AngularJS 1.4.9** — decisão separada e maior, fora do escopo
  (`docs/adr/0003-lift-frontend-freeze.md` apenas removeu a proibição).

## Como saberemos que funcionou

1. Para cada uma das 6 chaves, o **conjunto** de `id_unico_musica` retornado é
   idêntico ao do código atual (baseline golden commitada antes da mudança).
2. Cadastrar `Em,G` pela UI devolve `201`, aparece na lista e a busca funciona
   sem reload.
3. Cadastrar `C,G,Am,F` devolve `409` apontando o id existente.
4. `docker run` → cadastrar → `docker rm` → `docker run` novo: a sequência
   cadastrada continua lá (é o requisito de persistência, e o único que não se
   prova em teste unitário).
