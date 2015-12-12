#coding: utf-8
from bs4 import BeautifulSoup
import sys, os
import glob
if len(sys.argv) != 2:
    print 'usage: python cifra_parser.py cifras_dir'
    sys.exit()

path = sys.argv[1]
files = os.listdir(path)
for f in files:
    if os.path.isfile(path  + f):
        
        html = path+f
        print html
        '''
        soup = BeautifulSoup(open(html), "html.parser")
        try:
            tokens = html.split('/')
            artista = tokens[-1].split('_')[0]
            musica = tokens[-1].split('_')[1][:-5]
            out = artista + ',' + musica
            out += ',%s,' % soup.find(id="cifra_tom").find('a').text.encode('utf-8')
            notas = soup.find(id="cifra_tom").parent.find_all('b')
            for nota in notas:
                out += '%s;' % nota.text.encode('utf-8') 
            print out[0:-1]
        except Exception as e:
            print 'ERRO %s' % html'''
