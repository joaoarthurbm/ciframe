library(dplyr)

df_dataset = read.csv(file = "dataset.csv", header = F)
colnames(df_dataset) = c("ARTISTA", "MUSICA", "TOM", "CIFRA")

df_visu = read.csv(file = "visualizacoes.csv", header = F)
colnames(df_visu) = c("ARTISTA", "MUSICA", "VISUALIZACOES")

colnames(df_visu)
colnames(df_dataset)

df_out = inner_join(df_dataset, df_visu, by = c("ARTISTA", "MUSICA")) %>% select(ARTISTA, MUSICA, VISUALIZACOES, TOM, CIFRA)

nrow(df_out)
write.csv(df_out, file = "dataset_final.csv", row.names = F)
  

