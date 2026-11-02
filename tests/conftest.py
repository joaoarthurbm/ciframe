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
