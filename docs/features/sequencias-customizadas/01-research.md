# Pesquisa — Sequências de Acordes Customizadas

> Fase **R** do RePPIT (`commands/research-codebase.md`). Este documento descreve
> **apenas o que existe hoje**: fluxo real, dados reais, medições reais. Nenhuma
> decisão de solução é tomada aqui — as opções ficam registradas em
> [Trade-offs identificados](#trade-offs-identificados) e a escolha vai para
> `02-proposal.md`.

## Método e procedência da evidência

- **Código**: lido integralmente (`main.py`, `musica.py`, `Dockerfile`,
  `static/assets/js/`, `static/templates/`, `scripts/`), com referências
  `arquivo:linha` em cada achado.
- **Dados**: `data/top/dataset_final.csv` (15.866.887 bytes) foi reprocessado com
  o **mesmo parser** de `main.py:49-63` (inclusive o `readline()` e o
  `replace('NA','')`), para que os números reflitam o que a aplicação realmente
  carrega — não o CSV em abstrato. Resultado: **67.585 músicas carregadas**.
- **Comportamento em execução**: as views reais foram importadas e chamadas
  (`main.py` importado com um stub de `flask`, já que Flask não estava instalado
  no ambiente), com `PYTHONHASHSEED` variando entre 0, 1 e 42.
- **Benchmark**: a regra de matching foi reimplementada em script isolado e
  cronometrada sobre os 67.585 registros.
- **DeepWiki**: `https://deepwiki.com/joaoarthurbm/ciframe` respondeu **HTTP 429**
  em três tentativas (raiz, `/1-overview` e endpoint de API). A evidência deste
  documento vem do código-fonte, não da wiki.

## Perguntas que você precisa responder

1. **Algoritmo de matching** — o que define que a sequência X aparece na música Y?
2. **Validação da hipótese** — a regra considerada reproduz os matches das 6
   sequências hardcoded?
3. **Banco de dados** — quais bancos embarcados são viáveis no container único e
   local-only? O que cada um implica para o `Dockerfile` e para a persistência?
4. **Frontend existente** — o que `#/porsequencia` já faz hoje?

---

## Registro das descobertas

### 1. Algoritmo de matching

#### 1.1 Hoje não existe matching em tempo de execução

A busca por sequência é um **teste de pertinência a uma tag pré-computada**. O
caminho completo:

- `main.py:40-45` — o catálogo é um `dict` Python de 6 entradas, cuja chave é a
  concatenação dos acordes **sem separador**, e cujo valor é o id da tag:
  `{'BmGDA': 0, 'CGAmF': 1, 'EmG': 2, 'CA7DmG7': 3, 'GmF': 4, 'CC7FFm': 5}`.
- `main.py:190-197` — em `/similares`, quando vem `sequencia=`, o parâmetro sofre
  `sequencia_tag.replace(',','')` (então `Bm,G,D,A` e `BmGDA` são a mesma chave, e
  `CG,Am,F` colide com `CGAmF`) e é procurado nesse `dict`. Se não estiver lá, a
  resposta é `[]` com HTTP 200.
- `main.py:203-223` — `get_similares_por_sequencia` percorre a coleção já
  filtrada por gênero e mantém as músicas em que
  `str(id_seq) in musica.seqs_famosas` (`main.py:209`). **É só isso**: uma
  comparação de string contra uma coluna do CSV.
- `musica.py:17` / `main.py:63` — `seqs_famosas` vem da coluna `SEQ_FAMOSA`,
  dividida por `;`. Música sem tag fica com `['']`.

Nomes legíveis das 6 sequências existem apenas em
`data/mapeamento_sequencias_famosas.txt`, um arquivo de 6 linhas que **nenhum
código lê**.

#### 1.2 A tag foi gerada offline, com **duas** condições

`scripts/generate_data_set.py:7-24` é o script (Python 2, não executado pela
aplicação) que produziu a coluna:

```python
12:        acorde = acorde.lower()
13:        if s in acorde:                       # (a) substring contígua na cifra
14:            achou = True
15:            tem_seqs = []
16:            for l in acorde.split(';'):
17:                tokens = s.split(';')
18:                if l not in tokens:           # (b) todo acorde da música pertence à sequência
19:                    achou = False
20:                    break
```

Ou seja, a tag exige **as duas** coisas:

- **(a) contiguidade** — a sequência, unida por `;`, é substring contígua da
  cifra inteira da música, também unida por `;` (comparação em minúsculas);
- **(b) vocabulário contido** — *todos* os acordes usados na música estão entre
  os acordes da sequência. Uma música que toca a progressão mas usa um acorde a
  mais **não** é marcada.

A condição (b) é o que explica a seletividade do catálogo: ela é o análogo, no
eixo "sequência", do `diferenca` que a busca por acordes já usa (`main.py:230-263`).

Consequência prática: **(b) não pode ser reimplementada a partir de
`musica.acordes`** — `musica.py:17` faz `list(set(cifra))`, ou seja, deduplica e
perde a ordem. A ordem (condição a) só existe em `musica.cifra`.

#### 1.3 O que a tag significa, em números

Sobre as 67.585 músicas carregadas:

| seq | acordes | tag atual | só (a) contígua | só (b) vocabulário | todos os acordes presentes (sem ordem) |
|---|---|---|---|---|---|
| 0 | Bm G D A | **199** | 972 | 9.014 | 5.768 |
| 1 | C G Am F | **296** | 1.246 | 9.099 | 6.894 |
| 2 | Em G | **4** | 3.704 | 8.165 | 14.160 |
| 3 | C A7 Dm G7 | **5** | 96 | 8.194 | 582 |
| 4 | Gm F | **7** | 1.522 | 8.159 | 3.847 |
| 5 | C C7 F Fm | **3** | 144 | 8.198 | 365 |
| | **total** | **514** | | | |

A tag é de 2 a 5 vezes mais restritiva que a contiguidade sozinha. Qualquer
algoritmo que ignore (b) **não reproduz** o comportamento atual.

#### 1.4 Ordem, repetição e normalização

- **Repetição importa**: `musica.cifra` preserva a ordem de execução *e as
  repetições* (total de 3.505.331 tokens; média de 51,87 por música, máximo de
  2.065). `limpa_cifra` (`main.py:11-23`) descarta tokens vazios e, em linhas com
  `|`, mantém só o primeiro acorde antes da barra. Portanto `C;C` não é
  equivalente a `C`.
- **Ordem importa**: é o que a condição (a) testa. `Gm;F` e `F;Gm` são
  sequências diferentes.
- **Maiúsculas importam para a comparação, e a normalização é obrigatória**: os
  acordes são gravados como o cifraclub os escreve (`Bm`, `A/C#`, `Eb7M`), e
  apenas **26 de 6.653** tokens são inteiramente minúsculos — e são ruído de
  parsing (`add9`, `b9`, `9)`, `1a.vez`, `2x`), não acordes escritos em caixa
  baixa. A comparação só precisa ser case-insensitive porque **a tag é
  minúscula**; o script offline já fazia `acorde.lower()` nos dois lados.
- **Não há qualquer normalização enarmônica** (`C#` ≠ `Db`), nem unicode
  (`remover_combinantes`, `main.py:145-147`, existe só no `/search`).
- **8.141 músicas têm cifra vazia** (coluna `CIFRA` = `NA`), logo `cifra = []` e
  `acordes = []`: elas não podem casar com nenhuma sequência, por construção.

#### 1.5 Custo de calcular isso em tempo real

Benchmark da regra (a)+(b) sobre os 67.585 registros, em uma thread, sem
nenhum índice: **40–51 ms por sequência consultada** (a variação é ruído de
alocação). O conjunto de dados inteiro é percorrido a cada requisição.

Para comparação, o mesmo processo: importar `main.py` (parse do CSV) leva
~10 s, e esse parse acontece **uma vez, no import**, conforme `AGENTS.md`.

### 2. Validação da hipótese

A regra (a)+(b), reimplementada sobre `musica.cifra`, foi comparada com a tag
`SEQ_FAMOSA` música por música:

| seq | tag | algoritmo | conjuntos iguais? | faltando | sobrando |
|---|---|---|---|---|---|
| 0 Bm G D A | 199 | 199 | ✅ | 0 | 0 |
| 1 C G Am F | 296 | 296 | ✅ | 0 | 0 |
| 2 Em G | 4 | 4 | ✅ | 0 | 0 |
| 3 C A7 Dm G7 | 5 | 5 | ✅ | 0 | 0 |
| 4 Gm F | 7 | 7 | ✅ | 0 | 0 |
| 5 C C7 F Fm | 3 | 3 | ✅ | 0 | 0 |

**A hipótese se confirma sem uma única divergência.** O bar mínimo de correção
para a fase de testes é, portanto: *para cada uma das 6 chaves, o conjunto de
`id_unico_musica` retornado tem de ser idêntico ao conjunto retornado hoje*.

Três armadilhas que a baseline precisa evitar, todas verificadas:

- **comparar `list` em vez de `set`** falha por causa da ordem de
  `apply_filtro` (`main.py:266-272`), que percorre `generos` — um `set` cuja
  iteração muda com `PYTHONHASHSEED`. Com seeds 0, 1 e 42, o primeiro item de
  `?sequencia=CGAmF` foi, respectivamente, *Bryan Adams / I Will Be Right Here
  Waiting*, *Aviões do Forró / Eu Ela e a Amiga Dela* e *Bob Marley / Zion Train*.
  O **conjunto** é estável; a **ordem** não é.
- **comparar só a contagem** mascara trocas (199 pode ser 199 com uma música
  diferente).
- **usar `musica.acordes`** em vez de `musica.cifra` torna a condição (a)
  irrealizável (o campo é um `set` materializado em lista, sem ordem).

### 3. Banco de dados

#### 3.1 Restrições reais do container

- `Dockerfile` (12 linhas): `python:3.9-slim`, `WORKDIR /app`, `COPY . .`,
  `EXPOSE 8080`, `CMD gunicorn --bind 0.0.0.0:8080 main:app`. **Sem `VOLUME`**,
  sem `USER` (roda como root), sem healthcheck, sem multi-stage.
- **Um único worker gunicorn** (padrão `sync`, 1 processo). Não há concorrência
  entre processos, então um banco de arquivo não enfrenta contenção de escrita
  entre workers.
- `main.py:49` abre `'data/top/dataset_final.csv'` com **caminho relativo**, sem
  `encoding=`. Só funciona porque o `WORKDIR` é `/app`.
- `.dockerignore` exclui apenas `.git`, `.venv`, `__pycache__`, `*.pyc`: `data/`
  (77 MB), `docs/` e `scripts/` são copiados para dentro da imagem.
- O comando documentado (`AGENTS.md:17-21`, `README.md`) é
  `docker run -p 8080:8080 ciframe`, **sem volume**.

#### 3.2 Armadilha de persistência (a mais importante desta fase)

Duas coisas distintas precisam ser verdadeiras para "não se perde ao reiniciar":

1. o arquivo não pode estar apenas na **camada gravável** do container — ela
   sobrevive a `docker stop/start`, mas morre em `docker rm`/`docker run` novo;
2. o diretório do volume **não pode ser `/app/data`**.

O motivo do item 2: `/app/data` contém o `dataset_final.csv`, que é a base
inteira de músicas. Montar um volume nomeado ou bind mount sobre `/app/data`
**substitui o conteúdo do diretório** pelo conteúdo (vazio) do volume, e
`main.py:49` falha no import — a aplicação não sobe. O caminho gravável precisa
ser um diretório próprio, separado do CSV.

#### 3.3 Opções reais

| opção | dependência nova? | persistência | encaixe no container | observações |
|---|---|---|---|---|
| `sqlite3` (stdlib) | não | arquivo único | trivial; só o caminho do arquivo | `UNIQUE`/transação prontos; Python 3.9.0+ traz sqlite embutido |
| `TinyDB` | sim (pip) | arquivo JSON | trivial | sem `UNIQUE` real, sem transação, concorrência fraca |
| `dbm`/`shelve` (stdlib) | não | arquivo | trivial | chave-valor, sem consulta, sem integridade |
| arquivo JSON escrito à mão | não | arquivo | trivial | read-modify-write não é atômico; sem unicidade |
| PostgreSQL/Redis | sim (serviço) | fora do container | **exige segundo container** | viola `docs/adr/0001` ("container único, sem serviços externos adicionais") |

### 4. Frontend existente

#### 4.1 Rota e controller

`static/assets/js/routes.js:17-21` mapeia `#/porsequencia` →
`templates/sequencia.html` + `SequenciaController`. O acesso parte de
`static/templates/home.html:79`.

#### 4.2 A página mostra 4 das 6 sequências

`static/assets/js/controllers/sequencia.js:2-37` define **quatro** objetos
`sequencia1..4` hardcoded no JavaScript:

| var | acordes | chave gerada | tag no backend | exposta? |
|---|---|---|---|---|
| `sequencia1` | Bm, G, D, A | `BmGDA` | 0 | sim |
| `sequencia2` | C, G, Am, F | `CGAmF` | 1 | sim |
| `sequencia3` | Gm, F | `GmF` | 4 | sim |
| `sequencia4` | C, C7, F, Fm | `CC7FFm` | 5 | sim |
| — | Em, G | `EmG` | 2 | **não** |
| — | C, A7, Dm, G7 | `CA7DmG7` | 3 | **não** |

A divergência 6 (backend) × 4 (frontend) é pré-existente, não um defeito
introduzido pela tarefa.

#### 4.3 O que a requisição faz hoje

`sequencia.js:55-61` monta a string juntando os acordes com `,`;
`sequencia.js:72-90` chama `GET similares?sequencia=<acordes>[&generos=<um>]`
com `apiUrl = ""` (relativo). **Não envia `pagina`**, logo recebe sempre a
primeira página de `TAM_PAGINA = 100` (`main.py:35`) e trunca em silêncio: `CGAmF`
tem 296 músicas e a tela nunca mostra mais que 100. Nenhuma contagem é exibida.

Detalhes de acoplamento que a mudança precisa respeitar:

- `sequencia.js:47-53` (`temAcorde`) usa `indexOf` por **identidade de objeto**,
  o que só funciona porque os mesmos objetos literais são reusados — trocar o
  modelo de dados quebra o destaque dos hexágonos (verde/branco via `df-hex`).
- `sequencia.html:42-43` usa `ng-hide="music.diferenca.length"`: no caminho
  `?sequencia=` a resposta **não** traz `diferenca` (compare `main.py:210-220` com
  `main.py:246-258`), e o `undefined.length` do Angular 1.4 é falsy, então os
  cards aparecem por acidente feliz.
- A constante `GENEROS` (`app.js:6-58`) tem **51** gêneros; o backend serve
  **52** (`main.py:92`). Falta `R&B;` — que existe com esse `;` literal no CSV.
  Logo `R&B;` é inalcançável em qualquer filtro de gênero da UI.
- `app.js:3-5` define `RESTAPI = {url: 'http://localhost:5003'}`, que **nunca é
  usado** por nenhum controller.
- O `select` de gênero é de seleção única (`sequencia.html:24-30`) e dispara
  `pesquisarPorSequencia()`.

---

## Dívida técnica pré-existente (documentada, fora do escopo)

Encontrada durante a pesquisa e **deliberadamente não corrigida**: são defeitos
anteriores à tarefa, e corrigi-los mudaria resultados de endpoints que o
requisito manda manter estáveis.

| # | Achado | Evidência | Impacto | Bloqueia a feature? |
|---|---|---|---|---|
| 1 | A **primeira música do CSV é descartada**: o arquivo não tem cabeçalho, mas `main.py:50` chama `f.readline()` | 67.586 linhas → 67.585 carregadas; `14-bis_a-qualquer-tempo` ausente de `musicas` | essa música nunca aparece em busca nenhuma | não |
| 2 | `line.replace('NA','')` (`main.py:53`) corrompe títulos que contêm "NA" | 7 títulos: `DNA`→`D`, `CABANA`→`CABA`, `JULIANA`→`JULIA` | afeta `/search` e exibição | não |
| 3 | Ordem dos resultados depende de `PYTHONHASHSEED`, porque `generos` nasce de um `set` (`main.py:92`) e `apply_filtro` itera esse `set` | seeds 0/1/42 dão primeiros itens diferentes para `CGAmF` | como `get_pagina` (`main.py:226-228`) fatia **antes** de o frontend ordenar por popularidade, **quais** 100 músicas aparecem muda entre reinícios | não — mas o teste de regressão tem de comparar conjuntos |
| 4 | `get_similares` é definido duas vezes (`main.py:171` como view e `main.py:230` como helper) | import de `main` deixa `main.get_similares` apontando para o helper | confusão ao testar; o roteamento segue funcionando porque o decorator registrou o objeto anterior | não |
| 5 | `/musica/<id>` inexistente e `pagina=abc` devolvem **500** (`KeyError` / `ValueError`) | medido | sem contrato de erro na API legada | não |

---

## Trade-offs identificados

Nenhuma escolha é feita aqui; cada linha vira uma decisão em `02-proposal.md`.

### Algoritmo de matching

| opção | regra | `EmG` | `CGAmF` | prós | contras |
|---|---|---|---|---|---|
| **A** | contígua **+** vocabulário ⊆ sequência (réplica da tag) | 4 | 296 | regressão exata; mantém o sentido de "tocar com esses acordes e só eles" | sequências curtas devolvem pouquíssimo |
| **B** | só contígua, case-insensitive | 3.704 | 1.246 | intuitivo; funciona bem para sequências longas | **quebra a regressão** (199→972) |
| **C** | só conjunto de acordes, sem ordem | 14.160 | 6.894 | máxima descoberta | ignora o conceito de "sequência" |
| **D** | contígua, mas **ranqueando** em vez de filtrar | — | — | melhor UX de descoberta | não é o que o requisito pede (busca, não recomendação) |

### Banco de dados

| opção | prós | contras |
|---|---|---|
| SQLite (stdlib) | zero dependência; `UNIQUE`; transacional; arquivo único | exige decidir o caminho e o volume |
| TinyDB | API simples | dependência nova; sem unicidade real |
| `dbm`/`shelve` | stdlib | sem integridade, sem consulta |
| JSON em arquivo | trivial | escrita não atômica; corrupção sob concorrência |
| Postgres/Redis | robusto | segundo serviço: viola o ADR-0001 |

### Persistência entre reinícios

| opção | prós | contras |
|---|---|---|
| Volume nomeado em diretório próprio (`/var/lib/ciframe`) + `VOLUME` | sobrevive a `docker rm`; não toca no CSV | altera o comando `docker run` documentado |
| Volume sobre `/app/data` | "óbvio" | **quebra o app**: esconde o `dataset_final.csv` |
| Bind mount do repo | sem mudar `Dockerfile` | depende do host; exige `.gitignore` para o `.db` |
| Só a camada gravável do container | nenhuma config | morre no `docker rm`; não cumpre o requisito |

### Identidade da sequência na API

| opção | prós | contras |
|---|---|---|
| chave de acordes (`sequencia=C,G,Am,F`) | compatível com o frontend e com as URLs atuais | colisões do `replace(',','')`; string longa; sem nome |
| id numérico (`sequencia_id=1`) | curto, estável | quebra a URL atual; frontend precisa do id |
| nome/slug | legível | colide; exige unicidade de nome |

### Frontend

| opção | prós | contras |
|---|---|---|
| buscar catálogo do backend + formulário de cadastro | cumpre o requisito | quebra o `temAcorde` por identidade de objeto |
| manter os 4 hardcoded e só adicionar um form | mudança mínima | a página passa a divergir do catálogo real |
| reescrever a página | qualidade | fora de escopo; AngularJS 1.4.9 legado |

---

## Perguntas que ficaram para a Proposta

- Qual das opções de algoritmo/banco/persistência/API/frontend acima é escolhida,
  e por quê.
- Formato exato dos endpoints novos: nome do recurso, corpo de entrada, formato
  do erro e código HTTP.
- O que acontece ao cadastrar uma sequência que já existe (normalizada).
- Como validar entrada de um catálogo anônimo (limites, vocabulário de acordes).
- Como o `Dockerfile`/`README` passam a documentar o volume.
