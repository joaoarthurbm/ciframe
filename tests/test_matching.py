"""A regra de matching, testada na função, sem passar pela API.

`musica_contem_sequencia` recebe a música e a **chave já normalizada** (separador
`;`, minúsculas) — quem normaliza é `normalizar_chave`, testado em `test_db.py`.
Aqui o que importa é a regra em si, com as duas condições juntas:

1. a sequência aparece de forma contígua na cifra;
2. **todo** acorde usado na música está na sequência.

A condição 2 é a que dá sentido a "músicas que você toca só com esses acordes"
e é a que faz uma sequência parcial não casar com uma música que usa mais
acordes do que ela.
"""

from types import SimpleNamespace

import pytest


def musica(cifra):
    """Objeto mínimo: a função só lê `cifra`."""
    return SimpleNamespace(cifra=cifra)


def test_sequencia_inteira_contigua(modulo):
    assert modulo.musica_contem_sequencia(musica(["C", "G", "Am", "F"]), "c;g;am;f")


def test_musica_pode_repetir_a_sequencia(modulo):
    # a música é a sequência em loop: continua casando
    assert modulo.musica_contem_sequencia(
        musica(["C", "G", "Am", "F", "C", "G"]), "c;g;am;f")


def test_sequencia_maior_que_a_musica_nao_casa(modulo):
    # a sequência tem que aparecer na música; 'D' no fim não aparece
    assert not modulo.musica_contem_sequencia(musica(["C", "G", "Am", "F"]), "c;g;am;f;d")


def test_sequencia_parcial_nao_casa_com_musica_de_varios_acordes(modulo):
    # 'c;g' é contíguo na cifra, mas a música usa Am e F, que não estão em 'c;g'
    assert not modulo.musica_contem_sequencia(musica(["C", "G", "Am", "F"]), "c;g")


def test_acordes_fora_de_ordem_nao_contam(modulo):
    # mesmo vocabulário, ordem diferente: a condição 1 falha
    assert not modulo.musica_contem_sequencia(musica(["G", "C", "A"]), "c;g;a")


def test_vocabulario_fora_da_sequencia_desqualifica(modulo):
    # a sequência é contígua, mas 'Em' não está nela: a condição 2 falha
    assert not modulo.musica_contem_sequencia(
        musica(["C", "G", "Am", "F", "Em"]), "c;g;am;f")


def test_musica_com_menos_acordes_que_a_sequencia(modulo):
    assert not modulo.musica_contem_sequencia(musica(["C", "G"]), "c;g;am;f")


def test_repeticao_na_cifra_importa(modulo):
    # 'c;g' aparece dentro de 'c;c;g'; a regra é sobre a cifra, que tem repetições
    assert modulo.musica_contem_sequencia(musica(["C", "C", "G"]), "c;g")
    # e a sequência pode exigir a repetição
    assert modulo.musica_contem_sequencia(musica(["C", "C", "G"]), "c;c;g")
    assert not modulo.musica_contem_sequencia(musica(["C", "G"]), "c;c;g")


def test_caixa_alta_na_cifra_nao_impede(modulo):
    assert modulo.musica_contem_sequencia(musica(["c", "g", "am"]), "c;g;am")
    assert modulo.musica_contem_sequencia(musica(["C", "G", "AM"]), "c;g;am")


def test_cifra_vazia_nunca_casa(modulo):
    assert not modulo.musica_contem_sequencia(musica([]), "c;g")


def test_fronteira_de_acorde_nao_casa_por_engano(modulo):
    # 'am' não pode casar com 'am7': o acorde é comparado inteiro, não como
    # prefixo de outro acorde
    assert not modulo.musica_contem_sequencia(musica(["Am7"]), "am")
    assert modulo.musica_contem_sequencia(musica(["Am7"]), "am7")


@pytest.mark.parametrize("cifra", [
    ["Bm", "G", "D", "A"],
    ["C", "G", "Am", "F"],
    ["Em", "G"],
])
def test_vocabulario_identico_sempre_casa(modulo, cifra):
    chave = ";".join(acorde.casefold() for acorde in cifra)
    assert modulo.musica_contem_sequencia(musica(cifra), chave)
