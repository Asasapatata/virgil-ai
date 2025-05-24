# backend/app/services/agent_integration.py
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class IntegrationAgent:
    """
    Agente specializzato nella creazione di integrazioni con servizi esterni 
    come autenticazione, database, sistemi di pagamento, ecc.
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        logger.info("IntegrationAgent initialized")
    
    async def generate_integrations(self, 
                                  requirements: Dict[str, Any], 
                                  provider: str) -> Dict[str, str]:
        """
        Genera tutti i file necessari per integrare l'applicazione con servizi esterni.
        """
        logger.info("Generating integration files")
        
        # Identifica i servizi necessari
        required_services = self._identify_required_services(requirements)
        logger.info(f"Identified {len(required_services)} services: {', '.join(required_services)}")
        
        integration_files = {}
        
        # Genera file di integrazione per ogni servizio
        for service in required_services:
            service_files = await self._generate_service_integration(service, requirements, provider)
            integration_files.update(service_files)
        
        # Genera configurazione del client API se necessario
        if self._needs_api_client(requirements):
            api_client_files = await self._generate_api_client(requirements, provider)
            integration_files.update(api_client_files)
        
        # Genera file di autenticazione se necessario
        if self._needs_auth_integration(requirements):
            auth_files = await self._generate_auth_integration(requirements, provider)
            integration_files.update(auth_files)
        
        logger.info(f"Generated {len(integration_files)} integration files")
        return integration_files
    
    def _identify_required_services(self, requirements: Dict[str, Any]) -> List[str]:
        """
        Identifica i servizi esterni richiesti in base ai requisiti.
        """
        services = []
        
        # Controlla la sezione features
        if "features" in requirements:
            for feature in requirements["features"]:
                if isinstance(feature, dict):
                    # Esamina caratteristiche di autenticazione
                    if "authentication" in feature and "providers" in feature["authentication"]:
                        providers = feature["authentication"]["providers"]
                        for provider in providers:
                            if provider != "email" and provider not in services:
                                services.append(provider)
                    
                    # Esamina database
                    if "database" in feature and "type" in feature["database"]:
                        db_type = feature["database"]["type"]
                        if db_type not in ["sqlite", "memory"] and f"{db_type}_db" not in services:
                            services.append(f"{db_type}_db")
                    
                    # Esamina servizi esterni espliciti
                    if "external_services" in feature:
                        ext_services = feature["external_services"]
                        if isinstance(ext_services, list):
                            for service in ext_services:
                                if isinstance(service, str) and service not in services:
                                    services.append(service)
                                elif isinstance(service, dict) and "name" in service:
                                    if service["name"] not in services:
                                        services.append(service["name"])
        
        # Controlla la sezione backend.services
        if "backend" in requirements and "services" in requirements["backend"]:
            backend_services = requirements["backend"]["services"]
            if isinstance(backend_services, list):
                for service in backend_services:
                    if isinstance(service, str) and service not in services:
                        services.append(self._normalize_service_name(service))
                    elif isinstance(service, dict):
                        for service_name in service:
                            # Controlla se il servizio ha un provider esterno
                            service_details = service[service_name]
                            if isinstance(service_details, dict) and "provider" in service_details:
                                provider = service_details["provider"]
                                service_key = f"{provider}_{self._normalize_service_name(service_name)}"
                                if service_key not in services:
                                    services.append(service_key)
                            else:
                                normalized_name = self._normalize_service_name(service_name)
                                if normalized_name not in services:
                                    services.append(normalized_name)
        
        # Aggiungi integrazioni di pagamento se presenti
        if self._has_payment_features(requirements) and "payment" not in services:
            services.append("payment")
        
        # Aggiungi integrazioni di email se presenti
        if self._has_email_features(requirements) and "email" not in services:
            services.append("email")
        
        # Aggiungi integrazioni di storage se presenti
        if self._has_storage_features(requirements) and "storage" not in services:
            services.append("storage")
        
        return services
    
    def _normalize_service_name(self, service_name: str) -> str:
        """Normalizza il nome del servizio per uniformità"""
        # Rimuovi "Service" dal nome se presente
        name = service_name.replace("Service", "").lower()
        
        # Converti in snake_case se CamelCase
        if any(c.isupper() for c in name):
            result = name[0].lower()
            for c in name[1:]:
                if c.isupper():
                    result += "_" + c.lower()
                else:
                    result += c
            return result
        
        return name
    
    def _has_payment_features(self, requirements: Dict[str, Any]) -> bool:
        """Controlla se l'app ha funzionalità di pagamento"""
        # Cerca nella sezione features
        if "features" in requirements:
            for feature in requirements["features"]:
                if isinstance(feature, dict):
                    if "payment" in feature or "payments" in feature or "subscription" in feature:
                        return True
                    
                    # Cerca nella sottosezione e-commerce
                    if "ecommerce" in feature or "e-commerce" in feature or "e_commerce" in feature:
                        return True
        
        # Cerca nei servizi di backend
        if "backend" in requirements and "services" in requirements["backend"]:
            services = requirements["backend"]["services"]
            for service in services:
                if isinstance(service, dict) and any(
                    "payment" in s.lower() or "stripe" in s.lower() or "paypal" in s.lower() 
                    for s in service.keys()
                ):
                    return True
                elif isinstance(service, str) and any(
                    term in service.lower() for term in ["payment", "stripe", "paypal", "subscription"]
                ):
                    return True
        
        return False
    
    def _has_email_features(self, requirements: Dict[str, Any]) -> bool:
        """Controlla se l'app ha funzionalità di email"""
        # Cerca nella sezione features
        if "features" in requirements:
            for feature in requirements["features"]:
                if isinstance(feature, dict):
                    if "email" in feature or "notification" in feature:
                        return True
                    
                    # Cerca nella sottosezione authentication
                    if "authentication" in feature:
                        auth = feature["authentication"]
                        if isinstance(auth, dict) and "features" in auth:
                            auth_features = auth["features"]
                            if any(
                                feat in auth_features for feat in 
                                ["email_verification", "password_reset", "invitation"]
                            ):
                                return True
        
        # Cerca nei servizi di backend
        if "backend" in requirements and "services" in requirements["backend"]:
            services = requirements["backend"]["services"]
            for service in services:
                if isinstance(service, dict) and any(
                    "email" in s.lower() or "mail" in s.lower() or "notification" in s.lower()
                    for s in service.keys()
                ):
                    return True
                elif isinstance(service, str) and any(
                    term in service.lower() for term in ["email", "mail", "notification", "sendgrid", "ses"]
                ):
                    return True
        
        return False
    
    def _has_storage_features(self, requirements: Dict[str, Any]) -> bool:
        """Controlla se l'app ha funzionalità di storage"""
        # Cerca nella sezione features
        if "features" in requirements:
            for feature in requirements["features"]:
                if isinstance(feature, dict):
                    if "storage" in feature or "file" in feature or "upload" in feature or "media" in feature:
                        return True
        
        # Cerca nei servizi di backend
        if "backend" in requirements and "services" in requirements["backend"]:
            services = requirements["backend"]["services"]
            for service in services:
                if isinstance(service, dict) and any(
                    term in s.lower() for term in ["storage", "file", "s3", "blob", "upload", "media"]
                    for s in service.keys()
                ):
                    return True
                elif isinstance(service, str) and any(
                    term in service.lower() for term in ["storage", "file", "s3", "blob", "upload", "media"]
                ):
                    return True
        
        return False
    
    async def _generate_service_integration(self, 
                                         service: str, 
                                         requirements: Dict[str, Any], 
                                         provider: str) -> Dict[str, str]:
        """Genera file di integrazione per un servizio specifico"""
        logger.info(f"Generating integration files for {service}")
        
        # Mappa dei prompt di sistema ottimizzati per diversi tipi di servizio
        system_prompts = {
            "google": """You are an expert in Google service integrations, deeply familiar with OAuth2, Google APIs, 
                      and best practices for secure authentication flows.""",
            
            "facebook": """You are an expert in Facebook/Meta service integrations, deeply familiar with the Facebook API, 
                       social login flows, and secure authentication methods.""",
            
            "twitter": """You are an expert in Twitter X service integrations, deeply familiar with Twitter's API, 
                      OAuth authentication, and implementing secure social login.""",
            
            "apple": """You are an expert in Apple service integrations, deeply familiar with Sign in with Apple, 
                    App Store APIs, and Apple's security requirements for integrations.""",
            
            "github": """You are an expert in GitHub service integrations, deeply familiar with GitHub's OAuth flow, 
                     APIs, webhooks and implementing secure social login.""",
            
            "postgres_db": """You are an expert in PostgreSQL database integrations, deeply familiar with connection pooling, 
                         migrations, query optimization, and secure database access patterns.""",
            
            "mongodb_db": """You are an expert in MongoDB database integrations, deeply familiar with connection management, 
                        document modeling, indexes, and secure NoSQL database patterns.""",
            
            "mysql_db": """You are an expert in MySQL database integrations, deeply familiar with connection pooling, 
                       migrations, query optimization, and secure database access patterns.""",
            
            "payment": """You are an expert in payment gateway integrations, deeply familiar with Stripe, PayPal, 
                      and other payment providers, focusing on security, PCI compliance and robust error handling.""",
            
            "email": """You are an expert in email service integrations, deeply familiar with SendGrid, Amazon SES, 
                    SMTP configurations, email templating, and delivery optimization.""",
            
            "storage": """You are an expert in cloud storage integrations, deeply familiar with AWS S3, Google Cloud Storage, 
                      Azure Blob Storage, secure file uploads, and efficient retrieval systems."""
        }
        
        # Seleziona il prompt di sistema più appropriato
        system_prompt = None
        for key, prompt in system_prompts.items():
            if key in service.lower():
                system_prompt = prompt
                break
        
        # Usa un prompt generico se non è stata trovata una corrispondenza specifica
        if not system_prompt:
            system_prompt = f"""You are an expert in {service} integrations, deeply familiar with its APIs, 
                          authentication methods, and best practices for secure and reliable integration."""
        
        # Determina il percorso dei file di integrazione in base al tipo di progetto
        # e alla struttura identificata nei requisiti
        file_paths = self._determine_integration_file_paths(service, requirements)
        
        prompt = f"""Generate integration files for {service} with these requirements:
        
{json.dumps(requirements, indent=2)}

Create complete implementation files for the integration, including:
1. Connection/client setup
2. Authentication and secure communication
3. Error handling and retry logic
4. Key operations and methods
5. Configuration and environment variables

Generate files for these specific paths:
{json.dumps(file_paths, indent=2)}

For each file, use EXACTLY this format:
FILE: path/to/file.ext
```language
[complete file content]
```

Be sure to follow best practices for {service} integration, focusing on:
- Security (proper auth, secrets handling)
- Error resilience (retry logic, error handling)
- Maintainability (clear structure, good comments)
- Performance (connection pooling where appropriate)
- Testing (include tests where applicable)

Files should be complete, production-ready implementations with proper typing and documentation.
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai i file dalla risposta dell'LLM
        files = self._extract_files(response)
        
        # Se non sono stati generati file per tutti i percorsi richiesti, 
        # genera quelli mancanti in chiamate separate
        missing_paths = [path for path in file_paths if not any(file.endswith(path) for file in files.keys())]
        
        if missing_paths:
            logger.info(f"Generating {len(missing_paths)} missing integration files for {service}")
            for path in missing_paths:
                try:
                    file_content = await self._generate_single_integration_file(path, service, requirements, provider)
                    if file_content:
                        files[path] = file_content
                except Exception as e:
                    logger.error(f"Error generating file {path}: {e}")
        
        logger.info(f"Generated {len(files)} files for {service} integration")
        return files
    
    def _determine_integration_file_paths(self, service: str, requirements: Dict[str, Any]) -> List[str]:
        """Determina i percorsi dei file per l'integrazione basati sul servizio e requisiti"""
        
        paths = []
        
        # Identifica se il progetto è frontend, backend o fullstack
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        # Identifica la struttura delle cartelle di backend
        backend_structure = self._determine_backend_structure(requirements)
        
        # Determina i percorsi in base al tipo di servizio
        if "db" in service:
            # Percorsi per database
            db_type = service.replace("_db", "")
            if project_type in ["fullstack", "backend"]:
                paths.extend([
                    f"{backend_structure}/db/connection.py",
                    f"{backend_structure}/db/{db_type}_client.py",
                    f"{backend_structure}/db/models/base.py",
                    f"{backend_structure}/db/migrations/README.md"
                ])
        
        elif service in ["google", "facebook", "twitter", "github", "apple"]:
            # Percorsi per autenticazione social
            if project_type in ["fullstack", "backend"]:
                paths.extend([
                    f"{backend_structure}/services/auth/{service}_auth.py",
                    f"{backend_structure}/api/routes/auth/{service}.py",
                    f"{backend_structure}/config/{service}_config.py"
                ])
            if project_type in ["fullstack", "frontend"]:
                if "frontend" in requirements and "framework" in requirements["frontend"]:
                    framework = requirements["frontend"]["framework"].lower()
                    if framework == "react" or framework == "next":
                        paths.extend([
                            f"src/services/{service}Service.ts",
                            f"src/hooks/use{service.capitalize()}Auth.ts",
                            f"src/components/auth/{service.capitalize()}Button.tsx"
                        ])
                    elif framework == "vue" or framework == "nuxt":
                        paths.extend([
                            f"src/services/{service}Service.js",
                            f"src/composables/use{service.capitalize()}Auth.js",
                            f"src/components/auth/{service.capitalize()}Button.vue"
                        ])
                    elif framework == "angular":
                        paths.extend([
                            f"src/app/services/{service}.service.ts",
                            f"src/app/auth/{service}-auth/{service}-auth.component.ts",
                            f"src/app/auth/{service}-auth/{service}-auth.component.html"
                        ])
        
        elif service == "payment":
            # Percorsi per integrazioni di pagamento
            if project_type in ["fullstack", "backend"]:
                paths.extend([
                    f"{backend_structure}/services/payment_service.py",
                    f"{backend_structure}/api/routes/payments.py",
                    f"{backend_structure}/config/payment_config.py"
                ])
            if project_type in ["fullstack", "frontend"]:
                if "frontend" in requirements and "framework" in requirements["frontend"]:
                    framework = requirements["frontend"]["framework"].lower()
                    if framework in ["react", "next"]:
                        paths.extend([
                            "src/services/PaymentService.ts",
                            "src/components/payments/PaymentForm.tsx",
                            "src/hooks/usePayment.ts"
                        ])
                    elif framework in ["vue", "nuxt"]:
                        paths.extend([
                            "src/services/PaymentService.js",
                            "src/components/payments/PaymentForm.vue",
                            "src/composables/usePayment.js"
                        ])
        
        elif service == "email":
            # Percorsi per integrazioni email
            if project_type in ["fullstack", "backend"]:
                paths.extend([
                    f"{backend_structure}/services/email_service.py",
                    f"{backend_structure}/templates/emails/base.html",
                    f"{backend_structure}/config/email_config.py"
                ])
        
        elif service == "storage":
            # Percorsi per integrazioni di storage
            if project_type in ["fullstack", "backend"]:
                paths.extend([
                    f"{backend_structure}/services/storage_service.py",
                    f"{backend_structure}/api/routes/files.py",
                    f"{backend_structure}/config/storage_config.py"
                ])
            if project_type in ["fullstack", "frontend"]:
                if "frontend" in requirements and "framework" in requirements["frontend"]:
                    framework = requirements["frontend"]["framework"].lower()
                    if framework in ["react", "next"]:
                        paths.extend([
                            "src/services/StorageService.ts",
                            "src/components/files/FileUploader.tsx",
                            "src/hooks/useFileUpload.ts"
                        ])
                    elif framework in ["vue", "nuxt"]:
                        paths.extend([
                            "src/services/StorageService.js",
                            "src/components/files/FileUploader.vue",
                            "src/composables/useFileUpload.js"
                        ])
        
        else:
            # Percorsi generici per altre integrazioni
            if project_type in ["fullstack", "backend"]:
                paths.extend([
                    f"{backend_structure}/services/{service}_service.py",
                    f"{backend_structure}/config/{service}_config.py"
                ])
            if project_type in ["fullstack", "frontend"]:
                if "frontend" in requirements and "framework" in requirements["frontend"]:
                    framework = requirements["frontend"]["framework"].lower()
                    if framework in ["react", "next"]:
                        paths.append(f"src/services/{service.capitalize()}Service.ts")
                    elif framework in ["vue", "nuxt"]:
                        paths.append(f"src/services/{service.capitalize()}Service.js")
                    elif framework == "angular":
                        paths.append(f"src/app/services/{service}.service.ts")
        
        return paths
    
    def _determine_backend_structure(self, requirements: Dict[str, Any]) -> str:
        """Determina la struttura delle cartelle di backend dai requisiti"""
        
        if "backend" in requirements and "framework" in requirements["backend"]:
            framework = requirements["backend"]["framework"].lower()
            
            if framework == "fastapi":
                return "app"
            elif framework == "django":
                project_name = requirements.get("project", {}).get("name", "app")
                project_name = project_name.lower().replace(" ", "_").replace("-", "_")
                return project_name
            elif framework == "flask":
                return "app"
            elif framework == "express":
                return "src"
            elif framework == "spring":
                return "src/main/java"
            elif framework == "laravel":
                return "app"
        
        # Default structure
        return "app"
    
    async def _generate_single_integration_file(self, 
                                             file_path: str, 
                                             service: str,
                                             requirements: Dict[str, Any], 
                                             provider: str) -> Optional[str]:
        """Genera un singolo file di integrazione"""
        
        system_prompt = f"""You are an expert in creating {service} integrations for applications.
        Create a single high-quality file following best practices for security, maintainability, and performance."""
        
        prompt = f"""Generate a single integration file for {service} at path: {file_path}

Based on these project requirements:
{json.dumps(requirements, indent=2)}

Create a complete, production-ready implementation for this file. Include:
1. All necessary imports
2. Properly structured classes/functions
3. Error handling
4. Documentation and type hints
5. Configuration options

Focus on:
- Security best practices
- Error resilience and retry logic
- Clean code structure
- Performance considerations
- Integration with other system components

Provide only the file contents (no FILE: prefix or code blocks).
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Pulisci la risposta da eventuali blocchi di codice
        content = self._clean_code_blocks(response)
        
        return content
    
    def _clean_code_blocks(self, content: str) -> str:
        """Rimuove blocchi di codice dalla risposta per ottenere solo il contenuto"""
        import re
        
        # Rimuovi blocchi di codice ```python ... ```
        cleaned = re.sub(r'```(?:python|typescript|javascript|)\s*(.*?)\s*```', r'\1', content, flags=re.DOTALL)
        
        # Rimuovi prefissi "FILE: path/to/file"
        cleaned = re.sub(r'FILE:\s*[^\n]+\s*\n', '', cleaned)
        
        # Se contiene ancora tag, è probabile che non sia stato delimitato correttamente
        if "```" in cleaned:
            # Tenta di estrarre il contenuto principale
            parts = cleaned.split("```")
            for part in parts:
                if len(part.strip()) > 100:  # Assume una parte sostanziale è il codice
                    return part.strip()
        
        return cleaned.strip()
    
    def _extract_files(self, response: str) -> Dict[str, str]:
        """Estrai i file dalla risposta dell'LLM"""
        import re
        
        files = {}
        # Pattern to match FILE: path followed by code block
        pattern = r'FILE:\s*([^\n]+)\s*\n```(?:\w+)?\s*\n(.*?)\n```'
        matches = re.finditer(pattern, response, re.DOTALL)
        
        for match in matches:
            file_path, content = match.groups()
            file_path = file_path.strip()
            if file_path:
                files[file_path] = content.strip()
        
        return files
    
    def _needs_api_client(self, requirements: Dict[str, Any]) -> bool:
        """Determina se il progetto necessita di un client API personalizzato"""
        
        # Controlla se il progetto è fullstack
        project_type = requirements.get("project", {}).get("type", "fullstack")
        if project_type == "fullstack":
            return True
            
        # Controlla se ci sono chiamate API esplicite
        if "frontend" in requirements and "api_calls" in requirements["frontend"]:
            return True
            
        # Controlla se c'è un backend separato
        if "backend" in requirements and "api" in requirements["backend"]:
            return True
            
        return False
    
    async def _generate_api_client(self, requirements: Dict[str, Any], provider: str) -> Dict[str, str]:
        """Genera i file per il client API"""
        
        logger.info("Generating API client files")
        
        system_prompt = """You are an expert in creating robust API clients for web applications.
        Create production-ready API client files that handle authentication, requests, error handling,
        and data transformation in a secure and maintainable way."""
        
        # Determina il framework frontend
        frontend_framework = "react"  # default
        if "frontend" in requirements and "framework" in requirements["frontend"]:
            frontend_framework = requirements["frontend"]["framework"].lower()
        
        # Adatta il linguaggio in base al framework
        language = "typescript" if frontend_framework in ["react", "next", "angular", "vue3"] else "javascript"
        
        # Determina la struttura delle API dal backend, se presente
        api_endpoints = []
        if "backend" in requirements and "api_structure" in requirements["backend"]:
            api_structure = requirements["backend"]["api_structure"]
            if isinstance(api_structure, list):
                for group in api_structure:
                    if isinstance(group, dict):
                        for group_name, details in group.items():
                            if isinstance(details, dict) and "endpoints" in details:
                                for endpoint in details["endpoints"]:
                                    if isinstance(endpoint, dict) and "path" in endpoint:
                                        api_endpoints.append(endpoint)
        
        prompt = f"""Create API client files for the frontend based on these requirements:
        
{json.dumps(requirements, indent=2)}

{f"The backend has the following API endpoints:{chr(10)}{json.dumps(api_endpoints, indent=2)}" if api_endpoints else ''}

Generate these API client files for a {frontend_framework} application using {language}:

1. Core API client with base functionality:
   - Authentication header handling
   - Request/response interceptors
   - Error handling
   - Retry logic
   - Type definitions

2. Specialized API modules for different endpoints:
   - User/auth API methods
   - Feature-specific endpoints
   - Proper typing and documentation

For each file, use EXACTLY this format:
FILE: path/to/file.ext
```language
[complete file content]
```

Follow these best practices:
- Clean abstraction of API calls
- Proper error handling
- Authentication token management
- Type safety (if using TypeScript)
- Request cancellation support
- Loading state management
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai i file dalla risposta dell'LLM
        api_files = self._extract_files(response)
        logger.info(f"Generated {len(api_files)} API client files")
        
        return api_files
    
    def _needs_auth_integration(self, requirements: Dict[str, Any]) -> bool:
        """Determina se il progetto necessita di integrazioni di autenticazione"""
        
        # Controlla le caratteristiche di autenticazione
        if "features" in requirements:
            for feature in requirements["features"]:
                if isinstance(feature, dict) and "authentication" in feature:
                    return True
        
        # Controlla per endpoint API protetti
        if "backend" in requirements and "api_structure" in requirements["backend"]:
            api_structure = requirements["backend"]["api_structure"]
            if isinstance(api_structure, list):
                for group in api_structure:
                    if isinstance(group, dict):
                        for group_name, details in group.items():
                            if isinstance(details, dict) and "endpoints" in details:
                                for endpoint in details["endpoints"]:
                                    if isinstance(endpoint, dict) and endpoint.get("protected") == True:
                                        return True
        
        # Controlla per pagine protette nel frontend
        if "frontend" in requirements and "pages" in requirements["frontend"]:
            pages = requirements["frontend"]["pages"]
            if isinstance(pages, list):
                for page in pages:
                    if isinstance(page, dict) and page.get("protected") == True:
                        return True
        
        return False
    
    async def _generate_auth_integration(self, requirements: Dict[str, Any], provider: str) -> Dict[str, str]:
        """Genera i file per l'integrazione di autenticazione"""
        
        logger.info("Generating authentication integration files")
        
        system_prompt = """You are an expert in implementing secure, robust authentication systems for web applications.
        Create authentication files that implement industry best practices for security, user experience,
        and maintainability."""
        
        # Identifica il tipo di autenticazione dai requisiti
        auth_type = "jwt"  # default
        auth_providers = ["email"]
        auth_features = ["login", "register", "logout"]
        
        if "features" in requirements:
            for feature in requirements["features"]:
                if isinstance(feature, dict) and "authentication" in feature:
                    auth_feature = feature["authentication"]
                    if isinstance(auth_feature, dict):
                        if "type" in auth_feature:
                            auth_type = auth_feature["type"]
                        if "providers" in auth_feature:
                            auth_providers = auth_feature["providers"]
                        if "features" in auth_feature:
                            auth_features = auth_feature["features"]
        
        # Determina il framework frontend
        frontend_framework = None
        if "frontend" in requirements and "framework" in requirements["frontend"]:
            frontend_framework = requirements["frontend"]["framework"].lower()
        
        # Determina il framework backend
        backend_framework = None
        if "backend" in requirements and "framework" in requirements["backend"]:
            backend_framework = requirements["backend"]["framework"].lower()
        
        prompt = f"""Create authentication integration files based on these requirements:
        
{json.dumps(requirements, indent=2)}

Authentication type: {auth_type}
Providers: {", ".join(auth_providers)}
Features: {", ".join(auth_features)}
{f'Frontend framework: {frontend_framework}' if frontend_framework else ''}
{f'Backend framework: {backend_framework}' if backend_framework else ''}

Generate authentication files for both frontend and backend:

Backend auth files:
1. Authentication service implementation
2. Authentication middleware/guards
3. User identity management
4. Token handling and validation

Frontend auth files:
1. Authentication context/store
2. Login/Registration forms and logic
3. Protected route implementation
4. Auth state management

For each file, use EXACTLY this format:
FILE: path/to/file.ext
```language
[complete file content]
```

Follow these security best practices:
- Secure password handling (hashing, verification)
- Protection against common attacks (CSRF, XSS, injection)
- Proper token management (expiration, refresh, revocation)
- Input validation and sanitization
- Secure storage of sensitive information
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai i file dalla risposta dell'LLM
        auth_files = self._extract_files(response)
        logger.info(f"Generated {len(auth_files)} authentication files")
        
        return auth_files
    
    async def generate_database_integration(self, requirements: Dict[str, Any], provider: str) -> Dict[str, str]:
        """
        Genera file specifici per l'integrazione con il database, inclusi modelli,
        migrations, connessioni e query.
        """
        logger.info("Generating database integration files")
        
        # Identifica il tipo di database dai requisiti
        db_type = "sqlite"  # default
        db_models = []
        
        if "features" in requirements:
            for feature in requirements["features"]:
                if isinstance(feature, dict) and "database" in feature:
                    db_feature = feature["database"]
                    if isinstance(db_feature, dict):
                        if "type" in db_feature:
                            db_type = db_feature["type"]
                        if "models" in db_feature:
                            db_models = db_feature["models"]
        
        # Identifica il framework backend
        backend_framework = "fastapi"  # default
        if "backend" in requirements and "framework" in requirements["backend"]:
            backend_framework = requirements["backend"]["framework"].lower()
        
        system_prompt = f"""You are an expert in {db_type} database integration for {backend_framework} applications.
        Create production-ready database integration files with proper models, migrations, connection handling,
        and query optimization."""
        
        prompt = f"""Generate database integration files for a {backend_framework} application using {db_type}:
        
Project requirements:
{json.dumps(requirements, indent=2)}

Database models:
{json.dumps(db_models, indent=2)}

Create these database integration files:
1. Database connection/setup
2. Model definitions
3. Migration scripts/setup
4. Repository/DAO layer
5. Database utilities and helpers

For each file, use EXACTLY this format:
FILE: path/to/file.ext
```language
[complete file content]
```

Follow these best practices:
- Secure connection handling
- Proper transaction management
- Index optimization
- Connection pooling
- Migration strategy
- Proper typing and validation
- Defensive query techniques
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai i file dalla risposta dell'LLM
        db_files = self._extract_files(response)
        logger.info(f"Generated {len(db_files)} database integration files")
        
        return db_files