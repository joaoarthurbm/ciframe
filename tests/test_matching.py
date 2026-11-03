# coding: utf-8

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import custom_sequences as cs  # noqa: E402


class FakeMusica:
    def __init__(self, song_id, cifra, popularidade=0):
        self.id_unico_musica = song_id
        self.cifra = cifra
        self.popularidade = popularidade


class MatchingTests(unittest.TestCase):
    def setUp(self):
        self.musicas = {
            "a": FakeMusica("a", ["C", "G"], 10),
            "b": FakeMusica("b", ["C7", "G"], 20),
            "c": FakeMusica("c", ["G", "C"], 30),
            "d": FakeMusica("d", ["Em", "G", "D", "A"], 5),
            "e": FakeMusica("e", [], 1),
        }
        self.index = cs.build_cifra_index(self.musicas)

    def test_contiguous_ordered_match(self):
        self.assertEqual(cs.match_ordered(["C", "G"], self.index), ["a"])

    def test_reverse_order_does_not_match(self):
        self.assertEqual(cs.match_ordered(["G", "C"], self.index), ["c"])

    def test_non_contiguous_does_not_match(self):
        self.assertEqual(cs.match_ordered(["C", "D"], self.index), [])

    def test_token_boundaries(self):
        # "C" must not match the "C7" token.
        self.assertEqual(cs.match_ordered(["C"], self.index), ["a", "c"])
        self.assertEqual(cs.match_ordered(["C7"], self.index), ["b"])

    def test_case_insensitive(self):
        self.assertEqual(cs.match_ordered(["c"], self.index), ["a", "c"])

    def test_empty_cifra_does_not_match(self):
        self.assertEqual(cs.match_ordered(["E"], self.index), [])

    def test_index_covers_all_songs(self):
        self.assertEqual(set(self.index), {"a", "b", "c", "d", "e"})
        self.assertEqual(self.index["a"], ";c;g;")
        self.assertEqual(self.index["e"], ";;")

    def test_sort_is_popularity_then_id(self):
        ids = cs.sort_matched_ids(["c", "a", "b", "d"], self.musicas)
        self.assertEqual(ids, ["c", "b", "a", "d"])

    def test_matching_index_caches(self):
        matcher = cs.MatchingIndex(self.musicas)
        first = matcher.matches("seq", ["C", "G"])
        second = matcher.matches("seq", ["C", "G"])
        self.assertEqual(first, ["a"])
        self.assertEqual(second, ["a"])
        self.assertIn("seq", matcher._cache)

    def test_matching_index_returns_copy(self):
        matcher = cs.MatchingIndex(self.musicas)
        result = matcher.matches("seq", ["C", "G"])
        result.append("not-a-song")
        self.assertEqual(matcher.matches("seq", ["C", "G"]), ["a"])


if __name__ == "__main__":
    unittest.main()
