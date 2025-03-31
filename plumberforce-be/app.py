import os
import time
import logging
import gradio as gr
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

# Configurazione logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("salesforce-agent-api")

# Modelli per richieste
class QueryRequest(BaseModel):
    query: str
    client_id: str = "default"

# FastAPI app
app = FastAPI(title="Salesforce Assistant API")

# Configurazione del modello - scegli un modello di reasoning senza autenticazione
# Mixtral è ottimo per il reasoning e supporta l'inferenza gratuita
INFERENCE_MODEL = os.environ.get("INFERENCE_MODEL", "mistralai/Mixtral-8x7B-Instruct-v0.1")

# Cache per risposte recenti
response_cache = {}

# Dizionario per memorizzare la cronologia delle conversazioni
conversation_history = {}

def generate_text_with_inference_api(prompt, max_tokens=1024, temperature=0.7):
    """Genera testo usando l'API di inferenza di Hugging Face"""
    cache_key = f"{prompt}_{max_tokens}_{temperature}"
    
    # Verifica se la risposta è già in cache
    if cache_key in response_cache:
        logger.info("Risposta recuperata dalla cache")
        return response_cache[cache_key]
    
    try:
        logger.info(f"Chiamata API di inferenza per il modello {INFERENCE_MODEL}")
        
        # Configura l'API
        API_URL = f"https://api-inference.huggingface.co/models/{INFERENCE_MODEL}"
        
        # Prepara il payload - configurato per reasoning
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "return_full_text": False,
                "do_sample": True,
                "top_p": 0.95
            }
        }
        
        # Invia richiesta all'API
        start_time = time.time()
        response = requests.post(API_URL, json=payload)
        elapsed_time = time.time() - start_time
        
        # Log per debug
        logger.info(f"Risposta ricevuta in {elapsed_time:.2f} secondi")
        
        # Verifica risposta
        if response.status_code == 200:
            result = response.json()
            
            # Estrai il testo generato
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
            else:
                generated_text = str(result)
            
            # Salva in cache
            response_cache[cache_key] = generated_text
            
            # Limita dimensione cache
            if len(response_cache) > 100:
                # Rimuovi chiave più vecchia
                oldest_key = next(iter(response_cache))
                del response_cache[oldest_key]
            
            return generated_text
        else:
            error_message = f"Errore API ({response.status_code}): {response.text}"
            logger.error(error_message)
            
            # Verifica se è un errore di modello in caricamento
            if "loading" in response.text.lower() or "currently loading" in response.text.lower():
                return "Il modello è in fase di caricamento, riprova tra qualche secondo."
            
            return f"Errore: {error_message}"
    
    except Exception as e:
        logger.error(f"Errore durante la generazione: {str(e)}")
        return f"Si è verificato un errore: {str(e)}"

def answer_query(query, client_id="default"):
    """Elabora una query e genera una risposta ragionata con contesto"""
    try:
        # Inizializza la cronologia se non esiste per questo client
        if client_id not in conversation_history:
            conversation_history[client_id] = []
        
        # Recupera la cronologia per questo client
        client_history = conversation_history[client_id]
        
        # Formatta il prompt includendo la cronologia
        formatted_history = ""
        if client_history:
            formatted_history = "Cronologia della conversazione:\n"
            for i, exchange in enumerate(client_history[-3:]):  # Ultimi 3 scambi
                formatted_history += f"Utente: {exchange['user']}\n"
                if len(exchange['assistant']) > 150:
                    formatted_history += f"Assistente: {exchange['assistant'][:150]}...\n\n"
                else:
                    formatted_history += f"Assistente: {exchange['assistant']}\n\n"
        
        # Crea il prompt con la cronologia e pensiero strutturato
        prompt = f"""<s>[INST] Sei un esperto di Salesforce che fornisce soluzioni tecniche dettagliate e ragionate.

{formatted_history}
L'utente ha appena chiesto: {query}

Per rispondere in modo ottimale:
1. Prima analizza attentamente il problema o la richiesta dell'utente
2. Identifica i concetti chiave di Salesforce coinvolti
3. Ragiona passo dopo passo sulla soluzione migliore
4. Fornisci una spiegazione dettagliata che includa:
   - Analisi del problema/requisito
   - Approccio tecnico consigliato con esempi di codice o configurazioni
   - Best practices e considerazioni importanti
   - Alternative o approcci complementari se rilevanti

La tua risposta deve essere completa, ben ragionata e seguire le best practices di Salesforce.
RISPONDI SEMPRE IN ITALIANO, anche quando fornisci esempi di codice.

Ricorda di tenere conto della cronologia della conversazione per contestualizzare la tua risposta. [/INST]"""
        
        # Ottieni risposta
        response = generate_text_with_inference_api(prompt)
        
        # Aggiorna la cronologia
        client_history.append({
            "user": query,
            "assistant": response
        })
        
        # Limita la lunghezza della cronologia (ultimi 5 scambi)
        if len(client_history) > 5:
            conversation_history[client_id] = client_history[-5:]
        
        return response
        
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione della query: {str(e)}")
        return f"Mi dispiace, si è verificato un errore: {str(e)}"

# Endpoint API per query
@app.post("/query")
async def query_endpoint(request: QueryRequest):
    """Endpoint API per query"""
    start_time = time.time()
    
    try:
        # Ottieni l'ID client dalla richiesta o usa 'default'
        client_id = request.client_id
        
        logger.info(f"Elaborazione query per client {client_id}: {request.query[:50]}...")
        
        # Elabora la query
        response = answer_query(request.query, client_id)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Query elaborata in {elapsed_time:.2f} secondi")
        
        return {
            "response": response,
            "status": "success",
            "processing_time": elapsed_time
        }
    except Exception as e:
        logger.error(f"Errore nell'elaborazione della query: {str(e)}")
        return {
            "response": f"Si è verificato un errore: {str(e)}",
            "status": "error",
            "error": str(e)
        }

# Endpoint per verificare lo stato
@app.get("/status")
async def status_endpoint():
    """Endpoint per verificare lo stato del servizio"""
    return {
        "ready": True,
        "model": INFERENCE_MODEL,
        "type": "inference_api",
        "cache_size": len(response_cache),
        "active_conversations": len(conversation_history)
    }

# Interfaccia Gradio semplificata senza la distinzione tra tipi di risposta
with gr.Blocks(title="Salesforce Assistant") as demo:
    gr.Markdown("# Assistente Salesforce")
    gr.Markdown("Questo assistente risponde a domande tecniche su Salesforce e fornisce soluzioni complete e ragionate.")
    
    with gr.Row():
        with gr.Column():
            query_input = gr.Textbox(
                label="La tua domanda", 
                placeholder="Chiedi qualcosa su Salesforce...",
                lines=3
            )
            submit_btn = gr.Button("Invia", variant="primary")
        
        with gr.Column():
            response_output = gr.Textbox(
                label="Risposta",
                lines=15,
                show_copy_button=True
            )
    
    # Esempi pratici
    gr.Examples(
        [
            ["Come posso implementare un trigger Apex per l'aggiornamento automatico di campi correlati?"],
            ["Implementare un sistema di approvazione multi-livello basato sul valore dell'opportunità in Salesforce"],
            ["Qual è la differenza tra SOQL e SOSL in Salesforce?"],
            ["Come creare un componente Lightning personalizzato per visualizzare dati gerarchici"]
        ],
        inputs=[query_input]
    )
    
    # Connetti gli elementi - usa "gradio_client" come client_id per l'interfaccia Gradio
    def gradio_answer(query):
        if not query.strip():
            return "Per favore inserisci una domanda."
        return answer_query(query, "gradio_client")
    
    submit_btn.click(gradio_answer, inputs=[query_input], outputs=response_output)

# Monta l'app Gradio in FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

# Per esecuzione diretta
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)