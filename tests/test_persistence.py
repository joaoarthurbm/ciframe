# coding: utf-8

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import custom_sequences as cs  # noqa: E402


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "sequences.db")

    def tearDown(self):
        self.tmp.cleanup()

    def test_custom_sequence_survives_new_connection(self):
        first = cs.init_db(self.db_path)
        self.assertEqual(first["seeded"], 6)
        created = cs.create_sequence(
            self.db_path, "Persistente", ["D", "A", "Bm", "G"]
        )

        # Simula um novo processo/startup: nova conexão, novo init, sem seed
        # adicional e sem perder a sequência customizada.
        second = cs.init_db(self.db_path)
        self.assertEqual(second["seeded"], 0)
        self.assertEqual(second["total"], 7)

        sequences = cs.list_sequences(self.db_path)
        builtins = [item for item in sequences if item["origem"] == "builtin"]
        customs = [item for item in sequences if item["origem"] == "custom"]
        self.assertEqual(len(builtins), 6)
        self.assertEqual(len(customs), 1)

        loaded = cs.get_sequence(self.db_path, created["id"])
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["nome"], "Persistente")
        self.assertEqual(loaded["acordes"], ["D", "A", "Bm", "G"])

    def test_builtins_are_not_overwritten(self):
        cs.init_db(self.db_path)
        sequences = cs.list_sequences(self.db_path)
        original = {
            item["id"]: item["nome"] for item in sequences
        }

        cs.init_db(self.db_path)
        after = {
            item["id"]: item["nome"]
            for item in cs.list_sequences(self.db_path)
        }
        self.assertEqual(after, original)

    def test_future_schema_version_fails_loudly(self):
        cs.init_db(self.db_path)
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA user_version = 99")
            conn.commit()
        finally:
            conn.close()

        with self.assertRaises(RuntimeError):
            cs.init_db(self.db_path)

    def test_resolve_db_path_can_be_configured(self):
        old = os.environ.get("SEQUENCES_DB")
        os.environ["SEQUENCES_DB"] = "~/custom-sequences.db"
        try:
            self.assertEqual(
                cs.resolve_db_path(),
                os.path.abspath(os.path.expanduser("~/custom-sequences.db")),
            )
        finally:
            if old is None:
                os.environ.pop("SEQUENCES_DB", None)
            else:
                os.environ["SEQUENCES_DB"] = old


if __name__ == "__main__":
    unittest.main()
