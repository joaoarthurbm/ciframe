class Musica:

    def __init__(self, id_artista, nome_artista, id_musica, nome_musica,
    
            genero, popularidade, seqs_famosas, tom, cifra):

            self.id_artista = id_artista
            self.nome_artista = nome_artista
            
            self.id_musica = id_musica
            self.nome_musica = nome_musica

            self.genero = genero
            self.popularidade = popularidade
            self.tom = tom
            self.cifra = cifra
            self.acordes = list(set(cifra))
            self.seqs_famosas = seqs_famosas

            self.id_unico_musica = '%s_%s' % (id_artista, id_musica)

            self.url = 'http://www.cifraclub.com.br/%s/%s' % (id_artista, id_musica)

    def __str__(self):
        return '%s,%s,%s' % (self.id_unico_musica, self.genero, self.popularidade)
