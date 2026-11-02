# deciframe

Descubra as músicas que você já sabe tocar (e ainda não faz ideia). Busque por
título/artista, gênero, pelos acordes que você já manja, ou por sequências de
acordes famosas — o deciframe cruza isso com uma base de cifras e sugere
músicas parecidas.

Stack: backend Flask (Python) servindo uma API JSON + um frontend AngularJS
estático. As músicas vêm de um CSV carregado em memória; o catálogo de
sequências de acordes (as 6 originais e as cadastradas na tela) fica num SQLite.

## Rodando localmente

### Com Docker

```
docker build -t ciframe .
docker run -p 8080:8080 -v ciframe-data:/var/lib/ciframe ciframe
```

Acesse [http://localhost:8080](http://localhost:8080).

O volume `ciframe-data` guarda o catálogo de sequências. Sem o `-v`, as
sequências cadastradas somem quando o container é removido (as 6 originais
voltam, porque são semeadas no boot).

### Com virtualenv

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
CIFRAME_DB=./ciframe.db python main.py
```

Acesse [http://localhost:5000](http://localhost:5000).

`CIFRAME_DB` aponta o arquivo do banco. O default é
`/var/lib/ciframe/ciframe.db`, que só é gravável no container — por isso o
caminho local no comando acima.

---

Para convenções de contribuição, veja [CONTRIB.md](CONTRIB.md). Licença: [LICENSE](LICENSE).
