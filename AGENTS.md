# AGENTS.md

deciframe is a song-discovery tool for musicians: search by title/artist,
genre, chords you already know, or a famous chord sequence, and it finds
similar songs. Full description: [README.md](README.md).

## Stack

- Backend: Python 3.9, Flask 3.1, gunicorn. Single file (`main.py`) that
  loads `data/top/dataset_final.csv` into memory once at startup — there is
  no database.
- Frontend: AngularJS 1.4.9 + jQuery, loaded from CDN in `static/index.html`,
  no build step. This is legacy and was deliberately left untouched during
  the last modernization pass — don't upgrade it in passing; see
  [docs/adr/0001-local-only-docker-deploy.md](docs/adr/0001-local-only-docker-deploy.md).
- Deploy: local-only via Docker for now. No cloud target has been chosen.

## Run locally

Docker (matches how the app actually ships):

```
docker build -t ciframe .
docker run -p 8080:8080 ciframe
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
- Every endpoint returns `json.dumps(...)` as a plain string, not `jsonify` — responses come back `Content-Type: text/html`. This is intentional legacy behavior; changing it is a real API change, not a cleanup.
- Check `docs/adr/` before changing the deploy setup or touching the frontend stack — both have a documented reason for their current state.
