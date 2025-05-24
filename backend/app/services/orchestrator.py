# backend/app/services/orchestrator.py
import json
import logging
import re
import asyncio
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from app.services.llm_service import LLMService
from app.services.code_generator import CodeGenerator
from app.services.test_agent import TestAgent

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.code_generator = CodeGenerator(llm_service)
        self.test_agent = TestAgent(llm_service)
        self.stop_requested = False  # Aggiungi questa variabile per tenere traccia delle richieste di interruzione
        logger.info("OrchestratorAgent initialized")
    
    async def generate_application_with_orchestration(self, 
                                                    requirements: Dict[str, Any],
                                                    provider: str,
                                                    max_iterations: int,
                                                    project_path: Path,
                                                    progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Orchestrates the complete application generation with testing cycles
        Maintains all the existing logic from celery_app.py
        """
        
        stop_file = project_path / "STOP_REQUESTED"
        if stop_file.exists():
            logger.info(f"Stop file found for project {project_path.name}, stopping generation")
            return {
                "status": "stopped",
                "reason": "user_requested",
                "iteration": iteration - 1,
                "project_id": project_path.name
            }
        logger.info(f"Starting orchestrated generation with {max_iterations} max iterations")
        
        # Cleanup any existing empty iteration directories (dalla logica originale)
        self._cleanup_empty_directories(project_path, max_iterations)
        
        for iteration in range(1, max_iterations + 1):
            logger.info(f"Starting iteration {iteration} for project {project_path.name}")
            
            try:
                # Update current iteration in project.json (dalla logica originale)
                self._update_current_iteration(project_path, iteration)
                
                # Progress callback per Celery
                if progress_callback:
                    progress_callback(iteration, 'generating_code')
                    
                # Controlla se è stata richiesta l'interruzione
                if self.stop_requested:
                    logger.info("Stop requested, interrupting generation")
                    return {
                        "status": "stopped",
                        "reason": "user_requested",
                        "iteration": iteration - 1,
                        "project_id": project_path.name
                    }
                
                # Create iteration directory
                iter_path = project_path / f"iter-{iteration}"
                iter_path.mkdir(exist_ok=True)
                
                # Generate code (manteniamo la stessa logica)
                if iteration == 1:
                    code_files = await self._generate_initial_code(
                        requirements, provider, iter_path
                    )
                else:
                    # Verifica se l'iterazione precedente esiste (dalla logica originale)
                    prev_iter_path = project_path / f"iter-{iteration - 1}"
                    test_results_path = prev_iter_path / "test_results.json"
                    
                    if not test_results_path.exists():
                        logging.warning(f"Test results file not found for iteration {iteration-1}, starting fresh")
                        code_files = await self._generate_initial_code(
                            requirements, provider, iter_path
                        )
                    else:
                        # Procedi normalmente con fix dai test precedenti
                        with open(test_results_path, 'r') as f:
                            prev_results = json.load(f)
                        
                        # Usa il test_agent per analizzare i fallimenti
                        failures = self.test_agent.test_runner.analyze_test_failures(prev_results)
                        
                        code_files = await self._regenerate_code_with_fixes(
                            requirements, provider, failures, iteration, iter_path
                        )
                
                # Controlla di nuovo se è stata richiesta l'interruzione
                if self.stop_requested:
                    logger.info("Stop requested after code generation, interrupting")
                    return {
                        "status": "stopped",
                        "reason": "user_requested",
                        "iteration": iteration - 1,
                        "project_id": project_path.name,
                        "partial_iteration": iteration
                    }
                
                # Save generated code (stessa logica di save_code_files)
                self._save_code_files(iter_path, code_files)
                
                # Generate tests
                if progress_callback:
                    progress_callback(iteration, 'generating_tests')
                
                # Controlla di nuovo se è stata richiesta l'interruzione
                if self.stop_requested:
                    logger.info("Stop requested before test generation, interrupting")
                    return {
                        "status": "stopped",
                        "reason": "user_requested",
                        "iteration": iteration - 1,
                        "project_id": project_path.name,
                        "partial_iteration": iteration
                    }
                
                # Usa il test_agent invece di chiamare direttamente test_generator
                test_files = await self.test_agent.test_generator.generate_tests(
                    requirements, code_files, provider
                )
                
                # Controlla di nuovo se è stata richiesta l'interruzione
                if self.stop_requested:
                    logger.info("Stop requested after test generation, interrupting")
                    return {
                        "status": "stopped",
                        "reason": "user_requested",
                        "iteration": iteration - 1,
                        "project_id": project_path.name,
                        "partial_iteration": iteration
                    }
                
                # Run tests  
                if progress_callback:
                    progress_callback(iteration, 'running_tests')
                
                test_results = await self.test_agent.test_runner.run_tests(iter_path, test_files)
                
                # Save test results (stessa logica)
                with open(iter_path / "test_results.json", 'w') as f:
                    json.dump(test_results, f, indent=2)
                
                # Check if all tests pass (stessa logica)
                if test_results.get("success", False):
                    return {
                        "status": "completed",
                        "iteration": iteration,
                        "project_id": project_path.name,
                        "output_path": str(iter_path)
                    }
                
                # Controlla di nuovo se è stata richiesta l'interruzione dopo i test
                if self.stop_requested:
                    logger.info("Stop requested after tests, interrupting")
                    return {
                        "status": "stopped",
                        "reason": "user_requested",
                        "iteration": iteration,
                        "project_id": project_path.name
                    }
                
                # Se i test falliscono, continua con l'iterazione successiva
                
            except Exception as e:
                logging.error(f"Error in iteration {iteration}: {str(e)}")
                # Se c'è un errore nell'iterazione, pulisci la directory se è vuota
                if iter_path.exists() and not any(iter_path.iterdir()):
                    import shutil
                    shutil.rmtree(iter_path)
                    logging.info(f"Removed empty directory after error: {iter_path}")
                
                # Se è l'ultima iterazione, propaga l'errore
                if iteration == max_iterations:
                    raise
        
        # Max iterations reached without success (stessa logica)
        logger.warning(f"Max iterations ({max_iterations}) reached without success")
        return {
            "status": "failed",
            "reason": "max_iterations_reached",
            "iterations": max_iterations,
            "project_id": project_path.name
        }
    
    def request_stop(self):
        """
        Imposta la richiesta di interruzione.
        Questo metodo può essere chiamato da altri thread o processi
        per richiedere l'interruzione del processo di generazione.
        """
        logger.info("Stop requested for orchestrator")
        self.stop_requested = True
    
    def _cleanup_empty_directories(self, project_path: Path, max_iterations: int):
        """Cleanup empty iteration directories from previous runs"""
        for i in range(1, max_iterations + 1):
            cleanup_path = project_path / f"iter-{i}"
            if cleanup_path.exists() and not any(cleanup_path.iterdir()):
                import shutil
                shutil.rmtree(cleanup_path)
                logging.info(f"Removed empty directory: {cleanup_path}")
    
    def _update_current_iteration(self, project_path: Path, iteration: int):
        """Update current iteration in project.json (dalla logica originale)"""
        with open(project_path / "project.json", 'r') as f:
            project_data = json.load(f)
        
        project_data["current_iteration"] = iteration
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
    
    async def _generate_initial_code(self, requirements: Dict[str, Any], provider: str, output_path: Path) -> Dict[str, str]:
        """Generate initial code based on requirements (dalla logica originale)"""
        # Controlla se è stata richiesta l'interruzione
        if self.stop_requested:
            logger.info("Stop requested during code generation")
            raise Exception("Generation stopped by user request")
            
        code_files = {}
        
        # Generate frontend code if specified
        if "frontend" in requirements:
            frontend_files = await self.code_generator.generate_react_app(requirements, provider)
            code_files.update(frontend_files)
            
            # Controlla di nuovo se è stata richiesta l'interruzione
            if self.stop_requested:
                logger.info("Stop requested after frontend generation")
                raise Exception("Generation stopped by user request")
        
        # Generate backend code if specified
        if "backend" in requirements:
            backend_files = await self.code_generator.generate_backend_api(requirements, provider)
            code_files.update(backend_files)
            
            # Controlla di nuovo se è stata richiesta l'interruzione
            if self.stop_requested:
                logger.info("Stop requested after backend generation")
                raise Exception("Generation stopped by user request")
        
        return code_files
    
    async def _regenerate_code_with_fixes(self, requirements: Dict[str, Any], provider: str, 
                                        failures: List[Dict[str, Any]], iteration: int, 
                                        output_path: Path) -> Dict[str, str]:
        """Regenerate code with fixes for test failures (dalla logica originale)"""
        # Controlla se è stata richiesta l'interruzione
        if self.stop_requested:
            logger.info("Stop requested during code regeneration")
            raise Exception("Generation stopped by user request")

        # TEMPORANEO: per ora rigenera sempre tutto invece di fare solo le correzioni
        logger.warning("TEMPORARY FIX: Regenerating all code instead of just fixes")
        
        # Usa lo stesso codice della generazione iniziale
        return await self._generate_initial_code(requirements, provider, output_path)
        # Commenta questa parte per ora:
        # code_files = await self.code_generator.generate_code(
        #     requirements=requirements,
        #     provider=provider,
        #     iteration=iteration,
        #     previous_errors=failures
        # )
        # return code_files
    
    def _save_code_files(self, output_path: Path, code_files: Dict[str, str]):
        """Save generated code files to disk with import path correction (dalla logica originale)"""
        # Controlla se è stata richiesta l'interruzione
        if self.stop_requested:
            logger.info("Stop requested during file saving")
            raise Exception("Generation stopped by user request")
            
        # Funzione per correggere le importazioni in un file Python (stessa logica)
        def fix_imports(content: str) -> str:
            if not content.strip() or not content.endswith('.py'):
                return content
                
            # Correggi le importazioni
            lines = content.split('\n')
            fixed_lines = []
            
            for line in lines:
                # Correggi importazioni come "from api." a "from app.api."
                if re.match(r'^\s*from\s+(api|core|db|models|schemas|services)\.', line):
                    line = re.sub(r'from\s+(api|core|db|models|schemas|services)\.', r'from app.\1.', line)
                    
                # Correggi importazioni come "import api." a "import app.api."
                if re.match(r'^\s*import\s+(api|core|db|models|schemas|services)\.', line):
                    line = re.sub(r'import\s+(api|core|db|models|schemas|services)\.', r'import app.\1.', line)
                    
                fixed_lines.append(line)
                
            return '\n'.join(fixed_lines)
        
        # Salva i file e correggi le importazioni nei file Python
        for file_path, content in code_files.items():
            # Controlla periodicamente se è stata richiesta l'interruzione
            if self.stop_requested:
                logger.info("Stop requested during individual file saving")
                raise Exception("Generation stopped by user request")
                
            full_path = output_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if file_path.endswith('.py'):
                content = fix_imports(content)
                
            full_path.write_text(content, encoding='utf-8')