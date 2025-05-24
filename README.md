# Virgil AI

Generatore automatico di codice basato su AI multi-LLM con testing automatico

## Struttura del Progetto
ai-code-generator/
├── backend/                 # API Backend (FastAPI)
│   ├── app/
│   │   ├── init.py
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── tasks/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Frontend (Next.js)
│   ├── pages/
│   ├── components/
│   ├── styles/
│   ├── package.json
│   └── Dockerfile
├── deepseek-runpod/       # DeepSeek on RunPod
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── output/                # Output directory
├── docker-compose.yml
├── .env.example
├── nginx.conf
└── README.md

## Requisiti

- Docker & Docker Compose
- Server Linux (testato su Ubuntu 22.04)
- API Keys per:
  - OpenAI (ChatGPT)
  - Anthropic (Claude)
  - RunPod (per DeepSeek)

## Installazione Rapida

1. Clona il repository:
```bash
git clone https://github.com/your-username/ai-code-generator.git
cd ai-code-generator

Copia e configura le variabili d'ambiente:

bashcp .env.example .env
# Modifica .env con le tue API keys

Avvia i servizi:

bashdocker-compose up -d

Accedi all'applicazione:


Frontend: http://localhost:3000
API: http://localhost:8000
Docs API: http://localhost:8000/docs

Utilizzo

Carica i requisiti: Upload di un file YAML con le specifiche del progetto
Seleziona LLM: Scegli tra ChatGPT, Claude o DeepSeek
Genera codice: Il sistema genera automaticamente il codice
Test automatici: Vengono generati ed eseguiti test
Iterazioni: Il sistema corregge automaticamente gli errori

Formato Requisiti (YAML)
yamlproject:
  name: "My React App"
  type: "react"
  description: "App con login e registrazione"
  
features:
  - authentication:
      type: "jwt"
      providers: ["email", "google"]
  - database:
      type: "postgresql"
      models:
        - User:
            fields:
              - email: string
              - password: string
              - createdAt: timestamp
  
frontend:
  framework: "react"
  ui_library: "material-ui"
  pages:
    - name: "Login"
      route: "/login"
    - name: "Register"
      route: "/register"
    - name: "Dashboard"
      route: "/dashboard"
      protected: true
      
backend:
  framework: "fastapi"
  auth: "jwt"
  endpoints:
    - path: "/api/auth/login"
      method: "POST"
    - path: "/api/auth/register"
      method: "POST"
    - path: "/api/user/profile"
      method: "GET"
      protected: true
Architettura
Il sistema utilizza:

FastAPI per il backend
Next.js per il frontend
Celery per task asincroni
PostgreSQL per il database
Redis per caching e job queue
Docker per containerizzazione

LLM Supportati

ChatGPT (OpenAI)

Modello: gpt-4
Ottimo per codice generale


Claude (Anthropic)

Modello: claude-3-opus
Eccellente per architetture complesse


DeepSeek (RunPod)

Modello: deepseek-coder
Specializzato in coding



Monitoring
Dashboard di monitoring disponibile su: http://localhost:9090 (Prometheus/Grafana)
Contribuire

Fork il repository
Crea un branch per la feature (git checkout -b feature/AmazingFeature)
Commit delle modifiche (git commit -m 'Add some AmazingFeature')
Push al branch (git push origin feature/AmazingFeature)
Apri una Pull Request

License
MIT License - vedi LICENSE per dettagli