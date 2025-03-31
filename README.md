Architettura completa del progetto Plumberforce

Panoramica dell'architettura

Il sistema è strutturato secondo un'architettura distribuita che separa il frontend dall'elaborazione del backend, ottimizzata per servizi cloud gratuiti:

![image](https://github.com/user-attachments/assets/fbcc9a6e-602e-480b-be9a-bdd5da3e1591)


1. Componente Backend (Hugging Face Spaces)

     Tecnologie principali

        FastAPI (Python): Framework web per l'API REST

        Gradio: Interfaccia utente integrata per testing diretto

        Hugging Face Inference API: Per l'accesso ai modelli LLM

      Componenti funzionali

        API RESTful: Endpoint per query e gestione stato

        Motore di inferenza: Interfaccia verso modello LLM via API (Mistral AI - Mixtral-8x7B-Instruct-v0.1)

        Gestione contesto: Sistema per mantenere la cronologia delle conversazioni

        System prompt avanzato: Template con istruzioni per risposte strutturate

        Cache delle risposte: Memorizzazione temporanea per migliorare le prestazioni

  
      Flusso dati


        Ricezione della query con identificatore client

        Recupero contesto conversazione precedente

        Costruzione del prompt con cronologia e istruzioni

        Chiamata API di inferenza con il prompt

        Aggiornamento della cronologia

        Restituzione della risposta


2. Componente Frontend (Render)
   
    Tecnologie principali

        FastAPI (Python): Server web e gestione WebSocket

        Bootstrap: Framework CSS per l'interfaccia utente

        JavaScript: Logica client-side e gestione WebSocket


    Componenti funzionali


        Interfaccia web: UI responsive per interazioni utente

        WebSocket: Comunicazione in tempo reale con il client

        Gestione sessioni: Identificazione unica per ogni client

        Proxy API: Intermediazione verso il backend

        Cache locale: Memorizzazione conversazioni per client


    Flusso dati


        Connessione WebSocket dal browser

        Invio query dall'utente via WebSocket

        Inoltro della query al backend con client_id

        Ricezione risposta dal backend

        Aggiornamento UI in tempo reale

        Archiviazione conversazione in memoria


3. Flusso delle comunicazioni

   ![image](https://github.com/user-attachments/assets/735ee36e-b780-4684-8984-0e6d1a532da2)

        Browser → Frontend: Comunicazione in tempo reale via WebSocket

        Frontend → Backend: Chiamate HTTP REST con client ID

        Backend → LLM API: Chiamate all'API di inferenza con prompt strutturato

4. Gestione dei dati

     Strutture dati principali

        conversation_store: Dizionario client_id → lista di messaggi
  
        response_cache: Cache per risposte già generate
  
        conversation_history: Cronologia strutturata per il contesto
  

     Persistenza

        Memoria in-process per entrambi i componenti
  
        Cache locale nel browser (opzionale)

5. Meccanismi di resilienza

       Riconnessione automatica: Gestione disconnessioni WebSocket
  
       Recupero errori: Gestione graceful degli errori di comunicazione
  
       Timeout di sicurezza: Limite temporale per le richieste
  
       Controllo stato: Endpoint dedicati per verificare lo stato del sistema

6. Considerazioni di sicurezza

       Validazione input: Controllo delle richieste in ingresso
  
       Limiti di dimensione: Controllo sulla lunghezza delle query
  
       API key opzionale: Autenticazione base tra frontend e backend

7. Caratteristiche avanzate

        Contestualizzazione: Mantenimento della cronologia per risposte coerenti
  
        Reasoning strutturato: Prompt progettati per risposte ragionate
  
        Sistema feedback: Raccolta valutazioni per il miglioramento continuo

        Diagnostica: Monitoraggio prestazioni e utilizzo risorse

Questa architettura è ottimizzata per operare entro i limiti dei servizi cloud gratuiti, distribuendo il carico tra diverse piattaforme e limitando il consumo di risorse sul singolo servizio.
