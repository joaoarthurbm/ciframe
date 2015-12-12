import sys
seqs = ['c;a7;dm;g7','bm;g;d;a','c;g;am;f']

for linha in open(sys.argv[1]):
    acordes = linha.strip().lower().split(',')[-1].replace("\"","")
    for s in seqs:
        if s in acordes:
            achou = True
            tem_seqs = []
            for l in acordes.split(';'):
                tokens = s.split(';')
                if l not in tokens:
                    achou = False
                    break
                tem_seqs.append(s)
            if achou:
                tokens = linha.split(',')
                artista = tokens[0]
                musica = tokens[1]
                print ",".join([artista, musica,"-".join(tem_seqs)])

