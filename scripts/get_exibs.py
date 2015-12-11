#coding: utf-8
from bs4 import BeautifulSoup
import sys, os
import glob
if len(sys.argv) != 2:
    print 'usage: python cifra_parser.py cifras_dir'
    sys.exit()

path = sys.argv[1]
dirs = os.listdir(path)
for d in dirs:
    art_dir = '%s/%s' % (path,d)
    for html_file in os.listdir(art_dir):
        html = art_dir+"/"+html_file
        soup = BeautifulSoup(open(html), "html.parser")
        try:
            tokens = html.split('/')
            artista = tokens[-1].split('_')[0]
            musica = tokens[-1].split('_')[1][:-5]
            out = artista + ',' + musica
            mydivs = soup.findAll("div", { "class" : "cifra_exib" })
            if len(mydivs) == 1:
                out += ',' + mydivs[0].find('strong').text
            print out
        except Exception as e:
            print 'ERRO %s' % html
