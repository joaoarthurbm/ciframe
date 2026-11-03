# AGENTS.md

deciframe is a song-discovery tool for musicians: search by title/artist,
genre, chords you already know, or a famous chord sequence, and it finds
similar songs. Full description: [README.md](README.md).

## Stack

- Backend: Python 3.9, Flask 3.1, gunicorn. Single file (`main.py`) that
  loads `data/top/dataset_final.csv` into memory once at startup. The song and
  genre catalogue stays in the CSV; only the chord-sequence catalogue (the six
  built-ins and custom sequences) lives in SQLite at `instance/sequences.db`
  (configurable through `SEQUENCES_DB`).
- Frontend: AngularJS 1.4.9 + jQuery, loaded from CDN in `static/index.html`,
  no build step. Legacy, and it's no longer frozen when a task needs it; see
  [docs/adr/0003-lift-frontend-freeze.md](docs/adr/0003-lift-frontend-freeze.md).
- Deploy: local-only via Docker for now. No cloud target has been chosen.

## Run locally

Docker (matches how the app actually ships). Compose is the default path because
it mounts the named volume and restarts the same container after a host reboot:

```
docker compose up -d --build
docker compose ps
```

Equivalent without Compose (the `-v` is mandatory for recreation):

```
docker build -t ciframe .
docker run -d --name ciframe -p 8080:8080 \
  -v deciframe-instance:/app/instance --restart unless-stopped ciframe
```

Confirm the mount before relying on persistence (Compose; for the `docker run`
equivalent use `docker inspect ciframe`):

```
docker inspect "$(docker compose ps -q deciframe)" --format '{{json .Mounts}}'
```

Or a plain virtualenv:

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py        # serves on :5000 instead of :8080
```

## Verify it's up

```
curl http://localhost:8080/generos
```

Done when this returns a JSON array of genre names (e.g. `["Rock", "Samba", ...]`), not an error page. If it hangs on startup, it's still parsing the CSV — give it a few seconds.

## Gotchas

- Editing `data/top/*.csv` requires a restart: it's read once at import time, not per-request.
- The custom-sequence catalogue is the exception to the in-memory model: it is
  persisted in `instance/sequences.db`. Mount `/app/instance` (not `/app/data`)
  to keep it across container recreation; `instance/` is ignored by Git/Docker.
  The default `docker compose up -d --build` uses a named `deciframe-instance`
  volume and `restart: unless-stopped`. `docker compose down` keeps the volume;
  `docker compose down -v` deletes the catalogue. A bare `docker run` without
  `-v` is ephemeral across container recreation even though the Dockerfile
  declares `VOLUME /app/instance` (that only saves `stop/start`).
- Every endpoint returns `json.dumps(...)` as a plain string, not `jsonify` — responses come back `Content-Type: text/html`. This is intentional legacy behavior; changing it is a real API change, not a cleanup.
- Check `docs/adr/` before changing the deploy setup — it has a documented reason for its current state.
