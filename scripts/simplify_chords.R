require(dplyr)

get_chord_num <- function(chord,key,key_trans_df) {
  chord_num <- key_trans_df[key_trans_df$KEY==as.character(key),as.character(chord)]
  return (if (length(chord_num) == 0) "NA" else chord_num)
}

get_simple_chords <- function(chords,key,key_trans) {
  chords_vec <- strsplit(as.character(chords), split = ";")[[1]] 
  simple_chords_vec <- vector(length = length(chords_vec))
  
  for (i in seq(1:length(chords_vec))) {
    base <- substr(chords_vec[i],1,1)
    primary_note <- strsplit(chords_vec[i],split="/")[[1]][1]
    simple_chord <- if (grepl("#",primary_note)) paste(base,".",sep="") else base
    chord_num <- get_chord_num(toupper(simple_chord),toupper(key),key_trans)
    
#     cat(sprintf("Key: %s\n",key))
#     cat(sprintf("Chord: %s\n",chords_vec[i]))
#     cat(sprintf("Has #: %s\n",grepl("#",primary_note)))
#     cat(sprintf("Simple Chord: %s\n",simple_chord))
#     cat(sprintf("Chord Num: %s\n",chord_num))
    
    simple_chords_vec[i] <- chord_num
  }
  
  return(simple_chords_vec)
}


musicas_df <- read.csv("data/top/dataset_final.csv")
key_trans_matrix <- read.csv("data/transposition_matrix2.csv", stringsAsFactors = FALSE)

cifras_simples_df = musicas_df %>% group_by(ARTISTA, MUSICA) %>% do(NCIFRA = paste(get_simple_chords(.$CIFRA,.$TOM,key_trans_matrix), collapse = ";"))

musicas_simples_df <- inner_join(musicas_df,cifras_simples_df,by=c("ARTISTA","MUSICA"))
