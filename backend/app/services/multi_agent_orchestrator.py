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
        
        self.stop_requested = False
        logger.info("MultiAgentOrchestrator initialized")
    
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
        Genera un'applicazione completa utilizzando tutti gli agenti specializzati in modo collaborativo.
        """
        stop_file = project_path / "STOP_REQUESTED"
        if stop_file.exists():
            logger.info(f"Stop file found for project {project_path.name}, stopping generation")
            return {"status": "stopped", "reason": "user_requested"}
        
        logger.info(f"Starting multi-agent orchestrated generation with {max_iterations} max iterations")
        
        # Crea metadati del progetto aggiornati
        metadata_path = project_path / "multi_agent_metadata.json"
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        # 1. Analizza i requisiti e crea un piano del progetto
        if "analysis" not in metadata:
            if progress_callback:
                progress_callback(0, 'analyzing_requirements')
            
            analysis = await self.analyze_requirements(requirements, provider)
            metadata["analysis"] = analysis
            
            # Salva i metadati
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info("Requirements analysis completed and saved")
        else:
            analysis = metadata["analysis"]
            logger.info("Using existing requirements analysis")
        
        # 2. Genera file di sistema e configurazione
        if "system_files_generated" not in metadata or not metadata["system_files_generated"]:
            if progress_callback:
                progress_callback(0, 'generating_system_files')
            
            system_files = await self.system_agent.generate_system_files(requirements, provider)
            
            # Salva i file generati
            iter_path = project_path / "iter-1"
            iter_path.mkdir(exist_ok=True)
            self._save_code_files(iter_path, system_files)
            
            # Aggiorna i metadati
            metadata["system_files_generated"] = True
            metadata["system_files_count"] = len(system_files)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Generated {len(system_files)} system files")
        
        # Controlla se è stata richiesta l'interruzione
        if stop_file.exists() or self.stop_requested:
            logger.info("Stop requested, interrupting generation")
            return {
                "status": "stopped",
                "reason": "user_requested",
                "project_id": project_path.name
            }
            
        # 3. Genera integrazioni con servizi esterni se necessario
        if "integration_files_generated" not in metadata or not metadata["integration_files_generated"]:
            if progress_callback:
                progress_callback(0, 'generating_integration_files')
            
            integration_files = await self.integration_agent.generate_integrations(requirements, provider)
            
            # Salva i file generati
            iter_path = project_path / "iter-1"
            iter_path.mkdir(exist_ok=True)
            self._save_code_files(iter_path, integration_files)
            
            # Aggiorna i metadati
            metadata["integration_files_generated"] = True
            metadata["integration_files_count"] = len(integration_files)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Generated {len(integration_files)} integration files")
            
        # Controlla se è stata richiesta l'interruzione
        if stop_file.exists() or self.stop_requested:
            logger.info("Stop requested, interrupting generation")
            return {
                "status": "stopped",
                "reason": "user_requested",
                "project_id": project_path.name
            }
        
        # 4. Genera gli endpoint API se necessario
        if "endpoint_files_generated" not in metadata or not metadata["endpoint_files_generated"]:
            if progress_callback:
                progress_callback(0, 'generating_endpoint_files')
            
            endpoint_files = await self.endpoints_agent.generate_endpoints(requirements, provider)
            
            # Salva i file generati
            iter_path = project_path / "iter-1"
            iter_path.mkdir(exist_ok=True)
            self._save_code_files(iter_path, endpoint_files)
            
            # Aggiorna i metadati
            metadata["endpoint_files_generated"] = True
            metadata["endpoint_files_count"] = len(endpoint_files)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Generated {len(endpoint_files)} endpoint files")
            
        # Controlla se è stata richiesta l'interruzione
        if stop_file.exists() or self.stop_requested:
            logger.info("Stop requested, interrupting generation")
            return {
                "status": "stopped",
                "reason": "user_requested",
                "project_id": project_path.name
            }
        
        # 5. Procedi con le iterazioni di generazione e test
        start_iteration = metadata.get("current_iteration", 0)
        
        for iteration in range(start_iteration, max_iterations):
            iteration_number = iteration + 1  # 1-based per display
            logger.info(f"Starting iteration {iteration_number}/{max_iterations}")
            
            # Controlla per stop request
            if stop_file.exists() or self.stop_requested:
                logger.info("Stop requested, interrupting generation")
                return {
                    "status": "stopped",
                    "reason": "user_requested",
                    "iteration": iteration,
                    "project_id": project_path.name
                }
            
            # Aggiorna i metadati
            metadata["current_iteration"] = iteration
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Aggiorna l'iterazione corrente in project.json
            self._update_current_iteration(project_path, iteration_number)
            
            # Crea la directory dell'iterazione
            iter_path = project_path / f"iter-{iteration_number}"
            iter_path.mkdir(exist_ok=True)
            
            # Genera il codice per questa iterazione
            if progress_callback:
                progress_callback(iteration_number, 'generating_code')
            
            try:
                # Per la prima iterazione o se richiesto, genera il codice completo
                if iteration == 0:
                    # Carica i file già generati (sistema, integrazioni, endpoint)
                    existing_files = self._load_existing_files(project_path / "iter-1")
                    
                    # Genera codice aggiuntivo
                    additional_code = await self._generate_core_application_code(
                        requirements, provider, existing_files
                    )
                    
                    # Unisci con i file esistenti
                    all_files = dict(existing_files)
                    all_files.update(additional_code)
                    
                    # Salva tutti i file
                    self._save_code_files(iter_path, all_files)
                else:
                    # Carica i file dell'iterazione precedente
                    prev_iter_path = project_path / f"iter-{iteration}"
                    prev_files = self._load_existing_files(prev_iter_path)
                    
                    # Controlla se ci sono risultati di test dall'iterazione precedente
                    test_results_path = prev_iter_path / "test_results.json"
                    
                    if test_results_path.exists():
                        # Leggi i risultati dei test
                        with open(test_results_path, 'r') as f:
                            prev_results = json.load(f)
                        
                        # Analizza i fallimenti
                        failures = self.test_agent.test_runner.analyze_test_failures(prev_results)
                        
                        # Genera codice migliorato
                        improved_code = await self._regenerate_code_with_fixes(
                            requirements, provider, failures, iteration_number, prev_files
                        )
                        
                        # Salva il codice
                        self._save_code_files(iter_path, improved_code)
                    else:
                        # Se non ci sono risultati di test, copia i file dall'iterazione precedente
                        import shutil
                        for file_path in prev_iter_path.glob("**/*"):
                            if file_path.is_file() and file_path.name != "test_results.json":
                                target_path = iter_path / file_path.relative_to(prev_iter_path)
                                target_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(file_path, target_path)
                
                # Genera test
                if progress_callback:
                    progress_callback(iteration_number, 'generating_tests')
                
                # Carica i file attuali
                current_files = self._load_existing_files(iter_path)
                
                # Genera test per questi file
                test_files = await self.test_agent.test_generator.generate_tests(
                    requirements, current_files, provider
                )
                
                # Esegui i test
                if progress_callback:
                    progress_callback(iteration_number, 'running_tests')
                
                test_results = await self.test_agent.test_runner.run_tests(iter_path, test_files)
                
                # Salva i risultati dei test
                with open(iter_path / "test_results.json", 'w') as f:
                    json.dump(test_results, f, indent=2)
                
                # Controlla se tutti i test passano
                if test_results.get("success", False):
                    logger.info(f"All tests passed in iteration {iteration_number}")
                    
                    # Prepara il progetto finale
                    self._prepare_final_project(project_path, iteration_number)
                    
                    return {
                        "status": "completed",
                        "iteration": iteration_number,
                        "project_id": project_path.name,
                        "output_path": str(iter_path),
                        "analysis": analysis
                    }
                
            except Exception as e:
                logger.error(f"Error in iteration {iteration_number}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                
                if iteration_number == max_iterations:
                    raise
        
        # Se abbiamo raggiunto questo punto, significa che abbiamo completato tutte le iterazioni
        # ma i test non hanno avuto successo
        logger.warning(f"Max iterations ({max_iterations}) reached without success")
        
        # Prepara comunque il progetto finale
        self._prepare_final_project(project_path, max_iterations)
        
        return {
            "status": "completed_with_warnings",
            "message": "Max iterations reached without passing all tests",
            "iteration": max_iterations,
            "project_id": project_path.name,
            "output_path": str(project_path / f"iter-{max_iterations}"),
            "analysis": analysis
        }
    
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