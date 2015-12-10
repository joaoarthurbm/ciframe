#coding: utf-8
from bs4 import BeautifulSoup
import sys
if len(sys.argv) != 2:
    print 'usage: python cifra_parser.py cifra.html'
    sys.exit()

soup = BeautifulSoup(open(sys.argv[1]), "html.parser")
try:
    out = sys.argv[1]
    out += ',%s,' % soup.find(id="cifra_tom").find('a').text.encode('utf-8')
    notas = soup.find(id="cifra_tom").parent.find_all('b')
    for nota in notas:
        out += '%s;' % nota.text.encode('utf-8') 
    print out[0:-1]
except Exception as e:
    print 'ERRO %s' % sys.argv[1]
