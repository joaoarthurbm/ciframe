# deciframe

Descubra as músicas que você já sabe tocar (e ainda não faz ideia). Busque por
título/artista, gênero, pelos acordes que você já manja, ou por sequências de
acordes famosas — o deciframe cruza isso com uma base de cifras e sugere
músicas parecidas.

Stack: backend Flask (Python) servindo uma API JSON + um frontend AngularJS
estático, numa base de dados de músicas carregada de um CSV em memória. O
catálogo de sequências de acordes (as 6 originais + as cadastradas) fica em um
SQLite local, separado do CSV.

## Rodando localmente

### Com Docker (recomendado)

O `docker-compose.yml` já monta o volume nomeado e usa `restart: unless-stopped`,
então o catálogo sobrevive a `docker compose down`, à recriação do container e ao
reinício do host:

```
docker compose up -d --build
docker compose ps
```

Confira o mount antes de confiar na persistência:

```
docker inspect "$(docker compose ps -q deciframe)" --format '{{json .Mounts}}'
```

Se já houver um container antigo usando a porta 8080, pare-o antes
(`docker stop <nome>`). Se ele foi criado sem volume, recupere o banco dele com
`docker cp` antes de removê-lo; veja a seção de persistência abaixo.

Acesse [http://localhost:8080](http://localhost:8080).

Para acompanhar os logs e parar sem apagar o catálogo:

```
docker compose logs -f deciframe
docker compose down
```

`docker compose down -v` **apaga o volume e o catálogo**. Use apenas quando quiser
zerar as sequências (as 6 originais são semeadas de novo no próximo start).

### Com Docker sem Compose

O equivalente, com o mesmo volume nomeado:

```
docker build -t ciframe .
docker run -d --name ciframe \
  -p 8080:8080 \
  -v deciframe-instance:/app/instance \
  --restart unless-stopped \
  ciframe
```

`docker stop ciframe` + `docker start ciframe` preservam os dados. Para recriar o
container sem perder o catálogo, remova e rode de novo **com o mesmo `-v`**:

```
docker rm -f ciframe
docker run -d --name ciframe \
  -p 8080:8080 \
  -v deciframe-instance:/app/instance \
  --restart unless-stopped \
  ciframe
```

Confira que o mount existe antes de confiar na persistência:

```
docker inspect ciframe --format '{{json .Mounts}}'
```

A saída deve conter `"Destination":"/app/instance"` e o volume
`deciframe-instance`. Um `docker run` sem `-v` cria um banco apenas na camada
gravável do container; ele sobrevive a `stop/start`, mas não à remoção/recriação
do container nem à combinação de reiniciar o host e subir outro container.

### Com virtualenv

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Acesse [http://localhost:5000](http://localhost:5000).

### Persistência das sequências

O catálogo fica em `instance/sequences.db` dentro do container (ou no caminho
definido por `SEQUENCES_DB`). No Docker, o volume nomeado
`deciframe-instance:/app/instance` é o que preserva as sequências. Não monte
`/app/data`: o CSV de músicas/gêneros é copiado para a imagem nesse diretório.

Antes de remover um container antigo criado **sem** volume, verifique se há dados
recuperáveis nele e faça um backup consistente com a API do SQLite (o banco usa
WAL, então copiar só `sequences.db` com o app rodando pode perder escritas
recentes):

```
docker exec <container> python -c \
  "import sqlite3; s=sqlite3.connect('/app/instance/sequences.db'); d=sqlite3.connect('/tmp/sequences-backup.db'); s.backup(d)"
docker cp <container>:/tmp/sequences-backup.db ./sequences-recuperado.db
```

Se o container estiver parado, copie `sequences.db`, `sequences.db-wal` e
`sequences.db-shm` juntos (ou inicie o container e use o backup acima). Para
backup do catálogo em uso:

```
docker compose exec deciframe python -c \
  "import sqlite3; s=sqlite3.connect('/app/instance/sequences.db'); d=sqlite3.connect('/tmp/sequences-backup.db'); s.backup(d)"
docker compose cp deciframe:/tmp/sequences-backup.db ./sequences-backup.db
```

Para zerar o catálogo, remova o volume com `docker compose down -v` ou
`docker volume rm deciframe-instance`; as 6 sequências originais são semeadas de
novo no próximo start.

---

Para convenções de contribuição, veja [CONTRIB.md](CONTRIB.md). Licença: [LICENSE](LICENSE).
