# Relatório de testes — Sequências de Acordes Customizadas

## Cobertura

78 testes, em quatro arquivos, todos passando (`78 passed`). A divisão segue a
fronteira natural do que pode quebrar:

| arquivo | testes | o que verifica |
|---|---|---|
| `tests/test_matching.py` | 14 | a regra de matching isolada: contiguidade, vocabulário contido, ordem, repetição, caixa alta, cifra vazia, fronteira de acorde (`am` não casa com `am7`) |
| `tests/test_db.py` | 18 | `CIFRAME_DB`, falha no boot quando o diretório não é gravável, criação de diretórios, schema idempotente, seed idempotente (6 linhas depois de 3 chamadas), ids 1..6, `acordes` desserializado, `normalizar_chave`, `resolver_chave` |
| `tests/test_api.py` | 32 | `GET /sequencias` (shape e ordem), `POST` 201/400/409, duplicata que difere só por caixa/espaço, limites 2 e 12, acorde desconhecido citado na resposta, corpo sem JSON, corrida no `UNIQUE` virando 409, `sequencia_id` 200/400/404, precedência de parâmetros, `?sequencia=` desconhecida devolvendo `[]`/200, paginação, filtro por gênero |
| `tests/test_regressao.py` | 14 | as 6 sequências originais contra a baseline gerada **antes** da migração, pelas três URLs (`?sequencia=` concatenada, `?sequencia=` com vírgulas, `?sequencia_id=`) |

Dois detalhes que valem registro:

- O banco real nunca é aberto pela suíte: `tests/conftest.py` aponta
  `CIFRAME_DB` para um diretório temporário **antes** de importar `main.py`
  (o caminho é lido no import). Rodar como usuário comum, sem permissão em
  `/var/lib`, é a prova de que o default não é tocado.
- `main.py` é importado uma vez por sessão (`scope="session"`): o parse do CSV
  custa ~1,2 s e cada teste pagaria esse preço.

## Teste de regressão obrigatório

As 6 sequências originais saíram do `dict` hardcoded (`main.py`, antigas linhas
40-45) para `SEQUENCIAS_LEGADO` + seed no banco. A verificação não é "olhar e
achar igual":

1. **Antes** de qualquer mudança de código (passo 1/10 do plano, commit
   `passo 1/10`), `tests/fixtures/gerar_baseline.py` executou o código **antigo**
   — aquele que lia a coluna `SEQ_FAMOSA` — e gravou
   `tests/fixtures/sequencias_legado.json` com os `id_unico_musica` de cada uma
   das 6 chaves: **199, 296, 4, 5, 7, 3** músicas.
2. O gerador se recusa a sobrescrever esse arquivo sem `--force`: regerar depois
   da migração compararia o código novo com ele mesmo e o teste passaria a não
   provar nada.
3. `tests/test_regressao.py` compara **conjuntos** de `id_unico_musica`, não
   listas. A ordem do resultado depende de `PYTHONHASHSEED` (dívida
   pré-existente, documentada em `01-research.md`); comparar listas acusaria
   diferença onde não há.
4. Compara pelas três formas de URL: `?sequencia=BmGDA` (chave antiga),
   `?sequencia=Bm,G,D,A` (o que o frontend envia) e `?sequencia_id=<id>`.
   A paginação é percorrida até o fim — comparar só a primeira página esconderia
   diferença no fim do conjunto (BmGDA tem 199 músicas, duas páginas).

Resultado: conjuntos idênticos à baseline nas 18 combinações (6 sequências × 3
URLs), com as contagens originais preservadas.

Há também um teste de sanidade (`test_nenhuma_legada_devolve_tudo`) que falha se
alguma sequência passar a devolver mais de 10% do dataset — a regressão mais
provável seria um filtro que deixou de filtrar.

## Como rodar

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

Saída:

```
........................................................................ [ 92%]
......                                                                   [100%]
78 passed in 10.44s
```

Cobertura (`pytest -q --cov=main --cov-report=term-missing`):

```
Name      Stmts   Miss  Cover   Missing
---------------------------------------
main.py     299     28    91%   197, 265, 274, 278-304, 308-309, 318, 322, 326, 435, 456-457, 586
---------------------------------------
TOTAL       299     28    91%
```

As 28 linhas descobertas são, quase todas, código que esta feature não tocou:
`/search` (274, 278-304, 308-309), `/musicas`, `/acordes` (318, 322, 326),
`/musica/<id>` (435), o caminho `id_unico_musica` de `/similares` (456-457), a
rota `/` (265) e o branch `os.access` de `prepara_diretorio_db` (197, o caso em
que o `makedirs` funciona mas o diretório não é gravável).

## Verificação manual (o que a suíte não cobre)

### Persistência real no Docker

Feito com o volume nomeado, que é o que o `README.md` passa a documentar:

```
docker build -t ciframe .
docker run -d --name ciframe-demo -p 8080:8080 -v ciframe-data:/var/lib/ciframe ciframe
curl localhost:8080/sequencias                    # 6 registros (seed)
curl -X POST -H 'Content-Type: application/json' \
     -d '{"acordes":["Em","G","D","A"],"nome":"Em G D A (demo)"}' \
     localhost:8080/sequencias                    # 201, id=7
docker rm -f ciframe-demo
docker run -d --name ciframe-demo2 -p 8080:8080 -v ciframe-data:/var/lib/ciframe ciframe
curl localhost:8080/sequencias                    # 7 registros, id=7 presente
curl 'localhost:8080/similares?sequencia_id=7'    # 200, resultados
```

Também testado o caso sem `-v`: `docker run -d --name ciframe-semvolume -p 8081:8080 ciframe`
sobe normalmente e mostra as 6 semeadas (o `VOLUME` do Dockerfile cria um volume
anônimo), mas esse volume morre junto com o container — por isso a documentação
usa volume nomeado.

### Interface

`tests/manual/verifica_ui.py` abre a tela no Chrome já instalado (headless, via
DevTools Protocol), espera o Angular renderizar e executa o fluxo do usuário:
clica numa sequência, cadastra outra pelo formulário e repete o cadastro para ver
o aviso de duplicata.

```
$ .venv/bin/python tests/manual/verifica_ui.py http://127.0.0.1:5000/#/porsequencia
{
  "renderizou": true,
  "catalogoInicial": ["Sequência de Bm", "Sequência de C", "Sequência Em",
                      "Sequência de C (Samba)", "Sequência de Gm",
                      "Sequência de C (Samba cont.)"],
  "achouResultados": true,
  "aoClicar": {"titulo": "Encontrei essas músicas", "selecionada": "Sequência Em",
               "musicas": 4, "primeira": "Inútil"},
  "aposCadastro": {"criou": true, "total": 7, "entrada": "Dm - E7 - Am",
                   "selecionada": "Dm - E7 - Am", "musicas": 9, "erro": ""},
  "aposDuplicata": {"avisouDuplicata": true,
                    "aviso": "Essa sequência já está no catálogo.",
                    "voltouResultados": true, "musicas": 9, "total": 7,
                    "inputLimpo": true}
}

UI OK
```

O clique em "Sequência Em" devolve exatamente as 4 músicas da baseline — o mesmo
número que `tests/test_regressao.py` verifica por HTTP, agora conferido na tela.
O script exige `pip install websocket-client` e um banco sem a sequência de teste
(ele não apaga cadastro; use um `CIFRAME_DB` temporário).

## O que ficou de fora

- **Corrida real de duas conexões simultâneas.** O caminho de exceção
  (`sqlite3.IntegrityError` → 409) é testado com um `por_chave` que "não acha" na
  primeira chamada, não com duas threads de verdade. O comportamento do SQLite
  com `UNIQUE` é o mesmo, mas a simultaneidade em si não está sob teste.
- **Concorrência do gunicorn / p95.** O workaround de matching em memória foi
  medido no caminho de pesquisa manual, não em teste automatizado de carga. Não
  há teste de performance nem de múltiplos workers.
- **Endpoints pré-existentes.** `/search`, `/musicas`, `/acordes` e
  `/musica/<id>` não ganharam teste: eles já existiam sem teste e não foram
  tocados. As dívidas pré-existentes conhecidas (primeira linha do CSV
  descartada, `replace('NA','')` em títulos, ordem dependente de
  `PYTHONHASHSEED`, `/musica/<id>` inexistente devolvendo 500) continuam abertas
  e estão descritas em `01-research.md`.
- **JavaScript.** Não há teste automatizado do controller Angular — a verificação
  é o script de UI acima, que é manual (não roda em CI, depende do Chrome
  instalado na máquina).
- **Autenticação e abuso.** Não existe login nem rate limit por decisão de escopo
  (ver `02-proposal.md`), então não há teste de autorização nem de cadastro em
  massa. O único guardrail testado é a validação de entrada (2–12 acordes do
  vocabulário, nome ≤ 80).
- **Edição e remoção.** Fora de escopo: não há `PUT`/`DELETE`, e por isso não há
  teste de update, nem de unicidade na edição.
