"""Regressão obrigatória: as 6 sequências originais devolvem os mesmos conjuntos.

A baseline `fixtures/sequencias_legado.json` foi gerada **antes** da migração,
executando o código que comparava a coluna `SEQ_FAMOSA` do CSV. Comparar por
**conjunto** de `id_unico_musica` (e não por lista) é deliberado: a ordem do
resultado depende de `PYTHONHASHSEED`, então comparar listas acusaria diferença
onde não há.
"""

import pytest

from conftest import corpo_json

# chave na forma concatenada (a da baseline) e os acordes, para as duas URLs
LEGADAS = [
    ("BmGDA", "Bm,G,D,A", 199),
    ("CGAmF", "C,G,Am,F", 296),
    ("EmG", "Em,G", 4),
    ("CA7DmG7", "C,A7,Dm,G7", 5),
    ("GmF", "Gm,F", 7),
    ("CC7FFm", "C,C7,F,Fm", 3),
]


@pytest.mark.parametrize("concatenada,separada,total", LEGADAS)
def test_sequencia_legada_mantem_o_conjunto(client_limpo, coletar, baseline,
                                            concatenada, separada, total):
    esperado = set(baseline[concatenada])
    assert len(esperado) == total

    por_concatenacao = coletar(client_limpo, sequencia=concatenada)
    por_virgula = coletar(client_limpo, sequencia=separada)

    assert set(por_concatenacao) == esperado
    assert set(por_virgula) == esperado


@pytest.mark.parametrize("concatenada,separada,total", LEGADAS)
def test_sequencia_id_mantem_o_conjunto(client_limpo, coletar, baseline,
                                       concatenada, separada, total):
    catalogo = corpo_json(client_limpo.get("/sequencias"))
    registro = next(s for s in catalogo if s["chave"] == ";".join(
        acorde.casefold() for acorde in separada.split(",")))

    assert set(coletar(client_limpo, sequencia_id=registro["id"])) == set(
        baseline[concatenada])


def test_todas_as_legadas_cobrem_o_catalogo_semeado(client_limpo, baseline):
    catalogo = corpo_json(client_limpo.get("/sequencias"))
    chaves = {";".join(acorde.casefold() for acorde in separada.split(","))
              for _, separada, _ in LEGADAS}
    assert {registro["chave"] for registro in catalogo} == chaves


def test_nenhuma_legada_devolve_tudo(client_limpo, modulo, coletar):
    # guarda contra a regressão mais grosseira: filtro que não filtra
    total_de_musicas = len(modulo.musicas)
    for _, separada, _ in LEGADAS:
        assert len(coletar(client_limpo, sequencia=separada)) < total_de_musicas / 10
