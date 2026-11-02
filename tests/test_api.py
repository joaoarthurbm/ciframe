"""Contrato HTTP: catálogo, cadastro e busca por sequencia_id."""

import json

import pytest

from conftest import corpo_json


def test_get_sequencias_devolve_as_seis_com_ids_ordeiros(client_limpo):
    resposta = client_limpo.get("/sequencias")
    assert resposta.status_code == 200
    # herança: o corpo é json.dumps, então o MIME continua text/html
    assert resposta.headers["Content-Type"].startswith("text/html")

    catalogo = corpo_json(resposta)
    assert [registro["id"] for registro in catalogo] == [1, 2, 3, 4, 5, 6]
    assert set(catalogo[0]) == {"id", "nome", "acordes", "chave", "criado_em"}
    assert catalogo[0]["acordes"] == ["Bm", "G", "D", "A"]


def test_post_cria_e_devolve_o_registro(client_limpo):
    resposta = client_limpo.post("/sequencias", json={"acordes": ["D", "A", "Bm"]})
    assert resposta.status_code == 201

    criado = corpo_json(resposta)
    assert criado["id"] == 7
    assert criado["acordes"] == ["D", "A", "Bm"]
    assert criado["chave"] == "d;a;bm"
    # nome derivado dos acordes quando não vem no corpo
    assert criado["nome"] == "D - A - Bm"

    catalogo = corpo_json(client_limpo.get("/sequencias"))
    assert len(catalogo) == 7
    assert catalogo[-1] == criado


def test_post_aceita_nome_proprio_e_apara_espacos(client_limpo):
    resposta = client_limpo.post(
        "/sequencias", json={"acordes": [" C ", " G "], "nome": "  Minha  "})
    assert resposta.status_code == 201
    criado = corpo_json(resposta)
    assert criado["acordes"] == ["C", "G"]
    assert criado["nome"] == "Minha"


def test_post_duplicado_devolve_409_com_o_id_do_existente(client_limpo):
    resposta = client_limpo.post("/sequencias", json={"acordes": ["Em", "G"]})
    assert resposta.status_code == 409
    corpo = corpo_json(resposta)
    assert corpo["id"] == 3          # id da 'Sequência Em' semeada
    assert corpo["chave"] == "em;g"
    assert corpo["nome"] == "Sequência Em"
    assert len(corpo_json(client_limpo.get("/sequencias"))) == 6


@pytest.mark.parametrize("acordes", [
    ["em", "g"],           # caixa diferente
    [" Em ", " G "],       # espaços nas pontas
    ["Em", "G"],           # idêntica
])
def test_duplicata_ignora_caixa_e_espacos(client_limpo, acordes):
    assert client_limpo.post("/sequencias", json={"acordes": acordes}).status_code == 409


@pytest.mark.parametrize("corpo,campo", [
    ({"acordes": ["Em"]}, "acordes"),
    ({"acordes": ["C"] * 13}, "acordes"),
    ({"acordes": []}, "acordes"),
    ({"acordes": ["Em", "Xyz"]}, "acordes"),
    ({"acordes": ["Em", "G", ""]}, "acordes"),
    ({"acordes": ["Em", 7]}, "acordes"),
    ({"acordes": "Em,G"}, "acordes"),
    ({}, "acordes"),
    ({"acordes": ["C", "G"], "nome": "x" * 81}, "nome"),
    ({"acordes": ["C", "G"], "nome": 42}, "nome"),
])
def test_post_invalido_devolve_400_com_o_campo(client_limpo, corpo, campo):
    resposta = client_limpo.post("/sequencias", json=corpo)
    assert resposta.status_code == 400
    assert corpo_json(resposta)["campo"] == campo
    assert len(corpo_json(client_limpo.get("/sequencias"))) == 6


def test_post_de_acorde_desconhecido_cita_o_acorde(client_limpo):
    resposta = client_limpo.post("/sequencias", json={"acordes": ["Em", "Xyz"]})
    assert corpo_json(resposta)["acorde"] == "Xyz"


def test_post_sem_json_devolve_400(client_limpo):
    resposta = client_limpo.post("/sequencias", data="acordes=Em,G",
                                 content_type="application/json")
    assert resposta.status_code == 400


def test_corrida_no_banco_tambem_vira_409(client_limpo, modulo, monkeypatch):
    """Duas requisições simultâneas: o UNIQUE do banco decide, não o pré-check.

    Simula a corrida fazendo o `por_chave` da checagem não achar nada; o INSERT
    então bate no índice UNIQUE e o caminho de exceção precisa devolver o 409.
    """
    original = modulo.por_chave
    chamadas = {"n": 0}

    def por_chave_com_corrida(chave):
        chamadas["n"] += 1
        return None if chamadas["n"] == 1 else original(chave)

    monkeypatch.setattr(modulo, "por_chave", por_chave_com_corrida)

    resposta = client_limpo.post("/sequencias", json={"acordes": ["Em", "G"]})
    assert resposta.status_code == 409
    assert corpo_json(resposta)["id"] == 3



def test_post_aceita_os_limites_de_tamanho(client_limpo):
    assert client_limpo.post(
        "/sequencias", json={"acordes": ["C", "G"]}).status_code == 201
    doze = ["C", "G"] * 6
    assert client_limpo.post("/sequencias", json={"acordes": doze}).status_code == 201


def test_sequencia_id_devolve_o_mesmo_resultado_que_sequencia(client_limpo, coletar):
    por_id = coletar(client_limpo, sequencia_id=6)
    por_chave = coletar(client_limpo, sequencia="CC7FFm")
    assert por_id == por_chave
    assert len(por_id) == 3


def test_sequencia_id_inexistente_devolve_404(client_limpo):
    resposta = client_limpo.get("/similares", query_string={"sequencia_id": 999})
    assert resposta.status_code == 404
    assert corpo_json(resposta)["campo"] == "sequencia_id"


def test_sequencia_id_nao_numerico_devolve_400(client_limpo):
    resposta = client_limpo.get("/similares", query_string={"sequencia_id": "abc"})
    assert resposta.status_code == 400
    assert corpo_json(resposta)["campo"] == "sequencia_id"


def test_precedencia_acordes_vence_sequencia_id(client_limpo):
    resposta = client_limpo.get("/similares", query_string={
        "acordes": "C,G,Am,F", "sequencia_id": 3, "sequencia": "GmF"})
    resultado = corpo_json(resposta)
    # o caminho 'acordes' acrescenta 'diferenca', que os caminhos de sequência não têm
    assert "diferenca" in resultado[0]


def test_legado_sequencia_desconhecida_devolve_lista_vazia(client_limpo):
    for valor in ["CGDF", "", "zzz"]:
        resposta = client_limpo.get("/similares", query_string={"sequencia": valor})
        assert resposta.status_code == 200
        assert corpo_json(resposta) == []


@pytest.mark.parametrize("valor", ["EmG", "Em,G", "em g"])
def test_sequencia_aceita_concatencao_e_separadores(client_limpo, valor, coletar):
    assert len(coletar(client_limpo, sequencia=valor)) == 4


def test_resultado_de_sequencia_nao_tem_diferenca(client_limpo):
    resultado = corpo_json(client_limpo.get(
        "/similares", query_string={"sequencia_id": 3}))
    assert resultado
    assert "diferenca" not in resultado[0]
    assert len(resultado[0]) == 9


def test_pagina_recorta_o_resultado(client_limpo, coletar):
    primeira = corpo_json(client_limpo.get(
        "/similares", query_string={"sequencia_id": 1, "pagina": 1}))
    segunda = corpo_json(client_limpo.get(
        "/similares", query_string={"sequencia_id": 1, "pagina": 2}))
    assert len(primeira) == 100
    assert len(segunda) == 99
    assert not {m["id_unico_musica"] for m in primeira} & {
        m["id_unico_musica"] for m in segunda}
    assert len(coletar(client_limpo, sequencia_id=1)) == 199


def test_filtro_por_genero_reduz_o_resultado(client_limpo, modulo, coletar):
    todos = coletar(client_limpo, sequencia_id=3)
    genero = modulo.musicas[todos[0]].genero
    filtrado = coletar(client_limpo, sequencia_id=3, generos=genero)
    assert set(filtrado) <= set(todos)
    assert all(modulo.musicas[chave].genero == genero for chave in filtrado)
