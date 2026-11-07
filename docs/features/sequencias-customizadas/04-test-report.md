# Relatório de testes — Sequências de Acordes Customizadas

## Cobertura

Testes automatizados em `tests/test_sequencias_customizadas.py` (unittest), executados com banco SQLite temporário (`SEQUENCIAS_DB_PATH`).

| Teste | O que verifica |
|---|---|
| `test_usa_banco_temporario` | Usa `SEQUENCIAS_DB_PATH` fora de `data/sequencias.db` |
| `test_lista_catalogo_com_as_seis_originais` | `GET /sequencias` retorna as 6 originais com `origem: original` e acordes corretos |
| `test_regressao_das_seis_sequencias_originais` | Para cada original, resultado via `/similares?sequencia=` igual ao via `get_similares_por_sequencia` |
| `test_forma_com_virgulas_das_originais_retorna_o_mesmo` | Forma `A,B,C,...` das originais preserva o mesmo resultado |
| `test_agrupamento_ambiguo_nao_cai_no_catalogo_original` | Forma ambígua (ex. `E,mG`) não é redirecionada para o caminho original |
| `test_cadastro_listagem_e_busca_customizada` | `POST /sequencias`, listagem dinâmica e busca por vírgula/concatenado |
| `test_busca_customizada_encontra_musica_da_cifra` | `get_similares_por_sequencia_custom` encontra músicas usando `musica.cifra` (subsequência ordenada) |
| `test_duplicado_nao_cria_linha_redundante` | Duplicado não insere nova linha no banco |
| `test_duplicado_de_sequencia_original_e_rejeitado` | Tentativa de cadastrar sequência idêntica a uma original retorna `duplicado: true`, `origem: original`, sem gravar |
| `test_chaves_canonicas_nao_colidem` | `['A','C']` vs `['AC']` geram chaves distintas (`A C` e `AC`) |
| `test_normaliza_espacos_do_cadastro` | Espaços são removidos na normalização |
| `test_validacao_rejeita_entradas_invalidas` | Rejeita vazia, >32 acordes, acorde inválido/com >20 chars, tipo errado; sem inserções |
| `test_aceita_corpo_de_formulario` | Aceita `application/x-www-form-urlencoded` com `chords` separado por vírgulas |
| `test_compatibilidade_com_chave_legada_concatenada` | Lê registros antigos com `chords_key` concatenada |
| `test_persistencia_apos_reinicializacao_do_banco` | `init_db()` mantém dados; arquivo do banco é criado no caminho configurado (testado em diretório temporário) |
| `test_sequencia_vazia_retorna_lista` | `sequencia=` retorna `[]` |
| `test_sequencia_desconhecida_retorna_lista` | Sequência não cadastrada/sem correspondência retorna `[]` |

## Teste de regressão obrigatório

Verificado por `test_regressao_das_seis_sequencias_originais`: para `BmGDA`, `CGAmF`, `EmG`, `CA7DmG7`, `GmF`, `CC7FFm` os resultados de `GET /similares?sequencia=<chave>` foram comparados com `get_similares_por_sequencia` no mesmo processo. Valores obtidos: `BmGDA:100, CGAmF:100, EmG:4, CA7DmG7:5, GmF:7, CC7FFm:3`. Os caminhos hardcoded foram preservados (verificação também manual via smoke test).

## Como rodar

```bash
python -m unittest discover -s tests -v
```

Os testes configuram `SEQUENCIAS_DB_PATH` para um diretório temporário e limpam o banco entre testes; não modificam `data/sequencias.db`.

## Verificações manuais (curl/smoke)

- Smoke com `SEQUENCIAS_DB_PATH` temporário: `GET /sequencias` retorna 6 originais + cadastradas; `POST /sequencias` com `['Am','F','C','G']` cadastra com chave `Am F C G`; busca por `Am,F,C,G` e `AmFCG` retorna resultados; `POST` de original/duplicado retorna `duplicado: true` sem nova linha; entrada inválida retorna 400.
- Frontend: catálogo carregado via `GET /sequencias`, UI de cadastro adicionada, mensagem de erro no carregamento adicionada ao template. Verificação apenas estática (controller/template); não foi executado navegador neste ambiente.

## O que ficou de fora

- Teste automatizado completo no navegador (requer servidor estático/AngularJS + assets).
- Build/execução em Docker e teste com múltiplos workers gunicorn (lock SQLite) — não reproduzidos neste ambiente; `busy_timeout`/WAL e `timeout` de conexão foram adicionados.
- Match case-insensitive — proposta corrigida para case-sensitive (conforme notação dos acordes); normalização cobre apenas espaços/trim.
