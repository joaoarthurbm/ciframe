# Roteiro simples do vídeo

## Antes de gravar (uma vez)

```
docker rm -f ciframe 2>/dev/null; docker volume rm ciframe-data 2>/dev/null
docker build -t ciframe .
docker run -d --name ciframe -p 8080:8080 -v ciframe-data:/var/lib/ciframe ciframe
```

Abra `http://localhost:8080/#/porsequencia`.

## Na gravação

1. **Mostre o catálogo.** "O catálogo de sequências agora vem do banco: seis
   sequências, com nome."
2. **Clique em "Sequência Em".** "Busca por Em G — quatro músicas."
3. **Digite `Em G` e clique em Cadastrar.** "Já existe: a tela avisa e seleciona a
   existente, sem duplicar."
4. **Digite `Em G D A` e cadastre.** "Sequência nova: entra no catálogo e busca —
   54 músicas."
5. **No terminal:**
   ```
   docker rm -f ciframe
   docker run -d --name ciframe2 -p 8080:8080 -v ciframe-data:/var/lib/ciframe ciframe
   ```
   **Volte ao navegador e dê F5.** "Container novo, mesmo volume: as 7 sequências
   continuam lá." Clique em `Em G D A` e mostre as 54 músicas.
6. **Feche:** "78 testes passando; `docs/features/sequencias-customizadas/` tem as
   cinco fases."

## Detalhes que evitam confusão

- Depois do aviso de duplicata o campo limpa sozinho — é o esperado.
- Depois do F5 a sequência nova fica no fim da lista (o servidor ordena por id).
- Se o catálogo começar com mais de 6, sobrou volume: `docker volume rm ciframe-data`
  e rode o container de novo.
