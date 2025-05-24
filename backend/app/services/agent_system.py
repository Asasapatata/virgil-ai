# backend/app/services/agent_system.py
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class SystemAgent:
    """
    Agente di sistema che coordina la generazione di file di configurazione
    e integrazione con la struttura generale dell'applicazione.
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        logger.info("SystemAgent initialized")
    
    async def generate_system_files(self, 
                                  requirements: Dict[str, Any],
                                  provider: str) -> Dict[str, str]:
        """
        Genera file di configurazione e utilità di sistema necessari 
        per il funzionamento dell'applicazione.
        """
        logger.info("Generating system files")
        
        system_files = {}
        
        # Genera file di configurazione principali
        config_files = await self._generate_config_files(requirements, provider)
        system_files.update(config_files)
        
        # Genera utilità di sistema
        utility_files = await self._generate_utility_files(requirements, provider)
        system_files.update(utility_files)
        
        # Genera file di integrazione se necessario
        if self._needs_integration_files(requirements):
            integration_files = await self._generate_integration_files(requirements, provider)
            system_files.update(integration_files)
        
        logger.info(f"Generated {len(system_files)} system files")
        return system_files
    
    async def _generate_config_files(self, 
                                   requirements: Dict[str, Any],
                                   provider: str) -> Dict[str, str]:
        """Genera file di configurazione come .env, docker-compose, etc."""
        
        system_prompt = """You are an expert DevOps engineer specializing in application configuration.
        Generate comprehensive configuration files required for the application described.
        Include environment setup, deployment configuration, and integration settings."""
        
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        prompt = f"""Create necessary configuration files for a {project_type} application with these requirements:
        
{json.dumps(requirements, indent=2)}

Generate the following configuration files:
1. Docker and containerization setup
2. Environment configuration templates
3. Build and deployment scripts
4. Any other configuration files essential for the application

For each file, use EXACTLY this format:
FILE: path/to/file.ext
```language
[complete file content]
```

Do not use placeholders or incomplete sections. Files should be deployment-ready.
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai i file dalla risposta LLM
        config_files = self._extract_files(response)
        logger.info(f"Generated {len(config_files)} configuration files")
        
        return config_files
    
    async def _generate_utility_files(self, 
                                   requirements: Dict[str, Any],
                                   provider: str) -> Dict[str, str]:
        """Genera file di utilità come script, helpers, etc."""
        
        system_prompt = """You are an expert system architect specializing in application utilities.
        Generate high-quality utility files that improve application reliability, performance and security.
        Provide complete, production-ready implementations."""
        
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        prompt = f"""Create essential utility files for a {project_type} application with these requirements:
        
{json.dumps(requirements, indent=2)}

Generate the following utility files:
1. Error handling and logging utilities
2. Security-related helpers (encryption, authentication)
3. Data validation and sanitization utilities
4. Performance monitoring tools
5. Any other utilities essential for system operation

For each file, use EXACTLY this format:
FILE: path/to/file.ext
```language
[complete file content]
```

Make sure utilities integrate well with the rest of the system and follow best practices.
Files should be complete without placeholders or TODOs.
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai i file dalla risposta LLM
        utility_files = self._extract_files(response)
        logger.info(f"Generated {len(utility_files)} utility files")
        
        return utility_files
    
    async def _generate_integration_files(self, 
                                       requirements: Dict[str, Any],
                                       provider: str) -> Dict[str, str]:
        """Genera file di integrazione con sistemi esterni"""
        
        system_prompt = """You are an expert integration engineer specializing in connecting systems.
        Generate high-quality integration files that enable secure and efficient communication
        between the application and external services."""
        
        # Determine which integrations are needed
        integrations = self._identify_required_integrations(requirements)
        
        prompt = f"""Create integration files for connecting this application with external systems:
        
{json.dumps(requirements, indent=2)}

The following integrations are needed: {', '.join(integrations)}

Generate complete integration files for each external system:
1. API clients and connection handlers
2. Error handling and retry logic
3. Authentication and secure communication
4. Data transformation and normalization
5. Configuration and environment setup

For each file, use EXACTLY this format:
FILE: path/to/file.ext
```language
[complete file content]
```

Make sure integrations are secure, well-documented, and include proper error handling.
Files should be complete and production-ready.
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai i file dalla risposta LLM
        integration_files = self._extract_files(response)
        logger.info(f"Generated {len(integration_files)} integration files")
        
        return integration_files
    
    def _needs_integration_files(self, requirements: Dict[str, Any]) -> bool:
        """Determina se l'applicazione necessita di file di integrazione"""
        
        # Controlla le caratteristiche che indicano necessità di integrazione
        if "features" in requirements:
            for feature in requirements["features"]:
                if isinstance(feature, dict):
                    # Controlla integrazioni di autenticazione
                    if "authentication" in feature and "providers" in feature["authentication"]:
                        providers = feature["authentication"]["providers"]
                        if any(p != "email" for p in providers):
                            return True
                    
                    # Controlla integrazioni di database
                    if "database" in feature and feature["database"].get("type") not in ["sqlite", "memory"]:
                        return True
                    
                    # Controlla servizi esterni
                    if "external_services" in feature:
                        return True
        
        # Controlla i servizi di backend
        if "backend" in requirements and "services" in requirements["backend"]:
            for service in requirements["backend"]["services"]:
                if isinstance(service, dict) and any(
                    s_name in service for s_name in ["EmailService", "PaymentService", "NotificationService"]
                ):
                    return True
                elif isinstance(service, str) and any(
                    s_name in service for s_name in ["Email", "Payment", "Notification", "SMS", "Analytics"]
                ):
                    return True
        
        return False
    
    def _identify_required_integrations(self, requirements: Dict[str, Any]) -> List[str]:
        """Identifica le integrazioni necessarie in base ai requisiti"""
        
        integrations = []
        
        # Controlla i provider di autenticazione
        if "features" in requirements:
            for feature in requirements["features"]:
                if isinstance(feature, dict) and "authentication" in feature:
                    auth_feature = feature["authentication"]
                    if "providers" in auth_feature:
                        providers = auth_feature["providers"]
                        for provider in providers:
                            if provider != "email":
                                integrations.append(f"{provider} authentication")
                
                # Controlla tipo di database
                if isinstance(feature, dict) and "database" in feature:
                    db_type = feature["database"].get("type")
                    if db_type not in ["sqlite", "memory", None]:
                        integrations.append(f"{db_type} database")
        
        # Controlla i servizi backend
        if "backend" in requirements and "services" in requirements["backend"]:
            for service in requirements["backend"]["services"]:
                if isinstance(service, dict):
                    for service_name, details in service.items():
                        if "provider" in details:
                            integrations.append(f"{details['provider']} for {service_name}")
                        elif service_name in ["EmailService", "PaymentService", "NotificationService"]:
                            integrations.append(service_name)
                elif isinstance(service, str):
                    if any(s_type in service for s_type in ["Email", "Payment", "Notification", "SMS", "Analytics"]):
                        integrations.append(service)
        
        # Check deployment requirements
        if "deployment" in requirements:
            deployment = requirements["deployment"]
            if isinstance(deployment, dict):
                # Add cloud providers
                if "cloud" in deployment:
                    cloud = deployment["cloud"]
                    if isinstance(cloud, str):
                        integrations.append(f"{cloud} cloud integration")
                    elif isinstance(cloud, dict) or isinstance(cloud, list):
                        for provider in cloud if isinstance(cloud, list) else [cloud]:
                            if isinstance(provider, str):
                                integrations.append(f"{provider} cloud integration")
                            elif isinstance(provider, dict) and "provider" in provider:
                                integrations.append(f"{provider['provider']} cloud integration")
        
        return list(set(integrations))  # Remove duplicates
    
    def _extract_files(self, response: str) -> Dict[str, str]:
        """Estrai i file dalla risposta LLM utilizzando il pattern FILE: ... ```"""
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
    
    async def generate_ci_cd_config(self,
                                  requirements: Dict[str, Any],
                                  provider: str) -> Dict[str, str]:
        """
        Genera configurazioni specifiche per CI/CD come GitHub Actions,
        GitLab CI, o altri formati di pipeline.
        """
        logger.info("Generating CI/CD configuration files")
        
        system_prompt = """You are an expert DevOps engineer specializing in CI/CD pipelines.
        Generate comprehensive CI/CD configuration files that automate testing, building, and
        deployment of applications according to modern DevOps best practices."""
        
        # Determina il tipo di CI/CD in base ai requisiti
        ci_type = self._determine_ci_type(requirements)
        
        prompt = f"""Create CI/CD configuration files for a {ci_type} pipeline with these requirements:
        
{json.dumps(requirements, indent=2)}

Generate the following CI/CD configuration files:
1. Pipeline definition for building, testing, and deploying the application
2. Environment-specific configurations (dev, staging, production)
3. Security scanning and quality checks
4. Notification and alerting settings

For each file, use EXACTLY this format:
FILE: path/to/file.ext
```language
[complete file content]
```

Make sure configurations follow best practices for {ci_type} and include 
all necessary steps for a complete pipeline.
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai i file dalla risposta LLM
        ci_files = self._extract_files(response)
        logger.info(f"Generated {len(ci_files)} CI/CD configuration files")
        
        return ci_files
    
    def _determine_ci_type(self, requirements: Dict[str, Any]) -> str:
        """Determina il tipo di CI/CD da usare in base ai requisiti"""
        
        # Default to GitHub Actions as it's widely used
        ci_type = "GitHub Actions"
        
        # Check if deployment section specifies a CI provider
        if "deployment" in requirements:
            deployment = requirements["deployment"]
            if isinstance(deployment, dict):
                if "ci_cd" in deployment:
                    ci_cd = deployment["ci_cd"]
                    if isinstance(ci_cd, str):
                        ci_type = ci_cd
                    elif isinstance(ci_cd, dict) and "provider" in ci_cd:
                        ci_type = ci_cd["provider"]
        
        return ci_type
    
    async def analyze_requirements(self, 
                                 requirements: Dict[str, Any],
                                 provider: str) -> Dict[str, Any]:
        """
        Analizza i requisiti e fornisce informazioni utili per la generazione 
        come scelte architetturali, migliori pratiche, etc.
        """
        logger.info("Analyzing project requirements")
        
        system_prompt = """You are an expert software architect with deep knowledge of modern development practices.
        Analyze the provided requirements and provide valuable insights that will guide development decisions."""
        
        prompt = f"""Analyze these project requirements in depth:
        
{json.dumps(requirements, indent=2)}

Your task is to:
1. Identify the main architectural patterns that should be applied
2. Highlight potential challenges or risks in the requirements
3. Suggest best practices for implementation
4. Identify any missing critical components
5. Recommend technology choices where requirements are ambiguous

Provide your analysis in JSON format with the following structure:
```json
{{
  "architecture": [list of recommended architectural patterns],
  "challenges": [list of potential challenges with explanations],
  "best_practices": [list of recommended best practices],
  "missing_components": [list of any critical missing pieces],
  "technology_recommendations": {{key: value map of tech choices}}
}}
```

Be thorough and specific in your analysis, focusing on the most impactful insights.
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Estrai il JSON dalla risposta
        analysis = self._extract_json(response)
        logger.info("Requirements analysis completed")
        
        return analysis
    
    def _extract_json(self, response: str) -> Dict[str, Any]:
        """Estrai JSON dalla risposta LLM"""
        import re
        import json
        
        # Try to find JSON block
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        json_match = re.search(json_pattern, response)
        
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from code block, trying to extract JSON directly")
        
        # If no code block or parsing failed, try to extract JSON directly
        try:
            # Look for curly braces content
            braces_pattern = r'({[\s\S]*})'
            braces_match = re.search(braces_pattern, response)
            
            if braces_match:
                return json.loads(braces_match.group(1))
        except Exception:
            logger.error("Failed to extract JSON from response")
            
        # Return empty dict if everything fails
        return {}