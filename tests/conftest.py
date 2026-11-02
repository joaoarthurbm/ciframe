"""Fixtures da suíte.

Duas regras que valem para todos os testes:

1. O banco real **nunca** é aberto: `CIFRAME_DB` é apontada para um diretório
   temporário **antes** de `main` ser importado (o caminho é lido no import).
2. O CSV é carregado uma única vez por sessão (`scope="session"`): importar
   `main` custa ~1,2 s, e cada teste pagaria esse preço em um fixture de função.
"""

import importlib
import json
import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    return tmp_path_factory.mktemp("ciframe-db") / "ciframe.db"


@pytest.fixture(scope="session")
def modulo(db_path):
    """Importa `main` com o banco isolado e devolve o módulo."""
    os.environ["CIFRAME_DB"] = str(db_path)
    os.chdir(RAIZ)  # main.py abre o CSV por caminho relativo
    modulo = importlib.import_module("main")
    modulo.app.config.update(TESTING=True)
    return modulo


@pytest.fixture(scope="session")
def client(modulo):
    return modulo.app.test_client()


@pytest.fixture(scope="session")
def baseline():
    """Conjuntos de `id_unico_musica` das 6 sequências, gerados do código antigo."""
    return json.loads((FIXTURES / "sequencias_legado.json").read_text(encoding="utf-8"))


@pytest.fixture
def banco_limpo(modulo, tmp_path, monkeypatch):
    """Banco novo por teste, já com o schema e as 6 sementes.

    `db_path()` resolve a env var a cada conexão, então trocar `CIFRAME_DB`
    isola o teste sem reiniciar o processo (e sem tocar no banco da sessão).
    """
    caminho = tmp_path / "ciframe.db"
    monkeypatch.setenv("CIFRAME_DB", str(caminho))
    modulo.criar_schema()
    modulo.seed_sequencias_legado()
    return caminho


@pytest.fixture
def client_limpo(modulo, banco_limpo):
    return modulo.app.test_client()


@pytest.fixture
def coletar():
    """Percorre todas as páginas de /similares e devolve a lista de ids.

    A API pagina de 100 em 100; comparar só a primeira página esconderia
    diferença no fim do conjunto.
    """

    def _coletar(client, **params):
        ids = []
        pagina = 1
        while True:
            consulta = dict(params, pagina=str(pagina))
            resposta = client.get("/similares", query_string=consulta)
            assert resposta.status_code == 200, (consulta, resposta.status_code)
            lote = json.loads(resposta.data.decode())
            ids.extend(musica["id_unico_musica"] for musica in lote)
            if len(lote) < 100:
                return ids
            pagina += 1

    return _coletar


def corpo_json(resposta):
    """A API responde `Content-Type: text/html`, então `.get_json()` devolve None."""
    return json.loads(resposta.data.decode())

