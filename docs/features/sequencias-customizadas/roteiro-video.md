# Roteiro do vídeo — Sequências de Acordes Customizadas

Alvo: **3 a 4 minutos**, uma gravação só, sem edição. Se errar uma cena, refaça só
ela e corte na edição; não precisa acertar tudo de primeira.

O que a banca precisa ver, nesta ordem:

1. o limite de antes (catálogo fixo, sequências inalcançáveis);
2. o catálogo vindo do banco, com as 6 originais;
3. busca por `Em G` funcionando;
4. cadastro de uma sequência nova pela tela;
5. **o cadastro sobrevivendo a `docker rm` + `docker run` novo** — é o ponto que
   separa "tem persistência" de "parece que tem".

---

## 1. Preparo (fora do vídeo)

Rode tudo antes de apertar REC. O estado inicial precisa ser **6 sequências e
nenhuma cadastrada**:

```
docker rm -f ciframe-demo ciframe-demo2 2>/dev/null
docker volume rm ciframe-data 2>/dev/null
docker build -t ciframe .
docker run -d --name ciframe-demo -p 8080:8080 -v ciframe-data:/var/lib/ciframe ciframe
```

Confirme antes de abrir o navegador (tem que imprimir `6`):

```
curl -s localhost:8080/sequencias | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"
```

Abra `http://localhost:8080/#/porsequencia` e deixe a página já carregada.

**Tela:** navegador 1440×900 (é o tamanho que o layout espera), zoom 100%, barra
de favoritos escondida. Terminal com fonte 18 pt, ao lado do navegador — você vai
alternar entre os dois só na cena 6. Feche DevTools e notificações.

**Narração:** fale devagar; os textos abaixo são falas prontas, não roteiro de
leitura literal. Se travar, siga para a próxima ação — o que vale é a tela.

---

## 2. Cena a cena

### Cena 1 — 0:00–0:20 · O limite de antes

**Tela:** a tela de sequências, painel esquerdo visível.

**Fala:**
> "O deciframe acha músicas que você já sabe tocar a partir de sequências de
> acordes. O catálogo era fixo no código: quatro sequências na tela — e duas das
> seis que existiam na base, Em G e C A7 Dm G7, nem apareciam. Não dava para
> cadastrar nada."

*(Se quiser mostrar o "antes" de verdade, veja a Cena 1-B no fim; é opcional e
custa uns 5 minutos de preparo.)*

### Cena 2 — 0:20–0:45 · O catálogo agora vem do banco

**Ação:** recarregue a página (F5) e passe o mouse sobre os blocos do painel
esquerdo — cada um tem o nome no `title`.

**Fala:**
> "Agora o catálogo vem do backend, de um banco SQLite. Seis sequências, cada uma
> com nome: as quatro de antes e mais a Sequência Em e a Sequência de C (Samba),
> que eram inalcançáveis."

### Cena 3 — 0:45–1:15 · Busca por `Em G`

**Ação:** clique em **Sequência Em**.

**Fala:**
> "Clique na Sequência Em — Em, G. A busca vai pelo id do catálogo, não mais pela
> tag que vinha no CSV. Quatro músicas: é exatamente o conjunto que a versão
> antiga devolvia."

**Ação:** troque o gênero no seletor (ex.: Sertanejo) e mostre a lista filtrando;
volte para "-- Gênero --". Depois clique num hexágono do painel direito para
limpar a seleção.

**Fala (rápida):**
> "O filtro por gênero continua funcionando em cima do resultado da sequência."

### Cena 4 — 1:15–1:50 · Duplicata é recusada com aviso

**Ação:** no campo do formulário (placeholder `Ex.: Em G D A`), digite `Em G` e
clique em **Cadastrar sequência**.

**Fala:**
> "Vou tentar cadastrar Em G, que já existe. A API responde 409 com o id da
> existente, e a tela não cria uma segunda: mostra o aviso 'Essa sequência já
> está no catálogo', limpa o campo e seleciona a que já existia."

**Ação:** aponte o aviso amarelo e as 4 músicas voltando. Note que o catálogo
continua com 6.

### Cena 5 — 1:50–2:25 · Cadastro de uma sequência nova

**Ação:** digite `Em G D A` e clique em **Cadastrar sequência**.

**Fala:**
> "Agora uma que não existe: Em G D A. A API valida — de 2 a 12 acordes, todos do
> vocabulário do app — grava e responde 201. A sequência entra no topo, fica
> selecionada e a busca dispara na mesma ação: 54 músicas."

**Ação:** aponte a entrada nova no topo do catálogo, o nome no painel direito e a
lista de músicas.

*(Se quiser provar a validação, cadastre `Em Xyz` e mostre o erro citando o
acorde. Opcional: só se o tempo estiver sobrando.)*

### Cena 6 — 2:25–3:15 · A prova: persistência de verdade

**Ação:** vá para o terminal. Deixe os comandos prontos no histórico para colar
um por vez.

```
docker rm -f ciframe-demo
```

**Fala:**
> "O container foi removido — não reiniciado. Só o volume ciframe-data
> sobreviveu."

```
docker run -d --name ciframe-demo2 -p 8080:8080 -v ciframe-data:/var/lib/ciframe ciframe
docker exec ciframe-demo2 ls -l /var/lib/ciframe
```

**Fala:**
> "Container novo, mesmo volume. O banco está lá dentro. O seed não duplica as
> seis originais porque insere com INSERT OR IGNORE sobre a chave única."

**Ação:** volte ao navegador, recarregue `http://localhost:8080/#/porsequencia` e
role o painel esquerdo até o fim, se precisar (depois do reload a sequência nova
aparece no fim da lista, porque o servidor ordena por id).

**Fala:**
> "Sete sequências, com Em G D A no catálogo — e ela continua buscando as 54
> músicas, agora vindo do banco do container novo."

**Ação:** clique em **Em G D A** e mostre o resultado.

### Cena 7 — 3:15–3:35 · Fechamento

**Fala:**
> "No repositório, `docs/features/sequencias-customizadas/` tem as cinco fases:
> pesquisa, proposta com ADR, plano, implementação e o relatório de testes. A
> suíte tem 78 testes, incluindo a regressão que compara as seis sequências
> originais com a baseline gerada antes da migração. Ficou de fora, por escopo:
> edição e exclusão, login e paginação do catálogo — está tudo listado no
> relatório."

**Ação (opcional, 10 s):** mostre o terminal com `pytest -q` já rodado
(`78 passed`).

---

## 3. Contraprova opcional — 3:35–4:05 · Sem o `-v`

Vale a pena se sobrar tempo, porque é o erro que a feature convida a cometer:

```
docker rm -f ciframe-demo2
docker run -d --name ciframe-demo3 -p 8080:8080 ciframe
```

**Ação:** recarregue a página.

**Fala:**
> "Sem o `-v`, o VOLUME do Dockerfile cria um volume anônimo, que morre junto com
> o container: volta a ter seis. Por isso o README documenta o comando com volume
> nomeado."

---

## 4. Cena 1-B (opcional) — mostrar a versão antiga de verdade

Só faça isso se quiser o "antes" na tela. Precisa de outro checkout e de outra
porta:

```
git worktree add /tmp/ciframe-antes master
docker build -t ciframe-antes /tmp/ciframe-antes
docker run -d --name ciframe-antes -p 8081:8080 ciframe-antes
```

Abra `http://localhost:8081/#/porsequencia` numa aba: quatro sequências, sem nome,
sem formulário. Grave uns 10 segundos, volte para a aba da 8080 e siga da Cena 2.
No fim:

```
docker rm -f ciframe-antes
docker rmi ciframe-antes
git worktree remove /tmp/ciframe-antes
```

---

## 5. Contingências

| se acontecer | o que fazer |
|---|---|
| o catálogo começa com 7 ou mais | sobrou volume de teste: pare o container, `docker volume rm ciframe-data` e recrie (seção 1) |
| porta 8080 ocupada | use `-p 8081:8080` e troque a porta na URL do navegador |
| `Em G D A` já existe no catálogo | use `Dm E7 Am` (devolve 9 músicas) e ajuste a fala |
| página em branco ou catálogo vazio | `docker logs ciframe-demo` e `curl -s localhost:8080/sequencias`; se o curl responde, é só recarregar sem cache (Cmd+Shift+R) |
| o aviso de duplicata não aparece | confirme que digitou `Em G` e não `Em G D A`; o aviso fica embaixo do formulário |
| erro de CORS no console | não abra o HTML por `file://`; use sempre `http://localhost:8080` |

## 6. Checklist antes de publicar

- [ ] Aparece **6** antes e **7** depois — sem essa comparação a persistência não
      está demonstrada.
- [ ] `docker rm -f` aparece na gravação (não `docker restart`).
- [ ] A sequência cadastrada no vídeo não é uma das 6 originais (`Em G D A`).
- [ ] O `pytest -q` mostra `78 passed` se você decidir incluir.
- [ ] Áudio audível e terminal legível em 720p.
- [ ] Se publicar como GIF, corte para as cenas 3 e 6 (0:45–1:15 e 2:25–3:15).
