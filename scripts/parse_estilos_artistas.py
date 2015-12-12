#coding: utf-8
from bs4 import BeautifulSoup
import sys, os
import glob
if len(sys.argv) != 2:
    print 'usage: python cifra_parser.py cifras_dir'
    sys.exit()

folder = os.listdir()

html = sys.argv[1]
soup = BeautifulSoup(open(html), "html.parser")
try:
    
    divs = soup.findAll("a", { "class" : "html-attribute-value html-external-link" })
    if len(divs) >= 1:
        for div in divs:	
            if "/estilos/" in div['href'] and len(div['href'][36:-1]) > 0:
                print div['href'][36:-1]
               
except Exception as e:
    print e
