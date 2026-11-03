# Persist custom chord sequences in SQLite

The six "famous sequences" are currently hardcoded in `main.py:40-45`, and the
results for them come from the `SEQ_FAMOSA` tags precomputed into
`data/top/dataset_final.csv` by `scripts/generate_data_set.py:7-24`. The new feature
requires any anonymous visitor to register additional sequences and search them, and
the sequence catalogue must survive container restarts. The song and genre catalogue
must stay in the in-memory CSV, the project must keep its single local Dockerfile, and
every response must keep using `json.dumps(...)`. There is no database today.

We decided to add an SQLite database through the `sqlite3` module in the Python 3.9
standard library, stored at `/app/instance/sequences.db` (configurable through
`SEQUENCES_DB`). A `sequences` table stores the id, name, ordered chord list, a
normalized chord string for duplicate detection, the origin (`builtin`/`custom`), the
matching mode, the legacy tag id, and the creation timestamp. The six built-ins are
seeded idempotently at startup with `matching_mode = 'legacy_tag'` and their existing
tag ids; new sequences get a UUID4 and `matching_mode = 'ordered'`. The database lives
under `instance/`, not under `data/`: the image copies the repository to `/app`
(`Dockerfile:8`) and the app reads `data/top/dataset_final.csv` (`main.py:49`), so a
volume mounted at `/app/data` would hide the songs. The run command therefore becomes
`docker run -p 8080:8080 -v deciframe-instance:/app/instance ciframe`, and `instance/`
must be added to `.gitignore` and `.dockerignore`.

A follow-up incident confirmed that this volume must be part of the default
execution path, not just a documented flag. Two `ciframe` containers had been
started with `docker run -p 8080:8080 ciframe` (no `-v`); `docker inspect` reported
`Mounts=[]`, and each container had its own `sequences.db` in its writable layer.
The application did not delete or overwrite the database (`CREATE TABLE IF NOT
EXISTS` plus `INSERT OR IGNORE`); removing and re-running the container simply
created a fresh writable layer. Therefore the canonical command is now
`docker compose up -d --build`, backed by a single-service `docker-compose.yml`
with `restart: unless-stopped` and a named `deciframe-instance` volume. The
`Dockerfile` also declares `VOLUME ["/app/instance"]` as a safety net for bare
`docker run`: it survives `stop/start`, but named-volume removal/recreation still
requires the Compose/`-v` path. `docker compose down` keeps the volume;
`docker compose down -v` deletes the catalogue. Containers created before this
correction can still have recoverable data in their writable layer, so they must
be inspected with `docker cp` before removal.

The six built-ins keep the exact current path: a song matches when
`str(legacy_tag) in musica.seqs_famosas` (`main.py:203-223`), so their result sets,
ordering and pagination are unchanged by construction. New sequences use an ordered,
contiguous occurrence rule over `musica.cifra` (`musica.py:16`); `musica.acordes` is not
used because `list(set(cifra))` loses order and repetition (`musica.py:17`). A derived
`;`-joined index of each song's lowercased chords makes that check a substring test with
token boundaries, and matches for a custom sequence are cached in process after the
first search. The search endpoint gains `?sequencia_id=<id>` while `?sequencia=<legacy
key>` remains untouched. This deliberately creates two matching modes: the legacy tag
is a generation artifact that is much more restrictive than "the sequence appears in
the song" — research measured 199 matches for Bm–G–D–A against 866 by contiguous
token occurrence, and 4 for Em–G against 3,110 (see
`docs/features/sequencias-customizadas/01-research.md`) — so applying it to
user-created sequences would make the feature almost useless.

SQLite was chosen over the alternatives because it adds no dependency, gives ACID
transactions and a single file, fits the single local-only container from ADR 0001, and
needs no external service. TinyDB would add a runtime dependency, rewrite the whole JSON
file on every write and provide weaker concurrency and durability; a hand-written JSON
file would not be a database and would have the same atomicity problems; DuckDB is an
analytical database and is unnecessary for a catalogue of a few dozen sequences. The
song/genre catalogue and the `SEQ_FAMOSA` column stay where they are; only the sequence
catalogue is persisted.

The consequences are accepted for this phase. Schema creation and seeding happen at
startup, with `CREATE TABLE IF NOT EXISTS` and `PRAGMA user_version` for manual future
migrations; there is no Alembic or migration service. The catalogue is anonymous and
unmoderated, so validation is limited to name/chord limits, the `/acordes` vocabulary
and duplicate rejection; login, moderation and rate limiting remain open. The matching
cache is per process and rebuilt lazily after a restart. Backup must use the SQLite
backup API/`sqlite3 .backup` (or copy `sequences.db` together with `-wal`/`-shm`
after stopping the app); copying only the main file while WAL is active can lose
recent writes. A plain `docker restart` preserves the container
filesystem, but only the volume preserves the catalogue when the container is removed
or the image is rebuilt. Rolling back to the previous code is safe because it ignores
the database, but sequences created after the change would no longer be visible. If the
project later adopts multiple gunicorn workers, a different deploy target, or a single
matching semantics for all sequences, this decision must be revisited; the current
constraint is the local single container from ADR 0001.
