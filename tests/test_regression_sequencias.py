# coding: utf-8

import json
import os
import unittest

import helpers


FIXTURE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "fixtures",
    "sequencias_baseline.json",
)


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.client = helpers.reset_db()
        with open(FIXTURE, encoding="utf-8") as handle:
            self.baseline = json.load(handle)["sequences"]

    def fetch_pages(self, key, use_id):
        pages = []
        page = 1
        while True:
            params = {"pagina": str(page)}
            if use_id:
                params["sequencia_id"] = key
            else:
                params["sequencia"] = key
            response = self.client.get("/similares", query_string=params)
            self.assertEqual(response.status_code, 200)
            items = json.loads(response.get_data(as_text=True))
            if not items:
                break
            pages.append([item["id_unico_musica"] for item in items])
            page += 1
        return pages

    @staticmethod
    def flat(pages):
        return sorted(song_id for page in pages for song_id in page)

    def test_all_six_legacy_paths_match_baseline(self):
        for key, expected in self.baseline.items():
            with self.subTest(sequence=key, path="legacy"):
                actual = self.fetch_pages(key, use_id=False)
                self.assertEqual(
                    self.flat(actual),
                    self.flat(expected["pages"]),
                )

    def test_all_six_id_paths_match_baseline(self):
        for key, expected in self.baseline.items():
            with self.subTest(sequence=key, path="id"):
                actual = self.fetch_pages(key, use_id=True)
                self.assertEqual(
                    self.flat(actual),
                    self.flat(expected["pages"]),
                )

    def test_counts_match_baseline(self):
        expected_counts = {
            "BmGDA": 199,
            "CGAmF": 296,
            "EmG": 4,
            "CA7DmG7": 5,
            "GmF": 7,
            "CC7FFm": 3,
        }
        for key, expected in expected_counts.items():
            with self.subTest(sequence=key):
                pages = self.fetch_pages(key, use_id=False)
                self.assertEqual(
                    sum(len(page) for page in pages), expected
                )


if __name__ == "__main__":
    unittest.main()
