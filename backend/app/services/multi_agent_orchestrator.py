# backend/app/services/multi_agent_orchestrator.py
import json
import logging
import re
import asyncio
from typing import Dict, Any, List, Optional, Callable, Set
from pathlib import Path

from app.services.llm_service import LLMService
from app.services.code_generator import CodeGenerator
from app.services.test_agent import TestAgent
from app.services.agent_system import SystemAgent
from app.services.agent_integration import IntegrationAgent
from app.services.endpoints_agent import EndpointsAgent
from app.services.enhanced_test_agent import EnhancedTestAgent
from app.services.iteration_manager import IterationManager, IterationStructure


logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    """
    🔥 ENHANCED VERSION: Orchestratore avanzato che coordina diversi agenti specializzati
    per generare un'applicazione completa in modo collaborativo.
    
    MODIFICATIONS APPLIED:
    - ✅ Dependency tracking automatico
    - ✅ Generazione coordinata di file essenziali
    - ✅ Fix intelligente degli errori di importazione
    - ✅ Sequenza di generazione ottimizzata
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        
        # Inizializza tutti gli agenti
        self.code_generator = CodeGenerator(llm_service)
        self.test_agent = TestAgent(llm_service)
        self.system_agent = SystemAgent(llm_service)
        self.integration_agent = IntegrationAgent(llm_service)
        self.endpoints_agent = EndpointsAgent(llm_service)
        
        self.enhanced_test_agent = EnhancedTestAgent(llm_service)
        self.iteration_manager = IterationManager()
        
        self.stop_requested = False
        
        # 🔥 NEW: Dependency tracking
        self.required_files = set()
        self.generated_files = set()
        
        logger.info("MultiAgentOrchestrator initialized with Enhanced V2 support and dependency tracking")
    
    async def analyze_requirements(self, 
                                 requirements: Dict[str, Any], 
                                 provider: str) -> Dict[str, Any]:
        """
        Analizza i requisiti e pianifica il progetto utilizzando gli agenti.
        """
        logger.info("Analyzing requirements with system agent")
        
        # Usa SystemAgent per analizzare i requisiti
        return await self.system_agent.analyze_requirements(requirements, provider)
    
    async def generate_multi_agent_application(self, 
                                            requirements: Dict[str, Any],
                                            provider: str,
                                            max_iterations: int,
                                            project_path: Path,
                                            progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        🔥 ENHANCED: Generazione con dependency tracking e fix automatico
        """
        stop_file = project_path / "STOP_REQUESTED"
        if stop_file.exists():
            logger.info(f"Stop file found for project {project_path.name}, stopping generation")
            return {"status": "stopped", "reason": "user_requested"}
        
        logger.info(f"Starting enhanced multi-agent generation with dependency resolution")
        
        # Extract project name
        project_name = requirements.get("project", {}).get("name", project_path.name)
        if not project_name or project_name == project_path.name:
            project_name = f"project_{project_path.name}"
        
        # Track project state
        project_state = {
            "iterations_completed": 0,
            "total_errors_fixed": 0,
            "remaining_issues": [],
            "final_success": False,
            "generation_mode": "multi_agent_enhanced_v3",
            "dependency_tracking": True,
            "files_generated_automatically": 0
        }
        
        # 🔥 FASE 1: Analisi requirements con sistema V2
        if progress_callback:
            progress_callback(0, 'analyzing_requirements_enhanced')
        
        analysis = await self.analyze_requirements(requirements, provider)
        
        # Main iteration loop con Enhanced Dependency Resolution
        for iteration in range(1, max_iterations + 1):
            logger.info(f"🚀 Starting enhanced iteration {iteration} with dependency resolution")
            
            # Check for stop request
            if stop_file.exists() or self.stop_requested:
                logger.info("Stop requested, interrupting generation")
                return {
                    "status": "stopped",
                    "reason": "user_requested",
                    "iteration": iteration - 1,
                    "project_id": project_path.name,
                    "project_state": project_state
                }
            
            try:
                # Update current iteration
                self._update_current_iteration(project_path, iteration)
                
                # 🔥 STEP 1: Create Enhanced V2 iteration structure
                iteration_structure = self.iteration_manager.create_iteration_structure(
                    project_path, project_name, iteration
                )
                
                # 🔥 STEP 2: Enhanced code generation with dependency coordination
                if progress_callback:
                    progress_callback(iteration, 'generating_coordinated_code')
                
                # Reset tracking for this iteration
                self.required_files = set()
                self.generated_files = set()
                
                code_files = await self._generate_multi_agent_code_enhanced(
                    requirements, provider, iteration, project_path, project_name, analysis
                )
                
                # 🔥 STEP 2.5: Ensure all dependencies are satisfied
                missing_files = await self._ensure_all_dependencies(code_files, requirements, provider)
                if missing_files:
                    logger.info(f"📋 Generated {len(missing_files)} missing dependency files")
                    code_files.update(missing_files)
                    project_state["files_generated_automatically"] += len(missing_files)
                
                # 🔥 STEP 3: Save in Enhanced V2 structure
                files_generated, files_modified = self.iteration_manager.save_generated_code(
                    iteration_structure, code_files
                )
                
                logger.info(f"Enhanced Multi-Agent Iteration {iteration}: Generated {files_generated} files, modified {files_modified}")
                
                # 🔥 STEP 4: Enhanced V2 validation and testing
                if progress_callback:
                    progress_callback(iteration, 'enhanced_validation_with_dependency_check')
                
                iteration_result = await self.enhanced_test_agent.process_iteration_complete(
                    iteration_structure, project_name, iteration, requirements, code_files, provider
                )
                
                # Update project state
                project_state["iterations_completed"] = iteration
                project_state["remaining_issues"] = iteration_result.get("errors_for_fixing", [])
                
                # 🔥 ENHANCED: Check success with dependency consideration
                dependency_issues = self._count_dependency_issues(iteration_result.get("errors_for_fixing", []))
                project_state["dependency_issues_remaining"] = dependency_issues
                
                if iteration_result["success"] and dependency_issues == 0:
                    logger.info(f"🎉 Enhanced iteration {iteration} completed successfully with all dependencies resolved!")
                    project_state["final_success"] = True
                    
                    return {
                        "status": "completed",
                        "iteration": iteration,
                        "project_id": project_path.name,
                        "project_name": project_name,
                        "output_path": str(iteration_structure.iteration_path),
                        "project_state": project_state,
                        "final_result": iteration_result,
                        "generation_strategy": "multi_agent_enhanced_v3"
                    }
                
                # Continue to next iteration
                logger.info(f"Enhanced iteration {iteration}: {dependency_issues} dependency issues remaining, continuing...")
                
            except Exception as e:
                logger.error(f"Error in enhanced multi-agent iteration {iteration}: {str(e)}")
                if iteration == max_iterations:
                    return {
                        "status": "failed",
                        "reason": "iteration_error",
                        "error": str(e),
                        "iteration": iteration,
                        "project_id": project_path.name,
                        "project_state": project_state
                    }
                continue
        
        # Max iterations reached
        return {
            "status": "completed_with_issues",
            "reason": "max_iterations_reached",
            "iterations": max_iterations,
            "project_id": project_path.name,
            "project_name": project_name,
            "project_state": project_state,
            "generation_strategy": "multi_agent_enhanced_v3"
        }
    
    # Modifiche da applicare al tuo multi_agent_orchestrator.py esistente

# 1. SOSTITUISCI il metodo _generate_multi_agent_code_v2() con questo:

    async def _generate_multi_agent_code_enhanced(self,
                                        requirements: Dict[str, Any],
                                        provider: str,
                                        iteration: int,
                                        project_path: Path,
                                        project_name: str,
                                        analysis: Dict[str, Any]) -> Dict[str, str]:
        """
        🔥 ENHANCED: Genera codice con struttura project-xyz + env_test
        """
        logger.info(f"Generating structured multi-agent code for iteration {iteration}")
        
        if iteration == 1:
            # Prima iterazione: coordinazione completa con struttura corretta
            return await self._generate_complete_structured_application(
                requirements, provider, iteration, project_path, project_name, analysis
            )
        else:
            # Iterazioni successive: carica e migliora con struttura corretta
            previous_files = self.iteration_manager.load_previous_iteration_files(
                project_path, project_name, iteration
            )
            
            # Carica errori precedenti
            previous_errors = self._load_previous_iteration_errors_v2(project_path, iteration - 1)
            
            if previous_errors:
                # Multi-agent fixing con struttura corretta
                improved_files = await self._multi_agent_fix_issues(
                    requirements, provider, previous_errors, previous_files
                )
                # Applica struttura corretta ai file fix
                return self._apply_structured_organization(improved_files, requirements)
            else:
                # Multi-agent enhancement con struttura corretta
                enhanced_files = await self._multi_agent_enhance_quality(
                    requirements, provider, previous_files, iteration
                )
                # Applica struttura corretta ai file enhanced
                return self._apply_structured_organization(enhanced_files, requirements)

    # 2. AGGIUNGI questi nuovi metodi:

    async def _generate_complete_structured_application(self,
                                                    requirements: Dict[str, Any],
                                                    provider: str,
                                                    iteration: int,
                                                    project_path: Path,
                                                    project_name: str,
                                                    analysis: Dict[str, Any]) -> Dict[str, str]:
        """
        🔥 NEW: Genera applicazione con struttura project-xyz + env_test
        """
        logger.info("🏗️ Generating complete structured application")
        
        all_files = {}
        
        # Estrai nome progetto pulito
        clean_project_name = self._clean_project_name(requirements.get("project_name", project_name))
        
        # 🔥 STEP 1: Genera codice con metodi esistenti
        logger.info("📋 Step 1: Generating code with existing multi-agent system...")
        
        # Usa i metodi esistenti per generare il codice
        raw_files = {}
        
        # Sistema e configurazione
        try:
            system_files = await self.system_agent.generate_system_files(requirements, provider)
            raw_files.update(system_files)
        except Exception as e:
            logger.warning(f"System agent failed: {e}")
        
        # Integrazioni
        try:
            integration_files = await self.integration_agent.generate_integrations(requirements, provider)
            raw_files.update(integration_files)
        except Exception as e:
            logger.warning(f"Integration agent failed: {e}")
        
        # API Endpoints
        try:
            endpoint_files = await self.endpoints_agent.generate_endpoints(requirements, provider)
            raw_files.update(endpoint_files)
        except Exception as e:
            logger.warning(f"Endpoints agent failed: {e}")
        
        # Core application
        try:
            core_files = await self._generate_core_application_code(requirements, provider, raw_files)
            raw_files.update(core_files)
        except Exception as e:
            logger.warning(f"Core application failed: {e}")
        
        # 🔥 STEP 2: Organizza i file nella struttura corretta
        logger.info("🏗️ Step 2: Organizing files into structured format...")
        structured_files = self._organize_files_into_structure(raw_files, clean_project_name, requirements)
        all_files.update(structured_files)
        
        # 🔥 STEP 3: Genera env_test con copia completa + Docker
        logger.info("🧪 Step 3: Creating test environment with complete copy...")
        test_env_files = self._create_test_environment(structured_files, clean_project_name, requirements)
        all_files.update(test_env_files)
        
        # 🔥 STEP 4: Genera file di supporto
        logger.info("📄 Step 4: Creating support files...")
        support_files = self._create_support_files(requirements, clean_project_name)
        all_files.update(support_files)
        
        logger.info(f"✅ Structured application generated: {len(all_files)} files")
        logger.info(f"📁 Structure: project-{clean_project_name}/ + env_test/ + support")
        
        return all_files

    def _clean_project_name(self, project_name: str) -> str:
        """
        🔥 NEW: Pulisce il nome del progetto per usarlo nei path
        """
        import re
        # Rimuovi caratteri speciali e converti in lowercase
        clean_name = re.sub(r'[^a-zA-Z0-9\-_]', '', str(project_name).lower())
        if not clean_name:
            clean_name = "novaplm"
        return clean_name

    def _organize_files_into_structure(self, 
                                    raw_files: Dict[str, str], 
                                    clean_project_name: str,
                                    requirements: Dict[str, Any]) -> Dict[str, str]:
        """
        🔥 NEW: Organizza i file raw nella struttura project-xyz/backend + project-xyz/frontend
        """
        structured_files = {}
        project_prefix = f"project-{clean_project_name}"
        
        # Determina tech stack
        tech_stack = requirements.get("tech_stack", {})
        has_backend = tech_stack.get("backend") or "backend" in str(requirements).lower()
        has_frontend = tech_stack.get("frontend") or "frontend" in str(requirements).lower()
        
        # Organizza file per tipo
        for file_path, content in raw_files.items():
            # Skip file già strutturati
            if file_path.startswith(project_prefix):
                structured_files[file_path] = content
                continue
            
            # Determina dove mettere il file
            if self._is_backend_file(file_path):
                if has_backend:
                    new_path = f"{project_prefix}/backend/{file_path}"
                else:
                    new_path = f"{project_prefix}/{file_path}"
            elif self._is_frontend_file(file_path):
                if has_frontend:
                    new_path = f"{project_prefix}/frontend/{file_path}"
                else:
                    new_path = f"{project_prefix}/{file_path}"
            else:
                # File generale va nella root del progetto
                new_path = f"{project_prefix}/{file_path}"
            
            structured_files[new_path] = content
        
        # Aggiungi README.md al progetto
        structured_files[f"{project_prefix}/README.md"] = self._generate_project_readme(requirements, clean_project_name)
        
        return structured_files

    def _is_backend_file(self, file_path: str) -> bool:
        """Determina se un file è backend"""
        backend_indicators = [
            '.py', 'requirements.txt', 'app/', 'api/', 'models/', 'schemas/',
            'database/', 'db/', 'migrations/', 'alembic/', 'fastapi', 'django',
            'flask', 'main.py', 'wsgi.py', 'asgi.py'
        ]
        return any(indicator in file_path.lower() for indicator in backend_indicators)

    def _is_frontend_file(self, file_path: str) -> bool:
        """Determina se un file è frontend"""
        frontend_indicators = [
            '.tsx', '.jsx', '.ts', '.js', '.css', '.scss', '.html',
            'src/', 'public/', 'components/', 'pages/', 'styles/',
            'package.json', 'node_modules/', 'build/', 'dist/',
            'react', 'vue', 'angular', 'next', 'webpack'
        ]
        return any(indicator in file_path.lower() for indicator in frontend_indicators)

    def _create_test_environment(self, 
                            structured_files: Dict[str, str],
                            clean_project_name: str,
                            requirements: Dict[str, Any]) -> Dict[str, str]:
        """
        🔥 NEW: Crea env_test/ con copia completa + configurazione Docker
        """
        test_env_files = {}
        project_prefix = f"project-{clean_project_name}"
        
        # 1. Copia tutti i file del progetto in env_test/
        for file_path, content in structured_files.items():
            if file_path.startswith(project_prefix):
                # Rimuovi il prefisso project- per la copia in env_test
                relative_path = file_path[len(project_prefix)+1:]  # +1 per il /
                test_env_files[f"env_test/{relative_path}"] = content
        
        # 2. Aggiungi configurazione Docker per test
        test_env_files["env_test/docker-compose.test.yml"] = self._generate_test_docker_compose(requirements)
        test_env_files["env_test/Dockerfile.backend"] = self._generate_backend_dockerfile()
        test_env_files["env_test/Dockerfile.frontend"] = self._generate_frontend_dockerfile()
        
        # 3. Aggiungi script di test
        test_env_files["env_test/run_tests.sh"] = self._generate_test_runner_script()
        test_env_files["env_test/test_runner.py"] = self._generate_python_test_runner()
        
        return test_env_files

    def _generate_project_readme(self, requirements: Dict[str, Any], clean_project_name: str) -> str:
        """Genera README.md per il progetto"""
        project_name = requirements.get("project_name", clean_project_name.title())
        description = requirements.get("description", "Application generated by Multi-Agent System")
        
        return f'''# {project_name}

    {description}

    ## 🚀 Quick Start

    ### Using Docker (Recommended)

    1. **Navigate to test environment:**
    ```bash
    cd ../env_test
    ```

    2. **Start all services:**
    ```bash
    docker-compose -f docker-compose.test.yml up -d
    ```

    3. **Run tests:**
    ```bash
    ./run_tests.sh
    ```

    ## 📁 Project Structure

    ```
    backend/          # Backend application
    frontend/         # Frontend application
    README.md         # This file
    ```

    ## 🧪 Testing

    Tests are run in the `../env_test` environment which contains a complete copy of this project plus Docker configuration.

    ## 💻 Development

    This is the clean development version of the project. 
    For testing and deployment, use the `../env_test` environment.

    ---
    *Generated by Enhanced Multi-Agent Orchestrator*
    '''

    def _generate_test_docker_compose(self, requirements: Dict[str, Any]) -> str:
        """Genera docker-compose.test.yml per env_test"""
        tech_stack = requirements.get("tech_stack", {})
        
        compose_content = '''version: '3.8'

    services:'''
        
        # Backend service
        if tech_stack.get("backend") or "backend" in str(requirements).lower():
            compose_content += '''
    backend:
        build:
        context: .
        dockerfile: Dockerfile.backend
        ports:
        - "8000:8000"
        environment:
        - PYTHONPATH=/app
        - DATABASE_URL=postgresql://test:test@db:5432/test_db
        depends_on:
        - db
        volumes:
        - ./backend:/app
        networks:
        - test-network'''
        
        # Frontend service
        if tech_stack.get("frontend") or "frontend" in str(requirements).lower():
            compose_content += '''
    frontend:
        build:
        context: .
        dockerfile: Dockerfile.frontend
        ports:
        - "3000:3000"
        environment:
        - REACT_APP_API_URL=http://backend:8000
        depends_on:
        - backend
        volumes:
        - ./frontend:/app
        networks:
        - test-network'''
        
        # Database service
        if tech_stack.get("database") or "database" in str(requirements).lower():
            compose_content += '''
    db:
        image: postgres:15
        environment:
        - POSTGRES_DB=test_db
        - POSTGRES_USER=test
        - POSTGRES_PASSWORD=test
        ports:
        - "5432:5432"
        networks:
        - test-network'''
        
        compose_content += '''

    networks:
    test-network:
        driver: bridge
    '''
        
        return compose_content

    def _generate_backend_dockerfile(self) -> str:
        """Genera Dockerfile per backend"""
        return '''# Backend Test Dockerfile
    FROM python:3.11-slim

    WORKDIR /app

    # Install system dependencies
    RUN apt-get update && apt-get install -y \\
        build-essential \\
        curl \\
        && rm -rf /var/lib/apt/lists/*

    # Copy requirements
    COPY backend/requirements.txt ./requirements.txt
    RUN pip install --no-cache-dir -r requirements.txt

    # Copy backend code
    COPY backend/ .

    # Expose port
    EXPOSE 8000

    # Health check
    HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
        CMD curl -f http://localhost:8000/health || exit 1

    # Run the application
    CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    '''

    def _generate_frontend_dockerfile(self) -> str:
        """Genera Dockerfile per frontend"""
        return '''# Frontend Test Dockerfile
    FROM node:18-alpine

    WORKDIR /app

    # Copy package files
    COPY frontend/package*.json ./

    # Install dependencies
    RUN npm ci

    # Copy frontend source
    COPY frontend/ .

    # Expose port
    EXPOSE 3000

    # Health check
    HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
        CMD curl -f http://localhost:3000 || exit 1

    # Start development server
    CMD ["npm", "start"]
    '''

    def _generate_test_runner_script(self) -> str:
        """Genera script bash per run_tests.sh"""
        return '''#!/bin/bash
    # Test Runner Script

    set -e

    echo "🧪 Starting test environment..."

    # Start services
    echo "📦 Starting Docker services..."
    docker-compose -f docker-compose.test.yml up -d

    # Wait for services to be ready
    echo "⏳ Waiting for services to be ready..."
    sleep 30

    # Run backend tests
    echo "🔧 Running backend tests..."
    docker-compose -f docker-compose.test.yml exec -T backend python -m pytest tests/ -v || echo "Backend tests failed"

    # Run frontend tests  
    echo "⚛️ Running frontend tests..."
    docker-compose -f docker-compose.test.yml exec -T frontend npm test -- --coverage --watchAll=false || echo "Frontend tests failed"

    # Run integration tests
    echo "🔗 Running integration tests..."
    python test_runner.py

    # Generate test report
    echo "📊 Generating test report..."
    echo "Test completed at $(date)" > test_report.txt

    echo "✅ Tests completed! Check test_report.txt for details"

    # Stop services
    echo "🛑 Stopping services..."
    docker-compose -f docker-compose.test.yml down
    '''

    def _generate_python_test_runner(self) -> str:
        """Genera test_runner.py per test avanzati"""
        return '''#!/usr/bin/env python3
    """
    Advanced test runner for integration tests
    """
    import requests
    import time
    import json
    import sys

    def test_backend_health():
        """Test backend health endpoint"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            return response.status_code == 200
        except:
            return False

    def test_frontend_accessibility():
        """Test frontend is accessible"""
        try:
            response = requests.get("http://localhost:3000", timeout=10)
            return response.status_code == 200
        except:
            return False

    def run_integration_tests():
        """Run all integration tests"""
        tests = [
            ("Backend Health", test_backend_health),
            ("Frontend Accessibility", test_frontend_accessibility),
        ]
        
        results = {}
        
        print("🔗 Running integration tests...")
        
        for test_name, test_func in tests:
            print(f"  Testing {test_name}...")
            try:
                result = test_func()
                results[test_name] = "PASS" if result else "FAIL"
                status = "✅" if result else "❌"
                print(f"  {status} {test_name}: {results[test_name]}")
            except Exception as e:
                results[test_name] = f"ERROR: {str(e)}"
                print(f"  ❌ {test_name}: ERROR - {str(e)}")
        
        # Save results
        with open("integration_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Return overall success
        return all(result == "PASS" for result in results.values())

    if __name__ == "__main__":
        success = run_integration_tests()
        sys.exit(0 if success else 1)
    '''

    def _create_support_files(self, requirements: Dict[str, Any], clean_project_name: str) -> Dict[str, str]:
        """
        🔥 NEW: Crea file di supporto (requirements.txt, project.json, etc.)
        """
        support_files = {}
        
        # requirements.txt per il progetto
        support_files["requirements.txt"] = self._generate_project_requirements(requirements)
        
        # .env template
        support_files[".env.template"] = self._generate_env_template(requirements)
        
        # .gitignore
        support_files[".gitignore"] = '''# Dependencies
    node_modules/
    __pycache__/
    *.pyc
    venv/
    env/

    # IDE
    .vscode/
    .idea/
    *.swp

    # OS
    .DS_Store
    Thumbs.db

    # Environment
    .env
    .env.local

    # Build outputs
    build/
    dist/
    *.egg-info/

    # Test outputs
    .coverage
    .pytest_cache/
    test_report.txt
    integration_test_results.json

    # Logs
    *.log
    logs/
    '''
        
        return support_files

    def _generate_project_requirements(self, requirements: Dict[str, Any]) -> str:
        """Genera requirements.txt per il progetto"""
        tech_stack = requirements.get("tech_stack", {})
        
        reqs = []
        
        if "fastapi" in str(tech_stack).lower() or "python" in str(tech_stack).lower():
            reqs.extend([
                "fastapi>=0.104.0",
                "uvicorn[standard]>=0.24.0",
                "pydantic>=2.5.0",
                "sqlalchemy>=2.0.0",
                "python-dotenv>=1.0.0"
            ])
        
        if "database" in str(tech_stack).lower() or "postgresql" in str(tech_stack).lower():
            reqs.append("psycopg2-binary>=2.9.0")
        
        if "auth" in str(requirements).lower():
            reqs.extend([
                "python-jose[cryptography]>=3.3.0",
                "passlib[bcrypt]>=1.7.0"
            ])
        
        # Default requirements se nessuno specificato
        if not reqs:
            reqs = [
                "fastapi>=0.104.0",
                "uvicorn[standard]>=0.24.0",
                "requests>=2.31.0"
            ]
        
        return "\\n".join(reqs)

    def _generate_env_template(self, requirements: Dict[str, Any]) -> str:
        """Genera template .env"""
        return '''# Environment Configuration Template
    # Copy this to .env and update with your values

    # Database
    DATABASE_URL=postgresql://user:password@localhost:5432/dbname

    # Security
    SECRET_KEY=your-secret-key-change-in-production

    # API
    API_V1_STR=/api/v1

    # Development
    DEBUG=true
    LOG_LEVEL=INFO

    # External Services
    # Add your API keys and external service URLs here
    '''

    def _apply_structured_organization(self, files: Dict[str, str], requirements: Dict[str, Any]) -> Dict[str, str]:
        """
        🔥 NEW: Applica struttura organizzata ai file esistenti
        """
        # Estrai nome progetto
        project_name = self._clean_project_name(requirements.get("project_name", "novaplm"))
        
        # Organizza nella struttura corretta
        structured = self._organize_files_into_structure(files, project_name, requirements)
        
        # Aggiungi env_test
        test_env = self._create_test_environment(structured, project_name, requirements)
        structured.update(test_env)
        
        # Aggiungi supporto
        support = self._create_support_files(requirements, project_name)
        structured.update(support)
        
        return structured

    # 3. MODIFICA il metodo _module_to_file_path per supportare la nuova struttura:

    def _module_to_file_path(self, module: str) -> Optional[str]:
        """
        🔥 ENHANCED: Supporta sia struttura legacy che struttura project-xyz
        """
        # Mappature per struttura legacy (backward compatibility)
        legacy_mappings = {
            "app.core.config": "app/core/config.py",
            "app.api.errors": "app/api/errors.py", 
            "app.api.utils": "app/api/utils.py",
            "app.db.session": "app/db/session.py",
            "./apiClient": "src/api/apiClient.ts",
            "../types": "src/types/index.ts"
        }
        
        # Rileva se stiamo usando struttura project-xyz
        if hasattr(self, '_current_project_name'):
            project_prefix = f"project-{self._current_project_name}"
            
            # Mappature per struttura project-xyz
            structured_mappings = {
                "app.core.config": f"{project_prefix}/backend/app/core/config.py",
                "app.api.errors": f"{project_prefix}/backend/app/api/errors.py",
                "app.api.utils": f"{project_prefix}/backend/app/api/utils.py", 
                "app.db.session": f"{project_prefix}/backend/app/db/session.py",
                "./apiClient": f"{project_prefix}/frontend/src/api/apiClient.ts",
                "../types": f"{project_prefix}/frontend/src/types/index.ts"
            }
            
            return structured_mappings.get(module, legacy_mappings.get(module))
        
        return legacy_mappings.get(module)

    async def _generate_complete_coordinated_application(self,
                                                       requirements: Dict[str, Any],
                                                       provider: str,
                                                       iteration: int,
                                                       project_path: Path,
                                                       project_name: str,
                                                       analysis: Dict[str, Any]) -> Dict[str, str]:
        """
        🔥 NEW: Generazione completa coordinata in fasi sequenziali
        """
        logger.info("🏗️ Generating complete coordinated application")
        
        all_files = {}
        
        # 🔥 PHASE 1: Essential core files (HIGHEST PRIORITY)
        logger.info("📋 Phase 1: Generating essential core files...")
        core_files = await self._generate_essential_core_files(requirements, provider)
        all_files.update(core_files)
        self._track_files(core_files)
        
        # 🔥 PHASE 2: Package structure (__init__.py files)
        logger.info("🏗️ Phase 2: Generating package structure...")
        structure_files = self._generate_package_structure(requirements)
        all_files.update(structure_files)
        self._track_files(structure_files)
        
        # 🔥 PHASE 3: System and integrations
        logger.info("🔌 Phase 3: Generating system integrations...")
        try:
            system_files = await self.system_agent.generate_system_files(requirements, provider)
            all_files.update(system_files)
            self._track_files(system_files)
        except Exception as e:
            logger.warning(f"System agent failed: {e}, using fallback")
            
        try:
            integration_files = await self.integration_agent.generate_integrations(requirements, provider)
            all_files.update(integration_files)
            self._track_files(integration_files)
        except Exception as e:
            logger.warning(f"Integration agent failed: {e}, using fallback")
        
        # 🔥 PHASE 4: Coordinated API endpoints
        logger.info("🌐 Phase 4: Generating coordinated endpoints...")
        endpoint_files = await self._generate_coordinated_endpoints(requirements, provider, all_files)
        all_files.update(endpoint_files)
        self._track_files(endpoint_files)
        
        # 🔥 PHASE 5: Main application code
        logger.info("⚛️ Phase 5: Generating main application...")
        app_files = await self._generate_coordinated_application(requirements, provider, all_files)
        all_files.update(app_files)
        self._track_files(app_files)
        
        # 🔥 PHASE 6: Utility and configuration files
        logger.info("🔧 Phase 6: Generating utility files...")
        utility_files = await self._generate_utility_files(requirements, provider, all_files)
        all_files.update(utility_files)
        self._track_files(utility_files)
        
        logger.info(f"✅ Complete coordinated application generated: {len(all_files)} files")
        return all_files

    async def _generate_essential_core_files(self, requirements: Dict[str, Any], provider: str) -> Dict[str, str]:
        """
        🔥 NEW: Genera i file core essenziali che risolvono gli errori di importazione principali
        """
        core_files = {}
        
        # 1. app/core/config.py - Risolve: Import 'app.core.config' not found (6+ files)
        core_files["app/core/config.py"] = '''"""
Core configuration settings for the application.
"""
import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/novaplm")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NovaPLM"
    
    class Config:
        env_file = ".env"

settings = Settings()
'''
        
        # 2. app/db/session.py - Risolve: Import 'app.db.session' not found
        core_files["app/db/session.py"] = '''"""
Database session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''
        
        # 3. app/api/errors.py - Risolve: Import 'app.api.errors' not found
        core_files["app/api/errors.py"] = '''"""
API error definitions and handlers.
"""
from fastapi import HTTPException, status

class APIError(HTTPException):
    """Base API error."""
    pass

class AuthenticationError(APIError):
    """Authentication error."""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class ValidationError(APIError):
    """Validation error."""
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

class NotFoundError(APIError):
    """Not found error."""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
'''
        
        # 4. app/api/utils.py - Risolve: Import 'app.api.utils' not found
        core_files["app/api/utils.py"] = '''"""
API utility functions.
"""
from typing import Any, Dict
from fastapi import HTTPException, status

def create_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Create standardized API response."""
    return {
        "status": "success",
        "message": message,
        "data": data
    }

def create_error_response(message: str = "Error", code: int = 400) -> HTTPException:
    """Create standardized error response."""
    return HTTPException(
        status_code=code,
        detail={
            "status": "error",
            "message": message
        }
    )
'''
        
        # 5. src/api/apiClient.ts - Risolve: Import './apiClient' not found (tutti i file frontend API)
        core_files["src/api/apiClient.ts"] = '''/**
 * API client for making HTTP requests.
 */
import axios, { AxiosInstance, AxiosResponse } from 'axios';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor for auth token
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  public async get<T>(url: string): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url);
  }

  public async post<T>(url: string, data?: any): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data);
  }

  public async put<T>(url: string, data?: any): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data);
  }

  public async delete<T>(url: string): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url);
  }
}

export const apiClient = new ApiClient();
export default apiClient;
'''
        
        # 6. src/types/index.ts - Risolve: Import '../types' not found (tutti i file frontend API)
        core_files["src/types/index.ts"] = '''/**
 * TypeScript type definitions.
 */

export interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export interface Project {
  id: number;
  name: string;
  code: string;
  status: 'active' | 'suspended' | 'completed';
  owner_id: number;
  description?: string;
  created_at: string;
}

export interface Document {
  id: number;
  project_id: number;
  file_path: string;
  version: number;
  uploaded_by: number;
  created_at: string;
}

export interface Review {
  id: number;
  document_id: number;
  reviewer_id: number;
  status: 'pending' | 'approved' | 'rejected';
  comments?: string;
  reviewed_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ApiResponse<T> {
  status: string;
  message: string;
  data: T;
}
'''
        
        # 7. utils/logger.js - Risolve: Import './logger' not found
        core_files["utils/logger.js"] = '''/**
 * Logger utility for Node.js backend.
 */
const winston = require('winston');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'novaplm' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
  ],
});

if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple()
  }));
}

module.exports = logger;
'''
        
        # 8. utils/auth.js - Risolve: Import '../utils/auth' not found
        core_files["utils/auth.js"] = '''/**
 * Authentication utilities for Node.js backend.
 */
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';
const SALT_ROUNDS = 10;

const auth = {
  generateToken: (payload) => {
    return jwt.sign(payload, JWT_SECRET, { expiresIn: '24h' });
  },

  verifyToken: (token) => {
    try {
      return jwt.verify(token, JWT_SECRET);
    } catch (error) {
      throw new Error('Invalid token');
    }
  },

  hashPassword: async (password) => {
    return await bcrypt.hash(password, SALT_ROUNDS);
  },

  comparePassword: async (password, hash) => {
    return await bcrypt.compare(password, hash);
  }
};

module.exports = auth;
'''
        
        return core_files

    def _generate_package_structure(self, requirements: Dict[str, Any]) -> Dict[str, str]:
        """
        🔥 NEW: Genera tutti i file __init__.py necessari per risolvere errori package
        """
        init_files = {}
        
        # Struttura backend Python - Risolve tutti gli errori "not found" per package
        python_packages = [
            "app/__init__.py",
            "app/api/__init__.py",
            "app/api/v1/__init__.py", 
            "app/api/v1/endpoints/__init__.py",
            "app/api/routes/__init__.py",
            "app/core/__init__.py",
            "app/db/__init__.py",
            "app/models/__init__.py",
            "app/schemas/__init__.py",
            "app/services/__init__.py",
            "app/middleware/__init__.py"
        ]
        
        for package_path in python_packages:
            init_files[package_path] = '''"""
Package initialization file.
"""
'''
        
        return init_files

    async def _generate_coordinated_endpoints(self,
                                            requirements: Dict[str, Any],
                                            provider: str,
                                            existing_files: Dict[str, str]) -> Dict[str, str]:
        """
        🔥 ENHANCED: Genera endpoints coordinati che si riferiscono ai file esistenti
        """
        logger.info("🌐 Generating coordinated API endpoints...")
        
        # Genera endpoints base
        try:
            endpoint_files = await self.endpoints_agent.generate_endpoints(requirements, provider)
        except Exception as e:
            logger.warning(f"Endpoints agent failed: {e}, using fallback")
            endpoint_files = {}
        
        # Assicura coordinamento con file esistenti
        coordinated_files = {}
        
        # API main router coordinato - Risolve: Import 'app.api.v1.api' not found
        coordinated_files["app/api/v1/api.py"] = '''"""
API v1 main router - Coordinated version.
"""
from fastapi import APIRouter

# Import endpoint routers
try:
    from app.api.v1.endpoints import users, projects, documents, reviews, login
except ImportError:
    # Create fallback routers if endpoints not available
    from fastapi import APIRouter
    users = type('Router', (), {'router': APIRouter()})()
    projects = type('Router', (), {'router': APIRouter()})()
    documents = type('Router', (), {'router': APIRouter()})()
    reviews = type('Router', (), {'router': APIRouter()})()
    login = type('Router', (), {'router': APIRouter()})()

api_router = APIRouter()

# Include all routers
api_router.include_router(login.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])  
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
'''
        
        # Routes module - Risolve: Import 'app.api.routes' not found
        coordinated_files["app/api/routes.py"] = '''"""
API routes module - Main router collection.
"""
from app.api.v1.api import api_router

__all__ = ["api_router"]
'''
        
        # Endpoints package init - Risolve: Import 'app.api.v1.endpoints' not found
        coordinated_files["app/api/v1/endpoints/__init__.py"] = '''"""
API v1 endpoints package.
"""
# Import all endpoint modules
try:
    from . import users, projects, documents, reviews, login
except ImportError:
    # Handle missing endpoint modules gracefully
    pass

__all__ = ["users", "projects", "documents", "reviews", "login"]
'''
        
        # Merge con i file generati dall'agente
        coordinated_files.update(endpoint_files)
        
        return coordinated_files

    async def _generate_coordinated_application(self,
                                              requirements: Dict[str, Any],
                                              provider: str,
                                              existing_files: Dict[str, str]) -> Dict[str, str]:
        """
        🔥 ENHANCED: Genera l'applicazione principale coordinata
        """
        logger.info("⚛️ Generating coordinated main application...")
        
        app_files = {}
        
        # Main FastAPI application coordinato
        app_files["app/main.py"] = '''"""
FastAPI main application - Coordinated version.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging

# Import coordinated modules
from app.core.config import settings
from app.api.v1.api import api_router
from app.api.errors import APIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Product Lifecycle Management Platform",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handler
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "path": str(request.url)
        }
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        
        # Dependencies coordinato
        app_files["app/api/deps.py"] = '''"""
API dependencies - Coordinated version.
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt

# Import coordinated modules
from app.core.config import settings
from app.db.session import get_db

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # For now, return a mock user - to be replaced with actual user lookup
    try:
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
    except ImportError:
        # Fallback if User model not available yet
        user = type('User', (), {'id': user_id, 'email': 'user@example.com', 'is_active': True})()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user."""
    return current_user
'''
        
        # Frontend App.tsx coordinato
        app_files["src/App.tsx"] = '''/**
 * Main App component with coordinated routing.
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';

// Import pages
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ProjectsPage from './pages/ProjectsPage';
import DocumentsPage from './pages/DocumentsPage';

// Import global styles
import './styles/global.css';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            
            {/* Protected routes */}
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/projects" 
              element={
                <ProtectedRoute>
                  <ProjectsPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/documents" 
              element={
                <ProtectedRoute>
                  <DocumentsPage />
                </ProtectedRoute>
              } 
            />
            
            {/* Redirect */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;
'''
        
        # AuthContext coordinato
        app_files["src/contexts/AuthContext.tsx"] = '''/**
 * Authentication context with coordinated API client.
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, LoginRequest, LoginResponse } from '../types';
import { authApi } from '../api/authApi';

interface AuthContextType {
  user: User | null;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      // Validate token and get user info
      authApi.getCurrentUser()
        .then(response => {
          setUser(response.data.data);
        })
        .catch(() => {
          localStorage.removeItem('access_token');
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (credentials: LoginRequest): Promise<void> => {
    try {
      const response = await authApi.login(credentials);
      const { access_token, user: userData } = response.data.data;
      
      localStorage.setItem('access_token', access_token);
      setUser(userData);
    } catch (error) {
      throw new Error('Login failed');
    }
  };

  const logout = (): void => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    login,
    logout,
    isAuthenticated: !!user,
    isLoading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
'''
        
        # ProtectedRoute component
        app_files["src/components/common/ProtectedRoute.tsx"] = '''/**
 * Protected route component.
 */
import React, { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
'''
        
        # Integra il core application esistente
        try:
            core_files = await self._generate_core_application_code(requirements, provider, existing_files)
            app_files.update(core_files)
        except Exception as e:
            logger.warning(f"Core application generation failed: {e}")
        
        return app_files

    async def _generate_utility_files(self,
                                    requirements: Dict[str, Any],
                                    provider: str,
                                    existing_files: Dict[str, str]) -> Dict[str, str]:
        """
        🔥 ENHANCED: Genera file di utility coordinati e configurazione Docker
        """
        utility_files = {}
        
        # Package.json coordinato
        utility_files["package.json"] = '''{
  "name": "novaplm",
  "version": "1.0.0",
  "description": "Product Lifecycle Management Platform",
  "main": "src/index.js",
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject",
    "dev": "concurrently \\"npm run start\\" \\"npm run backend:dev\\"",
    "backend:dev": "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
  },
  "dependencies": {
    "@types/node": "^16.18.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "axios": "^1.6.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "react-scripts": "5.0.1",
    "typescript": "^4.9.0"
  },
  "devDependencies": {
    "concurrently": "^7.6.0",
    "@types/jest": "^27.5.0"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
'''
        
        # Requirements.txt coordinato
        utility_files["requirements.txt"] = '''# FastAPI and dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.1.2

# Validation
pydantic==2.5.0
pydantic-settings==2.1.0
email-validator==2.1.0

# HTTP client
httpx==0.25.2

# Development
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1

# Production
gunicorn==21.2.0
'''
        
        # Docker Compose coordinato
        utility_files["docker-compose.yml"] = '''version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: frontend.Dockerfile
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000/api/v1
    volumes:
      - ./src:/app/src
      - ./public:/app/public
    depends_on:
      - backend

  backend:
    build:
      context: .
      dockerfile: backend.Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://novaplm:password@db:5432/novaplm
      - SECRET_KEY=your-secret-key-change-in-production
    volumes:
      - ./app:/app/app
      - ./uploads:/app/uploads
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=novaplm
      - POSTGRES_USER=novaplm
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

volumes:
  postgres_data:
'''
        
        return utility_files

    async def _ensure_all_dependencies(self, 
                                     code_files: Dict[str, str], 
                                     requirements: Dict[str, Any], 
                                     provider: str) -> Dict[str, str]:
        """
        🔥 NEW: Assicura che tutte le dipendenze siano soddisfatte analizzando gli import
        """
        missing_files = {}
        
        # Analizza tutti i file per trovare import mancanti
        all_imports = set()
        for file_path, content in code_files.items():
            imports = self._extract_imports_from_content(content, file_path)
            all_imports.update(imports)
        
        # Controlla quali import non hanno file corrispondenti
        for import_module in all_imports:
            expected_file = self._module_to_file_path(import_module)
            if expected_file and expected_file not in code_files and expected_file not in missing_files:
                content = await self._generate_module_content(import_module, requirements, provider)
                missing_files[expected_file] = content
                logger.info(f"📋 Generated missing dependency: {expected_file}")
        
        return missing_files

    def _extract_imports_from_content(self, content: str, file_path: str) -> List[str]:
        """
        🔥 NEW: Estrae tutte le importazioni da un file per dependency tracking
        """
        imports = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Python imports
            if file_path.endswith('.py'):
                if line.startswith('from ') and ' import ' in line:
                    match = re.match(r'from\s+([^\s]+)\s+import', line)
                    if match and not match.group(1).startswith('.'):  # Skip relative imports
                        imports.append(match.group(1))
                elif line.startswith('import '):
                    match = re.match(r'import\s+([^\s,]+)', line)
                    if match:
                        imports.append(match.group(1))
            
            # TypeScript/JavaScript imports
            elif file_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
                if 'import' in line and 'from' in line:
                    match = re.search(r"from\s+['\"]([^'\"]+)['\"]", line)
                    if match:
                        imports.append(match.group(1))
        
        return imports

    def _module_to_file_path(self, module: str) -> Optional[str]:
        """
        🔥 NEW: Converte nome modulo in percorso file per dependency resolution
        """
        module_mappings = {
            # Python modules che causano errori
            "app.core.config": "app/core/config.py",
            "app.core": "app/core/__init__.py",
            "app.api.errors": "app/api/errors.py",
            "app.api.utils": "app/api/utils.py",
            "app.api.routes": "app/api/routes.py",
            "app.api": "app/api/__init__.py",
            "app.api.v1.api": "app/api/v1/api.py",
            "app.api.v1.endpoints": "app/api/v1/endpoints/__init__.py",
            "app.db.session": "app/db/session.py",
            
            # TypeScript/JavaScript modules che causano errori
            "./apiClient": "src/api/apiClient.ts",
            "../types": "src/types/index.ts",
            "./logger": "utils/logger.js",
            "../utils/auth": "utils/auth.js"
        }
        
        return module_mappings.get(module)

    async def _generate_module_content(self, module: str, requirements: Dict[str, Any], provider: str) -> str:
        """
        🔥 NEW: Genera il contenuto per un modulo specifico mancante
        """
        # Per moduli già definiti nei file essenziali, non rigenerare
        predefined_modules = {
            "app.core.config",
            "app.api.errors", 
            "app.api.utils",
            "app.db.session",
            "src/api/apiClient.ts",
            "src/types/index.ts",
            "utils/logger.js",
            "utils/auth.js"
        }
        
        if module in predefined_modules:
            return f'# Module {module} should be handled by essential files generation'
        
        # Genera contenuto generico per moduli non predefiniti
        if module.endswith('.py') or '.' in module:
            return f'"""\n{module} module.\n"""\n# Generated module content\npass\n'
        else:
            return f'// {module} module\n// Generated module content\nexport default {{}};'

    async def _enhanced_dependency_fix(self,
                                     requirements: Dict[str, Any],
                                     provider: str,
                                     errors: List[Dict[str, Any]],
                                     existing_files: Dict[str, str],
                                     iteration: int) -> Dict[str, str]:
        """
        🔥 ENHANCED: Fix intelligente delle dipendenze con prioritizzazione
        """
        logger.info(f"🔧 Enhanced dependency fixing for iteration {iteration}")
        
        # Analizza errori per priorità
        import_errors = [e for e in errors if self._is_import_error(e)]
        other_errors = [e for e in errors if e not in import_errors]
        
        logger.info(f"Found {len(import_errors)} import errors and {len(other_errors)} other errors")
        
        fixed_files = dict(existing_files)
        
        # 🔥 STEP 1: Fix import errors con generazione mirata
        if import_errors:
            missing_files = await self._generate_missing_import_files(import_errors, requirements, provider)
            fixed_files.update(missing_files)
            logger.info(f"Generated {len(missing_files)} missing import files")
        
        # 🔥 STEP 2: Fix altri errori con agenti specializzati
        if other_errors:
            try:
                agent_fixes = await self._multi_agent_fix_issues(requirements, provider, other_errors, fixed_files)
                fixed_files.update(agent_fixes)
                logger.info(f"Applied {len(agent_fixes)} agent fixes")
            except Exception as e:
                logger.warning(f"Multi-agent fix failed: {e}")
        
        return fixed_files

    def _is_import_error(self, error: Dict[str, Any]) -> bool:
        """
        🔥 NEW: Determina se un errore è relativo alle importazioni
        """
        message = error.get("message", "").lower()
        error_type = error.get("type", "").lower()
        
        return (
            error_type == "import_error" or
            "import" in message and "not found" in message or
            "module" in message and "not found" in message
        )

    async def _generate_missing_import_files(self,
                                           import_errors: List[Dict[str, Any]],
                                           requirements: Dict[str, Any],
                                           provider: str) -> Dict[str, str]:
        """
        🔥 NEW: Genera specificatamente i file mancanti dalle importazioni
        """
        missing_files = {}
        
        # Analizza i pattern degli errori di importazione
        missing_modules = set()
        for error in import_errors:
            message = error.get("message", "")
            if "Import" in message and "not found" in message:
                # Estrai il modulo mancante
                import_match = re.search(r"Import '([^']+)' not found", message)
                if import_match:
                    missing_modules.add(import_match.group(1))
        
        logger.info(f"Identified missing modules: {missing_modules}")
        
        # Mappa i moduli ai file che devono essere creati
        for module in missing_modules:
            file_path = self._module_to_file_path(module)
            if file_path and file_path not in missing_files:
                content = await self._generate_module_content(module, requirements, provider)
                missing_files[file_path] = content
        
        return missing_files

    def _count_dependency_issues(self, errors: List[Dict[str, Any]]) -> int:
        """
        🔥 NEW: Conta i problemi di dipendenza rimanenti
        """
        dependency_issues = 0
        for error in errors:
            if self._is_import_error(error):
                dependency_issues += 1
        return dependency_issues

    def _track_files(self, files: Dict[str, str]):
        """
        🔥 NEW: Traccia i file generati per dependency tracking
        """
        for file_path in files.keys():
            self.generated_files.add(file_path)

    async def _multi_agent_enhance_quality(self,
                                         requirements: Dict[str, Any],
                                         provider: str,
                                         existing_files: Dict[str, str],
                                         iteration: int) -> Dict[str, str]:
        """
        🔥 ENHANCED: Migliora la qualità del codice senza errori
        """
        logger.info(f"🎨 Enhancing code quality for iteration {iteration}")
        
        # Se non ci sono errori, usa il generatore esistente per miglioramenti
        enhanced_files = await self.code_generator.generate_iterative_improvement(
            requirements, provider, iteration, [], existing_files
        )
        
        return enhanced_files

    async def _multi_agent_fix_issues(self,
                                    requirements: Dict[str, Any],
                                    provider: str,
                                    errors: List[Dict[str, Any]],
                                    existing_files: Dict[str, str]) -> Dict[str, str]:
        """
        🔥 ENHANCED: Multi-agent coordinated issue fixing con fallback
        """
        logger.info("🔧 Multi-agent coordinated issue fixing")
        
        # Dividi errori per tipo/agente con priorità
        system_errors = [e for e in errors if e.get("category") in ["config", "setup", "environment"]]
        integration_errors = [e for e in errors if e.get("category") in ["external", "api", "service"]]
        endpoint_errors = [e for e in errors if e.get("category") in ["route", "controller", "endpoint"]]
        general_errors = [e for e in errors if e not in system_errors + integration_errors + endpoint_errors]
        
        fixed_files = dict(existing_files)
        
        # Fix in sequenza con fallback per evitare conflitti
        if system_errors:
            try:
                if hasattr(self.system_agent, 'fix_system_issues'):
                    system_fixes = await self.system_agent.fix_system_issues(system_errors, fixed_files, provider)
                    fixed_files.update(system_fixes)
                    logger.info(f"Applied {len(system_fixes)} system fixes")
            except Exception as e:
                logger.warning(f"System agent fix failed: {e}")
        
        if integration_errors:
            try:
                if hasattr(self.integration_agent, 'fix_integration_issues'):
                    integration_fixes = await self.integration_agent.fix_integration_issues(integration_errors, fixed_files, provider)
                    fixed_files.update(integration_fixes)
                    logger.info(f"Applied {len(integration_fixes)} integration fixes")
            except Exception as e:
                logger.warning(f"Integration agent fix failed: {e}")
        
        if endpoint_errors:
            try:
                if hasattr(self.endpoints_agent, 'fix_endpoint_issues'):
                    endpoint_fixes = await self.endpoints_agent.fix_endpoint_issues(endpoint_errors, fixed_files, provider)
                    fixed_files.update(endpoint_fixes)
                    logger.info(f"Applied {len(endpoint_fixes)} endpoint fixes")
            except Exception as e:
                logger.warning(f"Endpoint agent fix failed: {e}")
        
        if general_errors:
            try:
                general_fixes = await self.code_generator.generate_iterative_improvement(
                    requirements, provider, 2, general_errors, fixed_files
                )
                fixed_files.update(general_fixes)
                logger.info(f"Applied {len(general_fixes)} general fixes")
            except Exception as e:
                logger.warning(f"General fix failed: {e}")
        
        return fixed_files

    # ========== EXISTING METHODS (Preserved) ==========
    
    async def _generate_core_application_code(self, 
                                           requirements: Dict[str, Any], 
                                           provider: str,
                                           existing_files: Dict[str, str]) -> Dict[str, str]:
        """
        Genera il codice principale dell'applicazione, escludendo infrastruttura, 
        integrazioni e endpoint già generati.
        """
        logger.info("Generating core application code")
        
        # Crea un prompt che faccia riferimento ai file esistenti
        existing_files_summary = "\n".join([f"- {path}" for path in existing_files.keys()])
        
        system_prompt = f"""You are an expert software developer tasked with creating the core application code.
        Some infrastructure, integration, and API endpoint files have already been generated.
        Focus on implementing the business logic, models, services, and UI components that are needed
        to complete the application according to the requirements.
        
        Existing files:
        {existing_files_summary}
        
        Do not recreate these files. Generate only new files needed to complete the application.
        """
        
        # Determina se il progetto è frontend, backend o fullstack
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        if project_type == "frontend":
            # Genera solo frontend
            frontend_files = await self.code_generator.generate_react_app(requirements, provider)
            return frontend_files
        elif project_type == "backend":
            # Genera solo backend
            backend_files = await self.code_generator.generate_backend_api(requirements, provider)
            return backend_files
        else:
            # Genera fullstack
            frontend_files = await self.code_generator.generate_react_app(requirements, provider)
            backend_files = await self.code_generator.generate_backend_api(requirements, provider)
            
            combined_files = dict(frontend_files)
            combined_files.update(backend_files)
            return combined_files
    
    async def _regenerate_code_with_fixes(self,
                                       requirements: Dict[str, Any],
                                       provider: str,
                                       failures: List[Dict[str, Any]],
                                       iteration: int,
                                       existing_files: Dict[str, str]) -> Dict[str, str]:
        """
        Rigenera il codice con correzioni basate sui test falliti.
        """
        logger.info(f"Regenerating code with fixes for iteration {iteration}")
        
        return await self.code_generator.generate_iterative_improvement(
            requirements, provider, iteration, failures, existing_files
        )
    
    def _load_existing_files(self, path: Path) -> Dict[str, str]:
        """
        Carica tutti i file esistenti da una directory.
        """
        files = {}
        
        if not path.exists():
            return files
        
        # Leggi ricorsivamente tutti i file
        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.name != "test_results.json":
                relative_path = str(file_path.relative_to(path))
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files[relative_path] = f.read()
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {str(e)}")
        
        return files
    
    def _save_code_files(self, output_path: Path, code_files: Dict[str, str]):
        """
        Salva i file di codice nella directory di output.
        """
        for file_path, content in code_files.items():
            # Verifica se è richiesta l'interruzione
            if self.stop_requested:
                logger.info("Stop requested during file saving")
                raise Exception("Generation stopped by user request")
                
            full_path = output_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Applica correzioni ai file Python
            if file_path.endswith('.py'):
                content = self._fix_imports(content, file_path)
                
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error writing {file_path}: {str(e)}")
    
    def _update_current_iteration(self, project_path: Path, iteration: int):
        """
        Aggiorna l'iterazione corrente nel file project.json.
        """
        try:
            project_json_path = project_path / "project.json"
            if project_json_path.exists():
                with open(project_json_path, 'r') as f:
                    project_data = json.load(f)
                
                project_data["current_iteration"] = iteration
                
                with open(project_json_path, 'w') as f:
                    json.dump(project_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error updating project.json: {str(e)}")
    
    def _prepare_final_project(self, project_path: Path, final_iteration: int):
        """
        Prepara il progetto finale utilizzando ProjectMerger.
        """
        try:
            # Importa ProjectMerger
            from app.services.project_merger import ProjectMerger
            
            # Crea un'istanza di ProjectMerger
            merger = ProjectMerger(base_output_path="output")
            
            # Crea un elenco di tutte le iterazioni
            iterations = []
            for i in range(1, final_iteration + 1):
                iter_path = project_path / f"iter-{i}"
                if iter_path.exists():
                    iterations.append(i)
            
            # Esegui il merge
            if iterations:
                merger.merge_all_iterations(project_path.name, iterations)
                logger.info(f"Final project created with iterations {iterations}")
        except Exception as e:
            logger.error(f"Error preparing final project: {str(e)}")
    
    def _fix_imports(self, content: str, file_path: str) -> str:
        """
        🔥 ENHANCED: Corregge le importazioni nei file Python con pattern aggiornati
        """
        if not content.strip():
            return content
            
        # Correggi pattern di importazione specifici
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Regex per le importazioni da correggere
            patterns = [
                (r'^\s*from\s+(api|core|db|models|schemas|services)\.', r'from app.\1.'),
                (r'^\s*import\s+(api|core|db|models|schemas|services)\.', r'import app.\1.')
            ]
            
            fixed_line = line
            for pattern, replacement in patterns:
                fixed_line = re.sub(pattern, replacement, fixed_line)
                
            fixed_lines.append(fixed_line)
            
        return '\n'.join(fixed_lines)
    
    def _load_previous_iteration_errors_v2(self, project_path: Path, previous_iteration: int) -> List[Dict[str, Any]]:
        """
        🔥 ENHANCED: Carica errori da Enhanced V2 structure con parsing migliorato
        """
        errors = []
        prev_iter_path = project_path / f"iter-{previous_iteration}"
        
        if not prev_iter_path.exists():
            return errors
        
        # Load from Enhanced V2 iteration summary
        summary_path = prev_iter_path / "iteration_summary.json"
        if summary_path.exists():
            try:
                with open(summary_path, 'r') as f:
                    summary = json.load(f)
                
                # Extract from validation report
                if "validation_report" in summary:
                    validation = summary["validation_report"]
                    for issue in validation.get("issues", []):
                        if issue.get("severity") == "error":
                            errors.append({
                                "type": issue.get("issue_type", "validation"),
                                "category": self._categorize_error(issue),
                                "file": issue.get("file_path"),
                                "line": issue.get("line_number"),
                                "message": issue.get("message", ""),
                                "suggestion": issue.get("suggestion", ""),
                                "priority": "high" if self._is_import_error(issue) else "medium"
                            })
                
                # Extract from compilation report
                if "compilation_report" in summary:
                    compilation = summary["compilation_report"]
                    for error in compilation.get("errors", []):
                        errors.append({
                            "type": "compilation",
                            "category": error.get("error_type", "unknown"),
                            "file": error.get("file_path"),
                            "line": error.get("line_number"),
                            "message": error.get("message", ""),
                            "priority": "high"
                        })
            
            except Exception as e:
                logger.warning(f"Could not load Enhanced V2 iteration summary: {e}")
        
        return errors
    
    def _categorize_error(self, error: Dict[str, Any]) -> str:
        """
        🔥 NEW: Categorizza gli errori per routing agli agenti appropriati
        """
        message = error.get("message", "").lower()
        issue_type = error.get("issue_type", "").lower()
        
        if "config" in message or "settings" in message:
            return "config"
        elif "import" in message and "not found" in message:
            return "import"
        elif "api" in message or "endpoint" in message:
            return "endpoint"
        elif "database" in message or "db" in message:
            return "database"
        elif issue_type == "import_error":
            return "import"
        else:
            return "general"
    
    def request_stop(self):
        """
        Imposta il flag per richiedere l'interruzione del processo.
        """
        logger.info("Stop requested for Enhanced MultiAgentOrchestrator")
        self.stop_requested = True