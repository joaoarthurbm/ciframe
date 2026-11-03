# coding: utf-8

import json
import os
import sqlite3
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import custom_sequences as cs  # noqa: E402


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "sequences.db")
        self.info = cs.init_db(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_schema_and_seed(self):
        self.assertEqual(self.info["seeded"], 6)
        self.assertEqual(self.info["total"], 6)
        conn = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                conn.execute("PRAGMA user_version").fetchone()[0], 1
            )
            rows = conn.execute(
                "SELECT id, matching_mode, legacy_tag FROM sequences "
                "ORDER BY legacy_tag"
            ).fetchall()
        finally:
            conn.close()

        self.assertEqual([row[2] for row in rows], list(range(6)))
        self.assertTrue(all(row[1] == "legacy_tag" for row in rows))

    def test_seed_is_idempotent(self):
        second = cs.init_db(self.db_path)
        self.assertEqual(second["seeded"], 0)
        self.assertEqual(second["total"], 6)

    def test_lists_builtins_with_names_and_chords(self):
        sequences = cs.list_sequences(self.db_path)
        self.assertEqual(len(sequences), 6)
        by_id = {item["id"]: item for item in sequences}
        self.assertEqual(by_id["BmGDA"]["nome"], "Sequência de Bm")
        self.assertEqual(by_id["BmGDA"]["acordes"], ["Bm", "G", "D", "A"])
        self.assertEqual(by_id["BmGDA"]["origem"], "builtin")
        self.assertEqual(
            sorted(by_id), sorted(["BmGDA", "CGAmF", "EmG",
                                   "CA7DmG7", "GmF", "CC7FFm"])
        )

    def test_create_and_get_custom(self):
        created = cs.create_sequence(
            self.db_path, "Minha sequência", ["D", "A", "Bm", "G"]
        )
        self.assertEqual(created["origem"], "custom")
        self.assertEqual(created["matching_mode"], "ordered")
        self.assertIsNone(created["legacy_tag"])
        self.assertEqual(created["acordes"], ["D", "A", "Bm", "G"])

        loaded = cs.get_sequence(self.db_path, created["id"])
        self.assertEqual(loaded["nome"], "Minha sequência")
        self.assertEqual(loaded["acordes"], ["D", "A", "Bm", "G"])

        public = cs.list_sequences(self.db_path)
        self.assertEqual(len(public), 7)
        self.assertEqual(public[-1]["id"], created["id"])

    def test_duplicate_is_rejected_case_insensitively(self):
        created = cs.create_sequence(
            self.db_path, "Minha sequência", ["D", "A", "Bm", "G"]
        )
        with self.assertRaises(cs.DuplicateSequence) as context:
            cs.create_sequence(
                self.db_path, "Outro nome", ["d", "a", "bm", "g"]
            )
        self.assertEqual(context.exception.existing_id, created["id"])

    def test_builtin_duplicate_is_rejected(self):
        with self.assertRaises(cs.DuplicateSequence) as context:
            cs.create_sequence(
                self.db_path, "Copia", ["C", "G", "Am", "F"]
            )
        self.assertEqual(context.exception.existing_id, "CGAmF")

    def test_reads_json_chords(self):
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT acordes FROM sequences WHERE id = 'EmG'"
            ).fetchone()
        finally:
            conn.close()
        self.assertEqual(json.loads(row[0]), ["Em", "G"])


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.vocabulary = {"C", "G", "Am", "F", "Bm", "D", "A"}

    def test_canonicalizes_case(self):
        nome, acordes = cs.validate_sequence(
            "  Teste  ", ["c", "g", "AM"], self.vocabulary
        )
        self.assertEqual(nome, "Teste")
        self.assertEqual(acordes, ["C", "G", "Am"])

    def test_rejects_empty_name(self):
        with self.assertRaises(cs.ValidationError):
            cs.validate_sequence("   ", ["C"], self.vocabulary)

    def test_rejects_long_name(self):
        with self.assertRaises(cs.ValidationError):
            cs.validate_sequence("x" * 81, ["C"], self.vocabulary)

    def test_rejects_control_character_in_name(self):
        with self.assertRaises(cs.ValidationError):
            cs.validate_sequence("a\nb", ["C"], self.vocabulary)

    def test_rejects_non_list_chords(self):
        with self.assertRaises(cs.ValidationError):
            cs.validate_sequence("Teste", "C", self.vocabulary)

    def test_rejects_empty_chords(self):
        with self.assertRaises(cs.ValidationError):
            cs.validate_sequence("Teste", [], self.vocabulary)

    def test_rejects_too_many_chords(self):
        with self.assertRaises(cs.ValidationError):
            cs.validate_sequence("Teste", ["C"] * 17, self.vocabulary)

    def test_rejects_unknown_chord(self):
        with self.assertRaises(cs.ValidationError):
            cs.validate_sequence("Teste", ["ZZZ"], self.vocabulary)

    def test_rejects_semicolon(self):
        with self.assertRaises(cs.ValidationError):
            cs.validate_sequence("Teste", ["C;G"], self.vocabulary)

    def test_rejects_non_string_chord(self):
        with self.assertRaises(cs.ValidationError):
            cs.validate_sequence("Teste", [1], self.vocabulary)

    def test_normalize_acordes(self):
        self.assertEqual(
            cs.normalize_acordes([" D ", "a", "Bm"]),
            "d;a;bm",
        )


if __name__ == "__main__":
    unittest.main()
