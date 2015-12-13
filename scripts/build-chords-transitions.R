
get_chords_transitions <- function(chords) {
  chords_vec <- strsplit(as.character(chords), split = ";")[[1]]
  transitions <- vector(length = length(chords_vec))
  
  if (length(chords_vec) == 1) {
    transitions <- c("NA")
  } else if (length(chords_vec) > 1) {
    for (i in seq(1:length(chords_vec)-1)) {
      prevChord <- chords_vec[i]
      nextChord <- chords_vec[i+1]
      
#       cat(sprintf("Nota #: %s\n",i))
#       cat(sprintf("Prev-chord: %s\n",prevChord))
#       cat(sprintf("Next-chord: %s\n",nextChord))
      if (is.null(prevChord) | is.null(nextChord)) {
        transition <- "NA"
      } else if (prevChord == "" | nextChord == "" | is.na(prevChord) | is.na(nextChord) |
                 prevChord == "NA" | nextChord == "NA") {
        transition <- "NA"
      } else  {
        transition <- if (prevChord != nextChord) paste(prevChord,nextChord,sep=".") else "NA"
      }
      #cat(sprintf("Transition: %s\n",transition))
      
      transitions[i] <- transition
    }  
  }
  
  return (transitions)
}

get_transitions_hist <- function(chords_transitions) {
  transitions_hist <- vector(length=)
}

fill_transitions_df <- function(chords_transitions,chords_t_df) {
  #print(chords_transitions)
  for (i in seq(1:length(chords_transitions))) {
    curr_transition <- chords_transitions[i]
    #cat(sprintf("Curr Transition %d: %s\n",i,curr_transition))
    if (is.null(curr_transition) | is.na(curr_transition) | curr_transition == "NA" || curr_transition == "") next
    #cat(sprintf("Cell before: %s\n",chords_t_df[nrow(chords_t_df),as.character(curr_transition)]))
    chords_t_df[nrow(chords_t_df),as.character(curr_transition)] <- as.numeric(
      chords_t_df[nrow(chords_t_df),as.character(curr_transition)]) + 1
    #cat(sprintf("Cell later: %s\n",chords_t_df[nrow(chords_t_df),as.character(curr_transition)]))
  }
  return(chords_t_df)
}

build_transitions_df <- function(norm_chords_df, chords_trans_df) {
  for (i in seq(1:nrow(norm_chords_df))) {
    norm_chords <- norm_chords_df[i,"NCIFRA"]
    # cat(sprintf("Cifra Normalizada: %s\n",norm_chords))
    cat(sprintf("Musica #: %s\n",i))
#     print(norm_chords)
    transitions <- get_chords_transitions(norm_chords)
    #cat(sprintf("Length Transitions: %s\n",length(transitions)))
    #print(norm_chords[1])
    #print(transitions)
    
    chords_trans_df[i,] = rep(0,ncol(chords_trans_df))
    chords_trans_df <- fill_transitions_df(transitions,chords_trans_df)
  }
  return(chords_trans_df)
}



chords_transitions_empty <- read.csv("data/top/chords-transitions-empty.csv")
chords_transitions_empty[] <- lapply(chords_transitions_empty, function(x) as.numeric(x))

normalized_chords <- read.csv("data/dataset_seq_notas.csv")

chords_transitions_empty <- build_transitions_df(normalized_chords,chords_transitions_empty)

cifras_simples_df = musicas_df[1:100,] %>% group_by(ARTISTA, MUSICA) %>% do(print(.$ARTISTA))