# Roteiro do vídeo — Sequências de Acordes Customizadas

Alvo: **3 a 4 minutos**, uma gravação só, sem edição (se errar, refaça o trecho).
O que a banca precisa ver, nesta ordem:

1. o problema (catálogo fixo, sequências inalcançáveis);
2. o catálogo vindo do banco, com as 6 originais;
3. busca por `Em G` funcionando;
4. cadastro de uma sequência nova pela tela;
5. **o cadastro sobrevivendo a `docker rm` + `docker run` novo** — é o ponto que
   separa "tem persistência" de "parece que tem".

## Antes de gravar

Deixe o ambiente no estado inicial (6 sequências, nada cadastrado). Se você já
testou antes, o volume tem lixo e o vídeo começa com o catálogo errado:

```
docker rm -f ciframe-demo ciframe-demo2 2>/dev/null
docker volume rm ciframe-data 2>/dev/null
docker build -t ciframe .
docker run -d --name ciframe-demo -p 8080:8080 -v ciframe-data:/var/lib/ciframe ciframe
```

Confira antes de abrir o navegador:

```
curl -s localhost:8080/sequencias    # tem que listar 6
```

Dicas de tela: navegador em 1440×900 (é o tamanho que o layout espera), zoom em
100%, terminal com fonte grande, e uma janela só do navegador e do terminal
lado a lado — você vai alternar entre elas no minuto 2:40.

## 0:00–0:25 — O problema

Tela: `http://localhost:8080/#/porsequencia`.

Fale: o deciframe sugere músicas a partir de sequências de acordes famosas, mas o
catálogo era **fixo no código**: quatro sequências no `sequencia.js`, e duas das
seis que existiam na base (`EmG` e `CA7DmG7`) não apareciam na tela. Não havia
como cadastrar nada.

Mostre o painel esquerdo: quatro blocos de acordes, sem nome e sem formulário.

## 0:25–0:50 — O catálogo agora vem do banco

Recarregue a página (F5).

Fale: agora o catálogo vem de `GET /sequencias`, que lê do SQLite. A tela mostra
**seis** sequências, cada uma com nome legível, incluindo "Sequência Em" e
"Sequência de C (Samba)" — que antes eram inalcançáveis.

Passe o mouse: o nome aparece também no `title` do bloco.

## 0:50–1:20 — Busca por `Em G`

Clique em **Sequência Em** (é o `Em G`).

Fale: o clique busca por `?sequencia_id=3`, não mais por uma tag do CSV. O
resultado são **4 músicas** — o mesmo conjunto que a coluna `SEQ_FAMOSA` devolvia
antes da migração (está na baseline de regressão).

Mostre as 4 músicas ("Inútil" do Ultraje a Rigor aparece primeiro). Troque o
gênero no seletor e mostre que a lista filtra.

Clique num acorde (hexágono) do painel direito para limpar a seleção e voltar.

## 1:20–1:55 — Duplicata é recusada, e a tela explica

No campo do formulário (placeholder `Ex.: Em G D A`), digite `Em G` e clique em
**Cadastrar sequência**.

Fale: `Em G` já existe. A API responde **409** com o `id` da existente, e a tela
não cria uma segunda: mostra o aviso "Essa sequência já está no catálogo." e
seleciona a que já existia, já disparando a busca.

Mostre o aviso amarelo abaixo do formulário e o resultado voltando (4 músicas).

## 1:55–2:30 — Cadastro de uma sequência nova

Digite `Em G D A` e cadastre.

Fale: agora uma sequência que não existe. A API valida (2 a 12 acordes, todos do
vocabulário do CSV), grava e responde **201**. A sequência entra no catálogo,
fica selecionada e a busca dispara na mesma ação: **54 músicas**.

Mostre a nova entrada no topo da lista, o nome no painel direito e as 54 músicas.
(Se quiser provar a validação, digite `Em Xyz` e mostre o erro citando `Xyz` —
mas isso pode ficar de fora se o tempo apertar.)

## 2:30–3:20 — A prova: persistência de verdade

Este é o trecho que importa. Vá para o terminal.

```
docker rm -f ciframe-demo
docker run -d --name ciframe-demo2 -p 8080:8080 -v ciframe-data:/var/lib/ciframe ciframe
docker exec ciframe-demo2 ls -l /var/lib/ciframe
```

Fale: o container foi **removido**, não reiniciado. O volume `ciframe-data`
guardou o SQLite; o novo container encontra o banco já populado e as 6
sequências originais não são duplicadas porque o seed usa `INSERT OR IGNORE`
sobre `chave UNIQUE`.

Volte ao navegador e recarregue `http://localhost:8080/#/porsequencia`.

Mostre: **7 sequências**, com "Em G D A" na lista. Clique nela e mostre as 54
músicas de novo — agora vindas do banco do container novo.

Opcional, se sobrar tempo (30 s e vale a pena): mostre a contraprova.

```
docker rm -f ciframe-demo2
docker run -d --name ciframe-demo3 -p 8080:8080 ciframe   # sem -v
```

Recarregue: volta a ter 6. Fale: sem o `-v`, o `VOLUME` do Dockerfile cria um
volume anônimo que morre junto com o container — por isso o `README.md` documenta
o comando com volume nomeado.

## 3:20–3:40 — Fechamento

Fale: no repositório, `docs/features/sequencias-customizadas/` tem as cinco fases
(pesquisa, proposta, ADR, plano, relatório de testes); a suíte tem **78 testes**
(`pytest -q` → `78 passed`), incluindo o de regressão que compara as 6 sequências
originais com a baseline gerada **antes** da migração.

Diga o que ficou de fora, em uma frase: sem edição/exclusão, sem login, sem
paginação no catálogo — o `04-test-report.md` lista tudo.

## Checklist antes de publicar

- [ ] O vídeo mostra o número 6 antes e o 7 depois — sem isso a persistência não
      está demonstrada.
- [ ] `docker rm -f` aparece na gravação (não só `docker restart`).
- [ ] A sequência cadastrada no vídeo não é uma das 6 originais (use `Em G D A`).
- [ ] O áudio está audível e o texto do terminal legível em 720p.
- [ ] Se publicar como GIF, corte para os trechos 0:50–1:20 e 2:30–3:20.
