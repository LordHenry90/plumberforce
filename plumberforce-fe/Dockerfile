# Usa un'immagine Python slim come base
FROM python:3.10-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia solo il file dei requisiti per sfruttare la cache di Docker
COPY requirements.txt .

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice dell'applicazione
COPY . .

# Railway fornirà la variabile $PORT. Uvicorn la userà automaticamente.
# Non è necessario esporre la porta esplicitamente, ma è buona norma.
EXPOSE 8000

#
# --- COMANDO DI AVVIO CORRETTO PER LA PRODUZIONE ---
#
# Avvia l'applicazione usando Uvicorn, un server ASGI performante.
# --host 0.0.0.0: Rende l'applicazione accessibile dall'esterno del container.
# --port $PORT: Usa la porta fornita da Railway (o 8000 come default).
# app:app: Fa riferimento all'oggetto FastAPI "app" nel file "app.py".
#
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
