"""Gera a baseline de regressão das 6 sequências legadas a partir do código ATUAL.

Roda **antes** de qualquer mudança no matching, porque é o único artefato que
prova "mesmos resultados de antes":

    .venv/bin/python tests/fixtures/gerar_baseline.py

Produz `sequencias_legado.json` = {"<chave>": ["<id_unico_musica>", ...]}, com as
listas ordenadas (a ordem da API depende de PYTHONHASHSEED e não é comparável —
só o conjunto é).
"""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

import main  # noqa: E402  (precisa do sys.path acima e do CWD na raiz do repo)

SAIDA = Path(__file__).resolve().parent / "sequencias_legado.json"


def gerar():
    if not (RAIZ / "data" / "top" / "dataset_final.csv").exists():
        sys.exit("rode a partir da raiz do repositório (data/top/dataset_final.csv)")
    baseline = {}
    for chave, tag in main.sequencias.items():
        musicas = main.get_similares_por_sequencia(tag, main.generos)
        baseline[chave] = sorted(m["id_unico_musica"] for m in musicas)
        print(f"{chave:8s} tag={tag} {len(baseline[chave]):4d} músicas")

    SAIDA.write_text(
        json.dumps(baseline, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nescrito em {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    gerar()
