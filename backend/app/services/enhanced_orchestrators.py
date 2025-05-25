# backend/app/services/enhanced_orchestrators.py
"""
🎯 ORCHESTRATORI AGGIORNATI per usare la nuova struttura pulita dei progetti

Questo modulo contiene le versioni aggiornate degli orchestratori che utilizzano
ProjectStructureManager invece della vecchia logica iter-1, iter-2, etc.
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from app.services.llm_service import LLMService
from app.services.code_generator import CodeGenerator
from app.services.enhanced_test_agent import EnhancedTestAgent
from app.services.project_structure_manager import ProjectStructureManager, ProjectStructure
from app.services.code_validator import ValidationReport
from app.services.compilation_checker import CompilationResult

logger = logging.getLogger(__name__)

class CleanStructureOrchestrator:
    """
    🎯 NUOVO: Orchestratore che usa la struttura pulita dei progetti
    
    Sostituisce i vecchi orchestratori con una gestione intelligente:
    - Codice sempre pulito in ${project_name}/
    - Test isolati in .tests/
    - Report strutturati in .reports/
    - Nessuna confusione con iter-1, iter-2, etc.
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.code_generator = CodeGenerator(llm_service)
        self.enhanced_test_agent = EnhancedTestAgent(llm_service)
        self.structure_manager = ProjectStructureManager()
        self.stop_requested = False
        logger.info("CleanStructureOrchestrator initialized with clean project structure")
    
    async def generate_application_with_clean_structure(self, 
                                                      requirements: Dict[str, Any],
                                                      provider: str,
                                                      max_iterations: int,
                                                      project_path: Path,
                                                      progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        🎯 METODO PRINCIPALE: Genera l'applicazione con struttura pulita
        
        Args:
            requirements: Requisiti del progetto
            provider: Provider LLM da usare
            max_iterations: Numero massimo di iterazioni
            project_path: Path del progetto (es: output/project-abc123)
            progress_callback: Callback per aggiornamenti di stato
            
        Returns:
            Dict con risultati della generazione
        """
        # Extract project info
        project_id = project_path.name
        project_name = requirements.get("project", {}).get("name", f"app_{project_id[:8]}")
        
        logger.info(f"🎯 Starting clean generation for {project_id}/{project_name}")
        
        # Check for stop request
        stop_file = project_path / "STOP_REQUESTED"
        if stop_file.exists():
            logger.info("Stop file found, aborting generation")
            return {"status": "stopped", "reason": "user_requested"}
        
        # Create clean project structure
        structure = self.structure_manager.create_project_structure(project_id, project_name)
        
        # Save initial project metadata
        project_metadata = {
            "project_id": project_id,
            "project_name": project_name,
            "requirements": requirements,
            "generation_mode": "clean_structure",
            "provider": provider,
            "max_iterations": max_iterations,
            "status": "processing",
            "created_at": self._get_current_timestamp()
        }
        self.structure_manager.save_project_metadata(structure, project_metadata)
        
        # Track overall progress
        overall_stats = {
            "iterations_completed": 0,
            "total_errors_fixed": 0,
            "current_errors": 0,
            "compilation_successes": 0,
            "test_successes": 0
        }
        
        # Main iteration loop
        for iteration in range(1, max_iterations + 1):
            logger.info(f"🔄 Starting iteration {iteration}/{max_iterations}")
            
            # Check for stop request
            if stop_file.exists() or self.stop_requested:
                logger.info("Stop requested, interrupting generation")
                return self._create_stop_result(structure, iteration - 1, overall_stats)
            
            # Update progress
            if progress_callback:
                progress_callback(iteration, 'generating_code')
            
            try:
                # Generate code for this iteration
                code_files = await self._generate_code_for_iteration(
                    requirements, provider, iteration, structure
                )
                
                if not code_files:
                    logger.warning(f"No code generated in iteration {iteration}")
                    continue
                
                # Save code to clean structure
                files_created, files_modified = self.structure_manager.save_source_code(
                    structure, code_files, iteration
                )
                
                logger.info(f"💾 Saved code: {files_created} created, {files_modified} modified")
                
                # Update progress
                if progress_callback:
                    progress_callback(iteration, 'validating_and_testing')
                
                # Process iteration (validation, compilation, testing)
                iteration_result = await self._process_iteration_complete(
                    structure, iteration, requirements, provider
                )
                
                # Save iteration report
                self.structure_manager.save_iteration_report(
                    structure, iteration, iteration_result
                )
                
                # Update overall stats
                overall_stats["iterations_completed"] = iteration
                overall_stats["current_errors"] = len(iteration_result.get("errors_for_fixing", []))
                
                if iteration_result.get("compilation_success", False):
                    overall_stats["compilation_successes"] += 1
                
                if iteration_result.get("test_success", False):
                    overall_stats["test_successes"] += 1
                
                # Check if iteration was successful
                if iteration_result.get("success", False):
                    logger.info(f"🎉 Iteration {iteration} completed successfully!")
                    
                    # Create final report
                    final_data = {
                        "status": "completed",
                        "final_iteration": iteration,
                        "total_iterations": iteration,
                        "overall_stats": overall_stats,
                        "final_result": iteration_result
                    }
                    
                    self.structure_manager.create_final_report(structure, final_data)
                    
                    return self._create_success_result(structure, iteration, overall_stats, iteration_result)
                
                # Continue to next iteration if not successful
                logger.info(f"⚠️ Iteration {iteration} had issues, continuing...")
                
                # Update errors fixed counter
                if iteration > 1:
                    prev_errors = overall_stats.get("prev_errors", 0)
                    current_errors = overall_stats["current_errors"]
                    if current_errors < prev_errors:
                        overall_stats["total_errors_fixed"] += (prev_errors - current_errors)
                
                overall_stats["prev_errors"] = overall_stats["current_errors"]
                
            except Exception as e:
                logger.error(f"❌ Error in iteration {iteration}: {str(e)}")
                
                # Log error but continue if not final iteration
                if iteration == max_iterations:
                    return self._create_error_result(structure, iteration, str(e), overall_stats)
                
                logger.info("Attempting to continue after error...")
                continue
        
        # Max iterations reached
        logger.warning(f"⏰ Max iterations ({max_iterations}) reached")
        
        final_data = {
            "status": "completed_with_issues",
            "final_iteration": max_iterations,
            "total_iterations": max_iterations,
            "overall_stats": overall_stats,
            "message": "Reached maximum iterations without full success"
        }
        
        self.structure_manager.create_final_report(structure, final_data)
        
        return self._create_max_iterations_result(structure, max_iterations, overall_stats)
    
    async def _generate_code_for_iteration(self, 
                                         requirements: Dict[str, Any],
                                         provider: str,
                                         iteration: int,
                                         structure: ProjectStructure) -> Dict[str, str]:
        """
        🔄 Genera il codice per una specifica iterazione
        """
        logger.info(f"Generating code for iteration {iteration}")
        
        if iteration == 1:
            # First iteration: generate from requirements
            return await self._generate_initial_code(requirements, provider)
        else:
            # Subsequent iterations: load current code and improve
            current_files = self.structure_manager.get_current_source_files(structure)
            previous_errors = self._load_previous_errors(structure, iteration - 1)
            
            if previous_errors:
                logger.info(f"Found {len(previous_errors)} errors from previous iteration")
                return await self._generate_code_with_fixes(
                    requirements, provider, previous_errors, current_files, iteration
                )
            else:
                logger.info("No previous errors, generating improved code")
                return await self._generate_improved_code(
                    requirements, provider, current_files, iteration
                )
    
    async def _generate_initial_code(self, 
                                   requirements: Dict[str, Any], 
                                   provider: str) -> Dict[str, str]:
        """🆕 Genera il codice iniziale per la prima iterazione"""
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        if project_type == "frontend":
            return await self.code_generator.generate_react_app(requirements, provider)
        elif project_type == "backend":
            return await self.code_generator.generate_backend_api(requirements, provider)
        else:
            # Fullstack or mixed
            return await self.code_generator.generate_code(requirements, provider, 1)
    
    async def _generate_code_with_fixes(self,
                                      requirements: Dict[str, Any],
                                      provider: str,
                                      errors: List[Dict[str, Any]],
                                      existing_files: Dict[str, str],
                                      iteration: int) -> Dict[str, str]:
        """🔧 Genera codice con correzioni per errori specifici"""
        logger.info(f"Generating code with fixes for {len(errors)} errors")
        
        # Use enhanced code generator for fixing
        fixed_files = await self.code_generator.generate_code(
            requirements, provider, iteration, errors, existing_files
        )
        
        # Merge with existing files (only update what was fixed)
        merged_files = dict(existing_files) if existing_files else {}
        merged_files.update(fixed_files)
        
        return merged_files
    
    async def _generate_improved_code(self,
                                    requirements: Dict[str, Any],
                                    provider: str,
                                    existing_files: Dict[str, str],
                                    iteration: int) -> Dict[str, str]:
        """✨ Genera codice migliorato quando non ci sono errori specifici"""
        logger.info(f"Generating improved code for iteration {iteration}")
        
        # Use existing code generator with iteration context
        return await self.code_generator.generate_code(
            requirements, provider, iteration, existing_files=existing_files
        )
    
    async def _process_iteration_complete(self,
                                        structure: ProjectStructure,
                                        iteration: int,
                                        requirements: Dict[str, Any],
                                        provider: str) -> Dict[str, Any]:
        """
        🧪 Processa completamente un'iterazione: validazione, compilazione, test
        """
        logger.info(f"Processing complete iteration {iteration}")
        
        # Get current source files
        current_files = self.structure_manager.get_current_source_files(structure)
        
        # Create temporary iteration structure for enhanced test agent
        from app.services.iteration_manager import IterationStructure
        temp_iter_structure = IterationStructure(
            iteration_path=structure.base_path / f".temp_iter_{iteration}",
            project_path=structure.source_path,
            tests_path=structure.tests_path,
            validation_report_path=structure.reports_path / f"validation_{iteration}.json",
            compilation_report_path=structure.reports_path / f"compilation_{iteration}.json",
            test_results_path=structure.reports_path / f"test_results_{iteration}.json",
            iteration_summary_path=structure.reports_path / f"iteration_{iteration}.json"
        )
        
        # Ensure temp iteration path exists
        temp_iter_structure.iteration_path.mkdir(exist_ok=True)
        
        # Use enhanced test agent for complete processing
        result = await self.enhanced_test_agent.process_iteration_complete(
            temp_iter_structure, structure.project_name, iteration, 
            requirements, current_files, provider
        )
        
        # Clean up temp directory
        try:
            import shutil
            if temp_iter_structure.iteration_path.exists():
                shutil.rmtree(temp_iter_structure.iteration_path)
        except Exception as e:
            logger.warning(f"Could not clean up temp directory: {e}")
        
        return result
    
    def _load_previous_errors(self, 
                            structure: ProjectStructure, 
                            previous_iteration: int) -> List[Dict[str, Any]]:
        """📋 Carica gli errori dall'iterazione precedente"""
        errors = []
        
        try:
            prev_report_file = structure.reports_path / f"iteration_{previous_iteration}.json"
            if prev_report_file.exists():
                with open(prev_report_file, 'r') as f:
                    prev_report = json.load(f)
                
                # Extract errors from the report
                errors_for_fixing = prev_report.get("errors_for_fixing", [])
                return errors_for_fixing
        
        except Exception as e:
            logger.warning(f"Could not load previous errors: {e}")
        
        return errors
    
    def _create_success_result(self, 
                              structure: ProjectStructure,
                              iteration: int,
                              overall_stats: Dict[str, Any],
                              iteration_result: Dict[str, Any]) -> Dict[str, Any]:
        """🎉 Crea il risultato di successo"""
        return {
            "status": "completed",
            "project_id": structure.project_id,
            "project_name": structure.project_name,
            "final_iteration": iteration,
            "total_iterations": iteration,
            "source_path": str(structure.source_path),
            "tests_path": str(structure.tests_path),
            "overall_stats": overall_stats,
            "iteration_result": iteration_result,
            "structure": {
                "clean_source": True,
                "isolated_tests": True,
                "structured_reports": True
            }
        }
    
    def _create_stop_result(self, 
                           structure: ProjectStructure,
                           last_iteration: int,
                           overall_stats: Dict[str, Any]) -> Dict[str, Any]:
        """🛑 Crea il risultato quando fermato dall'utente"""
        return {
            "status": "stopped",
            "reason": "user_requested",
            "project_id": structure.project_id,
            "project_name": structure.project_name,
            "last_iteration": last_iteration,
            "source_path": str(structure.source_path),
            "overall_stats": overall_stats
        }
    
    def _create_error_result(self, 
                            structure: ProjectStructure,
                            iteration: int,
                            error: str,
                            overall_stats: Dict[str, Any]) -> Dict[str, Any]:
        """❌ Crea il risultato quando c'è un errore"""
        return {
            "status": "failed",
            "reason": "iteration_error",
            "error": error,
            "project_id": structure.project_id,
            "project_name": structure.project_name,
            "failed_iteration": iteration,
            "source_path": str(structure.source_path),
            "overall_stats": overall_stats
        }
    
    def _create_max_iterations_result(self, 
                                    structure: ProjectStructure,
                                    max_iterations: int,
                                    overall_stats: Dict[str, Any]) -> Dict[str, Any]:
        """⏰ Crea il risultato quando raggiunto il massimo delle iterazioni"""
        return {
            "status": "completed_with_issues",
            "reason": "max_iterations_reached",
            "project_id": structure.project_id,
            "project_name": structure.project_name,
            "total_iterations": max_iterations,
            "source_path": str(structure.source_path),
            "tests_path": str(structure.tests_path),
            "overall_stats": overall_stats,
            "message": f"Completed {max_iterations} iterations with remaining issues"
        }
    
    def _get_current_timestamp(self) -> str:
        """📅 Ottiene timestamp corrente"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def request_stop(self):
        """🛑 Richiede l'interruzione della generazione"""
        logger.info("Stop requested for CleanStructureOrchestrator")
        self.stop_requested = True
    
    # === COMPATIBILITY METHODS ===
    
    async def generate_application_with_orchestration(self, **kwargs):
        """🔄 Metodo di compatibilità per l'interfaccia esistente"""
        return await self.generate_application_with_clean_structure(**kwargs)


class MultiAgentCleanStructureOrchestrator(CleanStructureOrchestrator):
    """
    🤖 MULTI-AGENT: Orchestratore multi-agente con struttura pulita
    
    Estende CleanStructureOrchestrator con capacità multi-agente:
    - System Agent per configurazione
    - Integration Agent per servizi esterni  
    - Endpoints Agent per API
    - Struttura sempre pulita
    """
    
    def __init__(self, llm_service: LLMService):
        super().__init__(llm_service)
        
        # Initialize specialized agents
        from app.services.agent_system import SystemAgent
        from app.services.agent_integration import IntegrationAgent
        from app.services.endpoints_agent import EndpointsAgent
        
        self.system_agent = SystemAgent(llm_service)
        self.integration_agent = IntegrationAgent(llm_service)
        self.endpoints_agent = EndpointsAgent(llm_service)
        
        logger.info("MultiAgentCleanStructureOrchestrator initialized")
    
    async def generate_application_with_clean_structure(self, 
                                                      requirements: Dict[str, Any],
                                                      provider: str,
                                                      max_iterations: int,
                                                      project_path: Path,
                                                      progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        🤖 MULTI-AGENT: Generazione con agenti specializzati e struttura pulita
        """
        # Extract project info
        project_id = project_path.name
        project_name = requirements.get("project", {}).get("name", f"app_{project_id[:8]}")
        
        logger.info(f"🤖 Starting multi-agent clean generation for {project_id}/{project_name}")
        
        # Check for stop request
        stop_file = project_path / "STOP_REQUESTED"
        if stop_file.exists():
            return {"status": "stopped", "reason": "user_requested"}
        
        # Create clean project structure
        structure = self.structure_manager.create_project_structure(project_id, project_name)
        
        # Save initial project metadata
        project_metadata = {
            "project_id": project_id,
            "project_name": project_name,
            "requirements": requirements,
            "generation_mode": "multi_agent_clean_structure",
            "provider": provider,
            "max_iterations": max_iterations,
            "status": "processing",
            "created_at": self._get_current_timestamp()
        }
        self.structure_manager.save_project_metadata(structure, project_metadata)
        
        # Phase 1: Requirements Analysis
        if progress_callback:
            progress_callback(0, 'analyzing_requirements')
        
        analysis = await self.system_agent.analyze_requirements(requirements, provider)
        
        # Save analysis report
        analysis_report = {
            "phase": "requirements_analysis", 
            "analysis": analysis,
            "timestamp": self._get_current_timestamp()
        }
        self.structure_manager.save_iteration_report(structure, 0, analysis_report)
        
        # Phase 2: System Files Generation
        if progress_callback:
            progress_callback(0, 'generating_system_files')
        
        system_files = await self.system_agent.generate_system_files(requirements, provider)
        if system_files:
            self.structure_manager.save_source_code(structure, system_files, 0)
            logger.info(f"🔧 Generated {len(system_files)} system files")
        
        # Phase 3: Integration Files Generation
        if progress_callback:
            progress_callback(0, 'generating_integration_files')
        
        integration_files = await self.integration_agent.generate_integrations(requirements, provider)
        if integration_files:
            self.structure_manager.save_source_code(structure, integration_files, 0)
            logger.info(f"🔗 Generated {len(integration_files)} integration files")
        
        # Phase 4: API Endpoints Generation
        if progress_callback:
            progress_callback(0, 'generating_api_endpoints')
        
        endpoint_files = await self.endpoints_agent.generate_endpoints(requirements, provider)
        if endpoint_files:
            self.structure_manager.save_source_code(structure, endpoint_files, 0)
            logger.info(f"🌐 Generated {len(endpoint_files)} endpoint files")
        
        # Phase 5: Core Application Generation (use parent class logic)
        logger.info("🎯 Starting core application generation with iterative improvement")
        
        # Continue with standard iterative process
        result = await super().generate_application_with_clean_structure(
            requirements, provider, max_iterations, project_path, progress_callback
        )
        
        # Enhance result with multi-agent info
        if isinstance(result, dict):
            result["generation_mode"] = "multi_agent_clean_structure"
            result["agents_used"] = ["SystemAgent", "IntegrationAgent", "EndpointsAgent", "CodeGenerator", "TestAgent"]
            result["pre_generated_files"] = {
                "system_files": len(system_files) if system_files else 0,
                "integration_files": len(integration_files) if integration_files else 0,
                "endpoint_files": len(endpoint_files) if endpoint_files else 0
            }
        
        return result


# === FACTORY FUNCTION ===

def create_orchestrator(agent_mode: str, llm_service: LLMService) -> CleanStructureOrchestrator:
    """
    🏭 FACTORY: Crea l'orchestratore appropriato basato su agent_mode
    
    Args:
        agent_mode: Modalità agente ("enhanced_generator", "updated_orchestrator", "multi_agent")
        llm_service: Servizio LLM
        
    Returns:
        Orchestratore appropriato con struttura pulita
    """
    logger.info(f"Creating orchestrator for mode: {agent_mode}")
    
    if agent_mode == "multi_agent":
        return MultiAgentCleanStructureOrchestrator(llm_service)
    else:
        # Both "enhanced_generator" and "updated_orchestrator" use the same clean orchestrator
        # The difference is in the max_iterations and complexity handling
        return CleanStructureOrchestrator(llm_service)


# === BACKWARD COMPATIBILITY ===

class LegacyOrchestratorAdapter:
    """
    🔄 ADAPTER: Adatta i vecchi orchestratori alla nuova struttura
    
    Questo adapter permette di usare la nuova logica pulita mantenendo
    l'interfaccia dei vecchi orchestratori per compatibilità.
    """
    
    def __init__(self, llm_service: LLMService):
        self.clean_orchestrator = CleanStructureOrchestrator(llm_service)
        logger.info("LegacyOrchestratorAdapter initialized")
    
    async def generate_application_with_orchestration(self, 
                                                    requirements: Dict[str, Any],
                                                    provider: str,
                                                    max_iterations: int,
                                                    project_path: Path,
                                                    progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """🔄 Metodo di compatibilità che usa la nuova struttura pulita"""
        
        # Use clean orchestrator but adapt the result
        result = await self.clean_orchestrator.generate_application_with_clean_structure(
            requirements, provider, max_iterations, project_path, progress_callback
        )
        
        # Adapt result format for backward compatibility if needed
        if isinstance(result, dict):
            # Add legacy fields if expected by old code
            result["output_path"] = result.get("source_path", str(project_path))
            
            # Map new status to old status if needed
            status_mapping = {
                "completed": "completed",
                "completed_with_issues": "completed",  # Still counts as completed
                "stopped": "failed",  # Legacy treats stops as failures
                "failed": "failed"
            }
            
            old_status = status_mapping.get(result.get("status"), result.get("status"))
            result["legacy_status"] = old_status
        
        return result
    
    def request_stop(self):
        """🛑 Passa la richiesta di stop all'orchestratore pulito"""
        self.clean_orchestrator.request_stop()