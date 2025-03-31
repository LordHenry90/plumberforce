import os
import re
import time
import json
import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime

# Versione minimalista dell'agente Salesforce ottimizzata per Hugging Face Spaces

class SalesforceLocalAI:
    """Agente Salesforce estremamente ottimizzato per spazi limitati"""
    
    def __init__(self, model_path="TinyLlama/TinyLlama-1.1B-Chat-v1.0", 
                 quantize=True, load_in_4bit=True, use_minimal_memory=True):
        """Inizializza l'agente con impostazioni di risparmio memoria"""
        self.model_path = model_path
        self.quantize = quantize
        self.load_in_4bit = load_in_4bit
        self.use_minimal_memory = use_minimal_memory
        
        # Per verifiche di memoria
        self.last_memory_check = time.time()
        
        # Session per le richieste web
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        # Domini Salesforce principali
        self.salesforce_domains = [
            "developer.salesforce.com",
            "help.salesforce.com",
            "trailhead.salesforce.com",
            "salesforce.stackexchange.com"
        ]
        
        # Carica il modello in modo efficiente
        self._load_model()
    
    def _load_model(self):
        """Carica il modello con ottimizzazioni di memoria"""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
    
            # Controlla se è disponibile CUDA
            has_cuda = torch.cuda.is_available()
            device = "cuda" if has_cuda else "cpu"
            
            print(f"Caricamento modello {self.model_path} su {device}")
            
            # Carica tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # Carica il modello con impostazioni base
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float32,
                trust_remote_code=True
            )
            
            print(f"Modello caricato con successo: {self.model_path}")
            
        except Exception as e:
            print(f"Errore nel caricamento del modello: {e}")
            raise
    
    def _get_memory_info(self):
        """Ottieni informazioni sull'uso della memoria"""
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return {
            "rss_mb": memory_info.rss / (1024 * 1024),
            "vms_mb": memory_info.vms / (1024 * 1024),
            "percent": process.memory_percent()
        }
    
    def generate(self, prompt, max_tokens=512, temperature=0.7):
        """Genera testo usando il modello caricato"""
        try:
            # Format prompt for the model
            formatted_prompt = f"<s>[INST] {prompt} [/INST]"
            
            # Check memory usage occasionally
            current_time = time.time()
            if current_time - self.last_memory_check > 60:  # Check every minute
                memory_info = self._get_memory_info()
                print(f"Uso memoria: {memory_info['rss_mb']:.2f} MB ({memory_info['percent']:.2f}%)")
                self.last_memory_check = current_time
            
            # Generate text
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)
            
            # Use model.generate() with minimal parameters
            with torch.no_grad():  # Disable gradient calculation
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True if temperature > 0 else False,
                    top_p=0.95,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the generated part (after prompt)
            response_parts = response.split("[/INST]")
            if len(response_parts) > 1:
                return response_parts[1].strip()
            
            return response

        except Exception as e:
            print(f"Errore nella generazione: {e}")
            return f"Si è verificato un errore: {str(e)}"
    
    def search_documentation(self, query, num_results=3):
        """Cerca documentazione Salesforce con approccio minimo"""
        formatted_query = f"{query} salesforce documentation"
        
        # Usa DuckDuckGo invece di API a pagamento
        ddg_url = f"https://html.duckduckgo.com/html/?q={formatted_query}"
        
        try:
            response = self.session.get(ddg_url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Estrai risultati
            results = []
            for result in soup.select(".result"):
                title_elem = result.select_one(".result__title")
                url_elem = result.select_one(".result__url")
                snippet_elem = result.select_one(".result__snippet")
                
                if not title_elem or not url_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                url = url_elem.get("href", "")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                # Verifica che sia un dominio Salesforce
                if any(domain in url for domain in self.salesforce_domains):
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })
                
                if len(results) >= num_results:
                    break
            
            return results
        
        except Exception as e:
            print(f"Errore nella ricerca: {e}")
            return []
    
    def fetch_page_content(self, url, max_length=5000):
        """Estrai contenuto da una pagina web"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Rimuovi elementi non necessari
            for tag in soup.select("script, style, header, footer, nav"):
                tag.decompose()
            
            # Estrai contenuto
            title = soup.title.get_text(strip=True) if soup.title else ""
            
            # Prova selettori comuni per il contenuto principale
            main_selectors = [
                "article", ".article", "main", "#main", ".docs", ".doc-content",
                ".content", ".documentation", "#content"
            ]
            
            # Estrai il testo
            content = ""
            for selector in main_selectors:
                if content:
                    break
                    
                main_content = soup.select_one(selector)
                if main_content:
                    content = main_content.get_text(separator=" ", strip=True)
            
            # Se non è stato trovato nulla, prendi il body
            if not content:
                content = soup.body.get_text(separator=" ", strip=True) if soup.body else ""
            
            # Limita la lunghezza
            content = content[:max_length]
            
            return {
                "title": title,
                "url": url,
                "content": content
            }
            
        except Exception as e:
            print(f"Errore nell'estrazione del contenuto: {e}")
            return {"title": "", "url": url, "content": ""}
    
    def answer_question(self, question):
        """Risponde a una domanda usando il modello con ricerca web"""
        # Cerca documentazione pertinente
        docs = self.search_documentation(question)
        
        # Estrai contenuto dalle pagine
        context = ""
        if docs:
            for doc in docs[:2]:  # Limita a 2 documenti per risparmiare memoria
                page_content = self.fetch_page_content(doc["url"])
                if page_content["content"]:
                    context += f"\nTitolo: {page_content['title']}\n"
                    context += f"URL: {page_content['url']}\n"
                    context += f"Contenuto: {page_content['content'][:1000]}...\n\n"
        
        # Prepara prompt con contesto
        prompt = f"""Sei un assistente esperto di Salesforce che risponde a domande tecniche.
        
        Contesto dalla documentazione:
        {context if context else "Nessuna documentazione rilevante trovata."}
        
        Domanda: {question}
        
        Fornisci una risposta dettagliata e accurata basata sulle tue conoscenze di Salesforce e sul contesto fornito."""
        
        # Genera risposta
        response = self.generate(prompt, max_tokens=1024)
        
        return response
    
    def store_feedback(self, query, response, rating, feedback_text=None):
        """Archivia il feedback (versione minima)"""
        feedback_dir = "feedback"
        os.makedirs(feedback_dir, exist_ok=True)
        
        feedback_data = {
            "query": query,
            "response": response,
            "rating": rating,
            "feedback_text": feedback_text,
            "timestamp": datetime.now().isoformat()
        }
        
        filename = f"feedback_{int(time.time())}.json"
        try:
            with open(os.path.join(feedback_dir, filename), "w") as f:
                json.dump(feedback_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Errore nell'archiviazione del feedback: {e}")
            return False
    
    def get_feedback_analysis(self):
        """Analizza i feedback (versione minima)"""
        feedback_dir = "feedback"
        if not os.path.exists(feedback_dir):
            return {"status": "No feedback data"}
        
        try:
            feedbacks = []
            for filename in os.listdir(feedback_dir):
                if filename.endswith(".json"):
                    with open(os.path.join(feedback_dir, filename), "r") as f:
                        feedback = json.load(f)
                        feedbacks.append(feedback)
            
            if not feedbacks:
                return {"status": "No feedback data"}
            
            # Calcola statistiche di base
            total = len(feedbacks)
            avg_rating = sum(f["rating"] for f in feedbacks) / total if total > 0 else 0
            
            # Distribuzione dei rating
            rating_dist = {}
            for r in range(1, 6):
                rating_dist[r] = len([f for f in feedbacks if f["rating"] == r])
            
            return {
                "total_feedback": total,
                "average_rating": avg_rating,
                "rating_distribution": rating_dist
            }
            
        except Exception as e:
            print(f"Errore nell'analisi dei feedback: {e}")
            return {"status": "Error", "message": str(e)}
