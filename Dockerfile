FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# O catálogo de sequências fica em /app/instance. Declarar o volume aqui evita
# que um `docker run` sem `-v` grave o banco apenas na camada efêmera do
# container. Para remover/recriar o container sem perder dados, use o volume
# nomeado documentado no README (ou o docker-compose.yml).
VOLUME ["/app/instance"]

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
