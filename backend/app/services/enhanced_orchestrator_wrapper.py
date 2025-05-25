# backend/app/services/enhanced_generator_wrapper.py
import logging
import asyncio
import re
from typing import Dict, Any, List, Optional, Callable, Tuple
from pathlib import Path

from app.services.llm_service import LLMService
from app.services.enhanced_code_generator import EnhancedCodeGenerator
from app.services.code_generator import CodeGenerator
from app.services.test_agent import TestAgent

logger = logging.getLogger(__name__)

class EnhancedGeneratorWrapper:
    """
    Wrapper che integra EnhancedCodeGenerator nel flusso di generazione del sistema enhanced_v2.
    Questo permette di usare "enhanced_generator" come agent_mode mantenendo compatibilità
    con il sistema di validazione, compilazione e testing enhanced.
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.enhanced_generator = EnhancedCodeGenerator(llm_service)
        self.basic_generator = CodeGenerator(llm_service)  # Fallback
        self.test_agent = TestAgent(llm_service)
        self.stop_requested = False
        logger.info("EnhancedGeneratorWrapper initialized")
    
    async def generate_application_with_enhanced_flow(self, 
                                                    requirements: Dict[str, Any],
                                                    provider: str,
                                                    max_iterations: int,
                                                    project_path: Path,
                                                    progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Genera un'applicazione usando EnhancedCodeGenerator con il flusso enhanced_v2.
        
        Questo metodo:
        1. Analizza i requisiti per creare un piano architetturale
        2. Usa EnhancedCodeGenerator per generazione sofisticata
        3. Integra con il sistema di validazione/compilazione enhanced
        4. Applica iterazioni con fixing intelligente
        """
        stop_file = project_path / "STOP_REQUESTED"
        if stop_file.exists():
            logger.info(f"Stop file found for project {project_path.name}, stopping generation")
            return {"status": "stopped", "reason": "user_requested"}
        
        logger.info(f"Starting enhanced generator flow with {max_iterations} max iterations")
        
        # Estrai nome progetto
        project_name = requirements.get("project", {}).get("name", project_path.name)
        if not project_name or project_name == project_path.name:
            project_name = f"project_{project_path.name}"
        
        # Track project state
        project_state = {
            "iterations_completed": 0,
            "total_errors_fixed": 0,
            "remaining_issues": [],
            "final_success": False,
            "generation_strategy": "enhanced_single_agent"
        }
        
        # FASE 1: Analisi architetturale
        if progress_callback:
            progress_callback(0, 'analyzing_architecture')
        
        try:
            architecture_plan = await self._analyze_project_architecture(requirements, provider)
            logger.info("Architecture analysis completed")
        except Exception as e:
            logger.warning(f"Architecture analysis failed, using basic approach: {e}")
            architecture_plan = self._create_basic_architecture_plan(requirements)
        
        # Main iteration loop
        for iteration in range(1, max_iterations + 1):
            logger.info(f"Starting enhanced generation iteration {iteration} for project {project_name}")
            
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
                
                # Progress callback
                if progress_callback:
                    progress_callback(iteration, 'generating_code')
                
                # FASE 2: Generazione codice con Enhanced Generator
                if iteration == 1:
                    # Prima iterazione: genera da zero con piano architetturale
                    code_files = await self._generate_initial_code_enhanced(
                        requirements, architecture_plan, provider, project_path, project_name
                    )
                else:
                    # Iterazioni successive: carica errori precedenti e applica fix
                    previous_errors = self._load_previous_iteration_errors(project_path, iteration - 1)
                    existing_files = self._load_previous_files(project_path, project_name, iteration - 1)
                    
                    if previous_errors and existing_files:
                        logger.info(f"Found {len(previous_errors)} errors from previous iteration")
                        code_files = await self._generate_code_with_intelligent_fixes(
                            requirements, existing_files, previous_errors, provider, iteration
                        )
                    else:
                        logger.info("No previous errors found, enhancing code quality")
                        code_files = await self._enhance_existing_code(
                            requirements, existing_files or {}, provider, iteration
                        )
                
                # FASE 3: Salva codice generato nella struttura enhanced
                iteration_structure = self._create_iteration_structure(project_path, project_name, iteration)
                files_generated, files_modified = self._save_generated_code(iteration_structure, code_files)
                
                logger.info(f"Iteration {iteration}: Generated {files_generated} files, modified {files_modified}")
                
                # FASE 4: Validazione e compilazione (integrazione con enhanced system)
                if progress_callback:
                    progress_callback(iteration, 'validating_and_testing')
                
                validation_result = await self._validate_and_compile_enhanced(
                    iteration_structure, project_name, iteration, requirements, code_files, provider
                )
                
                # FASE 5: Analisi risultati
                project_state["iterations_completed"] = iteration
                project_state["remaining_issues"] = validation_result.get("errors_for_fixing", [])
                
                # Check success
                if validation_result["success"]:
                    logger.info(f"Enhanced generation iteration {iteration} completed successfully!")
                    project_state["final_success"] = True
                    
                    return {
                        "status": "completed",
                        "iteration": iteration,
                        "project_id": project_path.name,
                        "project_name": project_name,
                        "output_path": str(iteration_structure["iteration_path"]),
                        "project_state": project_state,
                        "final_result": validation_result,
                        "generation_strategy": "enhanced_single_agent"
                    }
                
                # Prepare for next iteration
                logger.info(f"Iteration {iteration} had issues, preparing for next iteration")
                
                # Update error progress tracking
                prev_errors = len(project_state["remaining_issues"])
                current_errors = len(validation_result.get("errors_for_fixing", []))
                
                if current_errors < prev_errors:
                    project_state["total_errors_fixed"] += (prev_errors - current_errors)
                
                # Check progress
                if iteration > 1 and current_errors >= prev_errors:
                    logger.warning(f"No progress made in iteration {iteration}, errors: {current_errors}")
                
                # Continue to next iteration
                if iteration < max_iterations:
                    logger.info(f"Continuing to iteration {iteration + 1}")
                    continue
                
            except Exception as e:
                logger.error(f"Error in enhanced generation iteration {iteration}: {str(e)}")
                
                # Clean up failed iteration if needed
                if iteration == max_iterations:
                    return {
                        "status": "failed",
                        "reason": "iteration_error",
                        "error": str(e),
                        "iteration": iteration,
                        "project_id": project_path.name,
                        "project_state": project_state
                    }
                
                logger.info(f"Attempting to continue after error in iteration {iteration}")
                continue
        
        # Max iterations reached
        logger.warning(f"Max iterations ({max_iterations}) reached")
        
        final_status = "completed_with_issues"
        if project_state["total_errors_fixed"] > 0:
            final_status = "completed_with_improvements"
        
        return {
            "status": final_status,
            "reason": "max_iterations_reached",
            "iterations": max_iterations,
            "project_id": project_path.name,
            "project_name": project_name,
            "project_state": project_state,
            "output_path": str(project_path / f"iter-{max_iterations}"),
            "generation_strategy": "enhanced_single_agent"
        }
    
    async def _analyze_project_architecture(self, requirements: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """
        Usa EnhancedCodeGenerator per analizzare l'architettura del progetto
        """
        logger.info("Analyzing project architecture with enhanced generator")
        
        # Crea un prompt specifico per l'analisi architetturale
        analysis_prompt = f"""
        Analyze the following project requirements and create a comprehensive architecture plan:
        
        {json.dumps(requirements, indent=2)}
        
        Create an architecture plan that includes:
        1. Overall system architecture pattern
        2. Component breakdown and responsibilities
        3. Data flow and integration points
        4. Technology stack recommendations
        5. File structure and organization
        6. Key design patterns to follow
        
        Provide the analysis in JSON format.
        """
        
        system_prompt = """
        You are an expert software architect. Analyze the requirements and create a detailed 
        architecture plan that will guide the code generation process. Focus on scalability,
        maintainability, and best practices for the specified technology stack.
        """
        
        try:
            response = await self.llm_service.generate(
                provider=provider,
                prompt=analysis_prompt,
                system_prompt=system_prompt
            )
            
            # Prova a estrarre JSON dalla risposta
            import re
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                import json
                return json.loads(json_match.group(1))
            else:
                # Fallback: crea una struttura base dalla risposta testuale
                return {
                    "analysis_type": "architecture",
                    "overview": response[:500],
                    "components": self._extract_components_from_text(response),
                    "patterns": ["MVC", "Component-based"],
                    "tech_stack": requirements.get("tech_stack", {}),
                    "file_structure": self._infer_file_structure(requirements)
                }
        except Exception as e:
            logger.error(f"Error in architecture analysis: {e}")
            return self._create_basic_architecture_plan(requirements)
    
    def _create_basic_architecture_plan(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un piano architetturale di base se l'analisi avanzata fallisce
        """
        tech_stack = requirements.get("tech_stack", {})
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        return {
            "analysis_type": "basic_architecture",
            "overview": f"Basic {project_type} application architecture",
            "components": {
                "frontend": tech_stack.get("frontend", "React"),
                "backend": tech_stack.get("backend", "Node.js"),
                "database": tech_stack.get("database", "PostgreSQL"),
                "api": tech_stack.get("api", "RESTful")
            },
            "patterns": ["MVC", "Component-based", "RESTful API"],
            "tech_stack": tech_stack,
            "file_structure": self._infer_file_structure(requirements)
        }
    
    def _infer_file_structure(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inferisce la struttura dei file dai requisiti
        """
        tech_stack = requirements.get("tech_stack", {})
        frontend = tech_stack.get("frontend", "").lower()
        backend = tech_stack.get("backend", "").lower()
        
        structure = {
            "root": ["package.json", "README.md", "docker-compose.yml"],
            "frontend": [],
            "backend": [],
            "config": ["Dockerfile"]
        }
        
        if "react" in frontend:
            structure["frontend"] = [
                "src/components/",
                "src/pages/", 
                "src/hooks/",
                "src/utils/",
                "public/index.html"
            ]
        
        if "node" in backend or "express" in backend:
            structure["backend"] = [
                "src/routes/",
                "src/controllers/", 
                "src/models/",
                "src/middleware/",
                "src/config/"
            ]
        
        return structure
    
    def _extract_components_from_text(self, text: str) -> List[str]:
        """
        Estrae i componenti principali da una risposta testuale
        """
        # Pattern comuni per identificare componenti
        component_patterns = [
            r'(\w+)\s+component',
            r'(\w+)\s+service',
            r'(\w+)\s+controller',
            r'(\w+)\s+model',
            r'(\w+)\s+module'
        ]
        
        components = set()
        for pattern in component_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            components.update(matches)
        
        return list(components)[:10]  # Limita a 10 componenti principali
    
    async def _generate_initial_code_enhanced(self, 
                                            requirements: Dict[str, Any],
                                            architecture_plan: Dict[str, Any],
                                            provider: str,
                                            project_path: Path,
                                            project_name: str) -> Dict[str, str]:
        """
        Genera codice iniziale usando EnhancedCodeGenerator con piano architetturale
        """
        logger.info("Generating initial code with enhanced generator and architecture plan")
        
        try:
            # Usa il metodo generate_with_architecture di EnhancedCodeGenerator
            code_files = await self.enhanced_generator.generate_with_architecture(
                requirements=requirements,
                architecture_plan=architecture_plan,
                provider=provider
            )
            
            logger.info(f"Enhanced generator produced {len(code_files)} files")
            return code_files
        
        except Exception as e:
            logger.warning(f"Enhanced generation failed, falling back to basic generator: {e}")
            # Fallback al generatore base
            return await self._generate_with_basic_generator(requirements, provider)
    
    async def _generate_code_with_intelligent_fixes(self,
                                                  requirements: Dict[str, Any],
                                                  existing_files: Dict[str, str],
                                                  errors: List[Dict[str, Any]],
                                                  provider: str,
                                                  iteration: int) -> Dict[str, str]:
        """
        Genera codice applicando fix intelligenti usando EnhancedCodeGenerator
        """
        logger.info(f"Applying intelligent fixes for {len(errors)} errors in iteration {iteration}")
        
        try:
            # Usa il metodo fix_issues di EnhancedCodeGenerator
            fixed_files = await self.enhanced_generator.fix_issues(
                code_files=existing_files,
                issues=errors,
                provider=provider
            )
            
            logger.info(f"Applied intelligent fixes to {len(fixed_files)} files")
            return fixed_files
        
        except Exception as e:
            logger.warning(f"Intelligent fixing failed, using basic approach: {e}")
            # Fallback: rigenera tutto con contesto degli errori
            return await self._regenerate_with_error_context(requirements, existing_files, errors, provider)
    
    async def _enhance_existing_code(self,
                                   requirements: Dict[str, Any],
                                   existing_files: Dict[str, str],
                                   provider: str,
                                   iteration: int) -> Dict[str, str]:
        """
        Migliora la qualità del codice esistente usando EnhancedCodeGenerator
        """
        logger.info(f"Enhancing code quality in iteration {iteration}")
        
        # Determina aree di focus per il miglioramento
        quality_focus = self._determine_quality_focus(requirements, iteration)
        
        try:
            # Usa il metodo enhance_code_quality di EnhancedCodeGenerator
            enhanced_files = await self.enhanced_generator.enhance_code_quality(
                code_files=existing_files,
                quality_focus=quality_focus,
                provider=provider
            )
            
            logger.info(f"Enhanced {len(enhanced_files)} files with focus on: {', '.join(quality_focus)}")
            return enhanced_files
        
        except Exception as e:
            logger.warning(f"Code enhancement failed, returning existing files: {e}")
            return existing_files
    
    def _determine_quality_focus(self, requirements: Dict[str, Any], iteration: int) -> List[str]:
        """
        Determina le aree di focus per il miglioramento della qualità in base all'iterazione
        """
        # Focus diversi per iterazioni diverse
        focus_by_iteration = {
            2: ["security", "documentation"],
            3: ["performance", "maintainability"], 
            4: ["testing", "accessibility"],
            5: ["optimization", "best_practices"]
        }
        
        base_focus = focus_by_iteration.get(iteration, ["quality", "documentation"])
        
        # Aggiungi focus specifici basati sui requisiti
        if "authentication" in str(requirements).lower():
            base_focus.append("security")
        if "database" in str(requirements).lower():
            base_focus.append("performance")
        
        return list(set(base_focus))  # Rimuovi duplicati
    
    async def _generate_with_basic_generator(self, requirements: Dict[str, Any], provider: str) -> Dict[str, str]:
        """
        Fallback al generatore base se Enhanced Generator fallisce
        """
        logger.info("Using basic generator as fallback")
        
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        if project_type == "frontend":
            return await self.basic_generator.generate_react_app(requirements, provider)
        elif project_type == "backend":
            return await self.basic_generator.generate_backend_api(requirements, provider)
        else:
            return await self.basic_generator.generate_code(requirements, provider, 1)
    
    async def _regenerate_with_error_context(self,
                                           requirements: Dict[str, Any],
                                           existing_files: Dict[str, str],
                                           errors: List[Dict[str, Any]],
                                           provider: str) -> Dict[str, str]:
        """
        Rigenera codice con contesto degli errori usando il generatore base
        """
        logger.info("Regenerating with error context using basic generator")
        
        # Aggiungi contesto degli errori ai requisiti
        enhanced_requirements = dict(requirements)
        enhanced_requirements["_error_context"] = {
            "previous_errors": errors,
            "files_with_issues": list(set(error.get("file", "") for error in errors if error.get("file")))
        }
        
        return await self.basic_generator.generate_iterative_improvement(
            requirements=enhanced_requirements,
            provider=provider,
            iteration=2,
            previous_errors=errors,
            existing_files=existing_files
        )
    
    # Metodi di utilità per integrazione con sistema enhanced
    def _create_iteration_structure(self, project_path: Path, project_name: str, iteration: int) -> Dict[str, Path]:
        """
        Crea la struttura directory per un'iterazione (compatibile con enhanced system)
        """
        iteration_path = project_path / f"iter-{iteration}"
        iteration_path.mkdir(exist_ok=True)
        
        project_code_path = iteration_path / project_name
        project_code_path.mkdir(exist_ok=True)
        
        tests_path = iteration_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        return {
            "iteration_path": iteration_path,
            "project_path": project_code_path,
            "tests_path": tests_path,
            "validation_report_path": iteration_path / "validation_report.json",
            "compilation_report_path": iteration_path / "compilation_report.json",
            "test_results_path": iteration_path / "test_results.json",
            "iteration_summary_path": iteration_path / "iteration_summary.json"
        }
    
    def _save_generated_code(self, iteration_structure: Dict[str, Path], code_files: Dict[str, str]) -> Tuple[int, int]:
        """
        Salva i file generati nella struttura dell'iterazione
        """
        files_generated = 0
        files_modified = 0
        
        for file_path, content in code_files.items():
            full_path = iteration_structure["project_path"] / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if full_path.exists():
                files_modified += 1
            else:
                files_generated += 1
            
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error saving {file_path}: {e}")
        
        return files_generated, files_modified
    
    async def _validate_and_compile_enhanced(self,
                                           iteration_structure: Dict[str, Path],
                                           project_name: str,
                                           iteration: int,
                                           requirements: Dict[str, Any],
                                           code_files: Dict[str, str],
                                           provider: str) -> Dict[str, Any]:
        """
        Esegue validazione e compilazione usando il sistema enhanced
        """
        logger.info(f"Running enhanced validation and compilation for iteration {iteration}")
        
        try:
            # Usa EnhancedTestAgent se disponibile, altrimenti TestAgent base
            try:
                from app.services.enhanced_test_agent import EnhancedTestAgent
                enhanced_test_agent = EnhancedTestAgent(self.llm_service)
                
                # Crea un oggetto IterationStructure compatibile
                from app.services.iteration_manager import IterationStructure
                iter_struct = IterationStructure(
                    iteration_path=iteration_structure["iteration_path"],
                    project_path=iteration_structure["project_path"],
                    tests_path=iteration_structure["tests_path"],
                    validation_report_path=iteration_structure["validation_report_path"],
                    compilation_report_path=iteration_structure["compilation_report_path"],
                    test_results_path=iteration_structure["test_results_path"],
                    iteration_summary_path=iteration_structure["iteration_summary_path"]
                )
                
                return await enhanced_test_agent.process_iteration_complete(
                    iter_struct, project_name, iteration, requirements, code_files, provider
                )
            
            except ImportError:
                logger.warning("EnhancedTestAgent not available, using basic TestAgent")
                # Fallback al TestAgent base
                return await self._basic_validation_and_testing(
                    iteration_structure, requirements, code_files, provider
                )
        
        except Exception as e:
            logger.error(f"Error in validation and compilation: {e}")
            return {
                "iteration": iteration,
                "success": False,
                "error": str(e),
                "validation_report": {"summary": {"error": 1, "warning": 0}},
                "compilation_report": {"success": False, "errors": [{"message": str(e)}]},
                "test_results": {"success": False, "error": str(e)},
                "errors_for_fixing": [{"type": "system", "message": str(e)}]
            }
    
    async def _basic_validation_and_testing(self,
                                          iteration_structure: Dict[str, Path],
                                          requirements: Dict[str, Any],
                                          code_files: Dict[str, str],
                                          provider: str) -> Dict[str, Any]:
        """
        Validazione e testing di base usando TestAgent
        """
        logger.info("Running basic validation and testing")
        
        # Genera test
        test_files = await self.test_agent.test_generator.generate_tests(
            requirements, code_files, provider
        )
        
        # Esegui test
        test_results = await self.test_agent.test_runner.run_tests(
            iteration_structure["iteration_path"], test_files
        )
        
        # Salva risultati
        import json
        with open(iteration_structure["test_results_path"], 'w') as f:
            json.dump(test_results, f, indent=2)
        
        # Analizza fallimenti
        failures = self.test_agent.test_runner.analyze_test_failures(test_results)
        
        return {
            "success": test_results.get("success", False),
            "test_results": test_results,
            "errors_for_fixing": failures,
            "validation_report": {"summary": {"error": len(failures), "warning": 0}},
            "compilation_report": {"success": len(failures) == 0, "errors": failures}
        }
    
    def _load_previous_iteration_errors(self, project_path: Path, previous_iteration: int) -> List[Dict[str, Any]]:
        """
        Carica gli errori dall'iterazione precedente
        """
        errors = []
        prev_iter_path = project_path / f"iter-{previous_iteration}"
        
        if not prev_iter_path.exists():
            return errors
        
        # Carica da iteration summary
        summary_path = prev_iter_path / "iteration_summary.json"
        if summary_path.exists():
            try:
                import json
                with open(summary_path, 'r') as f:
                    summary = json.load(f)
                
                # Estrai errori da validation report
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
                
                # Estrai errori di compilazione
                if "compilation_report" in summary:
                    compilation = summary["compilation_report"]
                    for error in compilation.get("errors", []):
                        errors.append({
                            "type": "compilation",
                            "category": error.get("error_type", "unknown"),
                            "file": error.get("file_path"),
                            "line": error.get("line_number"),
                            "message": error.get("message", ""),
                            "suggestion": error.get("suggestion", ""),
                            "priority": "high"
                        })
                
            except Exception as e:
                logger.warning(f"Could not load iteration summary: {e}")
        
        return errors
    
    def _load_previous_files(self, project_path: Path, project_name: str, previous_iteration: int) -> Optional[Dict[str, str]]:
        """
        Carica i file dall'iterazione precedente
        """
        if previous_iteration < 1:
            return None
        
        prev_path = project_path / f"iter-{previous_iteration}" / project_name
        if not prev_path.exists():
            return None
        
        files = {}
        try:
            for file_path in prev_path.rglob("*"):
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(prev_path))
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            files[relative_path] = f.read()
                    except Exception as e:
                        logger.warning(f"Could not read {relative_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading previous files: {e}")
            return None
        
        return files
    
    def _update_current_iteration(self, project_path: Path, iteration: int):
        """
        Aggiorna l'iterazione corrente nel file project.json
        """
        try:
            project_json_path = project_path / "project.json"
            if project_json_path.exists():
                import json
                with open(project_json_path, 'r') as f:
                    project_data = json.load(f)
                
                project_data["current_iteration"] = iteration
                
                with open(project_json_path, 'w') as f:
                    json.dump(project_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error updating project.json: {str(e)}")
    
    def request_stop(self):
        """Richiesta di interruzione"""
        logger.info("Stop requested for EnhancedGeneratorWrapper")
        self.stop_requested = True