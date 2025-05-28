# backend/app/services/updated_orchestrator.py
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from app.services.llm_service import LLMService
from app.services.code_generator import CodeGenerator
from app.services.enhanced_test_agent import EnhancedTestAgent
from app.services.iteration_manager import IterationManager, IterationStructure

logger = logging.getLogger(__name__)

class UpdatedOrchestratorAgent:
    """
    Updated orchestrator that implements the new enhanced flow:
    1. Structured iteration directories
    2. Code validation and compilation checking
    3. Enhanced test generation and execution
    4. Comprehensive error analysis and fixing
    
    🔥 AGGIORNATO: Aggiunge supporto per enhanced_generator mode
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.code_generator = CodeGenerator(llm_service)
        self.enhanced_test_agent = EnhancedTestAgent(llm_service)
        self.iteration_manager = IterationManager()
        self.stop_requested = False
        
        # 🔥 NUOVO: Supporto per Enhanced Generator
        try:
            from app.services.enhanced_code_generator import EnhancedCodeGenerator
            self.enhanced_code_generator = EnhancedCodeGenerator(llm_service)
            self.has_enhanced_generator = True
            logger.info("UpdatedOrchestratorAgent initialized with Enhanced Generator support")
        except ImportError:
            self.enhanced_code_generator = None
            self.has_enhanced_generator = False
            logger.info("UpdatedOrchestratorAgent initialized without Enhanced Generator")
    
    async def generate_application_with_enhanced_flow(self, 
                                                    requirements: Dict[str, Any],
                                                    provider: str,
                                                    max_iterations: int,
                                                    project_path: Path,
                                                    progress_callback: Optional[Callable] = None,
                                                    generation_mode: str = "orchestrated") -> Dict[str, Any]:
        """
        Main orchestration method with enhanced flow
        
        🔥 NUOVO: Parametro generation_mode per supportare enhanced_generator
        - "orchestrated": Usa il flusso orchestrato normale (default)
        - "enhanced_single": Usa Enhanced Generator con validazione orchestrata
        """
        stop_file = project_path / "STOP_REQUESTED"
        if stop_file.exists():
            logger.info(f"Stop file found for project {project_path.name}, stopping generation")
            return {"status": "stopped", "reason": "user_requested"}
        
        logger.info(f"Starting enhanced orchestrated generation with {max_iterations} max iterations, mode: {generation_mode}")
        
        # Extract project name
        project_name = requirements.get("project", {}).get("name", project_path.name)
        if not project_name or project_name == project_path.name:
            project_name = f"project_{project_path.name}"
        
        # Cleanup any existing empty iteration directories
        self._cleanup_empty_directories(project_path, max_iterations)
        
        # Track overall project state
        project_state = {
            "iterations_completed": 0,
            "total_errors_fixed": 0,
            "remaining_issues": [],
            "final_success": False,
            "generation_mode": generation_mode
        }
        
        # 🔥 NUOVO: Se mode è enhanced_single, usa Enhanced Generator per generazione iniziale
        if generation_mode == "enhanced_single" and self.has_enhanced_generator:
            logger.info("Using Enhanced Generator for initial code generation")
            
            try:
                # Genera codice con Enhanced Generator
                if progress_callback:
                    progress_callback(1, 'generating_with_enhanced_generator')
                
                enhanced_result = await self.enhanced_code_generator.generate_complete_project_enhanced(
                    requirements=requirements,
                    provider=provider,
                    max_iterations=min(max_iterations, 3)  # Limit per Enhanced Generator
                )
                
                if enhanced_result["success"]:
                    # Crea struttura iterazione per il risultato
                    iteration_structure = self.iteration_manager.create_iteration_structure(
                        project_path, project_name, 1
                    )
                    
                    # Salva i file generati
                    files_generated, files_modified = self.iteration_manager.save_generated_code(
                        iteration_structure, enhanced_result["code_files"]
                    )
                    
                    logger.info(f"Enhanced Generator: Generated {files_generated} files, modified {files_modified}")
                    
                    # Processa con validazione orchestrata
                    if progress_callback:
                        progress_callback(1, 'validating_enhanced_code')
                    
                    iteration_result = await self.enhanced_test_agent.process_iteration_complete(
                        iteration_structure, project_name, 1, requirements, enhanced_result["code_files"], provider
                    )
                    
                    project_state["iterations_completed"] = 1
                    project_state["remaining_issues"] = iteration_result.get("errors_for_fixing", [])
                    
                    # Se Enhanced Generator ha successo, ritorna subito
                    if iteration_result["success"]:
                        logger.info("Enhanced Generator completed successfully!")
                        project_state["final_success"] = True
                        
                        return {
                            "status": "completed",
                            "iteration": 1,
                            "project_id": project_path.name,
                            "project_name": project_name,
                            "output_path": str(iteration_structure.iteration_path),
                            "project_state": project_state,
                            "final_result": iteration_result,
                            "generation_strategy": "enhanced_single_agent"
                        }
                    
                    # Se ci sono errori, continua con orchestrazione normale per fixarli
                    logger.info(f"Enhanced Generator had {len(project_state['remaining_issues'])} issues, continuing with orchestrated fixing")
                    start_iteration = 2  # Inizia dalla iterazione 2
                else:
                    logger.warning("Enhanced Generator failed, falling back to orchestrated generation")
                    start_iteration = 1
                    
            except Exception as e:
                logger.error(f"Enhanced Generator error: {e}")
                logger.info("Falling back to orchestrated generation")
                start_iteration = 1
        else:
            start_iteration = 1
        
        # Main iteration loop (orchestrato normale o fixing dopo enhanced)
        for iteration in range(start_iteration, max_iterations + 1):
            logger.info(f"Starting iteration {iteration} for project {project_name}")
            
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
                # Update current iteration in project.json
                self._update_current_iteration(project_path, iteration)
                
                # Progress callback
                if progress_callback:
                    progress_callback(iteration, 'preparing_iteration')
                
                # Step 1: Create iteration structure
                iteration_structure = self.iteration_manager.create_iteration_structure(
                    project_path, project_name, iteration
                )
                
                # Step 2: Generate code
                if progress_callback:
                    progress_callback(iteration, 'generating_code')
                
                code_files = await self._generate_code_for_iteration(
                    requirements, provider, iteration, project_path, project_name
                )
                
                # Step 3: Save generated code
                files_generated, files_modified = self.iteration_manager.save_generated_code(
                    iteration_structure, code_files
                )
                
                logger.info(f"Iteration {iteration}: Generated {files_generated} files, modified {files_modified}")
                
                # Step 4: Process iteration (validation, compilation, testing)
                if progress_callback:
                    progress_callback(iteration, 'validating_and_testing')
                
                iteration_result = await self.enhanced_test_agent.process_iteration_complete(
                    iteration_structure, project_name, iteration, requirements, code_files, provider
                )
                
                # Step 5: Analyze results and determine next steps
                project_state["iterations_completed"] = iteration
                project_state["remaining_issues"] = iteration_result.get("errors_for_fixing", [])
                
                # Check if iteration was successful
                if iteration_result["success"]:
                    logger.info(f"Iteration {iteration} completed successfully!")
                    project_state["final_success"] = True
                    
                    return {
                        "status": "completed",
                        "iteration": iteration,
                        "project_id": project_path.name,
                        "project_name": project_name,
                        "output_path": str(iteration_structure.iteration_path),
                        "project_state": project_state,
                        "final_result": iteration_result,
                        "generation_strategy": "enhanced_orchestrated" if generation_mode == "enhanced_single" else "orchestrated"
                    }
                
                # If not successful, prepare for next iteration
                logger.info(f"Iteration {iteration} had issues, preparing for next iteration")
                
                # Update project state with errors fixed
                prev_errors = len(project_state["remaining_issues"])
                current_errors = len(iteration_result.get("errors_for_fixing", []))
                
                if current_errors < prev_errors:
                    project_state["total_errors_fixed"] += (prev_errors - current_errors)
                
                # Check if we're making progress
                if iteration > start_iteration and current_errors >= prev_errors:
                    logger.warning(f"No progress made in iteration {iteration}, errors: {current_errors}")
                    
                    # If no progress for 2 consecutive iterations, consider stopping
                    if iteration > start_iteration + 1:
                        logger.warning("No progress for multiple iterations, may stop early")
                
                # Continue to next iteration if we haven't reached max
                if iteration < max_iterations:
                    logger.info(f"Continuing to iteration {iteration + 1}")
                    continue
                
            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {str(e)}")
                
                # Clean up failed iteration
                if 'iteration_structure' in locals():
                    try:
                        self.iteration_manager.cleanup_iteration(
                            project_path, iteration, keep_reports=True
                        )
                    except Exception as cleanup_error:
                        logger.error(f"Error cleaning up failed iteration: {cleanup_error}")
                
                # If this is the last iteration, return failure
                if iteration == max_iterations:
                    return {
                        "status": "failed",
                        "reason": "iteration_error",
                        "error": str(e),
                        "iteration": iteration,
                        "project_id": project_path.name,
                        "project_state": project_state
                    }
                
                # Otherwise, try to continue
                logger.info(f"Attempting to continue after error in iteration {iteration}")
                continue
        
        # If we've reached here, max iterations completed without full success
        logger.warning(f"Max iterations ({max_iterations}) reached")
        
        # Determine final status based on last iteration
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
            "generation_strategy": "enhanced_orchestrated" if generation_mode == "enhanced_single" else "orchestrated"
        }
    
    # 🔥 NUOVO: Metodo wrapper per enhanced_generator mode
    async def generate_with_enhanced_generator_mode(self,
                                                   requirements: Dict[str, Any],
                                                   provider: str,
                                                   max_iterations: int,
                                                   project_path: Path,
                                                   progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Wrapper method specifically for enhanced_generator mode.
        Usa Enhanced Generator con validazione orchestrata.
        """
        return await self.generate_application_with_enhanced_flow(
            requirements=requirements,
            provider=provider,
            max_iterations=max_iterations,
            project_path=project_path,
            progress_callback=progress_callback,
            generation_mode="enhanced_single"
        )
    
    # Modifiche da applicare al tuo updated_orchestrator.py esistente

# 1. SOSTITUISCI il metodo _generate_code_for_iteration() con questo:

    async def _generate_code_for_iteration(self, 
                                        requirements: Dict[str, Any],
                                        provider: str,
                                        iteration: int,
                                        project_path: Path,
                                        project_name: str) -> Dict[str, str]:
        """
        🔥 ENHANCED: Generate code for a specific iteration with structured output
        """
        logger.info(f"Generating structured code for iteration {iteration}")
        
        if iteration == 1:
            # First iteration: generate from requirements with structure
            raw_code_files = await self._generate_initial_code_structured(requirements, provider)
            
            # Apply structured organization
            return await self._apply_structured_organization_updated(raw_code_files, requirements, project_name)
        else:
            # Subsequent iterations: load previous iteration and fix errors
            previous_files = self.iteration_manager.load_previous_iteration_files(
                project_path, project_name, iteration
            )
            
            # Load errors from previous iteration
            previous_errors = self._load_previous_iteration_errors(project_path, iteration - 1)
            
            if previous_errors:
                logger.info(f"Found {len(previous_errors)} errors from previous iteration")
                
                # 🔥 Enhanced Generator fixing if available
                if self.has_enhanced_generator and len(previous_errors) > 0:
                    logger.info("Using Enhanced Generator for intelligent error fixing")
                    try:
                        fixed_files = await self.enhanced_code_generator.fix_issues(
                            code_files=previous_files,
                            issues=previous_errors,
                            provider=provider,
                            context={
                                "iteration": iteration,
                                "project_type": requirements.get("project", {}).get("type", "fullstack"),
                                "tech_stack": requirements.get("tech_stack", {})
                            }
                        )
                        logger.info("Enhanced Generator fixed issues successfully")
                        
                        # Apply structured organization to fixed files
                        return await self._apply_structured_organization_updated(fixed_files, requirements, project_name)
                        
                    except Exception as e:
                        logger.warning(f"Enhanced Generator fixing failed: {e}, falling back to standard fixing")
                        
                # Fallback to standard fixing
                fixed_files = await self._generate_code_with_fixes_structured(
                    requirements, provider, previous_errors, previous_files, iteration
                )
                
                # Apply structured organization
                return await self._apply_structured_organization_updated(fixed_files, requirements, project_name)
            else:
                logger.info("No previous errors found, generating improved code")
                
                # Enhanced Generator for improvements if available
                if self.has_enhanced_generator:
                    logger.info("Using Enhanced Generator for code quality improvements")
                    try:
                        focus_areas = self._determine_improvement_focus(requirements, iteration)
                        
                        improved_files = await self.enhanced_code_generator.enhance_code_quality(
                            code_files=previous_files,
                            quality_focus=focus_areas,
                            provider=provider
                        )
                        logger.info(f"Enhanced Generator improved code with focus: {', '.join(focus_areas)}")
                        
                        # Apply structured organization
                        return await self._apply_structured_organization_updated(improved_files, requirements, project_name)
                        
                    except Exception as e:
                        logger.warning(f"Enhanced Generator improvement failed: {e}, falling back to standard")
                
                # Standard improvement
                improved_files = await self._generate_improved_code(
                    requirements, provider, previous_files, iteration
                )
                
                # Apply structured organization
                return await self._apply_structured_organization_updated(improved_files, requirements, project_name)

    # 2. AGGIUNGI questi metodi specifici per updated_orchestrator:

    async def _generate_initial_code_structured(self, 
                                            requirements: Dict[str, Any], 
                                            provider: str) -> Dict[str, str]:
        """Generate initial code for first iteration with enhanced structure support"""
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        # Use enhanced generator if available
        if self.has_enhanced_generator:
            logger.info("Using Enhanced Generator for initial code generation")
            try:
                enhanced_result = await self.enhanced_code_generator.generate_complete_project_enhanced(
                    requirements=requirements,
                    provider=provider,
                    max_iterations=1
                )
                
                if enhanced_result["success"]:
                    return enhanced_result["code_files"]
            except Exception as e:
                logger.warning(f"Enhanced Generator failed for initial generation: {e}")
        
        # Fallback to standard generation
        if project_type == "frontend":
            return await self.code_generator.generate_react_app(requirements, provider)
        elif project_type == "backend":
            return await self.code_generator.generate_backend_api(requirements, provider)
        else:
            # Fullstack or mixed
            return await self.code_generator.generate_code(requirements, provider, 1)

    async def _generate_code_with_fixes_structured(self,
                                                requirements: Dict[str, Any],
                                                provider: str,
                                                errors: List[Dict[str, Any]],
                                                existing_files: Dict[str, str],
                                                iteration: int) -> Dict[str, str]:
        """Generate code with specific fixes for errors - structured version"""
        logger.info(f"Generating structured code with fixes for {len(errors)} errors")
        
        # Create enhanced system prompt with error context and structure awareness
        system_prompt = f"""You are an expert software engineer fixing code issues in iteration {iteration}.
        
        CRITICAL: You must fix the following specific errors while maintaining all existing functionality:
        
        {self._format_errors_for_prompt(errors)}
        
        STRUCTURE REQUIREMENTS:
        - Backend files should be organized in backend/ directory
        - Frontend files should be organized in frontend/ directory  
        - Maintain clean separation between backend and frontend code
        - Ensure all import paths are correct for the new structure
        
        Focus on:
        1. Fixing compilation errors (highest priority)
        2. Resolving import and dependency issues with correct paths
        3. Correcting syntax errors
        4. Maintaining existing working code
        5. Ensuring proper file organization
        
        Make minimal changes to fix the issues. Do not rewrite working code.
        """
        
        # Create focused prompt for fixing specific issues
        prompt = self._create_error_fixing_prompt_structured(requirements, errors, existing_files, iteration)
        
        # Generate fixed code
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Extract and merge with existing files
        fixed_files = self._extract_files(response)
        
        # Merge with existing files (prioritize fixes)
        merged_files = dict(existing_files) if existing_files else {}
        merged_files.update(fixed_files)
        
        return merged_files

    def _create_error_fixing_prompt_structured(self,
                                            requirements: Dict[str, Any],
                                            errors: List[Dict[str, Any]],
                                            existing_files: Dict[str, str],
                                            iteration: int) -> str:
        """Create a focused prompt for fixing specific errors with structure awareness"""
        
        # Group errors by file for focused fixing
        errors_by_file = {}
        for error in errors:
            file_path = error.get('file', 'unknown')
            if file_path not in errors_by_file:
                errors_by_file[file_path] = []
            errors_by_file[file_path].append(error)
        
        # Create file context section with structure awareness
        file_context = ""
        for file_path, file_errors in errors_by_file.items():
            if file_path != 'unknown' and file_path in existing_files:
                content = existing_files[file_path]
                # Truncate very large files
                if len(content) > 2000:
                    content = content[:1000] + "\n... [content truncated] ...\n" + content[-1000:]
                
                file_context += f"\n## File: {file_path}\n"
                file_context += f"Errors in this file:\n"
                for error in file_errors:
                    file_context += f"- Line {error.get('line', '?')}: {error.get('message', '')}\n"
                file_context += f"\nCurrent content:\n```\n{content}\n```\n"
        
        return f"""# Structured Code Fixing Task - Iteration {iteration}

    ## Project Requirements
    {json.dumps(requirements, indent=2)}

    ## Target Structure
    - Backend files: backend/ directory
    - Frontend files: frontend/ directory
    - Clean separation and proper import paths

    ## Errors to Fix
    {self._format_errors_for_prompt(errors)}

    ## Files Requiring Changes
    {file_context}

    ## Instructions
    1. Fix ONLY the reported errors
    2. Maintain all existing functionality
    3. Make minimal changes
    4. Ensure all imports and dependencies are correct for structured layout
    5. Organize files properly (backend/ vs frontend/)
    6. Test that fixes don't break other parts

    ## Response Format
    For each file that needs changes, provide the complete corrected content with proper structure:

    FILE: proper/structured/path/to/file.ext
    ```language
    [complete corrected file content with proper imports]
    ```

    Focus on the most critical errors first (compilation, syntax, imports) and ensure proper file organization.
    """

    async def _apply_structured_organization_updated(self, 
                                                raw_files: Dict[str, str], 
                                                requirements: Dict[str, Any],
                                                project_name: str) -> Dict[str, str]:
        """
        🔥 NEW: Apply structured organization specifically for updated_orchestrator
        """
        logger.info("Applying structured organization to generated files")
        
        # Clean project name
        clean_project_name = self._clean_project_name_updated(
            requirements.get("project_name", project_name)
        )
        
        # Organize files into structure
        structured_files = self._organize_files_into_structure_updated(
            raw_files, clean_project_name, requirements
        )
        
        # Create test environment
        test_env_files = self._create_test_environment_updated(
            structured_files, clean_project_name, requirements
        )
        structured_files.update(test_env_files)
        
        # Create support files
        support_files = self._create_support_files_updated(requirements, clean_project_name)
        structured_files.update(support_files)
        
        logger.info(f"Structured organization complete: {len(structured_files)} total files")
        
        return structured_files

    def _clean_project_name_updated(self, project_name: str) -> str:
        """Clean project name for updated orchestrator"""
        import re
        clean_name = re.sub(r'[^a-zA-Z0-9\-_]', '', str(project_name).lower())
        if not clean_name:
            clean_name = "generated-project"
        return clean_name

    def _organize_files_into_structure_updated(self, 
                                            raw_files: Dict[str, str], 
                                            clean_project_name: str,
                                            requirements: Dict[str, Any]) -> Dict[str, str]:
        """Organize files into project-xyz structure for updated orchestrator"""
        structured_files = {}
        project_prefix = f"project-{clean_project_name}"
        
        # Determine tech stack
        tech_stack = requirements.get("tech_stack", {})
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        has_backend = (tech_stack.get("backend") or 
                    project_type in ["backend", "fullstack"] or 
                    "backend" in str(requirements).lower())
        has_frontend = (tech_stack.get("frontend") or 
                        project_type in ["frontend", "fullstack"] or 
                        "frontend" in str(requirements).lower())
        
        # Organize files by type
        for file_path, content in raw_files.items():
            # Skip already structured files
            if file_path.startswith(project_prefix):
                structured_files[file_path] = content
                continue
            
            # Determine file placement
            if self._is_backend_file_updated(file_path):
                if has_backend:
                    new_path = f"{project_prefix}/backend/{file_path}"
                else:
                    new_path = f"{project_prefix}/{file_path}"
            elif self._is_frontend_file_updated(file_path):
                if has_frontend:
                    new_path = f"{project_prefix}/frontend/{file_path}"
                else:
                    new_path = f"{project_prefix}/{file_path}"
            else:
                # General files go to project root
                new_path = f"{project_prefix}/{file_path}"
            
            structured_files[new_path] = content
        
        # Add project README
        structured_files[f"{project_prefix}/README.md"] = self._generate_project_readme_updated(
            requirements, clean_project_name
        )
        
        return structured_files

    def _is_backend_file_updated(self, file_path: str) -> bool:
        """Determine if file is backend for updated orchestrator"""
        backend_indicators = [
            '.py', 'requirements.txt', 'app/', 'api/', 'models/', 'schemas/',
            'database/', 'db/', 'migrations/', 'alembic/', 'fastapi', 'django',
            'flask', 'main.py', 'wsgi.py', 'asgi.py', 'manage.py', 'celery',
            '__pycache__/', '.pyc', 'pytest', 'test_', '_test.py'
        ]
        return any(indicator in file_path.lower() for indicator in backend_indicators)

    def _is_frontend_file_updated(self, file_path: str) -> bool:
        """Determine if file is frontend for updated orchestrator"""
        frontend_indicators = [
            '.tsx', '.jsx', '.ts', '.js', '.css', '.scss', '.html', '.vue',
            'src/', 'public/', 'components/', 'pages/', 'styles/', 'assets/',
            'package.json', 'node_modules/', 'build/', 'dist/', 'webpack',
            'react', 'vue', 'angular', 'next', 'vite', 'tailwind'
        ]
        return any(indicator in file_path.lower() for indicator in frontend_indicators)

    def _create_test_environment_updated(self, 
                                    structured_files: Dict[str, str],
                                    clean_project_name: str,
                                    requirements: Dict[str, Any]) -> Dict[str, str]:
        """Create test environment for updated orchestrator"""
        test_env_files = {}
        project_prefix = f"project-{clean_project_name}"
        
        # Copy all project files to env_test/
        for file_path, content in structured_files.items():
            if file_path.startswith(project_prefix):
                # Remove project prefix for env_test copy
                relative_path = file_path[len(project_prefix)+1:]
                test_env_files[f"env_test/{relative_path}"] = content
        
        # Add Docker configuration
        test_env_files["env_test/docker-compose.test.yml"] = self._generate_test_docker_compose_updated(requirements)
        test_env_files["env_test/Dockerfile.backend"] = self._generate_backend_dockerfile_updated()
        test_env_files["env_test/Dockerfile.frontend"] = self._generate_frontend_dockerfile_updated()
        
        # Add test scripts
        test_env_files["env_test/run_tests.sh"] = self._generate_test_runner_script_updated()
        test_env_files["env_test/test_runner.py"] = self._generate_python_test_runner_updated()
        
        return test_env_files

    def _create_support_files_updated(self, requirements: Dict[str, Any], clean_project_name: str) -> Dict[str, str]:
        """Create support files for updated orchestrator"""
        support_files = {}
        
        # Main requirements.txt
        support_files["requirements.txt"] = self._generate_project_requirements_updated(requirements)
        
        # Environment template
        support_files[".env.template"] = self._generate_env_template_updated(requirements)
        
        # GitIgnore
        support_files[".gitignore"] = '''# Dependencies
    node_modules/
    __pycache__/
    *.pyc
    venv/
    env/
    .venv/

    # IDE
    .vscode/
    .idea/
    *.swp
    *.swo

    # OS
    .DS_Store
    Thumbs.db
    .directory

    # Environment
    .env
    .env.local
    .env.development.local
    .env.test.local
    .env.production.local

    # Build outputs
    build/
    dist/
    *.egg-info/
    .eggs/

    # Test outputs
    .coverage
    .pytest_cache/
    test_report.txt
    integration_test_results.json
    htmlcov/

    # Logs
    *.log
    logs/
    npm-debug.log*
    yarn-debug.log*
    yarn-error.log*

    # Runtime
    .pid
    .seed
    .pid.lock
    '''
        
        return support_files

    def _generate_project_readme_updated(self, requirements: Dict[str, Any], clean_project_name: str) -> str:
        """Generate README for updated orchestrator"""
        project_name = requirements.get("project_name", clean_project_name.title())
        description = requirements.get("description", "Generated by Enhanced Multi-Agent System")
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        return f'''# {project_name}

    {description}

    **Project Type:** {project_type.title()}

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
    chmod +x run_tests.sh
    ./run_tests.sh
    ```

    ## 📁 Project Structure

    ```
    {f"backend/          # Backend application" if project_type in ["backend", "fullstack"] else ""}
    {f"frontend/         # Frontend application" if project_type in ["frontend", "fullstack"] else ""}
    README.md         # This file
    ```

    ## 🧪 Testing

    Tests are executed in the `../env_test` environment which contains:
    - Complete copy of this project
    - Docker configuration for all services
    - Automated test runners
    - Integration test suites

    ## 💻 Development

    This is the clean development version. For testing and deployment, always use the `../env_test` environment.

    ## 🔧 Technology Stack

    {self._format_tech_stack_for_readme(requirements)}

    ---
    *Generated by Enhanced Multi-Agent Orchestrator v2*
    '''

    def _format_tech_stack_for_readme(self, requirements: Dict[str, Any]) -> str:
        """Format tech stack for README"""
        tech_stack = requirements.get("tech_stack", {})
        if not tech_stack:
            return "- Technology stack not specified"
        
        formatted = []
        for key, value in tech_stack.items():
            if value:
                formatted.append(f"- **{key.title()}:** {value}")
        
        return "\n".join(formatted) if formatted else "- Technology stack details not available"

    # Helper methods for Docker and test generation (simplified versions)
    def _generate_test_docker_compose_updated(self, requirements: Dict[str, Any]) -> str:
        """Generate docker-compose for updated orchestrator"""
        return '''version: '3.8'

    services:
    backend:
        build:
        context: .
        dockerfile: Dockerfile.backend
        ports:
        - "8000:8000"
        environment:
        - PYTHONPATH=/app
        - DATABASE_URL=postgresql://test:test@db:5432/test_db
        networks:
        - test-network

    frontend:
        build:
        context: .
        dockerfile: Dockerfile.frontend
        ports:
        - "3000:3000"
        environment:
        - REACT_APP_API_URL=http://backend:8000
        networks:
        - test-network

    db:
        image: postgres:15
        environment:
        - POSTGRES_DB=test_db
        - POSTGRES_USER=test
        - POSTGRES_PASSWORD=test
        networks:
        - test-network

    networks:
    test-network:
        driver: bridge
    '''

    def _generate_backend_dockerfile_updated(self) -> str:
        """Generate backend Dockerfile for updated orchestrator"""
        return '''FROM python:3.11-slim
    WORKDIR /app
    COPY backend/requirements.txt ./requirements.txt
    RUN pip install -r requirements.txt
    COPY backend/ .
    EXPOSE 8000
    CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    '''

    def _generate_frontend_dockerfile_updated(self) -> str:
        """Generate frontend Dockerfile for updated orchestrator"""
        return '''FROM node:18-alpine
    WORKDIR /app
    COPY frontend/package*.json ./
    RUN npm ci
    COPY frontend/ .
    EXPOSE 3000
    CMD ["npm", "start"]
    '''

    def _generate_test_runner_script_updated(self) -> str:
        """Generate test runner script for updated orchestrator"""
        return '''#!/bin/bash
    set -e
    echo "🧪 Starting enhanced test environment..."
    docker-compose -f docker-compose.test.yml up -d
    sleep 30
    echo "🔧 Running tests..."
    python test_runner.py
    echo "✅ Tests completed!"
    docker-compose -f docker-compose.test.yml down
    '''

    def _generate_python_test_runner_updated(self) -> str:
        """Generate Python test runner for updated orchestrator"""
        return '''#!/usr/bin/env python3
    import requests
    import json
    import sys

    def run_tests():
        tests = [
            ("Backend Health", lambda: requests.get("http://localhost:8000/health", timeout=10).status_code == 200),
            ("Frontend Access", lambda: requests.get("http://localhost:3000", timeout=10).status_code == 200),
        ]
        
        results = {}
        for name, test in tests:
            try:
                results[name] = "PASS" if test() else "FAIL"
            except:
                results[name] = "FAIL"
        
        with open("test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        return all(r == "PASS" for r in results.values())

    if __name__ == "__main__":
        sys.exit(0 if run_tests() else 1)
    '''

    def _generate_project_requirements_updated(self, requirements: Dict[str, Any]) -> str:
        """Generate requirements.txt for updated orchestrator"""
        return '''fastapi>=0.104.0
    uvicorn[standard]>=0.24.0
    pydantic>=2.5.0
    python-dotenv>=1.0.0
    requests>=2.31.0
    '''

    def _generate_env_template_updated(self, requirements: Dict[str, Any]) -> str:
        """Generate .env template for updated orchestrator"""
        return '''# Environment Configuration
    DATABASE_URL=postgresql://user:password@localhost:5432/dbname
    SECRET_KEY=your-secret-key-change-in-production
    API_V1_STR=/api/v1
    DEBUG=true
    LOG_LEVEL=INFO
    '''

    def _determine_improvement_focus(self, requirements: Dict[str, Any], iteration: int) -> List[str]:
        """
        🔥 NUOVO: Determina le aree di focus per il miglioramento del codice
        """
        focus_areas = []
        
        # Focus basato sull'iterazione
        iteration_focus = {
            2: ["security", "error_handling"],
            3: ["performance", "optimization"],
            4: ["documentation", "maintainability"],
            5: ["testing", "code_quality"]
        }
        
        base_focus = iteration_focus.get(iteration, ["code_quality"])
        focus_areas.extend(base_focus)
        
        # Focus basato sui requisiti
        tech_stack = requirements.get("tech_stack", {})
        if "database" in str(tech_stack).lower():
            focus_areas.append("performance")
        
        if "authentication" in str(requirements).lower():
            focus_areas.append("security")
        
        features = requirements.get("features", [])
        if len(features) > 5:
            focus_areas.append("maintainability")
        
        # Rimuovi duplicati
        return list(set(focus_areas))
    
    async def _generate_initial_code(self, 
                                   requirements: Dict[str, Any], 
                                   provider: str) -> Dict[str, str]:
        """Generate initial code for first iteration"""
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
        """Generate code with specific fixes for errors"""
        logger.info(f"Generating code with fixes for {len(errors)} errors")
        
        # Create enhanced system prompt with error context
        system_prompt = f"""You are an expert software engineer fixing code issues in iteration {iteration}.
        
        CRITICAL: You must fix the following specific errors while maintaining all existing functionality:
        
        {self._format_errors_for_prompt(errors)}
        
        Focus on:
        1. Fixing compilation errors (highest priority)
        2. Resolving import and dependency issues
        3. Correcting syntax errors
        4. Maintaining existing working code
        
        Make minimal changes to fix the issues. Do not rewrite working code.
        """
        
        # Create focused prompt for fixing specific issues
        prompt = self._create_error_fixing_prompt(requirements, errors, existing_files, iteration)
        
        # Generate fixed code
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Extract and merge with existing files
        fixed_files = self._extract_files(response)
        
        # Merge with existing files (prioritize fixes)
        merged_files = dict(existing_files) if existing_files else {}
        merged_files.update(fixed_files)
        
        return merged_files
    
    async def _generate_improved_code(self,
                                    requirements: Dict[str, Any],
                                    provider: str,
                                    existing_files: Dict[str, str],
                                    iteration: int) -> Dict[str, str]:
        """Generate improved code when no specific errors to fix"""
        logger.info(f"Generating improved code for iteration {iteration}")
        
        # Use the existing code generator with iteration context
        return await self.code_generator.generate_code(
            requirements, provider, iteration, existing_files=existing_files
        )
    
    def _load_previous_iteration_errors(self, 
                                      project_path: Path, 
                                      previous_iteration: int) -> List[Dict[str, Any]]:
        """Load errors from previous iteration for fixing"""
        errors = []
        
        prev_iter_path = project_path / f"iter-{previous_iteration}"
        if not prev_iter_path.exists():
            return errors
        
        # Load from iteration summary
        summary_path = prev_iter_path / "iteration_summary.json"
        if summary_path.exists():
            try:
                with open(summary_path, 'r') as f:
                    summary = json.load(f)
                
                # Extract errors from validation report
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
                                "priority": "high" if issue.get("issue_type") in ["syntax_error", "import_error"] else "medium"
                            })
                
                # Extract errors from compilation report
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
                            "command": error.get("command", ""),
                            "priority": "high"
                        })
                
                # Extract test failures
                if "test_results" in summary and not summary["test_results"].get("success", False):
                    test_results = summary["test_results"]
                    if "failure_analysis" in test_results:
                        for failure in test_results["failure_analysis"]:
                            errors.append({
                                "type": "test_failure",
                                "category": failure.get("category", "unknown"),
                                "file": failure.get("file"),
                                "message": failure.get("error", failure.get("message", "")),
                                "suggestion": failure.get("suggested_fix", ""),
                                "priority": failure.get("severity", "medium")
                            })
                
            except Exception as e:
                logger.warning(f"Could not load iteration summary: {e}")
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        errors.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))
        
        logger.info(f"Loaded {len(errors)} errors from previous iteration")
        return errors
    
    def _format_errors_for_prompt(self, errors: List[Dict[str, Any]]) -> str:
        """Format errors for inclusion in LLM prompt"""
        if not errors:
            return "No specific errors to fix."
        
        formatted = []
        for i, error in enumerate(errors[:10], 1):  # Limit to top 10 errors
            error_text = f"{i}. {error.get('type', 'Unknown').upper()} ERROR"
            if error.get('file'):
                error_text += f" in {error['file']}"
            if error.get('line'):
                error_text += f" at line {error['line']}"
            error_text += f": {error.get('message', 'Unknown error')}"
            if error.get('suggestion'):
                error_text += f"\n   Suggestion: {error['suggestion']}"
            formatted.append(error_text)
        
        return "\n".join(formatted)
    
    def _create_error_fixing_prompt(self,
                                  requirements: Dict[str, Any],
                                  errors: List[Dict[str, Any]],
                                  existing_files: Dict[str, str],
                                  iteration: int) -> str:
        """Create a focused prompt for fixing specific errors"""
        
        # Group errors by file for focused fixing
        errors_by_file = {}
        for error in errors:
            file_path = error.get('file', 'unknown')
            if file_path not in errors_by_file:
                errors_by_file[file_path] = []
            errors_by_file[file_path].append(error)
        
        # Create file context section
        file_context = ""
        for file_path, file_errors in errors_by_file.items():
            if file_path != 'unknown' and file_path in existing_files:
                content = existing_files[file_path]
                # Truncate very large files
                if len(content) > 2000:
                    content = content[:1000] + "\n... [content truncated] ...\n" + content[-1000:]
                
                file_context += f"\n## File: {file_path}\n"
                file_context += f"Errors in this file:\n"
                for error in file_errors:
                    file_context += f"- Line {error.get('line', '?')}: {error.get('message', '')}\n"
                file_context += f"\nCurrent content:\n```\n{content}\n```\n"
        
        return f"""# Code Fixing Task - Iteration {iteration}

## Project Requirements
{json.dumps(requirements, indent=2)}

## Errors to Fix
{self._format_errors_for_prompt(errors)}

## Files Requiring Changes
{file_context}

## Instructions
1. Fix ONLY the reported errors
2. Maintain all existing functionality
3. Make minimal changes
4. Ensure all imports and dependencies are correct
5. Test that fixes don't break other parts

## Response Format
For each file that needs changes, provide the complete corrected content:

FILE: path/to/file.ext
```language
[complete corrected file content]
```

Focus on the most critical errors first (compilation, syntax, imports).
"""
    
    def _extract_files(self, response: str) -> Dict[str, str]:
        """Extract files from LLM response"""
        import re
        
        files = {}
        
        # Pattern: FILE: path followed by code block
        pattern = r'FILE:\s*([^\n]+)\s*\n```(?:\w+)?\s*\n(.*?)\n```'
        matches = re.finditer(pattern, response, re.DOTALL)
        
        for match in matches:
            file_path, content = match.groups()
            file_path = file_path.strip()
            
            # Clean up file path
            if file_path.startswith('./'):
                file_path = file_path[2:]
            
            # Skip invalid paths
            if not file_path or '..' in file_path:
                continue
            
            # Normalize paths
            file_path = file_path.replace('\\', '/')
            files[file_path] = content.strip()
        
        return files
    
    def _cleanup_empty_directories(self, project_path: Path, max_iterations: int):
        """Cleanup empty iteration directories from previous runs"""
        for i in range(1, max_iterations + 1):
            cleanup_path = project_path / f"iter-{i}"
            if cleanup_path.exists() and not any(cleanup_path.rglob("*")):
                import shutil
                shutil.rmtree(cleanup_path)
                logger.info(f"Removed empty directory: {cleanup_path}")
    
    def _update_current_iteration(self, project_path: Path, iteration: int):
        """Update current iteration in project.json"""
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
    
    def request_stop(self):
        """Set the stop flag to request stopping generation"""
        logger.info("Stop requested for UpdatedOrchestratorAgent")
        self.stop_requested = True
    
    async def generate_final_project(self, 
                                   project_path: Path, 
                                   project_name: str) -> Dict[str, Any]:
        """
        Generate final consolidated project from all iterations
        """
        logger.info("Generating final consolidated project")
        
        try:
            # Get iteration statistics
            stats = self.iteration_manager.get_iteration_statistics(project_path)
            
            if stats["total_iterations"] == 0:
                return {
                    "success": False,
                    "error": "No iterations found to consolidate"
                }
            
            # Find the best iteration (most successful)
            best_iteration = self._find_best_iteration(project_path, stats)
            logger.info(f"Selected iteration {best_iteration} as the best result")
            
            # Create final directory
            final_path = project_path / "final"
            if final_path.exists():
                import shutil
                shutil.rmtree(final_path)
            
            final_path.mkdir(parents=True, exist_ok=True)
            
            # Copy best iteration to final
            best_iter_path = project_path / f"iter-{best_iteration}" / project_name
            if best_iter_path.exists():
                import shutil
                shutil.copytree(best_iter_path, final_path / project_name)
            
            # Copy best iteration reports
            best_iter_base = project_path / f"iter-{best_iteration}"
            for report_file in ["validation_report.json", "compilation_report.json", 
                               "test_results.json", "iteration_summary.json"]:
                source_file = best_iter_base / report_file
                if source_file.exists():
                    import shutil
                    shutil.copy2(source_file, final_path / report_file)
            
            # Create final project summary
            final_summary = {
                "project_name": project_name,
                "best_iteration": best_iteration,
                "total_iterations": stats["total_iterations"],
                "final_success": stats["final_success"],
                "statistics": stats,
                "created_at": self._get_current_timestamp()
            }
            
            with open(final_path / "final_summary.json", 'w') as f:
                json.dump(final_summary, f, indent=2)
            
            logger.info(f"Final project created successfully from iteration {best_iteration}")
            
            return {
                "success": True,
                "best_iteration": best_iteration,
                "final_path": str(final_path),
                "statistics": stats,
                "summary": final_summary
            }
        
        except Exception as e:
            logger.error(f"Error generating final project: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _find_best_iteration(self, project_path: Path, stats: Dict[str, Any]) -> int:
        """Find the best iteration to use as final result"""
        
        # Priority 1: Last successful iteration
        for iteration_detail in reversed(stats["iteration_details"]):
            if (iteration_detail["validation_errors"] == 0 and 
                iteration_detail["compilation_success"] and 
                iteration_detail["test_success"]):
                return iteration_detail["iteration"]
        
        # Priority 2: Iteration with fewest validation errors and successful compilation
        best_iteration = 1
        best_score = float('inf')
        
        for iteration_detail in stats["iteration_details"]:
            # Score based on errors (lower is better)
            score = iteration_detail["validation_errors"] * 10
            
            if not iteration_detail["compilation_success"]:
                score += 50  # Heavy penalty for compilation failure
            
            if not iteration_detail["test_success"]:
                score += 20  # Penalty for test failure
            
            if score < best_score:
                best_score = score
                best_iteration = iteration_detail["iteration"]
        
        return best_iteration
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def cleanup_project_iterations(self, 
                                       project_path: Path, 
                                       keep_final: bool = True,
                                       keep_reports: bool = True) -> Dict[str, Any]:
        """
        Clean up all iteration directories, optionally keeping final and reports
        """
        logger.info(f"Cleaning up project iterations at {project_path}")
        
        try:
            iterations_cleaned = 0
            
            # Find all iteration directories
            for item in project_path.iterdir():
                if item.is_dir() and item.name.startswith("iter-"):
                    try:
                        iter_num = int(item.name.split("-")[1])
                        self.iteration_manager.cleanup_iteration(
                            project_path, iter_num, keep_reports=keep_reports
                        )
                        iterations_cleaned += 1
                    except ValueError:
                        continue
                    except Exception as e:
                        logger.error(f"Error cleaning iteration {item.name}: {e}")
            
            # Optionally remove final directory
            if not keep_final:
                final_path = project_path / "final"
                if final_path.exists():
                    import shutil
                    shutil.rmtree(final_path)
                    logger.info("Removed final directory")
            
            return {
                "success": True,
                "iterations_cleaned": iterations_cleaned,
                "kept_final": keep_final,
                "kept_reports": keep_reports
            }
        
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_project_health_report(self, project_path: Path) -> Dict[str, Any]:
        """
        Generate a comprehensive health report for the project
        """
        logger.info("Generating project health report")
        
        try:
            # Get iteration statistics
            stats = self.iteration_manager.get_iteration_statistics(project_path)
            
            # Calculate health metrics
            health_metrics = {
                "overall_health": "unknown",
                "completion_rate": 0.0,
                "error_reduction_rate": 0.0,
                "test_success_rate": 0.0,
                "compilation_success_rate": 0.0
            }
            
            if stats["total_iterations"] > 0:
                # Calculate completion rate
                health_metrics["completion_rate"] = (
                    stats["successful_iterations"] / stats["total_iterations"]
                )
                
                # Calculate test success rate
                successful_tests = sum(
                    1 for detail in stats["iteration_details"] 
                    if detail["test_success"]
                )
                health_metrics["test_success_rate"] = successful_tests / stats["total_iterations"]
                
                # Calculate compilation success rate
                successful_compilations = sum(
                    1 for detail in stats["iteration_details"] 
                    if detail["compilation_success"]
                )
                health_metrics["compilation_success_rate"] = successful_compilations / stats["total_iterations"]
                
                # Calculate error reduction (comparing first and last iteration)
                if len(stats["iteration_details"]) > 1:
                    first_errors = stats["iteration_details"][0]["validation_errors"]
                    last_errors = stats["iteration_details"][-1]["validation_errors"]
                    
                    if first_errors > 0:
                        health_metrics["error_reduction_rate"] = max(0, 
                            (first_errors - last_errors) / first_errors
                        )
                
                # Determine overall health
                if stats["final_success"]:
                    health_metrics["overall_health"] = "excellent"
                elif health_metrics["compilation_success_rate"] >= 0.8:
                    health_metrics["overall_health"] = "good"
                elif health_metrics["compilation_success_rate"] >= 0.5:
                    health_metrics["overall_health"] = "fair"
                else:
                    health_metrics["overall_health"] = "poor"
            
            # Generate recommendations
            recommendations = []
            if health_metrics["compilation_success_rate"] < 0.8:
                recommendations.append("Focus on fixing compilation errors in future iterations")
            if health_metrics["test_success_rate"] < 0.6:
                recommendations.append("Improve test coverage and fix failing tests")
            if health_metrics["error_reduction_rate"] < 0.5:
                recommendations.append("Review error fixing strategy - progress is slow")
            
            if not recommendations:
                recommendations.append("Project health is good - consider adding more comprehensive tests")
            
            return {
                "project_path": str(project_path),
                "statistics": stats,
                "health_metrics": health_metrics,
                "recommendations": recommendations,
                "generated_at": self._get_current_timestamp()
            }
        
        except Exception as e:
            logger.error(f"Error generating health report: {str(e)}")
            return {
                "error": str(e),
                "generated_at": self._get_current_timestamp()
            }