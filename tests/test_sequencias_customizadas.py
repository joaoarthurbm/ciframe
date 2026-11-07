import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TMP_DIR = tempfile.mkdtemp(prefix='ciframe-sequencias-tests-')
os.environ['SEQUENCIAS_DB_PATH'] = os.path.join(TMP_DIR, 'sequencias.db')

import main


def tearDownModule():
    shutil.rmtree(TMP_DIR, ignore_errors=True)


def _esvaziar_banco():
    conn = main._get_db_conn()
    try:
        conn.execute('DELETE FROM sequences')
        conn.commit()
    finally:
        conn.close()


def _chords_key_esperado(chords):
    return ' '.join(main._normalize_chords_list(chords))


class SequenciasCustomizadasTest(unittest.TestCase):

    def setUp(self):
        _esvaziar_banco()
        self.client = main.app.test_client()

    def _get_json(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.data)

    def _post_chords(self, chords):
        return self.client.post('/sequencias', json={'chords': chords})

    def _contar_linhas(self):
        conn = main._get_db_conn()
        try:
            return conn.execute('SELECT COUNT(*) FROM sequences').fetchone()[0]
        finally:
            conn.close()

    def test_usa_banco_temporario(self):
        self.assertTrue(os.path.abspath(main.DB_PATH).startswith(os.path.abspath(TMP_DIR)))
        self.assertNotEqual(
            os.path.abspath(main.DB_PATH),
            os.path.abspath(os.path.join(ROOT, 'data', 'sequencias.db')))

    def test_lista_catalogo_com_as_seis_originais(self):
        data = self._get_json('/sequencias')
        self.assertEqual([d['chords_key'] for d in data], list(main.SEQUENCIAS_ORIGINAIS))
        for item in data:
            self.assertEqual(item['origem'], 'original')
            self.assertEqual(item['chords'], main.SEQUENCIAS_ORIGINAIS[item['chords_key']])

    def test_regressao_das_seis_sequencias_originais(self):
        for key, index in main.sequencias.items():
            esperado = main.get_pagina(
                main.get_similares_por_sequencia(index, main.generos), '1')
            self.assertEqual(self._get_json('/similares?sequencia=' + key), esperado)

    def test_forma_com_virgulas_das_originais_retorna_o_mesmo(self):
        for key, chords in main.SEQUENCIAS_ORIGINAIS.items():
            esperado = self._get_json('/similares?sequencia=' + key)
            obtido = self._get_json('/similares?sequencia=' + ','.join(chords))
            self.assertEqual(obtido, esperado)

    def test_agrupamento_ambiguo_nao_cai_no_catalogo_original(self):
        self.assertEqual(self._get_json('/similares?sequencia=E,mG'), [])

    def test_cadastro_listagem_e_busca_customizada(self):
        response = self._post_chords(['Am', 'F', 'C', 'G'])
        self.assertEqual(response.status_code, 200)
        criado = json.loads(response.data)
        self.assertNotIn('duplicado', criado)
        self.assertEqual(criado['chords'], ['Am', 'F', 'C', 'G'])
        self.assertEqual(criado['chords_key'], 'Am F C G')

        catalogo = self._get_json('/sequencias')
        custom = [c for c in catalogo if c['origem'] == 'custom']
        self.assertEqual(len(custom), 1)
        self.assertEqual(custom[0]['chords'], ['Am', 'F', 'C', 'G'])
        self.assertEqual(custom[0]['chords_key'], 'Am F C G')

        com_virgula = self._get_json('/similares?sequencia=Am,F,C,G')
        concatenada = self._get_json('/similares?sequencia=AmFCG')
        self.assertIsInstance(com_virgula, list)
        self.assertEqual(com_virgula, concatenada)

    def test_busca_customizada_encontra_musica_da_cifra(self):
        sequencia = None
        musica = None
        originais = [list(v) for v in main.SEQUENCIAS_ORIGINAIS.values()]
        for candidata in main.musicas.values():
            tokens = [t for t in candidata.cifra
                      if main.CHORD_RE.match(t) and len(t) <= main.MAX_CHORD_LENGTH]
            if len(tokens) >= 2 and tokens[:2] not in originais:
                sequencia = tokens[:2]
                musica = candidata
                break
        self.assertIsNotNone(sequencia, 'nenhuma música com sequência válida encontrada')

        response = self._post_chords(sequencia)
        self.assertEqual(response.status_code, 200)

        similares = main.get_similares_por_sequencia_custom(sequencia, main.generos)
        ids = [s['id_unico_musica'] for s in similares]
        self.assertIn(musica.id_unico_musica, ids)

        pagina = self._get_json('/similares?sequencia=' + ','.join(sequencia))
        self.assertIsInstance(pagina, list)

    def test_duplicado_nao_cria_linha_redundante(self):
        self.assertEqual(self._post_chords(['Am', 'F']).status_code, 200)
        segunda = self._post_chords(['Am', 'F'])
        self.assertEqual(segunda.status_code, 200)
        self.assertTrue(json.loads(segunda.data)['duplicado'])
        self.assertEqual(self._contar_linhas(), 1)

    def test_duplicado_de_sequencia_original_e_rejeitado(self):
        response = self._post_chords(['Em', 'G'])
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['duplicado'])
        self.assertEqual(data['origem'], 'original')
        self.assertEqual(self._contar_linhas(), 0)

    def test_chaves_canonicas_nao_colidem(self):
        self.assertEqual(self._post_chords(['A', 'C']).status_code, 200)
        self.assertEqual(self._post_chords(['AC']).status_code, 200)
        chaves = {c['chords_key'] for c in self._get_json('/sequencias') if c['origem'] == 'custom'}
        self.assertEqual(chaves, {'A C', 'AC'})
        self.assertEqual(self._contar_linhas(), 2)

    def test_normaliza_espacos_do_cadastro(self):
        response = self._post_chords([' Am ', 'F'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['chords'], ['Am', 'F'])

    def test_validacao_rejeita_entradas_invalidas(self):
        self.assertEqual(self._post_chords([]).status_code, 400)
        self.assertEqual(self._post_chords(['C'] * 33).status_code, 400)
        self.assertEqual(self._post_chords(['<script>']).status_code, 400)
        self.assertEqual(self._post_chords(['C' * 21]).status_code, 400)
        self.assertEqual(self._post_chords([1, 2]).status_code, 400)
        self.assertEqual(self.client.post('/sequencias', json={'x': 1}).status_code, 400)
        self.assertEqual(self._contar_linhas(), 0)

    def test_aceita_corpo_de_formulario(self):
        response = self.client.post('/sequencias', data={'chords': 'Dm,G,C'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['chords'], ['Dm', 'G', 'C'])

    def test_compatibilidade_com_chave_legada_concatenada(self):
        conn = main._get_db_conn()
        try:
            conn.execute(
                'INSERT INTO sequences (chords, chords_key, created_at) VALUES (?,?,?)',
                ('Am,F,C,G', 'AmFCG', '2026-01-01T00:00:00'))
            conn.commit()
        finally:
            conn.close()

        result = self._get_json('/similares?sequencia=Am,F,C,G')
        self.assertIsInstance(result, list)

    def test_persistencia_apos_reinicializacao_do_banco(self):
        self.assertEqual(self._post_chords(['Dm', 'G', 'C']).status_code, 200)
        self.assertTrue(os.path.exists(main.DB_PATH))
        main.init_db()
        self.assertEqual(self._contar_linhas(), 1)

    def test_sequencia_vazia_retorna_lista(self):
        self.assertEqual(self._get_json('/similares?sequencia='), [])

    def test_sequencia_desconhecida_retorna_lista(self):
        self.assertEqual(self._get_json('/similares?sequencia=Zz,YY'), [])


if __name__ == '__main__':
    unittest.main()
