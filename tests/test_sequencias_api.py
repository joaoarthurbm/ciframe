# coding: utf-8

import json
import unittest
from concurrent.futures import ThreadPoolExecutor

import helpers


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = helpers.reset_db()
        self.main = helpers.main

    def get_json(self, path, **params):
        response = self.client.get(path, query_string=params)
        return response, json.loads(response.get_data(as_text=True))

    def post(self, payload):
        return self.client.post(
            "/sequencias", data=json.dumps(payload),
            content_type="application/json",
        )

    def test_catalog_has_six_builtins(self):
        response, catalog = self.get_json("/sequencias")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["Content-Type"], "text/html; charset=utf-8"
        )
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")
        self.assertEqual(len(catalog), 6)
        self.assertEqual({
            item["id"] for item in catalog
        }, set(self.main.sequencias))
        self.assertTrue(all(
            item["origem"] == "builtin" for item in catalog
        ))
        self.assertTrue(all(
            set(item) == {"id", "nome", "acordes", "origem"}
            for item in catalog
        ))

    def test_create_sequence_and_search_by_id(self):
        response = self.post({
            "nome": "D-A-Bm-G",
            "acordes": ["D", "A", "Bm", "G"],
        })
        self.assertEqual(response.status_code, 201)
        created = json.loads(response.get_data(as_text=True))
        self.assertEqual(created["nome"], "D-A-Bm-G")
        self.assertEqual(created["origem"], "custom")
        self.assertEqual(created["acordes"], ["D", "A", "Bm", "G"])

        _, catalog = self.get_json("/sequencias")
        self.assertEqual(len(catalog), 7)
        self.assertIn(created["id"], {item["id"] for item in catalog})

        response, results = self.get_json(
            "/similares", sequencia_id=created["id"]
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(results)
        self.assertEqual(
            set(results[0]),
            {
                "id_unico_musica", "id_artista", "id_musica",
                "nome_artista", "nome_musica", "popularidade",
                "acordes", "genero", "url",
            },
        )

        response, second_page = self.get_json(
            "/similares", sequencia_id=created["id"], pagina="2"
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(results, second_page)

    def test_duplicate_custom_returns_409(self):
        first = self.post({
            "nome": "Primeira",
            "acordes": ["D", "A", "Bm", "G"],
        })
        created = json.loads(first.get_data(as_text=True))
        second = self.post({
            "nome": "Segunda",
            "acordes": ["d", "a", "bm", "g"],
        })
        self.assertEqual(second.status_code, 409)
        conflict = json.loads(second.get_data(as_text=True))
        self.assertEqual(conflict["id"], created["id"])

    def test_duplicate_builtin_returns_409(self):
        response = self.post({
            "nome": "Copia",
            "acordes": ["C", "G", "Am", "F"],
        })
        self.assertEqual(response.status_code, 409)
        conflict = json.loads(response.get_data(as_text=True))
        self.assertEqual(conflict["id"], "CGAmF")

    def test_validation_errors(self):
        cases = [
            {"nome": "X", "acordes": ["ZZZ"]},
            {"nome": "X"},
            {"nome": "", "acordes": ["C"]},
            {"nome": "x" * 81, "acordes": ["C"]},
            {"nome": "X", "acordes": []},
            {"nome": "X", "acordes": ["C"] * 17},
            {"nome": "X", "acordes": ["C;G"]},
            {"nome": "X", "acordes": "C"},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                response = self.post(payload)
                self.assertEqual(response.status_code, 400)
                body = json.loads(response.get_data(as_text=True))
                self.assertIn("erro", body)

    def test_malformed_json_returns_400(self):
        response = self.client.post(
            "/sequencias", data="{", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("erro", json.loads(response.get_data(as_text=True)))

    def test_unknown_sequence_id_returns_empty_list(self):
        response, body = self.get_json(
            "/similares", sequencia_id="does-not-exist"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body, [])

    def test_builtin_sequence_id_matches_legacy(self):
        for key in self.main.sequencias:
            page = 1
            while True:
                _, legacy = self.get_json(
                    "/similares", sequencia=key, pagina=str(page)
                )
                _, by_id = self.get_json(
                    "/similares", sequencia_id=key, pagina=str(page)
                )
                self.assertEqual(legacy, by_id, (key, page))
                if not legacy:
                    break
                page += 1

    def test_legacy_sequence_is_unchanged(self):
        _, results = self.get_json("/similares", sequencia="EmG")
        self.assertEqual(len(results), 4)
        _, results = self.get_json("/similares", sequencia="BmGDA")
        self.assertEqual(len(results), 100)


    def test_concurrent_posts_create_all_sequences(self):
        base = ["D", "A", "Bm", "G", "Em", "C", "F", "Am", "C7", "Gm"]
        payloads = [
            {"nome": "Concorrente %d" % index,
             "acordes": base[:index + 1]}
            for index in range(10)
        ]

        def create(payload):
            client = self.main.app.test_client()
            response = client.post(
                "/sequencias", data=json.dumps(payload),
                content_type="application/json",
            )
            return response.status_code

        with ThreadPoolExecutor(max_workers=10) as pool:
            statuses = list(pool.map(create, payloads))

        self.assertEqual(statuses, [201] * 10)
        _, catalog = self.get_json("/sequencias")
        self.assertEqual(len(catalog), 16)

    def test_large_body_returns_413(self):
        response = self.post({
            "nome": "x" * (33 * 1024),
            "acordes": ["C"],
        })
        self.assertEqual(response.status_code, 413)
        self.assertIn("erro", json.loads(response.get_data(as_text=True)))

    def test_genre_filter_is_applied_to_custom_results(self):
        created = json.loads(self.post({
            "nome": "Filtro",
            "acordes": ["D", "A", "Bm", "G"],
        }).get_data(as_text=True))
        _, results = self.get_json(
            "/similares", sequencia_id=created["id"], generos="MPB"
        )
        self.assertTrue(results)
        self.assertTrue(all(item["genero"] == "MPB" for item in results))

    def test_acordes_precede_sequence_id(self):
        created = json.loads(self.post({
            "nome": "Precedência",
            "acordes": ["D", "A", "Bm", "G"],
        }).get_data(as_text=True))
        _, results = self.get_json(
            "/similares", acordes="C", sequencia_id=created["id"]
        )
        self.assertTrue(results)
        self.assertIn("diferenca", results[0])


if __name__ == "__main__":
    unittest.main()
