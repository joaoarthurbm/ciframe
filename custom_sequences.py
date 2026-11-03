# coding: utf-8

"""Persistence and matching helpers for custom chord sequences.

The song and genre catalogue stays in the CSV loaded by ``main.py``.  This
module only owns the sequence catalogue (the six built-ins plus sequences
created at runtime) and the in-memory index used to match the latter.
"""

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone


SCHEMA_VERSION = 1
DB_FILENAME = "sequences.db"
MAX_NOME = 80
MAX_ACORDES = 16
MAX_ACORDE = 16

BUILTIN_FALLBACK_NAMES = {
    "BmGDA": "Sequência de Bm",
    "CGAmF": "Sequência de C",
    "EmG": "Sequência Em",
    "CA7DmG7": "Sequência de C (Samba)",
    "GmF": "Sequência de Gm",
    "CC7FFm": "Sequência de C (Samba cont.)",
}

BUILTINS = (
    {
        "id": "BmGDA",
        "legacy_tag": 0,
        "acordes": ["Bm", "G", "D", "A"],
    },
    {
        "id": "CGAmF",
        "legacy_tag": 1,
        "acordes": ["C", "G", "Am", "F"],
    },
    {
        "id": "EmG",
        "legacy_tag": 2,
        "acordes": ["Em", "G"],
    },
    {
        "id": "CA7DmG7",
        "legacy_tag": 3,
        "acordes": ["C", "A7", "Dm", "G7"],
    },
    {
        "id": "GmF",
        "legacy_tag": 4,
        "acordes": ["Gm", "F"],
    },
    {
        "id": "CC7FFm",
        "legacy_tag": 5,
        "acordes": ["C", "C7", "F", "Fm"],
    },
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS sequences (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    acordes TEXT NOT NULL,
    acordes_norm TEXT NOT NULL UNIQUE,
    origem TEXT NOT NULL CHECK (origem IN ('builtin', 'custom')),
    matching_mode TEXT NOT NULL CHECK (
        matching_mode IN ('legacy_tag', 'ordered')
    ),
    legacy_tag INTEGER,
    created_at TEXT NOT NULL,
    CHECK (
        (origem = 'builtin'
            AND matching_mode = 'legacy_tag'
            AND legacy_tag IS NOT NULL)
        OR
        (origem = 'custom'
            AND matching_mode = 'ordered'
            AND legacy_tag IS NULL)
    )
);
"""


class ValidationError(ValueError):
    """Raised when a sequence payload is not acceptable."""


class DuplicateSequence(ValueError):
    """Raised when the ordered chord list already exists."""

    def __init__(self, existing_id):
        super().__init__("Sequência já cadastrada")
        self.existing_id = existing_id


def resolve_db_path(app=None):
    """Return the configured database path or ``instance/sequences.db``."""
    configured = os.environ.get("SEQUENCES_DB")
    if configured:
        return os.path.abspath(os.path.expanduser(configured))

    if app is not None:
        base = app.instance_path
    else:
        base = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "instance",
        )
    return os.path.join(base, DB_FILENAME)


def connect(db_path):
    """Open a short-lived SQLite connection with sane concurrency settings."""
    parent = os.path.dirname(os.path.abspath(db_path))
    if parent:
        os.makedirs(parent, exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _read_builtin_names():
    names = dict(BUILTIN_FALLBACK_NAMES)
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "mapeamento_sequencias_famosas.txt",
    )
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                parts = line.strip().split(",", 2)
                if len(parts) != 3:
                    continue
                try:
                    index = int(parts[0])
                except ValueError:
                    continue
                names[str(index)] = parts[1].strip()
    except OSError:
        pass
    return names


def _builtin_rows():
    names = _read_builtin_names()
    for item in BUILTINS:
        yield {
            "id": item["id"],
            "nome": names.get(str(item["legacy_tag"]), item["id"]),
            "acordes": list(item["acordes"]),
            "origem": "builtin",
            "matching_mode": "legacy_tag",
            "legacy_tag": item["legacy_tag"],
        }


def _json_acordes(acordes):
    return json.dumps(acordes, ensure_ascii=False)


def _row_to_sequence(row):
    data = dict(row)
    data["acordes"] = json.loads(data["acordes"])
    return data


def to_public(sequence):
    """Strip internal matching fields from a sequence record."""
    return {
        "id": sequence["id"],
        "nome": sequence["nome"],
        "acordes": list(sequence["acordes"]),
        "origem": sequence["origem"],
    }


def init_db(db_path):
    """Create/migrate the schema and seed the six built-ins.

    Returns a small summary used by the startup log.
    """
    conn = connect(db_path)
    try:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise RuntimeError(
                "Banco de sequências em versão %s; esta aplicação suporta "
                "até %s" % (version, SCHEMA_VERSION)
            )

        with conn:
            conn.executescript(SCHEMA)
            if version < SCHEMA_VERSION:
                conn.execute("PRAGMA user_version = %d" % SCHEMA_VERSION)

        seeded = seed_builtins(conn)
        total = conn.execute(
            "SELECT COUNT(*) FROM sequences"
        ).fetchone()[0]
    finally:
        conn.close()

    return {"seeded": seeded, "total": total, "version": SCHEMA_VERSION}


def seed_builtins(conn):
    """Insert missing built-ins without touching existing rows."""
    inserted = 0
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        for item in _builtin_rows():
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO sequences
                    (id, nome, acordes, acordes_norm, origem,
                     matching_mode, legacy_tag, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["id"],
                    item["nome"],
                    _json_acordes(item["acordes"]),
                    normalize_acordes(item["acordes"]),
                    item["origem"],
                    item["matching_mode"],
                    item["legacy_tag"],
                    now,
                ),
            )
            inserted += cursor.rowcount
    return inserted


def list_sequences(db_path):
    conn = connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, nome, acordes, origem
            FROM sequences
            ORDER BY
                CASE origem WHEN 'builtin' THEN 0 ELSE 1 END,
                nome COLLATE NOCASE,
                id
            """
        ).fetchall()
        return [to_public(_row_to_sequence(row)) for row in rows]
    finally:
        conn.close()


def get_sequence(db_path, sequence_id):
    conn = connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM sequences WHERE id = ?", (sequence_id,)
        ).fetchone()
        return _row_to_sequence(row) if row else None
    finally:
        conn.close()


def find_by_acordes_norm(conn, acordes_norm):
    row = conn.execute(
        "SELECT * FROM sequences WHERE acordes_norm = ?", (acordes_norm,)
    ).fetchone()
    return _row_to_sequence(row) if row else None


def create_sequence(db_path, nome, acordes):
    """Persist a validated custom sequence and return its public record."""
    sequence_id = uuid.uuid4().hex
    norm = normalize_acordes(acordes)
    created_at = datetime.now(timezone.utc).isoformat()

    conn = connect(db_path)
    try:
        existing = find_by_acordes_norm(conn, norm)
        if existing:
            raise DuplicateSequence(existing["id"])

        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO sequences
                        (id, nome, acordes, acordes_norm, origem,
                         matching_mode, legacy_tag, created_at)
                    VALUES (?, ?, ?, ?, 'custom', 'ordered', NULL, ?)
                    """,
                    (
                        sequence_id,
                        nome,
                        _json_acordes(acordes),
                        norm,
                        created_at,
                    ),
                )
        except sqlite3.IntegrityError:
            existing = find_by_acordes_norm(conn, norm)
            if existing:
                raise DuplicateSequence(existing["id"])
            raise

        row = conn.execute(
            "SELECT * FROM sequences WHERE id = ?", (sequence_id,)
        ).fetchone()
        return _row_to_sequence(row)
    finally:
        conn.close()


def normalize_acordes(acordes):
    """Normalize an ordered chord list for duplicate detection."""
    return ";".join(acorde.strip().lower() for acorde in acordes)


def canonicalize_acordes(acordes, vocabulary):
    """Validate chord names and return their canonical spelling."""
    if not isinstance(acordes, list):
        raise ValidationError("acordes deve ser uma lista")
    if not acordes:
        raise ValidationError("informe pelo menos um acorde")
    if len(acordes) > MAX_ACORDES:
        raise ValidationError(
            "no máximo %d acordes por sequência" % MAX_ACORDES
        )

    canonical_map = {}
    for acorde in sorted(vocabulary):
        canonical_map.setdefault(acorde.lower(), acorde)

    canonical = []
    for acorde in acordes:
        if not isinstance(acorde, str):
            raise ValidationError("cada acorde deve ser texto")
        acorde = acorde.strip()
        if not acorde:
            raise ValidationError("acorde vazio")
        if len(acorde) > MAX_ACORDE:
            raise ValidationError(
                "acorde muito longo: %s" % acorde[:MAX_ACORDE]
            )
        if ";" in acorde:
            raise ValidationError("acorde não pode conter ';'")
        if any(ord(char) < 32 or ord(char) == 127 for char in acorde):
            raise ValidationError("acorde contém caractere inválido")

        found = canonical_map.get(acorde.lower())
        if found is None:
            raise ValidationError("acorde desconhecido: %s" % acorde)
        canonical.append(found)
    return canonical


def validate_sequence(nome, acordes, vocabulary):
    """Validate a POST payload and return ``(nome, acordes canônicos)``."""
    if not isinstance(nome, str):
        raise ValidationError("nome deve ser texto")
    nome = nome.strip()
    if not nome:
        raise ValidationError("informe o nome da sequência")
    if len(nome) > MAX_NOME:
        raise ValidationError(
            "nome deve ter no máximo %d caracteres" % MAX_NOME
        )
    if any(ord(char) < 32 or ord(char) == 127 for char in nome):
        raise ValidationError("nome contém caractere inválido")

    return nome, canonicalize_acordes(acordes, vocabulary)


def build_cifra_index(musicas):
    """Map song id to its chord list as a token-delimited lowercase string."""
    values = musicas.values() if hasattr(musicas, "values") else musicas
    index = {}
    for musica in values:
        index[musica.id_unico_musica] = ";" + ";".join(
            acorde.lower() for acorde in musica.cifra
        ) + ";"
    return index


def match_ordered(sequence, cifra_index):
    """Return ids whose cifra contains the sequence contiguously in order."""
    needle = ";" + ";".join(acorde.lower() for acorde in sequence) + ";"
    return [
        song_id
        for song_id, cifra in cifra_index.items()
        if needle in cifra
    ]


def sort_matched_ids(ids, musicas):
    return sorted(
        ids,
        key=lambda song_id: (-musicas[song_id].popularidade, song_id),
    )


class MatchingIndex:
    """In-memory cifra index plus a cache of custom-sequence matches."""

    def __init__(self, musicas):
        self.musicas = musicas
        self.cifra_index = build_cifra_index(musicas)
        self._cache = {}
        self._lock = threading.Lock()

    def matches(self, sequence_id, sequence):
        with self._lock:
            if sequence_id not in self._cache:
                ids = match_ordered(sequence, self.cifra_index)
                self._cache[sequence_id] = sort_matched_ids(
                    ids, self.musicas
                )
            return list(self._cache[sequence_id])

    def clear_cache(self):
        with self._lock:
            self._cache.clear()
