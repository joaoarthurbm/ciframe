import json
from flask import Flask, request

app = Flask(__name__)

ARTISTA = 0
MUSICA = 1
GENERO = 2
TOM = 3
POPULARIDADE = 4
CIFRA = 5

POR_PAGINA = 50

musicas = []
generos = set()

def applyFiltro(nome_filtro, colecao, coluna):
	filtro = request.args.get(nome_filtro, '[]')
	filtro = set(json.loads(filtro))
	if len(filtro) > 0:
		return filter(lambda x: x[coluna] in filtro, colecao)
	return colecao

def init():
	global generos

	f = open('/home/arthur/Modelos/ciframe/data/top/dataset_final.csv')
	f.readline()

	for line in f:
		line = line.replace('"', '')[:-1]

		musica = line.split(',')
		musica[POPULARIDADE] = int(musica[POPULARIDADE].replace('.', ''))
		musica[CIFRA] = set(musica[CIFRA].split(';')) if musica[CIFRA] != '' else set()
		
		if musica[GENERO] != '' : 
			generos.add(musica[GENERO])
		
		# TRATAR NOS DADOS
		if len(musica[CIFRA]) > 0:
			musicas.append(musica)

	f.close()
	generos = list(generos)

def metodo_mestre(acordes):
	inicio = (int(request.args.get('pagina', 1))-1) * POR_PAGINA

	ranking = []
	for m in musicas:
		m = m[:-1] + [list(m[CIFRA] - acordes), 1.0 * len(m[CIFRA] & acordes) / len(m[CIFRA])]
		ranking.append(m)

	ranking.sort(key = lambda x : (-x[-1], -x[POPULARIDADE]))

	answer = [{
		'artista': r[0],
		'musica': r[1],
		'genero': r[2],
		'facilidade': r[6],
		'diferenca': r[5]
	} for r in ranking]

	answer = applyFiltro('filtro-artistas', answer, 'artista')
	answer = applyFiltro('filtro-generos', answer, 'genero')

	return json.dumps(answer[inicio:inicio+POR_PAGINA])


@app.route('/getByMusica')
def get_by_nome():
	nome_musica = request.args.get('nome-musica', '')
	for musica in musicas:
		if musica[MUSICA] == nome_musica:
			return metodo_mestre(musica[CIFRA])
	return '[]'


@app.route('/rankByFacilidade')
def conjunto():
	acordes_in = request.args.get('acordes', '[]')
	acordes_in = set(json.loads(acordes_in))
	return metodo_mestre(acordes_in)

@app.route('/getGeneros')
def get_generos():
	return json.dumps(generos)

if __name__ == '__main__':
	init()
	app.run(debug=True)

