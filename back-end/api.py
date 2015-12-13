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

def init():
	global generos

	f = open('../data/top/dataset_final.csv')
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
	musicas.sort(key = lambda x: -x[POPULARIDADE])

def applyFiltro(nome_filtro, colecao, coluna):
	filtro = request.args.get(nome_filtro, '[]')
	filtro = set(json.loads(filtro))

	return filter(lambda x: x[coluna] in filtro, colecao) if len(filtro) > 0 else colecao

def pagina(colecao):
	inicio = (int(request.args.get('pagina', 1))-1) * POR_PAGINA
	return colecao[inicio:inicio+POR_PAGINA]

def metodo_mestre(acordes):

	answer = applyFiltro('filtro-artistas', musicas, ARTISTA)
	answer = applyFiltro('filtro-generos', answer, GENERO)

	answer = [{
		'artista': m[0],
		'musica': m[1],
		'genero': m[2],
		'facilidade': 1.0 * len(m[CIFRA] & acordes) / len(m[CIFRA]),
		'diferenca': list(m[CIFRA] - acordes)
	} for m in answer]

	answer.sort(key = lambda x: -x['facilidade'])
	return json.dumps(pagina(answer))


@app.route('/rankByMusica')
def get_by_nome():
	musica = request.args.get('musica')
	artista = request.args.get('artista')

	for m in musicas:
		if m[MUSICA] == musica and m[ARTISTA] == artista:
			return metodo_mestre(m[CIFRA])
	return '[]'


@app.route('/rankByAcordes')
def conjunto():
	acordes = request.args.get('acordes', '[]')
	acordes = set(json.loads(acordes))
	return metodo_mestre(acordes)

@app.route('/busca')
def busca():
	filtered = applyFiltro('musica', musicas, MUSICA)

	return json.dumps([{
		'artista': m[0],
		'musica': m[1],
		'genero': m[2],
	} for m in filtered])

@app.route('/getGeneros')
def get_generos():
	return json.dumps(generos)

if __name__ == '__main__':
	init()
	app.run(debug=True)
