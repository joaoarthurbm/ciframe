#coding: utf-8
from bs4 import BeautifulSoup
import sys, os
import glob
if len(sys.argv) != 2:
    print 'usage: python cifra_parser.py cifras_dir'
    sys.exit()


html = sys.argv[1]
soup = BeautifulSoup(open(html), "html.parser")
try:
    divs = soup.findAll("div", { "class" : "lista_estilos" })
    if len(divs) == 1:
        div = divs[0]
        for ul in div.find_all('ul'):
           for li in ul.find_all('li'):
               a = li.find('a')
               print 'https://www.cifraclub.com.br/estilos/' + a['href']
               
except Exception as e:
    print e
