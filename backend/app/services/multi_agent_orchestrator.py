# backend/app/services/multi_agent_orchestrator.py
import json
import logging
import re
import asyncio
from typing import Dict, Any, List, Optional, Callable
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
    Orchestratore avanzato che coordina diversi agenti specializzati
    per generare un'applicazione completa in modo collaborativo.
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
        logger.info("MultiAgentOrchestrator initialized with Enhanced V2 support")
    
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
        🔥 AGGIORNATO: Usa struttura Enhanced V2
        """
        stop_file = project_path / "STOP_REQUESTED"
        if stop_file.exists():
            logger.info(f"Stop file found for project {project_path.name}, stopping generation")
            return {"status": "stopped", "reason": "user_requested"}
        
        logger.info(f"Starting enhanced multi-agent generation with {max_iterations} max iterations")
        
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
            "generation_mode": "multi_agent_enhanced_v2"
        }
        
        # 🔥 FASE 1: Analisi requirements con sistema V2
        if progress_callback:
            progress_callback(0, 'analyzing_requirements_v2')
        
        analysis = await self.analyze_requirements(requirements, provider)
        
        # Main iteration loop con Enhanced V2
        for iteration in range(1, max_iterations + 1):
            logger.info(f"Starting enhanced iteration {iteration} for project {project_name}")
            
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
                
                # 🔥 STEP 2: Generate code with multi-agent coordination
                if progress_callback:
                    progress_callback(iteration, 'generating_multi_agent_code')
                
                code_files = await self._generate_multi_agent_code_v2(
                    requirements, provider, iteration, project_path, project_name, analysis
                )
                
                # 🔥 STEP 3: Save in Enhanced V2 structure
                files_generated, files_modified = self.iteration_manager.save_generated_code(
                    iteration_structure, code_files
                )
                
                logger.info(f"Multi-Agent Iteration {iteration}: Generated {files_generated} files, modified {files_modified}")
                
                # 🔥 STEP 4: Enhanced V2 validation and testing
                if progress_callback:
                    progress_callback(iteration, 'enhanced_v2_validation')
                
                iteration_result = await self.enhanced_test_agent.process_iteration_complete(
                    iteration_structure, project_name, iteration, requirements, code_files, provider
                )
                
                # Update project state
                project_state["iterations_completed"] = iteration
                project_state["remaining_issues"] = iteration_result.get("errors_for_fixing", [])
                
                # Check success
                if iteration_result["success"]:
                    logger.info(f"Multi-Agent iteration {iteration} completed successfully!")
                    project_state["final_success"] = True
                    
                    return {
                        "status": "completed",
                        "iteration": iteration,
                        "project_id": project_path.name,
                        "project_name": project_name,
                        "output_path": str(iteration_structure.iteration_path),
                        "project_state": project_state,
                        "final_result": iteration_result,
                        "generation_strategy": "multi_agent_enhanced_v2"
                    }
                
                # Continue to next iteration
                logger.info(f"Multi-Agent iteration {iteration} had issues, continuing...")
                
            except Exception as e:
                logger.error(f"Error in multi-agent iteration {iteration}: {str(e)}")
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
            "generation_strategy": "multi_agent_enhanced_v2"
        }
    
    async def _generate_multi_agent_code_v2(self,
                                        requirements: Dict[str, Any],
                                        provider: str,
                                        iteration: int,
                                        project_path: Path,
                                        project_name: str,
                                        analysis: Dict[str, Any]) -> Dict[str, str]:
        """
        🔥 NUOVO: Genera codice con coordinazione multi-agent in Enhanced V2
        """
        logger.info(f"Generating multi-agent coordinated code for iteration {iteration}")
        
        if iteration == 1:
            # Prima iterazione: coordinazione completa
            all_files = {}
            
            # 1. Sistema e configurazione
            system_files = await self.system_agent.generate_system_files(requirements, provider)
            all_files.update(system_files)
            
            # 2. Integrazioni
            integration_files = await self.integration_agent.generate_integrations(requirements, provider)
            all_files.update(integration_files)
            
            # 3. API Endpoints
            endpoint_files = await self.endpoints_agent.generate_endpoints(requirements, provider)
            all_files.update(endpoint_files)
            
            # 4. Core application
            core_files = await self._generate_core_application_code(requirements, provider, all_files)
            all_files.update(core_files)
            
            return all_files
        
        else:
            # Iterazioni successive: carica e migliora
            previous_files = self.iteration_manager.load_previous_iteration_files(
                project_path, project_name, iteration
            )
            
            # Carica errori precedenti
            previous_errors = self._load_previous_iteration_errors_v2(project_path, iteration - 1)
            
            if previous_errors:
                # Multi-agent fixing
                improved_files = await self._multi_agent_fix_issues(
                    requirements, provider, previous_errors, previous_files
                )
                return improved_files
            else:
                # Multi-agent enhancement
                enhanced_files = await self._multi_agent_enhance_quality(
                    requirements, provider, previous_files, iteration
                )
                return enhanced_files

    async def _multi_agent_fix_issues(self,
                                    requirements: Dict[str, Any],
                                    provider: str,
                                    errors: List[Dict[str, Any]],
                                    existing_files: Dict[str, str]) -> Dict[str, str]:
        """
        🔥 NUOVO: Multi-agent coordinated issue fixing
        """
        logger.info("Multi-agent coordinated issue fixing")
        
        # Dividi errori per tipo/agente
        system_errors = [e for e in errors if e.get("category") in ["config", "setup", "environment"]]
        integration_errors = [e for e in errors if e.get("category") in ["external", "api", "service"]]
        endpoint_errors = [e for e in errors if e.get("category") in ["route", "controller", "endpoint"]]
        general_errors = [e for e in errors if e not in system_errors + integration_errors + endpoint_errors]
        
        fixed_files = dict(existing_files)
        
        # Fix in parallelo con agenti specializzati
        tasks = []
        
        if system_errors:
            tasks.append(self.system_agent.fix_system_issues(system_errors, fixed_files, provider))
        
        if integration_errors:
            tasks.append(self.integration_agent.fix_integration_issues(integration_errors, fixed_files, provider))
        
        if endpoint_errors:
            tasks.append(self.endpoints_agent.fix_endpoint_issues(endpoint_errors, fixed_files, provider))
        
        if general_errors:
            tasks.append(self.code_generator.generate_iterative_improvement(
                requirements, provider, 2, general_errors, fixed_files
            ))
        
        # Esegui tutti i fix in parallelo
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Merge results
            for result in results:
                if isinstance(result, dict):
                    fixed_files.update(result)
        
        return fixed_files

    def _load_previous_iteration_errors_v2(self, project_path: Path, previous_iteration: int) -> List[Dict[str, Any]]:
        """
        🔥 NUOVO: Carica errori da Enhanced V2 structure
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
                                "type": "validation",
                                "category": issue.get("issue_type", "unknown"),
                                "file": issue.get("file_path"),
                                "line": issue.get("line_number"),
                                "message": issue.get("message", ""),
                                "suggestion": issue.get("suggestion", ""),
                                "priority": "high"
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
        Corregge le importazioni nei file Python.
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
    
    def request_stop(self):
        """
        Imposta il flag per richiedere l'interruzione del processo.
        """
        logger.info("Stop requested for MultiAgentOrchestrator")
        self.stop_requested = True