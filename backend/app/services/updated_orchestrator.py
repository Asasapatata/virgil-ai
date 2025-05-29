# backend/app/services/updated_orchestrator.py
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from app.services.llm_service import LLMService
from app.services.code_generator import CodeGenerator
from app.services.unified_orchestration_manager import UnifiedOrchestrationManager

logger = logging.getLogger(__name__)

class UpdatedOrchestratorAgent:
    """
    🔥 UPDATED ORCHESTRATOR - Using Unified Components
    
    Specializes in complex orchestrated code generation with iterative improvements.
    Uses unified components for all structure management, file organization, and validation.
    
    Focus: Complex projects with multiple iterations and intelligent error fixing
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.code_generator = CodeGenerator(llm_service)
        
        # 🎯 UNIFIED COMPONENTS
        self.unified_manager = UnifiedOrchestrationManager()
        
        self.stop_requested = False
        
        # Enhanced Generator support
        try:
            from app.services.enhanced_code_generator import EnhancedCodeGenerator
            self.enhanced_code_generator = EnhancedCodeGenerator(llm_service)
            self.has_enhanced_generator = True
        except ImportError:
            self.enhanced_code_generator = None
            self.has_enhanced_generator = False
            
        logger.info("UpdatedOrchestratorAgent initialized with unified components")
    
    async def generate_application_with_enhanced_flow(self, 
                                                    requirements: Dict[str, Any],
                                                    provider: str,
                                                    max_iterations: int,
                                                    project_path: Path,
                                                    progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        🚀 GENERATE WITH ENHANCED FLOW - Using unified components
        
        This method now focuses only on the orchestration logic while
        delegating all structure, organization, and validation to unified components.
        """
        
        # Check for stop request
        stop_file = project_path / "STOP_REQUESTED"
        if stop_file.exists():
            logger.info(f"Stop file found for project {project_path.name}, stopping generation")
            return {"status": "stopped", "reason": "user_requested"}
        
        logger.info(f"🚀 Starting enhanced orchestrated generation with {max_iterations} max iterations")
        
        # Extract and clean project name
        project_name = requirements.get("project", {}).get("name", project_path.name)
        if not project_name or project_name == project_path.name:
            project_name = f"project_{project_path.name}"
        
        # 🎯 CREATE UNIFIED STRUCTURE (replaces all iter-X logic)
        structure = self.unified_manager.create_project_structure(project_path, project_name)
        logger.info(f"🏗️ Unified structure created for: {structure['project_name']}")
        
        # Track project state
        project_state = {
            "iterations_completed": 0,
            "total_errors_fixed": 0,
            "remaining_issues": [],
            "final_success": False,
            "generation_strategy": "enhanced_orchestrated_unified",
            "structure_type": "unified"
        }
        
        # Main iteration loop
        for iteration in range(1, max_iterations + 1):
            logger.info(f"🔄 Starting enhanced iteration {iteration} for {structure['project_name']}")
            
            # Check for stop request
            if stop_file.exists() or self.stop_requested:
                logger.info("Stop requested, interrupting generation")
                return {
                    "status": "stopped",
                    "reason": "user_requested",
                    "iteration": iteration - 1,
                    "project_id": project_path.name,
                    "project_state": project_state,
                    "output_path": str(structure["project_path"])
                }
            
            try:
                # Update current iteration in project.json
                self._update_current_iteration(project_path, iteration)
                
                # Progress callback
                if progress_callback:
                    progress_callback(iteration, f'enhanced_unified_iteration_{iteration}')
                
                # 🔧 GENERATE CODE (orchestrator-specific logic)
                if progress_callback:
                    progress_callback(iteration, 'generating_enhanced_code')
                
                code_files = await self._generate_code_for_enhanced_iteration(
                    requirements, provider, iteration, structure
                )
                
                # 📁 ORGANIZE AND SAVE (unified system)
                files_generated, files_modified = self.unified_manager.organize_and_save_files(
                    structure, code_files, requirements
                )
                
                logger.info(f"✅ Enhanced iteration {iteration}: Generated {files_generated} files, modified {files_modified}")
                
                # 🔍 VALIDATE (unified system)
                if progress_callback:
                    progress_callback(iteration, 'enhanced_validation_testing')
                
                validation_result = await self.unified_manager.validate_iteration(
                    structure, requirements, iteration
                )
                
                # Update project state
                project_state["iterations_completed"] = iteration
                project_state["remaining_issues"] = validation_result.get("errors_for_fixing", [])
                
                # Check if iteration was successful
                if validation_result["success"]:
                    logger.info(f"🎉 Enhanced iteration {iteration} completed successfully!")
                    project_state["final_success"] = True
                    
                    return {
                        "status": "completed",
                        "iteration": iteration,
                        "project_id": project_path.name,
                        "project_name": structure["project_name"],
                        "output_path": str(structure["project_path"]),
                        "project_state": project_state,
                        "final_result": validation_result,
                        "generation_strategy": "enhanced_orchestrated_unified",
                        "structure_type": "unified"
                    }
                
                # Continue to next iteration with error tracking
                logger.info(f"🔄 Enhanced iteration {iteration} had issues, continuing to iteration {iteration + 1}")
                
                # Update error tracking
                prev_errors = len(project_state["remaining_issues"])
                current_errors = len(validation_result.get("errors_for_fixing", []))
                
                if current_errors < prev_errors:
                    project_state["total_errors_fixed"] += (prev_errors - current_errors)
                
                # Check progress
                if iteration > 1 and current_errors >= prev_errors:
                    logger.warning(f"⚠️ No progress in enhanced iteration {iteration}, errors: {current_errors}")
                
            except Exception as e:
                logger.error(f"❌ Error in enhanced iteration {iteration}: {str(e)}")
                
                # If this is the last iteration, return failure
                if iteration == max_iterations:
                    return {
                        "status": "failed",
                        "reason": "iteration_error",
                        "error": str(e),
                        "iteration": iteration,
                        "project_id": project_path.name,
                        "project_state": project_state,
                        "structure_type": "unified"
                    }
                
                # Otherwise, try to continue
                logger.info(f"🔄 Attempting to continue after error in enhanced iteration {iteration}")
                continue
        
        # Max iterations reached
        logger.warning(f"⏱️ Max iterations ({max_iterations}) reached for enhanced orchestration")
        
        final_status = "completed_with_issues"
        if project_state["total_errors_fixed"] > 0:
            final_status = "completed_with_improvements"
        
        return {
            "status": final_status,
            "reason": "max_iterations_reached",
            "iterations": max_iterations,
            "project_id": project_path.name,
            "project_name": structure["project_name"],
            "project_state": project_state,
            "output_path": str(structure["project_path"]),
            "generation_strategy": "enhanced_orchestrated_unified",
            "structure_type": "unified"
        }
    
    async def _generate_code_for_enhanced_iteration(self,
                                                  requirements: Dict[str, Any],
                                                  provider: str,
                                                  iteration: int,
                                                  structure: Dict[str, Path]) -> Dict[str, str]:
        """
        🔧 GENERATE CODE FOR ENHANCED ITERATION
        
        This method focuses purely on code generation logic.
        All file organization and validation is handled by unified components.
        """
        logger.info(f"🔧 Generating enhanced code for iteration {iteration}")
        
        if iteration == 1:
            # First iteration: generate from requirements
            return await self._generate_initial_enhanced_code(requirements, provider)
        else:
            # Subsequent iterations: load previous files and apply fixes/improvements
            existing_files = self.unified_manager.load_previous_files(structure)
            previous_errors = self.unified_manager.load_previous_errors(structure, iteration - 1)
            
            if previous_errors and existing_files:
                logger.info(f"🔧 Found {len(previous_errors)} errors from previous iteration")
                
                # Enhanced Generator fixing if available
                if self.has_enhanced_generator and len(previous_errors) > 0:
                    logger.info("⚡ Using Enhanced Generator for intelligent error fixing")
                    try:
                        fixed_files = await self.enhanced_code_generator.fix_issues(
                            code_files=existing_files,
                            issues=previous_errors,
                            provider=provider,
                            context={
                                "iteration": iteration,
                                "project_type": requirements.get("project", {}).get("type", "fullstack"),
                                "tech_stack": requirements.get("tech_stack", {}),
                                "structure_type": "unified"
                            }
                        )
                        logger.info("✅ Enhanced Generator fixed issues successfully")
                        return fixed_files
                        
                    except Exception as e:
                        logger.warning(f"Enhanced Generator fixing failed: {e}, falling back to standard fixing")
                        
                # Fallback to standard fixing
                return await self._generate_enhanced_fixes(
                    requirements, provider, previous_errors, existing_files, iteration
                )
            else:
                logger.info("🎨 No previous errors found, generating enhanced improvements")
                return await self._generate_enhanced_improvements(
                    requirements, provider, existing_files or {}, iteration
                )

    async def _generate_initial_enhanced_code(self, 
                                            requirements: Dict[str, Any], 
                                            provider: str) -> Dict[str, str]:
        """Generate initial code with enhanced capabilities"""
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        # Use enhanced generator if available
        if self.has_enhanced_generator:
            logger.info("⚡ Using Enhanced Generator for initial code generation")
            try:
                enhanced_result = await self.enhanced_code_generator.generate_complete_project_enhanced(
                    requirements=requirements,
                    provider=provider,
                    max_iterations=1
                )
                
                if enhanced_result["success"]:
                    logger.info("✅ Enhanced Generator produced initial code successfully")
                    return enhanced_result["code_files"]
            except Exception as e:
                logger.warning(f"Enhanced Generator failed for initial generation: {e}")
        
        # Fallback to standard generation
        logger.info("🔧 Using standard code generator for initial code")
        if project_type == "frontend":
            return await self.code_generator.generate_react_app(requirements, provider)
        elif project_type == "backend":
            return await self.code_generator.generate_backend_api(requirements, provider)
        else:
            # Fullstack or mixed
            return await self.code_generator.generate_code(requirements, provider, 1)

    async def _generate_enhanced_fixes(self,
                                     requirements: Dict[str, Any],
                                     provider: str,
                                     errors: List[Dict[str, Any]],
                                     existing_files: Dict[str, str],
                                     iteration: int) -> Dict[str, str]:
        """Generate enhanced fixes for errors"""
        logger.info(f"🔧 Generating enhanced fixes for {len(errors)} errors")
        
        # Use iterative improvement with error context
        return await self.code_generator.generate_iterative_improvement(
            requirements, provider, iteration, errors, existing_files
        )

    async def _generate_enhanced_improvements(self,
                                           requirements: Dict[str, Any],
                                           provider: str,
                                           existing_files: Dict[str, str],
                                           iteration: int) -> Dict[str, str]:
        """Generate enhanced improvements without specific errors"""
        logger.info(f"🎨 Generating enhanced improvements for iteration {iteration}")
        
        # Use enhanced generator if available
        if self.has_enhanced_generator:
            try:
                focus_areas = self._determine_improvement_focus(requirements, iteration)
                logger.info(f"🎯 Enhancement focus areas: {', '.join(focus_areas)}")
                
                improved_files = await self.enhanced_code_generator.enhance_code_quality(
                    code_files=existing_files,
                    quality_focus=focus_areas,
                    provider=provider
                )
                logger.info(f"✅ Enhanced Generator improved code with focus: {', '.join(focus_areas)}")
                return improved_files
                
            except Exception as e:
                logger.warning(f"Enhanced Generator improvement failed: {e}")
        
        # Fallback to standard improvements
        return await self.code_generator.generate_iterative_improvement(
            requirements, provider, iteration, [], existing_files
        )

    def _determine_improvement_focus(self, requirements: Dict[str, Any], iteration: int) -> List[str]:
        """Determine improvement focus areas for enhanced generation"""
        iteration_focus = {
            2: ["security", "error_handling"],
            3: ["performance", "optimization"],
            4: ["documentation", "maintainability"],
            5: ["testing", "code_quality"]
        }
        
        base_focus = iteration_focus.get(iteration, ["code_quality"])
        
        # Add requirements-based focus
        req_str = str(requirements).lower()
        if "authentication" in req_str or "auth" in req_str:
            base_focus.append("security")
        if "database" in req_str or "db" in req_str:
            base_focus.append("performance")
        if "api" in req_str:
            base_focus.append("documentation")
        
        return list(set(base_focus))  # Remove duplicates
    
    def _update_current_iteration(self, project_path: Path, iteration: int):
        """Update current iteration in project.json"""
        try:
            project_json_path = project_path / "project.json"
            if project_json_path.exists():
                import json
                with open(project_json_path, 'r') as f:
                    project_data = json.load(f)
                
                project_data["current_iteration"] = iteration
                project_data["structure_type"] = "unified"
                
                with open(project_json_path, 'w') as f:
                    json.dump(project_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error updating project.json: {str(e)}")
    
    def request_stop(self):
        """Set the stop flag to request stopping generation"""
        logger.info("Stop requested for UpdatedOrchestratorAgent")
        self.stop_requested = True
    
    # 🎯 ENHANCED ORCHESTRATOR SPECIFIC METHODS
    
    async def generate_final_project(self, 
                                   project_path: Path, 
                                   project_name: str) -> Dict[str, Any]:
        """
        Generate final consolidated project using unified structure
        """
        logger.info("🏁 Generating final consolidated project")
        
        try:
            # Create unified structure if not exists
            structure = self.unified_manager.create_project_structure(project_path, project_name)
            
            # Get project status
            project_status = self.unified_manager.get_project_status(structure)
            
            # The project is already in unified structure, so just return status
            return {
                "success": True,
                "final_path": str(structure["project_path"]),
                "project_status": project_status,
                "structure_type": "unified",
                "message": "Project already in unified structure"
            }
        
        except Exception as e:
            logger.error(f"Error generating final project: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_project_iterations(self, 
                                       project_path: Path, 
                                       keep_reports: bool = True) -> Dict[str, Any]:
        """
        Clean up project using unified structure
        """
        logger.info(f"🗑️ Cleaning up project at {project_path}")
        
        try:
            # Determine project name
            project_name = project_path.name
            structure = self.unified_manager.create_project_structure(project_path, project_name)
            
            # Clean up using unified system
            cleanup_result = self.unified_manager.cleanup_project(structure, keep_reports)
            
            return {
                "success": True,
                "cleanup_result": cleanup_result,
                "structure_type": "unified"
            }
        
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_project_health_report(self, project_path: Path) -> Dict[str, Any]:
        """
        Generate comprehensive health report using unified structure
        """
        logger.info("📊 Generating project health report")
        
        try:
            # Determine project name
            project_name = project_path.name
            structure = self.unified_manager.create_project_structure(project_path, project_name)
            
            # Get comprehensive status using unified system
            project_status = self.unified_manager.get_project_status(structure)
            
            # Add orchestrator-specific analysis
            health_report = {
                "generated_at": project_status["timestamp"],
                "orchestrator_type": "enhanced_orchestrated_unified",
                "project_status": project_status,
                
                # Enhanced orchestrator specific metrics
                "orchestrator_analysis": {
                    "specialization": "Complex iterative code generation with intelligent error fixing",
                    "enhanced_generator_available": self.has_enhanced_generator,
                    "recommended_for": ["Complex applications", "Multi-iteration projects", "Error-prone codebases"],
                    "structure_type": "unified"
                }
            }
            
            return health_report
        
        except Exception as e:
            logger.error(f"Error generating health report: {str(e)}")
            return {
                "error": str(e),
                "generated_at": self._get_current_timestamp()
            }
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()