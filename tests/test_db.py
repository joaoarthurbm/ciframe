"""Camada de persistência: caminho, schema, seed e normalização."""

import os
import sqlite3

import pytest


def ler(caminho):
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(linha) for linha in conn.execute(
            "SELECT * FROM sequencias ORDER BY id")]
    finally:
        conn.close()


def test_caminho_vem_da_env_var(modulo, tmp_path, monkeypatch):
    alvo = tmp_path / "outro" / "banco.db"
    monkeypatch.setenv("CIFRAME_DB", str(alvo))
    assert modulo.db_path() == str(alvo)


def test_caminho_padrao_e_fora_do_diretorio_do_csv(modulo, monkeypatch):
    monkeypatch.delenv("CIFRAME_DB", raising=False)
    assert modulo.db_path() == "/var/lib/ciframe/ciframe.db"
    # /app/data guarda o dataset; um volume ali esconderia o CSV
    assert not modulo.db_path().startswith("/app/data")


def test_falha_no_boot_quando_diretorio_nao_e_gravavel(modulo, tmp_path, monkeypatch):
    if os.geteuid() == 0:
        pytest.skip("root ignora permissão de diretório")

    bloqueado = tmp_path / "sem-escrita"
    bloqueado.mkdir()
    bloqueado.chmod(0o500)
    try:
        monkeypatch.setenv("CIFRAME_DB", str(bloqueado / "sub" / "banco.db"))
        with pytest.raises(SystemExit) as erro:
            modulo.prepara_diretorio_db()
        assert "não foi possível criar o diretório" in str(erro.value)
    finally:
        bloqueado.chmod(0o700)


def test_cria_diretorios_que_faltam(modulo, tmp_path, monkeypatch):
    alvo = tmp_path / "a" / "b" / "banco.db"
    monkeypatch.setenv("CIFRAME_DB", str(alvo))
    modulo.prepara_diretorio_db()
    with modulo.conexao() as conn:
        assert conn.execute("SELECT 1").fetchone()[0] == 1
    assert alvo.exists()


def test_seed_cria_as_seis_com_ids_estaveis(modulo, banco_limpo):
    linhas = ler(banco_limpo)
    assert [linha["id"] for linha in linhas] == [1, 2, 3, 4, 5, 6]
    assert [linha["chave"] for linha in linhas] == [
        "bm;g;d;a", "c;g;am;f", "em;g", "c;a7;dm;g7", "gm;f", "c;c7;f;fm",
    ]
    assert all(linha["nome"] for linha in linhas)
    assert all(linha["criado_em"].endswith("Z") for linha in linhas)


def test_seed_e_idempotente(modulo, banco_limpo):
    for _ in range(3):
        modulo.seed_sequencias_legado()
    linhas = ler(banco_limpo)
    assert len(linhas) == 6
    assert [linha["id"] for linha in linhas] == [1, 2, 3, 4, 5, 6]


def test_schema_pode_ser_criado_duas_vezes(modulo, banco_limpo):
    modulo.criar_schema()  # IF NOT EXISTS: não explode na segunda subida
    assert len(ler(banco_limpo)) == 6


def test_acordes_sobrevivem_como_lista(modulo, banco_limpo):
    registro = modulo.por_chave("bm;g;d;a")
    assert registro["acordes"] == ["Bm", "G", "D", "A"]


def test_listar_ordena_por_id(modulo, banco_limpo):
    ids = [registro["id"] for registro in modulo.listar_sequencias()]
    assert ids == sorted(ids)


def test_procura_que_nao_acha_devolve_none(modulo, banco_limpo):
    assert modulo.por_chave("x;y") is None
    assert modulo.por_id(9999) is None


@pytest.mark.parametrize("acordes,esperado", [
    (["C", "G"], "c;g"),
    (["c", "g"], "c;g"),
    ([" C ", " G "], "c;g"),
    (["C", "C"], "c;c"),
    (["C", "G", "F"], "c;g;f"),
])
def test_normalizar_chave(modulo, acordes, esperado):
    assert modulo.normalizar_chave(acordes) == esperado


def test_normalizar_chave_distingue_ordem_e_repeticao(modulo):
    assert modulo.normalizar_chave(["C", "G"]) != modulo.normalizar_chave(["G", "C"])
    assert modulo.normalizar_chave(["C", "C"]) != modulo.normalizar_chave(["C"])


def test_resolver_chave_aceita_as_duas_formas_de_url(modulo, banco_limpo):
    assert modulo.resolver_chave("BmGDA") == "bm;g;d;a"
    assert modulo.resolver_chave("Bm,G,D,A") == "bm;g;d;a"
    assert modulo.resolver_chave("bm,g,d,a") == "bm;g;d;a"
    assert modulo.resolver_chave("CGDF") is None
    assert modulo.resolver_chave("") is None


def test_vocabulario_de_acordes_vem_do_csv(modulo):
    assert "c" in modulo.ACORDES_CANONICOS
    assert "bm" in modulo.ACORDES_CANONICOS
    assert "xyz" not in modulo.ACORDES_CANONICOS
