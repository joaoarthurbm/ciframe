# Relatório de testes — Sequências de Acordes Customizadas

Data da execução final: 2026-11-02.

Ambiente: Python 3.10.12, Flask 3.1.3, Docker 29.3.0, Google Chrome headless.
O código Python de produção não foi alterado para a correção de persistência
(as mudanças foram em `Dockerfile`, `docker-compose.yml` e documentação). A suíte
foi executada em um virtualenv limpo (`/tmp/opencode/deciframe-venv`) com
dependências de `requirements.txt` instaladas (o interpretador do sistema não
tinha Flask).

## Cobertura

A suíte tem **48 testes**, todos com `unittest` e o test client do Flask:

| Arquivo | Testes | O que verifica |
|---|---:|---|
| `tests/test_matching.py` | 10 | ocorrência contígua e ordenada, limites de token (`C` não casa em `C7`), não contiguidade, caixa, cifra vazia, índice, ordenação por popularidade/id e cache |
| `tests/test_sequencias_store.py` | 18 | schema/`user_version`, seed idempotente, nomes das 6, criação/leitura, duplicata case-insensitive, duplicata de builtin, JSON de acordes e validações de nome/acordes |
| `tests/test_sequencias_api.py` | 13 | catálogo, POST 201, busca por id, 400/409/413, JSON malformado, id desconhecido, builtin por id igual ao legado, filtro de gênero, precedência de parâmetros e 10 POSTs concorrentes |
| `tests/test_regression_sequencias.py` | 3 | as 6 contra o fixture da Fase 0 pelos caminhos `?sequencia=` e `?sequencia_id=`, além das contagens |
| `tests/test_persistence.py` | 4 | persistência em nova conexão/startup, seed que não sobrescreve builtins, versão futura do schema e `SEQUENCES_DB` |

Os testes usam um banco temporário por processo (`tests/helpers.py` define
`SEQUENCES_DB` antes de importar `main`) e recriam o catálogo em cada teste de API.

## Teste de regressão obrigatório

`tests/capture_baseline.py` capturou o comportamento anterior à integração com
`main.app.test_client()` e `?sequencia=`, gerando
`tests/fixtures/sequencias_baseline.json` com todas as páginas. O total é de **514
ids**: BmGDA 199, CGAmF 296, EmG 4, CA7DmG7 5, GmF 7 e CC7FFm 3.

A regressão compara o conjunto de ids e a contagem total, não a ordem página a
página. Motivo: `generos` é construído a partir de um `set` (`main.py`), então a
ordem relativa dos gêneros já variava entre processos antes desta feature; comparar
páginas exatas produziria falso negativo. O caminho novo `?sequencia_id=` é comparado
com o legado no mesmo processo e também reproduz exatamente as páginas. Os dois
testes passam.

A contagem de sanidade do matching novo ficou em **3.110** músicas para Em–G com
limites de token. A pesquisa registra 3.704 para busca por substring, que também casa
prefixos como `G5`; a implementação não usa essa variante. A decisão e a nota estão em
`01-research.md`, `02-proposal.md` e `03-plan.md`.

## Comandos executados na validação final

Os testes automatizados foram executados a partir da raiz do repositório, com
as dependências instaladas em um virtualenv limpo:

```
$ python3 -m venv /tmp/opencode/deciframe-venv
$ /tmp/opencode/deciframe-venv/bin/pip install -q -r requirements.txt
$ /tmp/opencode/deciframe-venv/bin/python -m unittest discover -s tests -v
```

Resultado observado na reexecução após a correção de persistência (últimas
linhas; o virtualenv foi recriado porque `/tmp` tinha sido limpo entre as
execuções):

```
test_rejects_unknown_chord (test_sequencias_store.ValidationTests) ... ok
----------------------------------------------------------------------
Ran 48 tests in 3.684s

OK
```

A primeira tentativa, usando o `python3` do sistema, terminou com 34 testes
executados e 2 erros de importação (`ModuleNotFoundError: No module named
'flask'`). Não era falha da feature: o ambiente não tinha as dependências do
projeto. Após criar o virtualenv e instalar `requirements.txt`, a suíte completa
passou.

## Teste de regressão: evidência

O comando acima executa `tests/test_regression_sequencias.py` contra
`tests/fixtures/sequencias_baseline.json`. Os três testes passaram:

- `test_all_six_legacy_paths_match_baseline`: para cada uma das 6 sequências,
  percorre todas as páginas de `?sequencia=<chave>` e compara o conjunto de
  `id_unico_musica` com o fixture capturado antes da feature.
- `test_all_six_id_paths_match_baseline`: repete a comparação usando o caminho
  novo `?sequencia_id=<id>` e confirma que ele reproduz o legado.
- `test_counts_match_baseline`: confirma as contagens totais do fixture:
  BmGDA 199, CGAmF 296, EmG 4, CA7DmG7 5, GmF 7 e CC7FFm 3 (514 no total).

A comparação é por conjunto e contagem, não por ordem de página, porque
`generos` vem de um `set` em `main.py` e a ordem relativa entre gêneros já
variava entre processos antes desta feature.

## Falhas identificadas e correções durante o desenvolvimento

- **Em–G: 3.704 versus 3.110.** A primeira medição do matching contíguo usava
  substring simples (`"em;g" in cifra`) e casava prefixos como `G5`, resultando
  em 3.704 músicas. A implementação final passou a delimitar a sequência com
  `;` nas duas pontas, exigindo limites de token; a contagem correta ficou em
  **3.110**. A pesquisa e a proposta foram corrigidas para registrar que 3.704
  era a variante de substring.
- **Teste de concorrência com dados duplicados.** A primeira versão do teste
  disparava 10 POSTs com a mesma lista de acordes, então recebia 409 em vez de
  201. O teste foi corrigido para usar prefixos distintos da mesma base
  (`base[:index + 1]`), exercitando 10 inserções concorrentes reais.
- **Ordem não determinística nos testes de regressão.** Comparar páginas
  exatas produzia falso negativo por causa da ordem de `generos`; os testes
  passaram a comparar conjunto de ids e contagem total, mantendo a ordem apenas
  para inspeção do fixture.

## Incidente de persistência e correção (2026-11-02)

### Causa raiz

Os dois containers `ciframe` encontrados no host foram criados sem volume:

```
$ docker inspect lucid_bell --format '{{json .Mounts}}'
[]
$ docker inspect lucid_bell --format '{{json .HostConfig.Binds}}'
null
$ docker inspect clever_almeida --format '{{json .Mounts}}'
[]
$ docker volume inspect deciframe-instance
Error response from daemon: get deciframe-instance: no such volume
```

O histórico do shell mostrou que o comando usado foi
`docker run -p 8080:8080 ciframe`, sem `-v`. O banco existia apenas na camada
gravável do container, confirmado por `docker diff`:

```
$ docker diff lucid_bell | grep instance
A /app/instance
A /app/instance/sequences.db
```

A aplicação **não** recria nem sobrescreve o banco no startup: `init_db` usa
`CREATE TABLE IF NOT EXISTS` e o seed usa `INSERT OR IGNORE`, sem `DROP` ou
`DELETE`. Também foi verificado no container antigo sem volume: depois de
`docker stop` + `docker start`, ele continuou com **8 registros** e as mesmas 2
sequências customizadas. Parar e iniciar o mesmo container preserva a camada
gravável; remover o container e executar outro `docker run` sem volume cria uma
camada nova e vazia. O container antigo não foi removido justamente para não
destruir os dados recuperáveis. A causa raiz foi, portanto, a execução sem volume
nomeado, não uma rotina de inicialização destrutiva.

### Dados recuperáveis (não apagados)

Antes de qualquer operação destrutiva, os bancos dos containers existentes foram
inspecionados em modo somente leitura. Havia dados recuperáveis:

- `clever_almeida` (parado): 8 registros, sendo 6 builtins e 2 customizados
  (`BmGDF` e `Alexandre Sequencia`).
- `lucid_bell` (em execução): 8 registros na verificação final, sendo 6 builtins
  e 2 customizados (`Sequencia de alexandre` e `Sequencia teste`). O container
  continuou em uso durante a sessão; no primeiro diagnóstico ele tinha 7
  registros e 1 customizado.

O banco do container parado foi copiado com `docker cp`; o do container em
execução foi copiado com a API `sqlite3.backup` (snapshot consistente) e ambos
foram salvos em `instance/recovery/` (ignorado pelo Git) e em
`/tmp/opencode/ciframe-recovery/`. Nenhum container, volume ou banco existente
foi removido.

### Correção aplicada

- `docker-compose.yml`: um único serviço, volume nomeado
  `deciframe-instance:/app/instance`, `restart: unless-stopped` e porta 8080.
- `Dockerfile`: `VOLUME ["/app/instance"]` como proteção adicional para
  `docker run` sem `-v` (sobrevive a `stop/start`; remoção/recriação exige o
  volume nomeado).
- `README.md` e `AGENTS.md`: caminho padrão via Compose, equivalente com
  `docker run`, verificação do mount, recuperação de containers antigos e aviso
  de que `docker compose down -v` apaga o catálogo.
- ADR 0002 e proposta atualizados com a decisão e o incidente.

### Teste real com volume nomeado

Imagem de teste construída sem substituir a imagem em uso:

```
$ docker build -t ciframe-persist-test .
...
naming to docker.io/library/ciframe-persist-test done
```

Container e volume isolados (porta 18080 para não conflitar com o container do
usuário na 8080):

```
$ docker run -d --name deciframe-persist-ctr-20261102 \
    -p 18080:8080 \
    -v deciframe-persist-test-20261102:/app/instance \
    --restart unless-stopped \
    ciframe-persist-test
```

Mount observado:

```
$ docker inspect deciframe-persist-ctr-20261102 --format '{{json .Mounts}}'
[{"Type":"volume","Name":"deciframe-persist-test-20261102",
  "Source":"/var/lib/docker/volumes/deciframe-persist-test-20261102/_data",
  "Destination":"/app/instance","Driver":"local","Mode":"z","RW":true,
  "Propagation":""}]
```

Criação de uma sequência customizada:

```
$ curl -s -X POST http://localhost:18080/sequencias \
    -H 'Content-Type: application/json' \
    -d '{"nome":"Persistencia Teste 2026-11-02",
         "acordes":["D","A","Bm","G"]}'
HTTP/1.1 201 CREATED
{"id": "43cc4cf66ca843efbec93a126cafb40d", "nome": "Persistencia Teste 2026-11-02",
 "acordes": ["D", "A", "Bm", "G"], "origem": "custom"}
```

Catálogo e banco depois do POST: **7 registros**, sendo **6 builtins + 1
customizado**. `GET /generos` continuou devolvendo **52 gêneros**, confirmando que
montar `/app/instance` não esconde o CSV em `/app/data`.

Depois de `docker stop` + `docker start` no mesmo container:

```
count 7
custom [('43cc4cf66ca843efbec93a126cafb40d', 'Persistencia Teste 2026-11-02')]
total 7
builtin 6
custom 1
```

Depois de `docker rm -f` e recriar o container com o **mesmo volume**:

```
count 7
custom [('43cc4cf66ca843efbec93a126cafb40d', 'Persistencia Teste 2026-11-02')]
total 7
builtin 6
custom 1
user_version 1
```

O seed foi idempotente: as 6 continuaram com os mesmos ids e nenhuma sequência
customizada foi apagada ou duplicada. A política de reinício observada foi
`{"Name":"unless-stopped"}`; a declaração de volume da imagem foi
`{"/app/instance":{}}`.

### Teste do caminho Compose

O `docker-compose.yml` foi validado com `docker compose config` (um serviço,
porta 8080, volume nomeado e `restart: unless-stopped`). Para não ocupar a porta
do container do usuário, o comportamento de parar/recriar foi exercitado em um
projeto Compose isolado, com o mesmo volume de teste e porta 18081:

```
$ docker compose -p deciframe-compose-test \
    -f /tmp/opencode/deciframe-compose-test.yml up -d
count 7
custom [('43cc4cf66ca843efbec93a126cafb40d', 'Persistencia Teste 2026-11-02')]

$ docker compose -p deciframe-compose-test \
    -f /tmp/opencode/deciframe-compose-test.yml down
# remove o container e a rede, mas não o volume

$ docker compose -p deciframe-compose-test \
    -f /tmp/opencode/deciframe-compose-test.yml up -d
count 7
custom [('43cc4cf66ca843efbec93a126cafb40d', 'Persistencia Teste 2026-11-02')]
```

O volume permaneceu em
`/var/lib/docker/volumes/deciframe-persist-test-20261102/_data`, fora da camada
gravável do container, que é o que o mantém após o reinício do host. Não foi
possível reiniciar fisicamente a máquina no ambiente de teste sem interromper
outros containers; a persistência no nível do host foi validada pelo volume
nomeado e pela política `unless-stopped`, e a remoção/recriação do container foi
testada de fato. O container `deciframe-persist-ctr-20261102` foi deixado parado e
o volume de teste foi mantido (não removido) para auditoria; o container
temporário do projeto Compose foi removido sem remover o volume. Os
containers/volumes antigos do usuário permanecem intactos.

## Frontend

Verificado no Chrome headless via CDP em `#/porsequencia`:

- as 6 sequências do catálogo aparecem, incluindo EmG e CA7DmG7;
- o formulário carregou o typeahead de acordes, aceitou nome e quatro chips
  (D–A–Bm–G) e habilitou o botão;
- o POST atualizou a lista para 7 itens e disparou a busca, retornando 100 cartões;
- o filtro MPB reduziu o resultado para 9 músicas, todas MPB;
- o único erro de console foi o `og:image` externo
  `http://deciframe.com/static/assets/img/deciframe.png` respondendo vazio; não é
  recurso da aplicação.

### Alinhamento do catálogo (2026-11-02)

**Diagnóstico.** No template anterior, o nome ficava em um `<p>` fora do
`.acordes-container`, e o container só tinha filhos `float: left`. A medição no
Chrome headless, antes da correção, mostrou `.acordes-container` com
`height: 0` e o seguinte padrão nos 6 itens:

```
item 0: nome 189.8–209.8 | hexágonos 211.8–267.7
item 1: nome 211.8–231.8 | hexágonos 267.7–323.7
item 2: nome 267.7–307.7 | hexágonos 323.7–379.6
...
```

O nome de cada item começava exatamente no topo dos hexágonos do item anterior.
Por isso o último nome parecia pertencer à sequência anterior e a última
sequência parecia não ter identificação.

**Correção.** Cada `ng-repeat` agora é um `.sequencia-catalogo` que contém o
nome (`.sequencia-catalogo-nome`) e a fileira de acordes. O wrapper usa Flexbox em
coluna; a fileira usa Flexbox em linha com `flex-wrap`, `justify-content: center`
e `max-width: 100%`. O `float` interno do hexágono foi mantido e passou a ser
contido pelo item Flexbox, preservando o SVG, as cores, a tipografia e o formato
dos acordes. Não houve alteração no controller, no backend, nos contratos JSON ou
na persistência.

**Evidência no Chrome headless (CDP).** Para cobrir também os casos de 1 e 8
acordes e um nome com 80 caracteres, duas sequências de teste foram inseridas
apenas no escopo Angular em memória; nada foi salvo no banco nem enviado à API.
Depois da correção:

| Cenário | Resultado |
|---|---|
| Desktop 1200×1461, 8 itens (6 builtins + 2 em memória) | nenhuma sobreposição entre itens; nome e fileira dentro do wrapper em todos |
| 1 acorde | uma linha, nome acima e alinhado; sem sobreposição |
| 8 acordes | duas linhas de hexágonos no desktop; sem sobreposição |
| Nome de 80 caracteres | quebrou em 2 linhas no desktop e 3 no viewport de 320px, sem overflow horizontal |
| Viewport estreito 320×900 | wrapper e fileira com 290px, 8 acordes em 2 linhas, `documentWidth = 320`, sem overflow |
| Intervalos após a correção | nome 0 em 189.8–209.8, hexágonos em 211.8–267.7; nome 1 em 277.7–297.7, hexágonos em 299.7–355.7 |

A suíte completa foi reexecutada depois da alteração:

```
Ran 48 tests in 3.539s

OK
```

Também foi executado `git diff --check`, sem erros de whitespace. A correção é
visual e não alterou o comportamento de cadastro, busca, persistência ou as
respostas `json.dumps` (`Content-Type: text/html`).

## Performance

Medições locais, sem outros processos pesados em execução:

| Medida | Resultado |
|---|---:|
| carga do CSV | 1,89 s |
| banco/seed | 0,02 s |
| índice de cifras | 0,38 s |
| startup interno (CSV + banco + índice) | ~2,3 s |
| startup do processo (`/usr/bin/time`) | 2,6–3,1 s, variando com carga |
| RSS do processo após carga | ~290 MB |
| índice de cifras (`tracemalloc`) | 15,7 MB |
| POST de sequência | 0,017 s |
| primeira busca customizada (cache frio) | 0,045 s |
| busca seguinte (cache quente) | 0,004 s |
| `GET /sequencias` | 0,001 s |

O startup interno e a primeira busca ficaram dentro dos limites do plano; o tempo
total do processo fica na fronteira de 3 s em execuções com o ambiente carregado.

## Como rodar

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Para regerar o fixture (apenas antes de uma mudança de comportamento legado):

```
python tests/capture_baseline.py
```

## O que ficou de fora

- Edição/exclusão de sequências, login, moderação, rate limiting e invalidação de
  cache: fora do escopo desta fase.
- Múltiplos workers/HA: o desenho atual assume o container local com um worker
  gunicorn; concorrência foi testada dentro desse limite.
- Teste de carga com catálogo grande, restore real de backup com `sqlite3 .backup` e
  matriz de navegadores/dispositivos.
- Reinício físico do host não foi executado no ambiente de teste para não
  interromper outros containers; a persistência foi validada por volume nomeado
  fora da camada do container, remoção/recriação e `restart: unless-stopped`.
- O container `deciframe-persist-ctr-20261102` (parado) e o volume de teste
  (`deciframe-persist-test-20261102`) foram mantidos para auditoria; o container
  temporário do projeto Compose foi removido sem apagar o volume. Os
  containers/volumes antigos do usuário não foram removidos.
- A ordem relativa entre gêneros no caminho legado continua não determinística entre
  processos; os testes de regressão cobrem conjunto e contagem, não a ordem.
- O `og:image` externo do `index.html` continua falhando no ambiente headless; não
  tem relação com esta feature.
