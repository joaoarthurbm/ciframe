library(dplyr)

dff = read.csv("dataset_final.csv")

df_pop = dff %>% group_by(ARTISTA) %>% summarise(POPULARIDADE = sum(VISUALIZACOES)) %>% arrange(desc(POPULARIDADE))


dff %>% filter(ARTISTA == "nx-zero") %>% select(ARTISTA, MUSICA, VISUALIZACOES)


