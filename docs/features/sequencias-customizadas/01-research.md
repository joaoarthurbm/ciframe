# Pesquisa — Sequências de Acordes Customizadas

## Perguntas que você precisa responder

### 1) Algoritmo de matching
Hoje, as 6 sequências hardcoded em `main.py:40-45` são comparadas contra músicas via uma tag pré-computada (`SEQ_FAMOSA`/`seqs_famosas`, vinda do CSV). Sequências cadastradas pelo usuário não têm essa tag — o matching precisa ser calculado em tempo real a partir da lista de acordes de cada música (`musica.acordes`/`musica.cifra`).

**Evidências concretas:**
- Mapeamento hardcoded: `main.py:40-45` (`{'BmGDA':0,'CGAmF':1,'EmG':2,'CA7DmG7':3,'GmF':4,'CC7FFm':5}`)
- Rota `/similares?sequencia=`: lê `sequencia_tag` (`main.py:175`), faz `acordes = sequencia_tag.replace(',','')` (`main.py:191`), se em `sequencias` busca por `id_seq` e chama `get_similares_por_sequencia` (`main.py:194-197`).
- `get_similares_por_sequencia` (`main.py:203-223`): filtra com `apply_filtro`, inclui se `str(id_seq) in musica.seqs_famosas`, retorna dict sem `diferenca`/`intersecao`.
- CSV: `SEQ_FAMOSA` em coluna index 7 (`main.py:33`); carregado como `musica[SEQ_FAMOSA] = musica[SEQ_FAMOSA].split(";")` (`main.py:63`), passado a `Musica` e armazenado em `self.seqs_famosas` (`musica.py:18`).
- Cifra: processada por `limpa_cifra` (`main.py:11-23`, `58-61`); `Musica` seta `self.acordes = list(set(cifra))` (conjunto único, sem ordem) e guarda `self.cifra` (`musica.py:17`).

**Conclusão:** hoje matching é por **pertencimento** de `id_seq` em `musica.seqs_famosas` (tag pré-computada). Para sequências customizadas sem tag, precisa-se definir critério em tempo real sobre `musica.acordes`/`musica.cifra`. Definição exata (ordem, repetições, normalização) é decisão da proposta; requisito de regressão: reproduzir resultados das 6 originais.

### 2) Validação da hipótese
**Evidência:** mecanismo atual depende de tags pré-computadas. "Mesmos resultados esperados de hoje para as 6 originais" é o critério mínimo. Inspeção de `data/top/dataset_final.csv` mostra `SEQ_FAMOSA` majoritariamente `NA` com apenas subconjunto contendo valores numéricos (linhas 1-5 e amostra). Validação completa exigiria rodar contra dados reais, mas não foram feitas alterações nesta pesquisa.

### 3) Banco de dados
**Restrições:** sem banco hoje (`AGENTS.md:9-11`), container único local-only (`AGENTS.md:16`, `docs/adr/0001-local-only-docker-deploy.md`), sem serviços externos adicionais (enunciado).
**Opções viáveis (embutidas):** SQLite via `sqlite3` (stdlib, arquivo local, persistente com volume), TinyDB (dependência, arquivo JSON), JSON puro. `Dockerfile` atual não adiciona DB externo. Persistência entre reinícios requer caminho gravável/volume conforme setup.

### 4) Frontend existente (`#/porsequencia`)
**Evidências:**
- Rota `static/assets/js/routes.js:20-23` -> `templates/sequencia.html` controller `SequenciaController as Sequencia`.
- `static/assets/js/controllers/sequencia.js:2-44`: **4 sequências hardcoded** (`sequencia1-4`) vs **6 no backend** (`main.py:40-45`) — detalhe real e pré-existente.
- Busca: `sequencia.js:78-110` monta `similares?sequencia=` com acordes concatenados por vírgula via `createChordsString` e faz GET relativo.
- Template `static/templates/sequencia.html`: renderiza `Sequencia.sequenciasFamosas`, filtra resultados com `ng-hide="music.diferenca.length"` (respostas de sequência famosa não têm `diferenca`/`intersecao`), ordena por `-popularidade`. Requisito exige catálogo real vindo do backend (não mais hardcoded) e permitir cadastrar nova sequência.

## Registro das descobertas
- Matching por tag pré-computada (`seqs_famosas`) via dict hardcoded (`main.py:40-45`, `170-223`); `musica.acordes` é `list(set(cifra))` sem ordem (`musica.py:17`).
- CSV em `data/top/dataset_final.csv`; muitas entradas com `SEQ_FAMOSA` `NA`.
- Sem DB, apenas in-memory CSV (`AGENTS.md:11`). Endpoints retornam `json.dumps` string (`AGENTS.md:46`).
- Frontend tem 4 sequências hardcoded diferentes das 6 do backend; precisa virar dinâmico + cadastro.

## Trade-offs identificados
**Algoritmo:** subsequência em `musica.cifra` (ordem) vs sobre sequência normalizada vs conjunto/interseção — definição nova para customizadas; regressão obrigatória para 6 originais.
**Banco:** SQLite (stdlib, embutido) vs TinyDB vs JSON — alinhado com container único sem serviços externos.
**Frontend:** carregar catálogo do backend, remover hardcode, adicionar UI de cadastro — atende requisito de refletir catálogo real e permitir cadastro.
