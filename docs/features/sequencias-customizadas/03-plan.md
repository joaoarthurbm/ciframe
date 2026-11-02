# Plano — Sequências de Acordes Customizadas

> Fase **P** do RePPIT (`commands/make-plan.md`): nenhuma mudança de código nesta
> fase, só o roteiro. A ordem abaixo é a ordem de execução e **cada passo é um
> commit** — a mensagem cita o passo (`passo 3/10: ...`). Se um passo se revelar
> errado no meio, o commit seguinte corrige **este arquivo antes** do código.

## Decisões estruturais que o plano assume

- **Backend continua single-file**: todo o código novo (schema, seed, conexão,
  normalização, matching e endpoints) vive em `main.py`. `musica.py` **não é
  tocado** — o matching não vira método de `Musica`.
- **Consequência aceita**: testar o matching exige `import main`, e portanto o
  parse do CSV (~1,2 s, medido), uma vez por sessão de `pytest` (fixture de
  escopo `session`). Não há módulo isolável por decisão de arquitetura.
- **Fonte de verdade do dado**: `musica.cifra` (ordenada, com repetições), nunca
  `musica.acordes`.
- **Sem schema de migração**: uma tabela, criada com `CREATE TABLE IF NOT EXISTS`
  no import. Não há versão anterior do banco a migrar.

## Passos

1. [x] **Baseline de regressão, antes de qualquer mudança.** Criar
   `requirements-dev.txt` (`pytest`, `pytest-cov`, `flask`, `gunicorn` já em
   `requirements.txt`), `.venv` local, `tests/conftest.py` com fixture de sessão
   que importa `main` e expõe o test client. Gerar
   `tests/fixtures/sequencias_legado.json` = `{chave: [id_unico_musica
   ordenados]}` para as 6, **executando o código atual**, e commitar. Este
   arquivo é a única coisa que prova "igual a antes" depois; por isso vem antes
   de tudo.
2. [x] **Caminho e conexão do banco.** `CIFRAME_DB` (default
   `/var/lib/ciframe/ciframe.db`), `db_path()`, `conexao()` (context manager:
   conexão por chamada, `row_factory = sqlite3.Row`, commit no fim),
   `prepara_diretorio_db()` com `os.makedirs(..., exist_ok=True)` e checagem de
   escrita. O caminho é resolvido a cada conexão; a checagem de gravabilidade
   acontece **no import**, terminando o processo com mensagem explícita — falha
   no boot, não no primeiro `POST`.
3. [x] **Schema + seed idempotente.** `CREATE TABLE IF NOT EXISTS sequencias`,
   `SEQUENCIAS_LEGADO` em `main.py` (substitui o `dict sequencias` de
   `main.py:40-45`, com os nomes de
   `data/mapeamento_sequencias_famosas.txt`), `normalizar_chave(acordes)` e
   `seed()` com `INSERT OR IGNORE` por `chave`. Ids 1..6 atribuídos pelo banco;
   nenhum id escrito à mão. Chamada no import.
4. [x] **Matching em tempo real.** `musica_contem_sequencia(musica, chave)` =
   as duas condições (contígua + vocabulário contido, `casefold`), e
   `get_similares_por_chave(chave, generos_key)` substituindo
   `get_similares_por_sequencia` (`main.py:203-223`). `?sequencia=` passa a
   resolver a chave no banco. Verificar à mão contra a fixture do passo 1 antes
   de commitar.
5. [x] **`GET /sequencias`.** Lista ordenada por `id`, shape
   `{id, nome, acordes, chave, criado_em}`; `acordes` desserializado do JSON.
6. [x] **`POST /sequencias`.** Parse do corpo, validação (2–12 acordes,
   vocabulário, nome ≤ 80, nome derivado quando ausente), normalização, `201`;
   `400` com `campo`/`acorde`; `409` com `id` e `chave` do existente. Corpo
   sempre `json.dumps(...)`, nunca `jsonify`.
7. [x] **`sequencia_id` em `/similares`.** Precedência `acordes` >
   `id_unico_musica` > `sequencia_id` > `sequencia`; `404` para id inexistente;
   mesmo shape de 9 campos (sem `diferenca`, preservando o `ng-hide` de
   `sequencia.html:42-43`).
8. [x] **Frontend.** `sequencia.js`: catálogo via `GET /sequencias`, `temAcorde`
   comparando string (não identidade de objeto), busca por `sequencia_id`,
   formulário inline com parse de `,`/`;`/espaço, tratamento de `201` (seleciona
   e busca) e `409` (seleciona a existente + aviso). `sequencia.html`: bloco do
   formulário e mensagem de erro.
9. [x] **Deploy e documentação.** `VOLUME /var/lib/ciframe` no `Dockerfile`;
   `docker run -p 8080:8080 -v ciframe-data:/var/lib/ciframe ciframe` no
   `README.md` e no `AGENTS.md`, com uma frase dizendo que sem o `-v` os
   cadastros morrem com o container. `AGENTS.md` ganha também a nota de que
   `main.py` agora tem estado gravável externo ao CSV.
10. [x] **Relatório de testes (fase 5/5).** Preencher `04-test-report.md` com a
    saída de `pytest -q`, o teste manual de persistência no Docker (cadastrar →
    `docker rm` → `docker run` novo) e o que ficou de fora. Escrever também o
    roteiro do vídeo em `docs/features/sequencias-customizadas/roteiro-video.md`.

## Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `main.py` | `CIFRAME_DB`, `db()`, schema, seed, `normalizar_chave`, `musica_contem_sequencia`, `get_similares_por_chave`, `GET/POST /sequencias`, `sequencia_id` em `/similares` |
| `musica.py` | **não muda** (decisão explícita: matching fica em `main.py`) |
| `Dockerfile` | `VOLUME /var/lib/ciframe` |
| `README.md` | comando `docker run` com `-v` + nota sobre persistência |
| `AGENTS.md` | idem, e a nota de que o catálogo de sequências deixou de vir do CSV |
| `static/assets/js/controllers/sequencia.js` | catálogo dinâmico, `temAcorde` por string, POST, `sequencia_id` |
| `static/templates/sequencia.html` | formulário inline + área de erro |
| `requirements-dev.txt` | **novo**: `pytest`, `pytest-cov` |
| `tests/conftest.py` | **novo**: fixture de sessão (importa `main`) + test client + DB em `tmp_path` |
| `tests/fixtures/sequencias_legado.json` | **novo**: baseline gerada do código atual (passo 1) |
| `tests/test_matching.py`, `test_db.py`, `test_api.py`, `test_regressao.py` | **novos** |
| `docs/adr/0002-persist-custom-sequences.md` | já escrito (fase 2) |
| `data/top/dataset_final.csv` | **não muda** (proibido pelo enunciado; `SEQ_FAMOSA` fica intacta e deixa de ser lida) |

## Riscos e mitigação

| risco | como percebo | o que faço |
|---|---|---|
| A normalização nova divergir em algum detalhe do script offline (`casefold` vs `lower`, token vazio, `|`) e mudar resultados | fixture do passo 1 falha no `test_regressao` | comparar antes de commitar o passo 4; a diferença aparece como `id` a mais ou a menos, não como contagem |
| `docker run` sem `-v` e o cadastro "sumir" na demonstração | teste de persistência do passo 10 falha | falha explícita no boot se `CIFRAME_DB` não for gravável + nota no README; o roteiro do vídeo inclui o reinício |
| `CIFRAME_DB` lida no import impedir o teste de isolar o banco | teste escrever no banco de dev | `conftest.py` define a env var **antes** de importar `main`, com `tmp_path`; o banco real nunca é aberto pela suíte |
| 45 ms por requisição × concorrência no worker único (`sync`) enfileirar | p95 alto no teste manual | medir com requisições repetidas; se p95 passar de ~1 s, registrar como decisão futura (índice invertido/cache), não otimizar por reflexo |
| `POST` a partir de origem diferente do servidor (abrir o HTML por `file://`) falhar no preflight | `$http` com erro CORS na UI | a app serve o próprio frontend; se acontecer, registrar como dívida — não abrir `Access-Control-Allow-Methods` sem necessidade |
| `temAcorde` por string marcar acorde errado quando a música/seleção tem repetições | destaque visual incorreto no vídeo | comparar `acorde` a acorde sobre `vm.minhaSequencia.acordes`, que é o que o template percorre |
| Alterar `?sequencia=` para consultar o banco e quebrar o contrato de `[]`/`200` | `curl` devolvendo 404 onde antes era `[]` | o caminho legado mantém o early-return de `[]`; 404 é exclusivo de `sequencia_id` |
| Seed duplicar as 6 a cada restart | `GET /sequencias` com mais de 6 na primeira subida | `INSERT OR IGNORE` sobre `chave TEXT UNIQUE`, verificado 2× seguidas |

## Definição de pronto

A feature está implementada quando **todos** os itens abaixo passarem, na ordem:

1. `docker build -t ciframe .` e `docker run -p 8080:8080 -v ciframe-data:/var/lib/ciframe ciframe` sobem, e `curl localhost:8080/generos` devolve o array de gêneros.
2. `GET /sequencias` devolve exatamente 6 registros na primeira subida, com nomes legíveis.
3. `POST /sequencias` com `{"acordes":["Em","G"]}` devolve `201` e o registro aparece no `GET` seguinte.
4. O mesmo `POST` repetido devolve `409` com o `id` do existente, e o catálogo continua com 6 (não 7, não 8).
5. `POST` com acorde inexistente (`{"acordes":["Em","Xyz"]}`) devolve `400` citando `Xyz`.
6. Para cada uma das 6 chaves, `?sequencia=<chave>` devolve **conjunto** de `id_unico_musica` idêntico ao da fixture do passo 1.
7. `?sequencia_id=1` devolve o mesmo resultado que `?sequencia=BmGDA`; `?sequencia_id=999` devolve `404`.
8. Na UI: cadastrar uma sequência nova a adiciona à lista, seleciona e dispara a busca na mesma ação; `EmG` e `CA7DmG7` aparecem (hoje são inalcançáveis).
9. Persistência real: cadastrar → `docker rm -f` → `docker run` novo → a sequência cadastrada continua no catálogo.
10. `pytest -q` verde, e `04-test-report.md` com a saída colada e as lacunas declaradas.
