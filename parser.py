import sys
start = 'www.cifraclub.com.br'
for linha in open(sys.argv[1]):
    if '<a href=' in linha and len(linha) < 200:
        tokens = linha.split('/')
        print start+'/'+tokens[1]
