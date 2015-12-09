#zeze-di-camargo-e-luciano-voce-vai-ver.html
from bs4 import BeautifulSoup
import sys
soup = BeautifulSoup(open(sys.argv[1]), "html.parser")
try:
    print 'Tom %s' % soup.find(id="cifra_tom").find('a').text
    notas = soup.find(id="cifra_tom").parent.find_all('b')
    for nota in notas:
        print nota.text, 
except:
    print sys.argv[1]
