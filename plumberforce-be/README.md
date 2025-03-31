---
title: Plumberforce
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.4.0
app_file: app.py
pinned: false
---

# Salesforce Assistant API

Questo è un assistente AI specializzato per Salesforce che fornisce risposte a domande tecniche e soluzioni a requisiti di business.

## Funzionalità

L'assistente può:
- Rispondere a domande tecniche su Salesforce
- Fornire soluzioni complete con esempi di codice 
- Offrire best practices e consigli di implementazione
- Generare codice Apex e configurazioni

## API Endpoints

L'assistente espone API RESTful per l'integrazione:

- `GET /status` - Verifica lo stato del servizio
- `POST /query` - Invia una query all'assistente

### Esempio di richiesta

```json
{
  "query": "Come implementare un trigger Apex in Salesforce?",
  "type": "standard"  // o "complete" per risposte più dettagliate
}
```

## Interfaccia utente

Oltre all'API, è disponibile anche un'interfaccia Gradio per test diretti in questa pagina.

## Come usare l'API

```python
import requests

url = "https://lordhenry-salesforce-agent.hf.space/query"
payload = {
    "query": "Come implementare un trigger Apex in Salesforce?",
    "type": "standard"
}

response = requests.post(url, json=payload)
print(response.json())
```

## Modello

Questo assistente utilizza l'API di inferenza di Hugging Face con modelli performanti per fornire risposte accurate e dettagliate.