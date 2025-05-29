# backend/app/services/unified_orchestration_manager.py
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from app.services.unified_structure_manager import UnifiedStructureManager
from app.services.unified_file_organizer import UnifiedFileOrganizer
from app.services.unified_test_validator import UnifiedTestValidator

logger = logging.getLogger(__name__)

class UnifiedOrchestrationManager:
    """
    🎯 UNIFIED ORCHESTRATION MANAGER
    
    Coordina tutti i componenti condivisi per tutti gli orchestratori:
    - Gestisce la struttura unificata
    - Organizza i file
    - Esegue validazione e test
    - Fornisce interfaccia comune per tutti gli orchestratori
    
    Usage:
    orchestrator_manager = UnifiedOrchestrationManager()
    result = await orchestrator_manager.process_iteration(
        structure, code_files, requirements, iteration
    )
    """
    
    def __init__(self):
        self.structure_manager = UnifiedStructureManager()
        self.file_organizer = UnifiedFileOrganizer()
        self.test_validator = UnifiedTestValidator()
        logger.info("UnifiedOrchestrationManager initialized with all components")
    
    def create_project_structure(self, project_path: Path, project_name: str) -> Dict[str, Path]:
        """
        🏗️ CREATE PROJECT STRUCTURE - Entry point for all orchestrators
        """
        logger.info(f"🏗️ Creating unified project structure for: {project_name}")
        return self.structure_manager.create_unified_structure(project_path, project_name)
    
    def organize_and_save_files(self,
                               structure: Dict[str, Path],
                               raw_files: Dict[str, str],
                               requirements: Dict[str, Any]) -> tuple[int, int]:
        """
        📁 ORGANIZE AND SAVE FILES - Complete file processing pipeline
        """
        logger.info("📁 Starting unified file organization and saving")
        
        project_name = structure["project_name"]
        
        # Step 1: Organize raw files into unified structure
        organized_files = self.file_organizer.organize_files(raw_files, requirements, project_name)
        logger.info(f"✅ Organized {len(organized_files)} files")
        
        # Step 2: Create env_test environment
        env_test_files = self.file_organizer.create_env_test_copy(organized_files, requirements)
        organized_files.update(env_test_files)
        logger.info(f"🧪 Added {len(env_test_files)} env_test files")
        
        # Step 3: Create support files
        support_files = self.file_organizer.create_support_files(requirements, project_name)
        organized_files.update(support_files)
        logger.info(f"📄 Added {len(support_files)} support files")
        
        # Step 4: Save to unified structure
        files_generated, files_modified = self.structure_manager.save_to_unified_structure(
            structure, organized_files
        )
        
        logger.info(f"💾 Unified save complete: {files_generated} generated, {files_modified} modified")
        return files_generated, files_modified
    
    async def validate_iteration(self,
                               structure: Dict[str, Path],
                               requirements: Dict[str, Any],
                               iteration: int) -> Dict[str, Any]:
        """
        🔍 VALIDATE ITERATION - Complete validation using unified structure
        """
        logger.info(f"🔍 Starting unified validation for iteration {iteration}")
        
        # Load current files from unified structure
        current_files = self.structure_manager.load_from_unified_structure(structure)
        if not current_files:
            logger.error("❌ No files found in unified structure for validation")
            return {
                "success": False,
                "error": "No files found for validation",
                "iteration": iteration
            }
        
        # Run comprehensive validation
        project_name = structure["project_name"]
        validation_result = await self.test_validator.validate_iteration(
            structure, current_files, requirements, iteration, project_name
        )
        
        logger.info(f"✅ Unified validation complete: {'SUCCESS' if validation_result['success'] else 'ISSUES FOUND'}")
        return validation_result
    
    def load_previous_files(self, structure: Dict[str, Path]) -> Optional[Dict[str, str]]:
        """
        📖 LOAD PREVIOUS FILES - From unified structure
        """
        return self.structure_manager.load_from_unified_structure(structure)
    
    def load_previous_errors(self, structure: Dict[str, Path], previous_iteration: int) -> list[Dict[str, Any]]:
        """
        📋 LOAD PREVIOUS ERRORS - From unified reports
        """
        return self.test_validator.load_previous_errors(structure, previous_iteration)
    
    def get_project_status(self, structure: Dict[str, Path]) -> Dict[str, Any]:
        """
        📊 GET PROJECT STATUS - Comprehensive project health check
        """
        logger.info("📊 Generating unified project status")
        
        # Get structure info
        structure_info = self.structure_manager.get_structure_info(structure)
        
        # Get validation summary
        validation_summary = self.test_validator.get_validation_summary(structure)
        
        # Validate structure integrity
        structure_validation = self.structure_manager.validate_structure(structure)
        
        # Combine all status information
        status = {
            "timestamp": datetime.now().isoformat(),
            "project_name": structure["project_name"],
            "structure_type": "unified",
            
            # Structure information
            "structure_info": structure_info,
            "structure_validation": structure_validation,
            
            # Validation summary
            "validation_summary": validation_summary,
            
            # Overall health
            "overall_health": self._calculate_overall_health(
                structure_info, validation_summary, structure_validation
            ),
            
            # Quick stats
            "quick_stats": {
                "total_files": structure_info["file_counts"].get("project_path", 0),
                "test_files": structure_info["file_counts"].get("env_test_path", 0),
                "reports": structure_info["file_counts"].get("reports_path", 0),
                "total_size_mb": structure_info["total_size_mb"],
                "latest_iteration": validation_summary["latest_iteration"],
                "remaining_errors": validation_summary["remaining_critical_errors"]
            }
        }
        
        logger.info(f"📊 Project status: {status['overall_health']}")
        return status
    
    def cleanup_project(self, structure: Dict[str, Path], keep_reports: bool = True) -> Dict[str, Any]:
        """
        🗑️ CLEANUP PROJECT - Clean unified structure
        """
        logger.info("🗑️ Starting unified project cleanup")
        return self.structure_manager.cleanup_structure(structure, keep_reports)
    
    def _calculate_overall_health(self,
                                structure_info: Dict[str, Any],
                                validation_summary: Dict[str, Any],
                                structure_validation: Dict[str, Any]) -> str:
        """Calculate overall project health"""
        
        # Check structure validity
        if not structure_validation["valid"]:
            return "critical"
        
        # Check if project has files
        total_files = sum(structure_info["file_counts"].values())
        if total_files == 0:
            return "empty"
        
        # Check validation status
        remaining_errors = validation_summary["remaining_critical_errors"]
        current_status = validation_summary["current_status"]
        trend = validation_summary["overall_trend"]
        
        # Determine health based on errors and trend
        if remaining_errors == 0 and current_status == "success":
            return "excellent"
        elif remaining_errors <= 2 and trend == "improving":
            return "good"
        elif remaining_errors <= 5 and trend != "worsening":
            return "fair"
        elif remaining_errors > 10 or trend == "worsening":
            return "poor"
        else:
            return "needs_attention"


class SimpleUnifiedOrchestrator:
    """
    🎯 SIMPLE UNIFIED ORCHESTRATOR
    
    Esempio di come usare i componenti unificati.
    Gli orchestratori esistenti possono ereditare da questa classe
    o usare UnifiedOrchestrationManager direttamente.
    """
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.unified_manager = UnifiedOrchestrationManager()
        self.stop_requested = False
        logger.info("SimpleUnifiedOrchestrator initialized")
    
    async def generate_application_unified(self,
                                         requirements: Dict[str, Any],
                                         provider: str,
                                         max_iterations: int,
                                         project_path: Path,
                                         progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        🚀 GENERATE APPLICATION - Using unified components
        
        This shows how any orchestrator can use the unified system:
        1. Create structure
        2. Generate code (orchestrator-specific)
        3. Organize and save files
        4. Validate iteration
        5. Repeat or finish
        """
        
        # Extract project name
        project_name = requirements.get("project", {}).get("name", project_path.name)
        if not project_name:
            project_name = f"project_{project_path.name}"
        
        # 🏗️ CREATE UNIFIED STRUCTURE (once)
        structure = self.unified_manager.create_project_structure(project_path, project_name)
        logger.info(f"🏗️ Unified structure created for: {project_name}")
        
        # Track project state
        project_state = {
            "iterations_completed": 0,
            "total_errors_fixed": 0,
            "final_success": False,
            "structure_type": "unified"
        }
        
        # Main iteration loop
        for iteration in range(1, max_iterations + 1):
            logger.info(f"🔄 Starting unified iteration {iteration}")
            
            if self.stop_requested:
                return {
                    "status": "stopped",
                    "reason": "user_requested",
                    "iteration": iteration - 1,
                    "project_state": project_state
                }
            
            try:
                # Progress callback
                if progress_callback:
                    progress_callback(iteration, f'unified_iteration_{iteration}')
                
                # 🔧 GENERATE CODE (orchestrator-specific)
                # This is where each orchestrator implements its own logic
                code_files = await self._generate_code_for_iteration(
                    requirements, provider, iteration, structure
                )
                
                # 📁 ORGANIZE AND SAVE FILES (unified)
                files_generated, files_modified = self.unified_manager.organize_and_save_files(
                    structure, code_files, requirements
                )
                logger.info(f"💾 Iteration {iteration}: {files_generated} generated, {files_modified} modified")
                
                # 🔍 VALIDATE ITERATION (unified)
                validation_result = await self.unified_manager.validate_iteration(
                    structure, requirements, iteration
                )
                
                # Update project state
                project_state["iterations_completed"] = iteration
                
                # Check success
                if validation_result["success"]:
                    project_state["final_success"] = True
                    logger.info(f"🎉 Unified iteration {iteration} completed successfully!")
                    
                    return {
                        "status": "completed",
                        "iteration": iteration,
                        "project_id": project_path.name,
                        "project_name": project_name,
                        "output_path": str(structure["project_path"]),
                        "project_state": project_state,
                        "final_result": validation_result,
                        "structure_type": "unified"
                    }
                
                # Continue to next iteration
                remaining_errors = len(validation_result.get("errors_for_fixing", []))
                logger.info(f"🔄 Iteration {iteration}: {remaining_errors} errors remaining")
                
            except Exception as e:
                logger.error(f"❌ Error in unified iteration {iteration}: {e}")
                
                if iteration == max_iterations:
                    return {
                        "status": "failed",
                        "error": str(e),
                        "iteration": iteration,
                        "project_state": project_state
                    }
                continue
        
        # Max iterations reached
        return {
            "status": "completed_with_issues",
            "reason": "max_iterations_reached",
            "iterations": max_iterations,
            "project_state": project_state,
            "structure_type": "unified"
        }
    
    async def _generate_code_for_iteration(self,
                                         requirements: Dict[str, Any],
                                         provider: str,
                                         iteration: int,
                                         structure: Dict[str, Path]) -> Dict[str, str]:
        """
        🔧 GENERATE CODE - Orchestrator-specific implementation
        
        Each orchestrator should override this method with their own logic.
        This is a simple example implementation.
        """
        
        if iteration == 1:
            # First iteration: generate from requirements
            return await self._generate_initial_code(requirements, provider)
        else:
            # Subsequent iterations: load previous and fix errors
            existing_files = self.unified_manager.load_previous_files(structure)
            previous_errors = self.unified_manager.load_previous_errors(structure, iteration - 1)
            
            if previous_errors and existing_files:
                return await self._generate_fixes(requirements, provider, previous_errors, existing_files)
            else:
                return await self._generate_improvements(requirements, provider, existing_files or {})
    
    async def _generate_initial_code(self, requirements: Dict[str, Any], provider: str) -> Dict[str, str]:
        """Generate initial code - override in specific orchestrators"""
        # This is a placeholder - each orchestrator implements its own logic
        return {
            "main.py": '''"""
Example generated code
"""
print("Hello from unified orchestrator!")
''',
            "README.md": "# Generated Project\\n\\nThis is an example project."
        }
    
    async def _generate_fixes(self,
                            requirements: Dict[str, Any],
                            provider: str,
                            errors: list[Dict[str, Any]],
                            existing_files: Dict[str, str]) -> Dict[str, str]:
        """Generate fixes for errors - override in specific orchestrators"""
        # This is a placeholder - each orchestrator implements its own logic
        return existing_files
    
    async def _generate_improvements(self,
                                   requirements: Dict[str, Any],
                                   provider: str,
                                   existing_files: Dict[str, str]) -> Dict[str, str]:
        """Generate improvements - override in specific orchestrators"""
        # This is a placeholder - each orchestrator implements its own logic
        return existing_files
    
    def request_stop(self):
        """Request stop for the orchestrator"""
        self.stop_requested = True
        logger.info("Stop requested for SimpleUnifiedOrchestrator")


# 🎯 UTILITY FUNCTIONS FOR ORCHESTRATORS

def create_unified_orchestrator_mixin():
    """
    🔧 MIXIN FOR EXISTING ORCHESTRATORS
    
    Existing orchestrators can use this mixin to add unified capabilities
    without changing their core logic.
    """
    
    class UnifiedOrchestratorMixin:
        """Mixin to add unified capabilities to existing orchestrators"""
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if not hasattr(self, 'unified_manager'):
                self.unified_manager = UnifiedOrchestrationManager()
                logger.info("Added unified capabilities to orchestrator")
        
        def setup_unified_structure(self, project_path: Path, project_name: str) -> Dict[str, Path]:
            """Setup unified structure - call this in your orchestrator"""
            return self.unified_manager.create_project_structure(project_path, project_name)
        
        def save_with_unified_structure(self,
                                      structure: Dict[str, Path],
                                      code_files: Dict[str, str],
                                      requirements: Dict[str, Any]) -> tuple[int, int]:
            """Save files using unified structure - call this instead of manual saving"""
            return self.unified_manager.organize_and_save_files(structure, code_files, requirements)
        
        async def validate_with_unified_system(self,
                                             structure: Dict[str, Path],
                                             requirements: Dict[str, Any],
                                             iteration: int) -> Dict[str, Any]:
            """Validate using unified system - call this instead of manual validation"""
            return await self.unified_manager.validate_iteration(structure, requirements, iteration)
        
        def load_unified_files(self, structure: Dict[str, Path]) -> Optional[Dict[str, str]]:
            """Load files from unified structure"""
            return self.unified_manager.load_previous_files(structure)
        
        def load_unified_errors(self, structure: Dict[str, Path], iteration: int) -> list[Dict[str, Any]]:
            """Load errors from unified structure"""
            return self.unified_manager.load_previous_errors(structure, iteration)
    
    return UnifiedOrchestratorMixin


# 🎯 INTEGRATION HELPERS

class UnifiedIntegrationHelper:
    """
    🔗 INTEGRATION HELPER
    
    Utility methods to help integrate unified system with existing code.
    """
    
    @staticmethod
    def convert_legacy_structure_to_unified(legacy_path: Path, project_name: str) -> Dict[str, Path]:
        """
        Convert legacy iter-X structure to unified structure
        """
        logger.info(f"🔄 Converting legacy structure to unified for: {project_name}")
        
        # Create unified structure
        manager = UnifiedStructureManager()
        unified_structure = manager.create_unified_structure(legacy_path.parent, project_name)
        
        # Copy files from legacy structure if it exists
        if legacy_path.exists():
            try:
                # Load all files from legacy structure
                legacy_files = {}
                for file_path in legacy_path.rglob("*"):
                    if file_path.is_file():
                        relative_path = str(file_path.relative_to(legacy_path))
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                legacy_files[relative_path] = f.read()
                        except:
                            pass
                
                # Save to unified structure
                if legacy_files:
                    manager.save_to_unified_structure(unified_structure, legacy_files)
                    logger.info(f"✅ Converted {len(legacy_files)} files to unified structure")
                
            except Exception as e:
                logger.error(f"❌ Error converting legacy structure: {e}")
        
        return unified_structure
    
    @staticmethod
    def wrap_existing_orchestrator(orchestrator_class):
        """
        🎁 WRAP EXISTING ORCHESTRATOR
        
        Decorator to automatically add unified capabilities to existing orchestrators.
        
        Usage:
        @UnifiedIntegrationHelper.wrap_existing_orchestrator
        class MyExistingOrchestrator:
            # existing code...
        """
        
        class WrappedOrchestrator(orchestrator_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.unified_manager = UnifiedOrchestrationManager()
                logger.info(f"Wrapped {orchestrator_class.__name__} with unified capabilities")
            
            # Add unified methods if they don't exist
            if not hasattr(orchestrator_class, 'setup_unified_structure'):
                def setup_unified_structure(self, project_path: Path, project_name: str):
                    return self.unified_manager.create_project_structure(project_path, project_name)
            
            if not hasattr(orchestrator_class, 'save_with_unified_structure'):
                def save_with_unified_structure(self, structure, code_files, requirements):
                    return self.unified_manager.organize_and_save_files(structure, code_files, requirements)
        
        return WrappedOrchestrator
    
    @staticmethod
    def create_unified_result_format(orchestrator_result: Dict[str, Any], 
                                   structure: Dict[str, Path]) -> Dict[str, Any]:
        """
        📊 CREATE UNIFIED RESULT FORMAT
        
        Standardize result format across all orchestrators.
        """
        
        # Base unified result structure
        unified_result = {
            "status": orchestrator_result.get("status", "unknown"),
            "structure_type": "unified",
            "generation_timestamp": datetime.now().isoformat(),
            
            # Project info
            "project_id": orchestrator_result.get("project_id"),
            "project_name": structure.get("project_name"),
            "output_path": str(structure.get("project_path", "")),
            
            # Generation info  
            "iteration": orchestrator_result.get("iteration", 0),
            "iterations_completed": orchestrator_result.get("iterations_completed", 0),
            "generation_strategy": orchestrator_result.get("generation_strategy", "unknown"),
            
            # Results
            "success": orchestrator_result.get("status") == "completed",
            "final_result": orchestrator_result.get("final_result"),
            "project_state": orchestrator_result.get("project_state"),
            
            # Paths
            "paths": {
                "project_code": str(structure.get("project_path", "")),
                "test_environment": str(structure.get("env_test_path", "")),
                "reports": str(structure.get("reports_path", ""))
            }
        }
        
        # Add original result for reference
        unified_result["original_result"] = orchestrator_result
        
        return unified_result


# 🎯 CONFIGURATION AND SETUP

class UnifiedSystemConfig:
    """
    ⚙️ UNIFIED SYSTEM CONFIGURATION
    
    Configuration settings for the unified system.
    """
    
    # Default structure settings
    DEFAULT_STRUCTURE = {
        "project_prefix": "project-",
        "env_test_dir": "env_test",
        "reports_dir": "reports",
        "support_files": [".env.template", ".gitignore", "requirements.txt"]
    }
    
    # Validation settings
    VALIDATION_CONFIG = {
        "syntax_check_enabled": True,
        "import_check_enabled": True,
        "compilation_check_enabled": True,
        "functional_test_enabled": True,
        "report_retention_days": 30
    }
    
    # File organization settings
    FILE_ORGANIZATION = {
        "backend_indicators": [
            '.py', 'requirements.txt', 'app/', 'api/', 'models/', 'schemas/',
            'database/', 'db/', 'migrations/', 'alembic/', 'fastapi', 'django',
            'flask', 'main.py', 'wsgi.py', 'asgi.py', 'manage.py'
        ],
        "frontend_indicators": [
            '.tsx', '.jsx', '.ts', '.js', '.css', '.scss', '.html', '.vue',
            'src/', 'public/', 'components/', 'pages/', 'styles/', 'assets/',
            'package.json', 'node_modules/', 'build/', 'dist/', 'webpack'
        ],
        "config_indicators": [
            'dockerfile', 'docker-compose', '.env', '.gitignore', 'readme.md',
            'license', 'makefile', '.editorconfig', '.prettierrc'
        ]
    }
    
    @classmethod
    def get_structure_config(cls) -> Dict[str, Any]:
        """Get structure configuration"""
        return cls.DEFAULT_STRUCTURE
    
    @classmethod
    def get_validation_config(cls) -> Dict[str, Any]:
        """Get validation configuration"""
        return cls.VALIDATION_CONFIG
    
    @classmethod
    def get_file_organization_config(cls) -> Dict[str, Any]:
        """Get file organization configuration"""
        return cls.FILE_ORGANIZATION


# 🎯 MONITORING AND METRICS

class UnifiedSystemMonitor:
    """
    📊 UNIFIED SYSTEM MONITOR
    
    Monitoring and metrics collection for the unified system.
    """
    
    def __init__(self):
        self.metrics = {
            "total_projects": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "average_generation_time": 0.0,
            "total_files_generated": 0,
            "orchestrator_usage": {},
            "error_patterns": {}
        }
        logger.info("UnifiedSystemMonitor initialized")
    
    def record_generation_start(self, project_id: str, orchestrator_type: str):
        """Record the start of a generation process"""
        self.metrics["total_projects"] += 1
        
        if orchestrator_type not in self.metrics["orchestrator_usage"]:
            self.metrics["orchestrator_usage"][orchestrator_type] = 0
        self.metrics["orchestrator_usage"][orchestrator_type] += 1
        
        logger.info(f"📊 Generation started: {project_id} with {orchestrator_type}")
    
    def record_generation_complete(self, 
                                 project_id: str, 
                                 result: Dict[str, Any], 
                                 duration_seconds: float):
        """Record the completion of a generation process"""
        
        if result.get("status") == "completed":
            self.metrics["successful_generations"] += 1
        else:
            self.metrics["failed_generations"] += 1
        
        # Update average generation time
        total_gens = self.metrics["successful_generations"] + self.metrics["failed_generations"]
        current_avg = self.metrics["average_generation_time"]
        self.metrics["average_generation_time"] = (
            (current_avg * (total_gens - 1) + duration_seconds) / total_gens
        )
        
        # Count files generated
        files_generated = result.get("project_state", {}).get("files_generated", 0)
        self.metrics["total_files_generated"] += files_generated
        
        logger.info(f"📊 Generation completed: {project_id} - {result.get('status')}")
    
    def record_error_pattern(self, error_type: str, error_category: str):
        """Record error patterns for analysis"""
        pattern_key = f"{error_type}:{error_category}"
        
        if pattern_key not in self.metrics["error_patterns"]:
            self.metrics["error_patterns"][pattern_key] = 0
        self.metrics["error_patterns"][pattern_key] += 1
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        total_gens = self.metrics["successful_generations"] + self.metrics["failed_generations"]
        success_rate = (
            self.metrics["successful_generations"] / total_gens 
            if total_gens > 0 else 0.0
        )
        
        return {
            "total_projects": self.metrics["total_projects"],
            "success_rate": round(success_rate, 2),
            "average_generation_time_minutes": round(self.metrics["average_generation_time"] / 60, 2),
            "total_files_generated": self.metrics["total_files_generated"],
            "most_used_orchestrator": max(self.metrics["orchestrator_usage"], key=self.metrics["orchestrator_usage"].get) if self.metrics["orchestrator_usage"] else "none",
            "top_error_patterns": sorted(
                self.metrics["error_patterns"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        }