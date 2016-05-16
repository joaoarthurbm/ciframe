class Musica:
    def __init__(self, artista_id, musica_id, artista, 
            musica, genero, pop, seqs_famosas, tom, cifra):

            self.artista_id = artista_id
            self.musica_id = musica_id
            self.artista = artista
            self.musica = musica
            self.genero = genero
            self.pop = pop
            self.tom = tom
            self.cifra = cifra
            self.acordes = list(set(cifra))
            self.seqs_famosas = seqs_famosas

            self.id_musica = '%s_%s' % (artista_id, musica_id)

            self.url = 'http://www.cifraclub.com.br/%s/%s' % (artista_id, musica_id)
