FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Catálogo de sequências cadastradas (SQLite). Sem um volume nomeado no
# `docker run -v ciframe-data:/var/lib/ciframe`, esses dados morrem com o
# container. Ver docs/adr/0002-persist-custom-sequences.md.
VOLUME /var/lib/ciframe

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
