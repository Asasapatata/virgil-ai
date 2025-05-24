# backend/app/services/agent_endpoints.py
import logging
import asyncio
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.llm_service import LLMService
from app.tasks.celery_app import process_agent_generation

logger = logging.getLogger(__name__)

# Crea un router
router = APIRouter()


# Modello di richiesta per l'endpoint
class AgentGenerateRequest(BaseModel):
    project_id: str
    llm_provider: str = "openai"
    max_iterations: int = 10
    agent_mode: str = "multi_agent"  # multi_agent, updated_orchestrator, enhanced_generator, original

# Inizializza LLM Service
llm_service = LLMService()

@router.post("/generate-with-agents")
async def generate_with_agents(request: AgentGenerateRequest):
    """
    Genera codice utilizzando il sistema di agenti
    """
    try:
        # Verifica che il progetto esista
        project_path = Path(f"output/{request.project_id}")
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Carica i dati del progetto
        try:
            with open(project_path / "project.json", 'r') as f:
                project_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading project data: {e}")
            raise HTTPException(status_code=500, detail=f"Error loading project data: {str(e)}")
        
        # Estrai i requirements
        requirements = project_data.get('requirements', {})
        
        logger.info(f"Starting agent-based generation for {request.project_id} using {request.agent_mode} mode")
        
        # Aggiorna lo stato del progetto
        project_data['status'] = 'processing'
        project_data['agent_mode'] = request.agent_mode
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        # Avvia un task asincrono per la generazione
        from app.tasks.celery_app import process_agent_generation
        task = process_agent_generation.delay(
            project_id=request.project_id,
            llm_provider=request.llm_provider,
            max_iterations=request.max_iterations,
            agent_mode=request.agent_mode
        )
        
        # Aggiorna il progetto con l'ID del task
        project_data['task_id'] = task.id
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        return {
            "project_id": request.project_id,
            "task_id": task.id,
            "status": "processing",
            "agent_mode": request.agent_mode,
            "message": f"Code generation started using {request.agent_mode} agent system"
        }
        
    except HTTPException as he:
        # Rilancia le eccezioni HTTP
        raise he
    except Exception as e:
        logger.error(f"Agent generation error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))





class EndpointsAgent:
    """
    Agente specializzato nella generazione di endpoint API e relativi handler.
    Crea file per API RESTful, GraphQL, o altre interfacce di comunicazione.
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        logger.info("EndpointsAgent initialized")

   
    async def generate_endpoints(self, 
                              requirements: Dict[str, Any], 
                              provider: str) -> Dict[str, str]:
        """
        Genera tutti i file necessari per implementare gli endpoint dell'API.
        """
        logger.info("Generating API endpoint files")
        
        # Determina il tipo di API richiesto
        api_type = self._determine_api_type(requirements)
        logger.info(f"Identified API type: {api_type}")
        
        endpoint_files = {}
        
        # Genera endpoint in base al tipo di API
        if api_type == "rest":
            endpoint_files = await self._generate_rest_endpoints(requirements, provider)
        elif api_type == "graphql":
            endpoint_files = await self._generate_graphql_endpoints(requirements, provider)
        elif api_type == "rpc":
            endpoint_files = await self._generate_rpc_endpoints(requirements, provider)
        else:
            logger.warning(f"Unknown API type: {api_type}, defaulting to REST")
            endpoint_files = await self._generate_rest_endpoints(requirements, provider)
        
        # Genera file condivisi per tutti i tipi di API
        common_files = await self._generate_common_api_files(requirements, provider)
        endpoint_files.update(common_files)
        
        # Genera documentazione API se richiesto
        if self._needs_api_docs(requirements):
            doc_files = await self._generate_api_docs(requirements, provider, api_type)
            endpoint_files.update(doc_files)
        
        logger.info(f"Generated {len(endpoint_files)} API endpoint files")
        return endpoint_files
    
    def _determine_api_type(self, requirements: Dict[str, Any]) -> str:
        """
        Determina il tipo di API richiesto in base ai requisiti.
        Possibili valori: "rest", "graphql", "rpc"
        """
        # Default a REST API
        api_type = "rest"
        
        # Verifica esplicita in backend
        if "backend" in requirements:
            backend = requirements["backend"]
            
            # Controlla se c'è un tipo API specificato
            if isinstance(backend, dict):
                if "api_type" in backend:
                    api_type_raw = backend["api_type"]
                    
                    # Normalizza il tipo API
                    if isinstance(api_type_raw, str):
                        api_type_norm = api_type_raw.lower()
                        if "graphql" in api_type_norm:
                            return "graphql"
                        elif "rpc" in api_type_norm or "grpc" in api_type_norm:
                            return "rpc"
                
                # Controlla framework che suggeriscono GraphQL
                if "framework" in backend:
                    framework = backend["framework"].lower() if isinstance(backend["framework"], str) else ""
                    if "apollo" in framework or "graphql" in framework:
                        return "graphql"
                
                # Controlla la struttura dell'API
                if "api_structure" in backend and isinstance(backend["api_structure"], list):
                    for section in backend["api_structure"]:
                        if isinstance(section, dict):
                            for section_name, details in section.items():
                                if "graphql" in section_name.lower():
                                    return "graphql"
                                elif "rpc" in section_name.lower() or "grpc" in section_name.lower():
                                    return "rpc"
        
        # Cerca riferimenti a GraphQL o RPC in features
        if "features" in requirements and isinstance(requirements["features"], list):
            for feature in requirements["features"]:
                if isinstance(feature, dict):
                    for feature_name, details in feature.items():
                        if "graphql" in feature_name.lower():
                            return "graphql"
                        elif "rpc" in feature_name.lower() or "grpc" in feature_name.lower():
                            return "rpc"
        
        return api_type
    
    async def _generate_rest_endpoints(self, requirements: Dict[str, Any], provider: str) -> Dict[str, str]:
        """
        Genera file per endpoint REST API e relativi handler.
        """
        logger.info("Generating REST API endpoint files")
        
        system_prompt = """You are an expert backend developer specializing in RESTful API design and implementation.
        Create clean, maintainable, and secure API routes and handlers following REST best practices,
        with proper error handling, validation, and authentication integration."""
        
        # Determina il framework di backend
        backend_framework = self._determine_backend_framework(requirements)
        logger.info(f"Using {backend_framework} for REST endpoints")
        
        # Determina la struttura delle API dai requisiti
        api_structure = self._extract_api_structure(requirements)
        
        # Determina i percorsi file in base al framework
        file_paths = self._determine_rest_file_paths(backend_framework, api_structure, requirements)
        
        prompt = f"""Create RESTful API endpoint files for a {backend_framework} application with these requirements:
        
{json.dumps(requirements, indent=2)}

API Structure:
{json.dumps(api_structure, indent=2)}

Generate the following REST API files:
1. Route definitions and controllers/handlers
2. Input validation and request parsing
3. Response formatting and error handling
4. Authentication and authorization middleware
5. Rate limiting and security measures

For the following paths:
{json.dumps(file_paths, indent=2)}

Each file should include:
- Proper imports and dependencies
- Complete route handlers with CRUD operations
- Input validation
- Error handling
- Authentication checks where needed
- Clear documentation and comments

For each file, use EXACTLY this format:
FILE: path/to/file.ext
```language
[complete file content]
```

Follow RESTful API best practices with:
- Clear resource naming
- Proper HTTP methods (GET, POST, PUT, DELETE)
- Appropriate status codes
- Consistent response formatting
- Comprehensive error handling
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai i file dalla risposta LLM
        rest_files = self._extract_files(response)
        logger.info(f"Generated {len(rest_files)} REST API files")
        
        # Se non sono stati generati tutti i file necessari, genera quelli mancanti
        if len(rest_files) < len(file_paths):
            missing_paths = self._identify_missing_paths(rest_files.keys(), file_paths)
            logger.info(f"Found {len(missing_paths)} missing REST API files to generate")
            
            for path in missing_paths:
                try:
                    # Genera il file singolarmente
                    endpoint_part = self._extract_endpoint_from_path(path)
                    endpoint_structure = self._find_endpoint_structure(endpoint_part, api_structure)
                    
                    file_content = await self._generate_single_rest_file(
                        path, endpoint_structure, backend_framework, requirements, provider
                    )
                    
                    if file_content:
                        rest_files[path] = file_content
                except Exception as e:
                    logger.error(f"Error generating REST file {path}: {e}")
        
        return rest_files
    
    async def _generate_graphql_endpoints(self, requirements: Dict[str, Any], provider: str) -> Dict[str, str]:
        """
        Genera file per endpoint GraphQL, inclusi schema, resolver e tipi.
        """
        logger.info("Generating GraphQL API endpoint files")
        
        system_prompt = """You are an expert backend developer specializing in GraphQL API design and implementation.
        Create clean, maintainable, and secure GraphQL schemas, resolvers, and types that follow best practices
        and provide efficient, flexible APIs with proper error handling and authentication."""
        
        # Determina il framework di backend
        backend_framework = self._determine_backend_framework(requirements)
        logger.info(f"Using {backend_framework} for GraphQL endpoints")
        
        # Determina la struttura delle API dai requisiti
        api_structure = self._extract_api_structure(requirements)
        
        # Determina i percorsi file in base al framework e GraphQL
        file_paths = self._determine_graphql_file_paths(backend_framework, api_structure, requirements)
        
        prompt = f"""Create GraphQL API endpoint files for a {backend_framework} application with these requirements:
        
{json.dumps(requirements, indent=2)}

API Structure:
{json.dumps(api_structure, indent=2)}

Generate the following GraphQL files:
1. Schema definitions
2. Type definitions
3. Resolvers
4. Input validation
5. Context and authentication integration

For the following paths:
{json.dumps(file_paths, indent=2)}

Each file should include:
- Proper imports and dependencies
- Complete schema and type definitions
- Resolver functions with proper error handling
- Authentication checks where needed
- Clear documentation and comments

For each file, use EXACTLY this format:
FILE: path/to/file.ext
```language
[complete file content]
```

Follow GraphQL best practices:
- Clear type naming
- Proper schema organization
- Efficient resolver implementation
- N+1 query prevention
- Comprehensive error handling
- Authentication and authorization
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai i file dalla risposta LLM
        graphql_files = self._extract_files(response)
        logger.info(f"Generated {len(graphql_files)} GraphQL API files")
        
        # Se non sono stati generati tutti i file necessari, genera quelli mancanti
        if len(graphql_files) < len(file_paths):
            missing_paths = self._identify_missing_paths(graphql_files.keys(), file_paths)
            logger.info(f"Found {len(missing_paths)} missing GraphQL API files to generate")
            
            for path in missing_paths:
                try:
                    # Genera il file singolarmente
                    entity_type = self._extract_graphql_entity_from_path(path)
                    
                    file_content = await self._generate_single_graphql_file(
                        path, entity_type, backend_framework, requirements, provider
                    )
                    
                    if file_content:
                        graphql_files[path] = file_content
                except Exception as e:
                    logger.error(f"Error generating GraphQL file {path}: {e}")
        
        return graphql_files
    
    async def _generate_rpc_endpoints(self, requirements: Dict[str, Any], provider: str) -> Dict[str, str]:
        """
        Genera file per endpoint RPC (gRPC, JSON-RPC, ecc.).
        """
        logger.info("Generating RPC API endpoint files")
        
        system_prompt = """You are an expert backend developer specializing in RPC API design and implementation.
        Create clean, efficient, and secure RPC service definitions, method implementations, and client interfaces
        that follow best practices for high-performance, type-safe APIs."""
        
        # Determina il framework di backend
        backend_framework = self._determine_backend_framework(requirements)
        logger.info(f"Using {backend_framework} for RPC endpoints")
        
        # Determina la struttura delle API dai requisiti
        api_structure = self._extract_api_structure(requirements)
        
        # Determina il tipo specifico di RPC
        rpc_type = self._determine_rpc_type(requirements)
        logger.info(f"Using {rpc_type} for RPC implementation")
        
        # Determina i percorsi file in base al framework e tipo RPC
        file_paths = self._determine_rpc_file_paths(backend_framework, rpc_type, api_structure, requirements)
        
        prompt = f"""Create {rpc_type} API endpoint files for a {backend_framework} application with these requirements:
        
{json.dumps(requirements, indent=2)}

API Structure:
{json.dumps(api_structure, indent=2)}

Generate the following {rpc_type} files:
1. Service definitions (.proto files for gRPC or service interfaces)
2. Server implementation
3. Client stubs
4. Serialization and error handling
5. Authentication integration

For the following paths:
{json.dumps(file_paths, indent=2)}

Each file should include:
- Proper imports and dependencies
- Complete service and method definitions
- Server-side implementation
- Client interfaces where needed
- Authentication and error handling
- Clear documentation and comments

For each file, use EXACTLY this format:
FILE: path/to/file.ext
```language
[complete file content]
```

Follow {rpc_type} best practices:
- Clear service and method naming
- Efficient message definitions
- Proper error handling
- Authentication integration
- Performance optimization
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai i file dalla risposta LLM
        rpc_files = self._extract_files(response)
        logger.info(f"Generated {len(rpc_files)} RPC API files")
        
        # Se non sono stati generati tutti i file necessari, genera quelli mancanti
        if len(rpc_files) < len(file_paths):
            missing_paths = self._identify_missing_paths(rpc_files.keys(), file_paths)
            logger.info(f"Found {len(missing_paths)} missing RPC API files to generate")
            
            for path in missing_paths:
                try:
                    # Genera il file singolarmente
                    service_name = self._extract_rpc_service_from_path(path)
                    
                    file_content = await self._generate_single_rpc_file(
                        path, service_name, rpc_type, backend_framework, requirements, provider
                    )
                    
                    if file_content:
                        rpc_files[path] = file_content
                except Exception as e:
                    logger.error(f"Error generating RPC file {path}: {e}")
        
        return rpc_files
    
    async def _generate_common_api_files(self, requirements: Dict[str, Any], provider: str) -> Dict[str, str]:
        """
        Genera file comuni a tutti i tipi di API, come middleware, 
        gestione errori, utilità di risposta, ecc.
        """
        logger.info("Generating common API files")
        
        system_prompt = """You are an expert backend developer specializing in API infrastructure.
        Create high-quality, reusable components for API implementations, focusing on middleware,
        error handling, response formatting, and other shared utilities."""
        
        # Determina il framework di backend
        backend_framework = self._determine_backend_framework(requirements)
        
        # Determina i percorsi file comuni
        file_paths = self._determine_common_api_file_paths(backend_framework, requirements)
        
        prompt = f"""Create common API infrastructure files for a {backend_framework} application with these requirements:
        
{json.dumps(requirements, indent=2)}

Generate the following common API files:
1. Middleware (authentication, logging, error handling)
2. Response formatters and utilities
3. Error handling and exception classes
4. Common validators and helpers
5. API initialization and configuration

For the following paths:
{json.dumps(file_paths, indent=2)}

Each file should include:
- Proper imports and dependencies
- Complete implementations with documentation
- Integration points with the rest of the system
- Error handling
- Clear documentation and comments

For each file, use EXACTLY this format:
FILE: path/to/file.ext
```language
[complete file content]
```

Follow API infrastructure best practices:
- Clean separation of concerns
- Reusable components
- Consistent error handling
- Proper logging
- Security considerations
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai i file dalla risposta LLM
        common_files = self._extract_files(response)
        logger.info(f"Generated {len(common_files)} common API files")
        
        return common_files
    
    async def _generate_api_docs(self, requirements: Dict[str, Any], provider: str, api_type: str) -> Dict[str, str]:
        """
        Genera file di documentazione API come OpenAPI/Swagger,
        GraphQL Playground, ecc.
        """
        logger.info(f"Generating {api_type} API documentation files")
        
        system_prompt = """You are an expert in API documentation and developer experience.
        Create comprehensive, clear, and user-friendly API documentation that helps developers
        understand and use the API effectively, with examples, schema information, and usage guidelines."""
        
        # Determina il tipo di documentazione in base al tipo di API
        doc_type = "swagger" if api_type == "rest" else api_type
        
        # Determina il framework di backend
        backend_framework = self._determine_backend_framework(requirements)
        
        # Determina i percorsi file per la documentazione
        file_paths = self._determine_api_doc_file_paths(backend_framework, doc_type, requirements)
        
        # Estrai la struttura API per la documentazione
        api_structure = self._extract_api_structure(requirements)
        
        prompt = f"""Create API documentation files for a {backend_framework} application with {api_type} API:
        
{json.dumps(requirements, indent=2)}

API Structure:
{json.dumps(api_structure, indent=2)}

Generate the following API documentation files:
1. OpenAPI/Swagger specifications (for REST)
2. GraphQL schema documentation (for GraphQL)
3. RPC service documentation (for RPC)
4. Setup and configuration for documentation UI
5. Example requests and responses

For the following paths:
{json.dumps(file_paths, indent=2)}

Each file should include:
- Proper schema definitions
- Clear descriptions of endpoints/operations
- Request/response examples
- Authentication requirements
- Error responses
- Complete and accurate information

For each file, use EXACTLY this format:
FILE: path/to/file.ext
```language
[complete file content]
```

Follow documentation best practices:
- Clear and consistent naming
- Comprehensive descriptions
- Useful examples
- Authentication details
- Error handling information
- Version information
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai i file dalla risposta LLM
        doc_files = self._extract_files(response)
        logger.info(f"Generated {len(doc_files)} API documentation files")
        
        return doc_files
    
    def _determine_backend_framework(self, requirements: Dict[str, Any]) -> str:
        """
        Determina il framework di backend dai requisiti.
        """
        # Default a FastAPI
        framework = "fastapi"
        
        if "backend" in requirements and isinstance(requirements["backend"], dict):
            backend = requirements["backend"]
            if "framework" in backend and isinstance(backend["framework"], str):
                framework_raw = backend["framework"].lower()
                
                # Mapping di framework comuni
                if "django" in framework_raw:
                    return "django"
                elif "flask" in framework_raw:
                    return "flask"
                elif "express" in framework_raw:
                    return "express"
                elif "node" in framework_raw:
                    return "express"
                elif "spring" in framework_raw:
                    return "spring"
                elif "fastapi" in framework_raw:
                    return "fastapi"
                elif "nest" in framework_raw:
                    return "nestjs"
                elif "laravel" in framework_raw:
                    return "laravel"
                elif "rails" in framework_raw:
                    return "rails"
        
        return framework
    
    def _extract_api_structure(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Estrae la struttura dell'API dai requisiti.
        """
        api_structure = []
        
        if "backend" in requirements and isinstance(requirements["backend"], dict):
            backend = requirements["backend"]
            if "api_structure" in backend:
                api_raw = backend["api_structure"]
                if isinstance(api_raw, list):
                    return api_raw
        
        # Se non è presente una struttura esplicita, prova ad estrarla dalle features
        if "features" in requirements and isinstance(requirements["features"], list):
            for feature in requirements["features"]:
                if isinstance(feature, dict):
                    for feature_name, details in feature.items():
                        # Crea una struttura base per questa feature
                        api_group = {feature_name: {"endpoints": []}}
                        
                        # Cerca di estrarre endpoint
                        if isinstance(details, dict):
                            if "endpoints" in details and isinstance(details["endpoints"], list):
                                api_group[feature_name]["endpoints"] = details["endpoints"]
                            elif "operations" in details and isinstance(details["operations"], list):
                                # Converti operations in endpoints
                                for operation in details["operations"]:
                                    if isinstance(operation, str):
                                        # Crea un endpoint basic per questa operazione
                                        endpoint = {
                                            "path": f"/api/{feature_name}/{operation}",
                                            "method": self._guess_method_for_operation(operation),
                                            "description": f"{operation} {feature_name}"
                                        }
                                        api_group[feature_name]["endpoints"].append(endpoint)
                        
                        if api_group[feature_name]["endpoints"]:
                            api_structure.append(api_group)
        
        # Se ancora vuota, crea una struttura basic
        if not api_structure:
            # Identifica entità principali
            entities = self._extract_entities_from_requirements(requirements)
            for entity in entities:
                api_structure.append({
                    entity: {
                        "endpoints": [
                            {
                                "path": f"/api/{entity.lower()}",
                                "method": "GET",
                                "description": f"Get all {entity}"
                            },
                            {
                                "path": f"/api/{entity.lower()}/{{id}}",
                                "method": "GET",
                                "description": f"Get {entity} by ID"
                            },
                            {
                                "path": f"/api/{entity.lower()}",
                                "method": "POST",
                                "description": f"Create {entity}"
                            },
                            {
                                "path": f"/api/{entity.lower()}/{{id}}",
                                "method": "PUT",
                                "description": f"Update {entity}"
                            },
                            {
                                "path": f"/api/{entity.lower()}/{{id}}",
                                "method": "DELETE",
                                "description": f"Delete {entity}"
                            }
                        ]
                    }
                })

                return api_structure
    
    def _guess_method_for_operation(self, operation: str) -> str:
        """
        Indovina il metodo HTTP appropriato per un'operazione.
        """
        operation = operation.lower()
        
        if operation.startswith("get") or operation.startswith("read") or operation.startswith("list") or operation.startswith("find"):
            return "GET"
        elif operation.startswith("create") or operation.startswith("add") or operation.startswith("insert"):
            return "POST"
        elif operation.startswith("update") or operation.startswith("edit") or operation.startswith("modify"):
            return "PUT"
        elif operation.startswith("delete") or operation.startswith("remove"):
            return "DELETE"
        elif operation.startswith("patch"):
            return "PATCH"
        else:
            return "POST"  # Default a POST per sicurezza
    
    def _extract_entities_from_requirements(self, requirements: Dict[str, Any]) -> List[str]:
        """
        Estrae le entità principali dai requisiti.
        """
        entities = []
        
        # Cerca modelli di database
        if "features" in requirements and isinstance(requirements["features"], list):
            for feature in requirements["features"]:
                if isinstance(feature, dict) and "database" in feature:
                    db_feature = feature["database"]
                    if isinstance(db_feature, dict) and "models" in db_feature:
                        models = db_feature["models"]
                        if isinstance(models, list):
                            for model in models:
                                if isinstance(model, dict):
                                    # Aggiungi la chiave del modello come entità
                                    entities.extend(model.keys())
                                elif isinstance(model, str):
                                    entities.append(model)
        
        # Se ancora non abbiamo entità, cerca di estrarle dalle features
        if not entities and "features" in requirements and isinstance(requirements["features"], list):
            for feature in requirements["features"]:
                if isinstance(feature, dict):
                    for feature_name in feature.keys():
                        # Escludi features comuni non-entità
                        if feature_name.lower() not in ["authentication", "database", "authorization", "logging"]:
                            entities.append(feature_name)
        
        # Aggiungi sempre User se ci sono feature di autenticazione
        if self._has_auth_feature(requirements) and "User" not in entities:
            entities.append("User")
        
        return entities
    
    def _has_auth_feature(self, requirements: Dict[str, Any]) -> bool:
        """
        Verifica se il progetto ha feature di autenticazione.
        """
        if "features" in requirements and isinstance(requirements["features"], list):
            for feature in requirements["features"]:
                if isinstance(feature, dict) and "authentication" in feature:
                    return True
        
        return False
    
    def _determine_rest_file_paths(self, 
                                framework: str, 
                                api_structure: List[Dict[str, Any]], 
                                requirements: Dict[str, Any]) -> List[str]:
        """
        Determina i percorsi file per endpoint REST API in base al framework.
        """
        file_paths = []
        
        # Estrai i gruppi di API
        api_groups = []
        for item in api_structure:
            if isinstance(item, dict):
                api_groups.extend(item.keys())
        
        # Determina i percorsi in base al framework
        if framework == "fastapi":
            # Main router
            file_paths.append("app/api/router.py")
            
            # API group routers
            for group in api_groups:
                file_paths.append(f"app/api/routes/{group.lower()}.py")
            
            # Se ci sono feature di autenticazione, aggiungi router auth
            if self._has_auth_feature(requirements) and "auth" not in api_groups:
                file_paths.append("app/api/routes/auth.py")
        
        elif framework == "django":
            # URLs
            file_paths.append("project_name/urls.py")
            
            # API group views and urls
            for group in api_groups:
                file_paths.append(f"api/{group.lower()}/views.py")
                file_paths.append(f"api/{group.lower()}/urls.py")
            
            # Se ci sono feature di autenticazione, aggiungi views auth
            if self._has_auth_feature(requirements) and "auth" not in api_groups:
                file_paths.append("api/auth/views.py")
                file_paths.append("api/auth/urls.py")
        
        elif framework == "flask":
            # Main app
            file_paths.append("app/__init__.py")
            
            # API group routes
            for group in api_groups:
                file_paths.append(f"app/api/{group.lower()}.py")
            
            # Se ci sono feature di autenticazione, aggiungi routes auth
            if self._has_auth_feature(requirements) and "auth" not in api_groups:
                file_paths.append("app/api/auth.py")
        
        elif framework == "express":
            # Main app
            file_paths.append("src/app.js")
            
            # API group routes
            for group in api_groups:
                file_paths.append(f"src/routes/{group.toLowerCase()}.js")
                file_paths.append(f"src/controllers/{group.toLowerCase()}.js")
            
            # Se ci sono feature # Se ci sono feature di autenticazione, aggiungi routes auth
            if self._has_auth_feature(requirements) and "auth" not in api_groups:
                file_paths.append("src/routes/auth.js")
                file_paths.append("src/controllers/auth.js")
        
        elif framework == "spring":
            # Main application
            file_paths.append("src/main/java/com/example/Application.java")
            
            # API group controllers
            for group in api_groups:
                pascal_case = ''.join(word.capitalize() for word in group.split('_'))
                file_paths.append(f"src/main/java/com/example/controllers/{pascal_case}Controller.java")
                file_paths.append(f"src/main/java/com/example/services/{pascal_case}Service.java")
            
            # Se ci sono feature di autenticazione, aggiungi controller auth
            if self._has_auth_feature(requirements) and "auth" not in api_groups:
                file_paths.append("src/main/java/com/example/controllers/AuthController.java")
                file_paths.append("src/main/java/com/example/services/AuthService.java")
        
        return file_paths
    
    def _determine_graphql_file_paths(self, 
                                    framework: str, 
                                    api_structure: List[Dict[str, Any]], 
                                    requirements: Dict[str, Any]) -> List[str]:
        """
        Determina i percorsi file per endpoint GraphQL in base al framework.
        """
        file_paths = []
        
        # Estrai i gruppi di API che rappresentano entità
        entities = []
        for item in api_structure:
            if isinstance(item, dict):
                entities.extend(item.keys())
        
        # Se non ci sono entità, usa quelle estratte dai requisiti
        if not entities:
            entities = self._extract_entities_from_requirements(requirements)
        
        # Determina i percorsi in base al framework
        if framework == "fastapi":
            # Main GraphQL schema
            file_paths.append("app/graphql/schema.py")
            
            # Type definitions and resolvers
            for entity in entities:
                file_paths.append(f"app/graphql/types/{entity.lower()}.py")
                file_paths.append(f"app/graphql/resolvers/{entity.lower()}.py")
            
            # Query and mutation definitions
            file_paths.append("app/graphql/queries.py")
            file_paths.append("app/graphql/mutations.py")
        
        elif framework == "django":
            # Main GraphQL schema
            file_paths.append("project_name/schema.py")
            
            # App-specific schemas
            for entity in entities:
                file_paths.append(f"api/{entity.lower()}/schema.py")
            
            # Type definitions
            file_paths.append("api/graphql/types.py")
        
        elif framework == "flask":
            # Main GraphQL schema
            file_paths.append("app/graphql/schema.py")
            
            # Type definitions and resolvers
            for entity in entities:
                file_paths.append(f"app/graphql/types/{entity.lower()}.py")
                file_paths.append(f"app/graphql/resolvers/{entity.lower()}.py")
        
        elif framework == "express":
            # Main GraphQL schema
            file_paths.append("src/graphql/schema.js")
            
            # Type definitions
            file_paths.append("src/graphql/typeDefs.js")
            
            # Resolvers
            file_paths.append("src/graphql/resolvers.js")
            
            # Entity-specific type definitions and resolvers
            for entity in entities:
                file_paths.append(f"src/graphql/types/{entity.toLowerCase()}.js")
                file_paths.append(f"src/graphql/resolvers/{entity.toLowerCase()}.js")
        
        elif framework == "spring":
            # Main GraphQL configuration
            file_paths.append("src/main/java/com/example/config/GraphQLConfig.java")
            
            # GraphQL types
            for entity in entities:
                pascal_case = ''.join(word.capitalize() for word in entity.split('_'))
                file_paths.append(f"src/main/java/com/example/graphql/{pascal_case}Resolver.java")
            
            # Schema definition
            file_paths.append("src/main/resources/graphql/schema.graphqls")
        
        return file_paths
    
    def _determine_rpc_type(self, requirements: Dict[str, Any]) -> str:
        """
        Determina il tipo specifico di RPC dai requisiti.
        """
        # Default a gRPC come più comune
        rpc_type = "gRPC"
        
        if "backend" in requirements and isinstance(requirements["backend"], dict):
            backend = requirements["backend"]
            if "api_type" in backend:
                api_type = backend["api_type"]
                if isinstance(api_type, str):
                    api_type_lower = api_type.lower()
                    if "jsonrpc" in api_type_lower or "json-rpc" in api_type_lower:
                        return "JSON-RPC"
                    elif "xmlrpc" in api_type_lower or "xml-rpc" in api_type_lower:
                        return "XML-RPC"
                    elif "grpc" in api_type_lower:
                        return "gRPC"
                    elif "thrift" in api_type_lower:
                        return "Thrift"
        
        return rpc_type
    
    def _determine_rpc_file_paths(self, 
                               framework: str, 
                               rpc_type: str,
                               api_structure: List[Dict[str, Any]], 
                               requirements: Dict[str, Any]) -> List[str]:
        """
        Determina i percorsi file per endpoint RPC in base al framework e tipo RPC.
        """
        file_paths = []
        
        # Estrai i gruppi di API che rappresentano servizi
        services = []
        for item in api_structure:
            if isinstance(item, dict):
                services.extend(item.keys())
        
        # Se non ci sono servizi, usa le entità estratte dai requisiti
        if not services:
            services = self._extract_entities_from_requirements(requirements)
        
        # Percorsi comuni per tutti i framework se è gRPC
        if rpc_type == "gRPC":
            # Proto files
            file_paths.append("protos/service.proto")
            
            for service in services:
                file_paths.append(f"protos/{service.lower()}.proto")
        
        # Determina i percorsi specifici in base al framework
        if framework == "fastapi" or framework == "flask":
            # Main RPC server
            file_paths.append(f"app/rpc/server.py")
            
            # Service implementations
            for service in services:
                file_paths.append(f"app/rpc/services/{service.lower()}.py")
            
            # Client implementations
            file_paths.append(f"app/rpc/client.py")
        
        elif framework == "django":
            # Main RPC server
            file_paths.append(f"project_name/rpc/server.py")
            
            # Service implementations
            for service in services:
                file_paths.append(f"api/rpc/{service.lower()}.py")
        
        elif framework == "express":
            # Main RPC server
            file_paths.append("src/rpc/server.js")
            
            # Service implementations
            for service in services:
                file_paths.append(f"src/rpc/services/{service.toLowerCase()}.js")
            
            # Client implementations
            file_paths.append("src/rpc/client.js")
        
        elif framework == "spring":
            # Main RPC configuration
            file_paths.append("src/main/java/com/example/config/RpcConfig.java")
            
            # Service implementations
            for service in services:
                pascal_case = ''.join(word.capitalize() for word in service.split('_'))
                file_paths.append(f"src/main/java/com/example/rpc/{pascal_case}Service.java")
        
        return file_paths
    
    def _determine_common_api_file_paths(self, 
                                      framework: str, 
                                      requirements: Dict[str, Any]) -> List[str]:
        """
        Determina i percorsi file comuni per API in base al framework.
        """
        file_paths = []
        
        if framework == "fastapi":
            file_paths.extend([
                "app/api/deps.py",
                "app/api/utils.py",
                "app/api/errors.py",
                "app/middleware/auth.py",
                "app/middleware/error_handler.py"
            ])
        
        elif framework == "django":
            file_paths.extend([
                "api/middleware/auth.py",
                "api/middleware/error_handler.py",
                "api/utils/response.py",
                "api/utils/pagination.py"
            ])
        
        elif framework == "flask":
            file_paths.extend([
                "app/api/utils.py",
                "app/api/errors.py",
                "app/middleware/auth.py",
                "app/middleware/error_handler.py"
            ])
        
        elif framework == "express":
            file_paths.extend([
                "src/middleware/auth.js",
                "src/middleware/error-handler.js",
                "src/utils/response.js",
                "src/utils/validation.js"
            ])
        
        elif framework == "spring":
            file_paths.extend([
                "src/main/java/com/example/config/WebConfig.java",
                "src/main/java/com/example/exceptions/GlobalExceptionHandler.java",
                "src/main/java/com/example/security/SecurityConfig.java",
                "src/main/java/com/example/utils/ResponseUtil.java"
            ])
        
        return file_paths
    
    def _determine_api_doc_file_paths(self, 
                                   framework: str, 
                                   doc_type: str,
                                   requirements: Dict[str, Any]) -> List[str]:
        """
        Determina i percorsi file per documentazione API in base al framework e tipo doc.
        """
        file_paths = []
        
        if doc_type == "swagger":
            if framework == "fastapi":
                file_paths.append("app/api/docs.py")
            elif framework == "django":
                file_paths.append("project_name/swagger.py")
            elif framework == "flask":
                file_paths.append("app/api/docs.py")
            elif framework == "express":
                file_paths.append("src/docs/swagger.js")
                file_paths.append("src/docs/swagger.json")
            elif framework == "spring":
                file_paths.append("src/main/java/com/example/config/SwaggerConfig.java")
        
        elif doc_type == "graphql":
            if framework == "fastapi" or framework == "flask":
                file_paths.append("app/graphql/playground.py")
            elif framework == "django":
                file_paths.append("project_name/graphql_playground.py")
            elif framework == "express":
                file_paths.append("src/graphql/playground.js")
            elif framework == "spring":
                file_paths.append("src/main/java/com/example/config/GraphQLPlaygroundConfig.java")
        
        return file_paths
    
    def _needs_api_docs(self, requirements: Dict[str, Any]) -> bool:
        """
        Determina se è necessaria la documentazione API dai requisiti.
        """
        # Default a True perché la documentazione è quasi sempre utile
        docs_needed = True
        
        # Controlla esplicitamente nelle options di documentazione
        if "documentation" in requirements:
            docs = requirements["documentation"]
            if isinstance(docs, dict) and "api_docs" in docs:
                return bool(docs["api_docs"])
            elif isinstance(docs, bool):
                return docs
        
        # Controlla nelle options di backend
        if "backend" in requirements and isinstance(requirements["backend"], dict):
            backend = requirements["backend"]
            if "documentation" in backend:
                doc_option = backend["documentation"]
                if isinstance(doc_option, bool):
                    return doc_option
                elif isinstance(doc_option, dict) and "api_docs" in doc_option:
                    return bool(doc_option["api_docs"])
        
        return docs_needed
    
    def _identify_missing_paths(self, generated_paths: List[str], required_paths: List[str]) -> List[str]:
        """
        Identifica i percorsi file mancanti rispetto a quelli richiesti.
        """
        generated_set = set(generated_paths)
        required_set = set(required_paths)
        
        return list(required_set - generated_set)
    
    def _extract_endpoint_from_path(self, path: str) -> str:
        """
        Estrae il nome dell'endpoint dal percorso del file.
        """
        # Pattern più comuni:
        # app/api/routes/users.py -> users
        # api/users/views.py -> users
        # src/routes/users.js -> users
        # src/controllers/users.js -> users
        
        parts = path.split('/')
        
        for part in parts:
            # Rimuovi estensioni comuni
            for ext in ['.py', '.js', '.ts', '.java']:
                part = part.replace(ext, '')
            
            # Escludi nomi comuni di cartelle o file
            if part.lower() not in ['app', 'api', 'routes', 'views', 'controllers', 'src', 'main', 'graphql', 'rpc', 'services']:
                return part
        
        # Fallback al penultimo elemento del percorso (assumendo che l'ultimo sia un file)
        if len(parts) >= 2:
            return parts[-2]
        
        return "unknown"
    
    def _find_endpoint_structure(self, endpoint: str, api_structure: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cerca la struttura dell'endpoint specifico nella struttura API.
        """
        # Normalizza endpoint per il confronto
        endpoint_norm = endpoint.lower()
        
        for group in api_structure:
            if isinstance(group, dict):
                for group_name, details in group.items():
                    # Confronta normalizzato
                    if group_name.lower() == endpoint_norm:
                        return {group_name: details}
        
        # Endpoint non trovato, ritorna struttura vuota
        return {endpoint: {"endpoints": []}}
    
    def _extract_graphql_entity_from_path(self, path: str) -> str:
        """
        Estrae il nome dell'entità GraphQL dal percorso del file.
        """
        # Esempi:
        # app/graphql/types/user.py -> user
        # app/graphql/resolvers/user.py -> user
        # src/graphql/types/user.js -> user
        
        parts = path.split('/')
        
        # Assume che il nome dell'entità sia l'ultimo componente prima dell'estensione
        if len(parts) > 0:
            last_part = parts[-1]
            for ext in ['.py', '.js', '.ts', '.java', '.graphqls']:
                last_part = last_part.replace(ext, '')
            
            # Se è un file schema o generico, cerca nella directory precedente
            if last_part in ['schema', 'types', 'resolvers', 'typeDefs']:
                if len(parts) > 1:
                    return parts[-2]
            
            return last_part
        
        return "unknown"
    
    def _extract_rpc_service_from_path(self, path: str) -> str:
        """
        Estrae il nome del servizio RPC dal percorso del file.
        """
        # Esempi:
        # protos/user.proto -> user
        # app/rpc/services/user.py -> user
        # src/rpc/services/user.js -> user
        
        parts = path.split('/')
        
        # Assume che il nome del servizio sia l'ultimo componente prima dell'estensione
        if len(parts) > 0:
            last_part = parts[-1]
            for ext in ['.py', '.js', '.ts', '.java', '.proto']:
                last_part = last_part.replace(ext, '')
            
            # Se è un file client o server generico, cerca nella directory precedente
            if last_part in ['client', 'server', 'service']:
                if len(parts) > 1:
                    return parts[-2]
            
            return last_part
        
        return "unknown"
    
    async def _generate_single_rest_file(self, 
                                      path: str, 
                                      endpoint_structure: Dict[str, Any],
                                      framework: str,
                                      requirements: Dict[str, Any],
                                      provider: str) -> str:
        """
        Genera un singolo file di endpoint REST.
        """
        logger.info(f"Generating single REST file for {path}")
        
        system_prompt = f"""You are an expert backend developer specializing in {framework} REST API development.
        Create a high-quality {path} file that implements REST endpoints following best practices for
        security, performance, and maintainability."""
        
        # Estrai informazioni sulla struttura dell'endpoint
        endpoint_name = next(iter(endpoint_structure.keys()))
        endpoints = endpoint_structure[endpoint_name].get("endpoints", [])
        
        prompt = f"""Create a single REST API file for path: {path}
        
Framework: {framework}
Endpoint name: {endpoint_name}
Endpoint structure:
{json.dumps(endpoints, indent=2)}

Project requirements:
{json.dumps(requirements, indent=2)}

Create a complete implementation of this file with:
1. All necessary imports
2. Route definitions and handlers
3. Input validation
4. Error handling
5. Authentication integration where needed
6. Clear documentation and comments

Follow REST API best practices:
- Clean code structure
- Input validation
- Proper HTTP methods and status codes
- Response formatting
- Error handling
- Security considerations

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
    
    async def _generate_single_graphql_file(self, 
                                         path: str, 
                                         entity_type: str,
                                         framework: str,
                                         requirements: Dict[str, Any],
                                         provider: str) -> str:
        """
        Genera un singolo file di endpoint GraphQL.
        """
        logger.info(f"Generating single GraphQL file for {path}")
        
        system_prompt = f"""You are an expert backend developer specializing in {framework} GraphQL API development.
        Create a high-quality {path} file that implements GraphQL types, resolvers or schemas following best practices
        for security, performance, and maintainability."""
        
        # Determina il tipo di file GraphQL
        file_type = "schema"
        if "types" in path:
            file_type = "type"
        elif "resolvers" in path:
            file_type = "resolver"
        elif "mutations" in path:
            file_type = "mutation"
        elif "queries" in path:
            file_type = "query"
        
        prompt = f"""Create a single GraphQL API file for path: {path}
        
Framework: {framework}
Entity name: {entity_type}
File type: {file_type}

Project requirements:
{json.dumps(requirements, indent=2)}

Create a complete implementation of this GraphQL {file_type} file with:
1. All necessary imports
2. Type definitions, resolvers, or schema
3. Field specifications
4. Authorization checks if needed
5. Error handling
6. Clear documentation and comments

Follow GraphQL best practices:
- Clean type definitions
- Efficient resolver implementation
- N+1 query prevention
- Authorization integration
- Error handling
- Descriptive documentation

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
    
    async def _generate_single_rpc_file(self, 
                                     path: str, 
                                     service_name: str,
                                     rpc_type: str,
                                     framework: str,
                                     requirements: Dict[str, Any],
                                     provider: str) -> str:
        """
        Genera un singolo file di endpoint RPC.
        """
        logger.info(f"Generating single {rpc_type} file for {path}")
        
        system_prompt = f"""You are an expert backend developer specializing in {framework} {rpc_type} API development.
        Create a high-quality {path} file that implements {rpc_type} services, clients, or protos following best practices
        for security, performance, and maintainability."""
        
        # Determina il tipo di file RPC
        file_type = "service"
        if path.endswith(".proto"):
            file_type = "proto"
        elif "client" in path:
            file_type = "client"
        elif "server" in path:
            file_type = "server"
        
        prompt = f"""Create a single {rpc_type} API file for path: {path}
        
Framework: {framework}
Service name: {service_name}
File type: {file_type}

Project requirements:
{json.dumps(requirements, indent=2)}

Create a complete implementation of this {rpc_type} {file_type} file with:
1. All necessary imports
2. Service definitions
3. Method implementations
4. Error handling
5. Authentication integration if needed
6. Clear documentation and comments

Follow {rpc_type} best practices:
- Clean service definitions
- Efficient method implementation
- Error handling
- Authentication integration
- Performance considerations
- Descriptive documentation

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
    
    def _extract_files(self, response: str) -> Dict[str, str]:
        """
        Estrai i file dalla risposta LLM utilizzando il pattern FILE: ... ```
        """
        import re
        
        files = {}
        # Pattern per individuare FILE: path seguito da un blocco di codice
        pattern = r'FILE:\s*([^\n]+)\s*\n```(?:\w+)?\s*\n(.*?)\n```'
        matches = re.finditer(pattern, response, re.DOTALL)
        
        for match in matches:
            file_path, content = match.groups()
            file_path = file_path.strip()
            if file_path:
                files[file_path] = content.strip()
        
        return files
    
    def _clean_code_blocks(self, content: str) -> str:
        """
        Rimuove blocchi di codice dalla risposta per ottenere solo il contenuto.
        """
        import re
        
        # Rimuovi blocchi di codice ```python ... ```
        cleaned = re.sub(r'```(?:python|typescript|javascript|java|graphql|proto|)\s*(.*?)\s*```', r'\1', content, flags=re.DOTALL)
        
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
    
    async def generate_api_gateway(self, requirements: Dict[str, Any], provider: str) -> Dict[str, str]:
        """
        Genera file per implementare un API gateway che unifica più servizi backend.
        Utile per architetture di microservizi.
        """
        logger.info("Generating API gateway files")
        
        system_prompt = """You are an expert in API gateway design and implementation.
        Create comprehensive API gateway files that efficiently route requests, handle authentication,
        implement rate limiting, and provide a unified API interface for client applications."""
        
        # Determina il tipo di API gateway
        gateway_type = self._determine_gateway_type(requirements)
        logger.info(f"Using {gateway_type} gateway type")
        
        # Determina i servizi che il gateway deve integrare
        services = self._extract_gateway_services(requirements)
        
        prompt = f"""Create API gateway files for a {gateway_type} gateway with these services:
        
Services to integrate:
{json.dumps(services, indent=2)}

Project requirements:
{json.dumps(requirements, indent=2)}

Generate the following API gateway files:
1. Gateway configuration and setup
2. Route definitions and service mappings
3. Authentication and authorization
4. Rate limiting and throttling
5. Response transformation and error handling
6. Monitoring and logging

For each file, use EXACTLY this format:
FILE: path/to/file.ext
```language
[complete file content]
```

Follow API gateway best practices:
- Clean routing configuration
- Proper authentication forwarding
- Efficient request handling
- Load balancing
- Rate limiting
- Monitoring and logging
- Security considerations
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai i file dalla risposta LLM
        gateway_files = self._extract_files(response)
        logger.info(f"Generated {len(gateway_files)} API gateway files")
        
        return gateway_files
    
    def _determine_gateway_type(self, requirements: Dict[str, Any]) -> str:
        """
        Determina il tipo di API gateway dai requisiti.
        """
        # Default a "Nginx" come gateway di base
        gateway_type = "Nginx"
        
        if "backend" in requirements and isinstance(requirements["backend"], dict):
            backend = requirements["backend"]
            
            if "gateway" in backend:
                gateway_info = backend["gateway"]
                if isinstance(gateway_info, str):
                    return gateway_info
                elif isinstance(gateway_info, dict) and "type" in gateway_info:
                    return gateway_info["type"]
            
            # Check per architettura di microservizi
            if "architecture" in backend:
                arch = backend["architecture"]
                if isinstance(arch, str) and "microservice" in arch.lower():
                    return "Kong"  # Kong è una buona scelta per microservizi
                elif isinstance(arch, dict) and arch.get("type") == "microservices":
                    return "Kong"
        
        return gateway_type
    
    def _extract_gateway_services(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Estrae i servizi che il gateway deve integrare dai requisiti.
        """
        services = []
        
        # Controlla se ci sono servizi esplicitamente definiti
        if "backend" in requirements and isinstance(requirements["backend"], dict):
            backend = requirements["backend"]
            
            if "services" in backend:
                backend_services = backend["services"]
                if isinstance(backend_services, list):
                    for service in backend_services:
                        if isinstance(service, dict):
                            for service_name, details in service.items():
                                services.append({
                                    "name": service_name,
                                    "details": details
                                })
                        elif isinstance(service, str):
                            services.append({
                                "name": service,
                                "details": {}
                            })
        
        # Se non ci sono servizi espliciti, usa la struttura API per definire servizi logici
        if not services and "backend" in requirements and "api_structure" in requirements["backend"]:
            api_structure = requirements["backend"]["api_structure"]
            if isinstance(api_structure, list):
                for group in api_structure:
                    if isinstance(group, dict):
                        for group_name, details in group.items():
                            services.append({
                                "name": group_name,
                                "path": f"/api/{group_name.lower()}",
                                "endpoints": details.get("endpoints", [])
                            })
        
        # Se ancora non ci sono servizi, crea servizi basati sulle entità
        if not services:
            entities = self._extract_entities_from_requirements(requirements)
            for entity in entities:
                services.append({
                    "name": entity,
                    "path": f"/api/{entity.lower()}",
                    "methods": ["GET", "POST", "PUT", "DELETE"]
                })
        
        return services