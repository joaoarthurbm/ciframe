# Tarefa: Sequências de Acordes Customizadas — deciframe

## Contexto

Vimos em sala de aula que os princípios de engenharia é que são fundamentais, independente da tecnologia. Então vamos focar em exercitar nossas habilidades de engenheiros através dos workflows que apresentei em sala de aula.

Como disse, temos 3 bons candidatos: o RePPIT, o do Matt Pocock (o que mais uso até agora) e o /pstack da @poteto.

Vamos começar com o RePPIT por dois motivos: é um framework que está alinhado com o que a gente vem discutindo e, principalmente, há uma implementação dele que ainda é incipiente. 

A ideia é usarmos como está agora e tentarmos sugerir mudanças nos comandos que ele definiu aqui: (https://github.com/levelup-labs-ai/reppit-framework/tree/main/commands)

# A tarefa

Há muito tempo atrás, eu fiz o deciframe, um app em que você lista os acordes que você sabe tocar e ele minera músicas do cifraclub para mostrar quais você pode já sabe tocar com os acordes que você apontou. Também lista algumas músicas que, se você aprender alguns acordes a mais, você saberá tocar. Veja [README.md](../../../README.md) e [AGENTS.md](../../../AGENTS.md) na raiz do projeto para a stack e as
convenções do backend antes de começar.

Hoje, a busca por "sequência famosa" (`GET /similares?sequencia=...`) só
reconhece 6 sequências *hardcoded* no backend (`main.py`), e o
frontend (`#/porsequencia`) mostra apenas 4 delas, também hardcoded em
JavaScript. Essas sequências vêm de uma tag pré-computada no CSV
(`SEQ_FAMOSA`). Não existe nenhuma lógica que calcule, em tempo real, se uma
sequência de acordes aparece em uma música.

## O que você vai construir

Uma feature que permite a **qualquer visitante cadastrar uma nova sequência de
acordes famosa** e **buscar músicas por ela**, exatamente do mesmo jeito que já
funciona hoje para as 6 sequências pré-existentes. O catálogo de sequências
passa a ser persistido em um **banco de dados** (não mais no CSV), para
sobreviver a reinícios do servidor e poder crescer sem precisar de um novo
deploy.

Esta é uma tarefa **full-stack**: ela toca o backend (Flask), a persistência
(novo: um banco de dados) e o frontend (AngularJS).

## O que é obrigatório (requisitos funcionais)

- Qualquer pessoa pode cadastrar uma nova sequência de acordes (lista ordenada
  de acordes). Sem login. Catálogo aberto e anônimo.
- Qualquer sequência cadastrada (as 6 originais + as novas) pode ser usada para
  buscar músicas, com os mesmos resultados esperados de hoje para as 6
  originais.
- O catálogo de sequências é persistido em um banco de dados. Não volta a ser
  perdido ao reiniciar o container.
- A página `#/porsequencia` do frontend reflete o catálogo real (vindo do
  backend, não mais hardcoded em JS) e permite cadastrar uma sequência nova.

## O que está fixo (não é decisão sua)

- É obrigado o uso do `opencode` e do modelo `BigPickle`.
- O catálogo de **músicas e gêneros continua vindo do CSV**, carregado em
  memória como hoje. Não migre `musicas`/`generos` para o banco. Só o
  catálogo de sequências precisa de persistência.
- A aplicação continua rodando via o `Dockerfile` único e local-only já
  documentado em `docs/adr/0001-local-only-docker-deploy.md` (container único,
  sem serviços externos adicionais).
- As 6 sequências hoje hardcoded precisam continuar produzindo os mesmos
  resultados de busca depois da sua mudança. É o seu critério para teste de regressão.
- Endpoints continuam retornando `json.dumps(...)` como string, não `jsonify`.

## O que é decisão sua (faz parte do trabalho)

- O **algoritmo de matching**: o que define que uma sequência "aparece" em uma
  música.
- A **tecnologia de banco de dados** (desde que caiba no container Docker
  único e local).
- O formato exato da API nova, o esquema do banco, e os detalhes de validação
  (ex.: o que fazer com sequências duplicadas).

## Fluxo de trabalho obrigatório

Este exercício avalia principalmente o **processo**, não só o resultado final.
Siga as 5 fases usando [este ferramental](https://github.com/levelup-labs-ai/reppit-framework/tree/main/commands), nesta ordem, e documente cada uma antes de passar para a próxima:

1. **Pesquisa** — investigue as perguntas em
   [`01-research.md`](01-research.md) com evidência real, não suposição.
2. **Proposta** — decida e justifique a abordagem em
   [`02-proposal.md`](02-proposal.md). Inclua uma ADR em
   [`docs/adr/0002-persist-custom-sequences.md`](../../adr/0002-persist-custom-sequences.md)
   documentando a decisão de introduzir persistência, no mesmo estilo de
   `0001-local-only-docker-deploy.md`.
3. **Plano** — decomponha a proposta em passos executáveis em
   [`03-plan.md`](03-plan.md).
4. **Implementação** — siga o plano. Se mudar de ideia no meio do caminho,
   volte e atualize o plano antes de continuar (não deixe o plano
   desatualizado).
5. **Testes** — documente cobertura e o resultado do teste de regressão
   obrigatório em [`04-test-report.md`](04-test-report.md).


### O que você vai entregar

- Os templates de cada fase já existem no diretório docs/features/sequencias-customizadas. Preencha-os (e apague as
instruções em bloco de citação de cada um antes de entregar).

- Um vídeo/gif demonstrando a feature funcionando no browser.

- O arquivo da sessão.

Suba tudo para o seu fork e compartilhe o link no form. 

## Como vai ser corrigido?

| Fase | Peso |
|---|---|
| Pesquisa | 15% |
| Proposta (+ ADR) | 20% |
| Plano | 20% |
| Implementação | 25% |
| Testes | 20% |

A nota de cada fase reflete a honestidade do raciocínio documentado,
não só se a feature "funciona" no final.
