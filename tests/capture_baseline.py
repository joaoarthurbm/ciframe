# coding: utf-8

"""Capture the current results of the six legacy sequences.

Run from the repository root, before changing the application:

    /tmp/opencode/deciframe-venv/bin/python tests/capture_baseline.py

The generated fixture is used by the regression tests.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import main  # noqa: E402


FIXTURE_PATH = os.path.join(
    ROOT, "tests", "fixtures", "sequencias_baseline.json"
)


def capture_sequence(client, key, tag):
    pages = []
    page = 1
    while True:
        response = client.get(
            "/similares",
            query_string={"sequencia": key, "pagina": str(page)},
        )
        assert response.status_code == 200, (key, page, response.status_code)
        items = json.loads(response.get_data(as_text=True))
        if not items:
            break
        pages.append([item["id_unico_musica"] for item in items])
        page += 1
    return {
        "tag": tag,
        "count": sum(len(p) for p in pages),
        "pages": pages,
    }


def main_capture():
    client = main.app.test_client()
    fixture = {"sequences": {}}
    for key, tag in main.sequencias.items():
        fixture["sequences"][key] = capture_sequence(client, key, tag)

    os.makedirs(os.path.dirname(FIXTURE_PATH), exist_ok=True)
    with open(FIXTURE_PATH, "w", encoding="utf-8") as handle:
        json.dump(fixture, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    for key, item in fixture["sequences"].items():
        print("%s: %s songs in %s page(s)" % (
            key, item["count"], len(item["pages"])
        ))


if __name__ == "__main__":
    main_capture()
