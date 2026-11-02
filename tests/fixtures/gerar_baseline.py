"""Gera a baseline de regressão das 6 sequências legadas a partir do código ATUAL.

O arquivo `sequencias_legado.json` foi gerado **antes** da migração para o banco,
executando o código antigo (que comparava a coluna SEQ_FAMOSA). Ele é a única
evidência de "mesmos resultados de antes", então este script **se recusa a
sobrescrevê-lo**:

    .venv/bin/python tests/fixtures/gerar_baseline.py            # falha, por padrão
    .venv/bin/python tests/fixtures/gerar_baseline.py --force     # só se souber o que faz

Regerar depois da migração produziria uma baseline do código novo — ou seja,
compararia a implementação com ela mesma e o teste de regressão passaria a não
provar nada.
"""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

import main  # noqa: E402  (precisa do sys.path acima e do CWD na raiz do repo)

SAIDA = Path(__file__).resolve().parent / "sequencias_legado.json"


def gerar(forcar=False):
    if SAIDA.exists() and not forcar:
        sys.exit(
            '%s já existe e é a baseline do código ANTES da migração.\n'
            'Regerar agora compararia o código novo com ele mesmo. '
            'Use --force apenas se souber exatamente por quê.' % SAIDA.name
        )
    if not (RAIZ / "data" / "top" / "dataset_final.csv").exists():
        sys.exit("rode a partir da raiz do repositório (data/top/dataset_final.csv)")

    baseline = {}
    for sequencia in main.SEQUENCIAS_LEGADO:
        chave_url = ''.join(sequencia['acordes'])          # 'BmGDA', forma antiga
        chave = main.normalizar_chave(sequencia['acordes'])  # 'bm;g;d;a'
        musicas = main.get_similares_por_chave(chave, main.generos)
        baseline[chave_url] = sorted(m["id_unico_musica"] for m in musicas)
        print(f"{chave_url:8s} {len(baseline[chave_url]):4d} músicas")

    SAIDA.write_text(
        json.dumps(baseline, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nescrito em {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    gerar(forcar="--force" in sys.argv[1:])
