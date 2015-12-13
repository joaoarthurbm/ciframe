import json
from flask import Flask, request

app = Flask(__name__)

ARTISTA_ID = 0
MUSICA_ID = 1
ARTISTA = 2
MUSICA = 3
GENERO = 4
POPULARIDADE = 5
TOM = 6
SEQ_FAMOSA = 7
CIFRA = 8

POR_PAGINA = 50

musicas = []
generos = set()

def init():
	global generos

	f = open('../data/top/dataset_final.csv')
	f.readline()

	for line in f:
		line = line.replace('"', '').replace('NA', '')[:-1]

		musica = line.split(',')
		musica[POPULARIDADE] = int(musica[POPULARIDADE].replace('.', ''))
		musica[CIFRA] = set(musica[CIFRA].split(';')) if musica[CIFRA] != '' else set()
		musica[SEQ_FAMOSA] = musica[SEQ_FAMOSA].split(";")

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
		'artista': m[ARTISTA],
		'musica': m[MUSICA],
		'genero': m[GENERO],
		'artista_id': m[ARTISTA_ID],
		'musica_id': m[MUSICA_ID],
		'facilidade': 1.0 * len(m[CIFRA] & acordes) / len(m[CIFRA]),
		'diferenca': list(m[CIFRA] - acordes)
	} for m in answer]

	minimo = float(request.args.get('min', 0))/ 100
	maximo = float(request.args.get('max', 100))/ 100

	answer = filter(lambda x: minimo <= x['facilidade'] <= maximo, answer)

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
	filtered = filter(lambda x: x[MUSICA].lower() == request.args.get('musica').lower(), musicas)

	return json.dumps([{
		'artista': m[ARTISTA],
		'musica': m[MUSICA],
		'genero': m[GENERO],
	} for m in filtered])

@app.route('/generos')
def get_generos():
	return json.dumps(generos)

@app.route('/porSequencia')
def por_sequencia():
	sequencia_famosa = request.args.get('sequencia')
	answer = filter(lambda x: sequencia_famosa in x[SEQ_FAMOSA], musicas)
	answer = applyFiltro('filtro-artistas', answer, ARTISTA)
	answer = applyFiltro('filtro-generos', answer, GENERO)

	return json.dumps(pagina([{
		'artista': m[ARTISTA],
		'musica': m[MUSICA],
		'genero': m[GENERO],
		'artista_id': m[ARTISTA_ID],
		'musica_id': m[MUSICA_ID],
	} for m in answer]))

@app.after_request
def add_header(response):
	response.headers['Access-Control-Allow-Origin'] = '*'
	return response

if __name__ == '__main__':
	init()
	app.run(debug=True)
