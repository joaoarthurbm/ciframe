musicas_df <- read.csv("data/top/dataset_final.csv")
estilos_df <- read.csv("data/top/artista_musica_estilo.txt", header = FALSE)

names(estilos_df) <- c("ARTISTA","MUSICA","ESTILO")

musicas_df$ARTISTA <- as.character(musicas_df$ARTISTA)
estilos_df$ARTISTA <- as.character(estilos_df$ARTISTA)
estilos_df <- estilos_df[c(1,3)]

musicas_estilos_df <- left_join(musicas_df, estilos_df, by="ARTISTA")