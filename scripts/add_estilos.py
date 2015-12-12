import csv
from collections import defaultdict

def readCSVIntoDict(csv_file):
    columns = defaultdict(list) # each value in each column is appended to a list
    
    with open(csv_file) as f:
        reader = csv.DictReader(f) # read rows into a dictionary format
        for row in reader: # read a row as {column1: value1, column2: value2,...}
            for (k,v) in row.items(): # go over each column name and value 
                columns[k].append(v) # append the value into the appropriate list
                                     # based on column name k    

    return columns

def findArtistStyle(artist, styles_map):
    ctr = 0
    for artist2 in styles_map["artista"]:
        if (artist2 == artist):
            return styles_map["estilo"][ctr]
        ctr += 1
            
def findStyles(artists, styles_map):
    styles_list = list()
    for artist in artists:
        styles_list.append(findArtistStyle(artist,styles_map))

    return styles_list


songs = readCSVIntoDict("dataset_final.csv")
styles = readCSVIntoDict("artista_musica_estilo.txt")

songs_styles = findStyles(songs["ARTISTA"],styles)

print len(songs_styles)
print len(songs["ARTISTA"])

songs["ESTILO"] = songs_styles

keys = sorted(songs.keys())
with open("test.csv", "wb") as outfile:
   writer = csv.writer(outfile, delimiter = ",")
   writer.writerow(keys)
   writer.writerows(zip(*[songs[key] for key in keys]))
