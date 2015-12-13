#coding: utf-8
from bs4 import BeautifulSoup
import sys, os
import glob
import traceback

def get_famosas(acorde):
    seqs = ['bm;g;d;a','c;g;am;f', 'em;g' , 'c;a7;dm;g7', 'gm;f', 'c;c7;f;fm' ]
    out = []
    for i in range(len(seqs)):
        s = seqs[i]
        acorde = acorde.lower()
        if s in acorde:
            achou = True
            tem_seqs = []
            for l in acorde.split(';'):
                tokens = s.split(';')
                if l not in tokens:
                    achou = False
                    break
            if achou:
                tem_seqs.append(str(i))
                out.append("-".join(tem_seqs))
    return out

if len(sys.argv) != 2:
    print 'usage: python get_nomes_artistas_musicas.py cifras_dir'
    sys.exit()
reload(sys)  
sys.setdefaultencoding('utf8')

path = sys.argv[1]
dirs = os.listdir(path)
musicas = []
for d in dirs:
    art_dir = '%s/%s' % (path,d)
    for html_file in os.listdir(art_dir):
        if html_file.endswith('.html'):
            html = art_dir+"/"+html_file
            soup = BeautifulSoup(open(html), "html.parser")
            try:
                tokens = html.split('/')
                artista = tokens[-1].split('_')[0]
                musica = tokens[-1].split('_')[1][:-5]
                # tom
                tom_obj = soup.find(id="cifra_tom")
                tom = 'NA'
                if tom_obj != None:
                    tom = tom_obj.find('a').text.encode('utf-8')
                
                # estilo
                a_tag_obj = soup.find("div", { "id" : "breadcrumb" })
                nome_estilo = 'NA'
                if a_tag_obj:
                    nome_estilo = a_tag_obj.find_all('a')[1].find('span').text.strip()

                # nome artista
                nome_artista_obj = soup.find("h2", { "class" : "subtitulo" })
                nome_artista = 'NA'
                if nome_artista_obj:
                    nome_artista = nome_artista_obj.find('a').text.strip().replace(',','')
                
                # nome música
                nome_musica_obj = soup.find("h1", { "class" : "titulo" })
                nome_musica = 'NA'
                if nome_musica_obj:
                    nome_musica = nome_musica_obj.text.strip().replace(',','')

                # sequência de notas
                notas = soup.find(id="cifra_tom").parent.find_all('b')
                str_notas = ''
                for nota in notas:
                    str_notas += '%s;' % nota.text.encode('utf-8') 
                str_notas = str_notas.encode('utf-8')[0:-1]
                if str_notas == '':
                    str_notas = 'NA'

                # visualizações
                mydivs = soup.findAll("div", { "class" : "cifra_exib" })
                popularidade = 'NA'
                if len(mydivs) == 1:
                    popularidade = mydivs[0].find('strong').text.replace('.','')
                
                # sequencias famosas
                famosas = 'NA'
                famosas_list = get_famosas(str_notas)
                if famosas_list:
                    famosas = ''.join(get_famosas(str_notas))
                print ','.join([artista,musica,nome_artista,nome_musica,nome_estilo,popularidade,tom,famosas,str_notas])
            except Exception as e:
                print 'ERRO %s' % html

