# backend/app/services/unified_structure_manager.py
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class UnifiedStructureManager:
    """
    🔥 UNIFIED STRUCTURE MANAGER
    Gestisce SEMPRE la stessa struttura per tutti gli orchestratori:
    - {project-name}/ (codice pulito)
    - env_test/ (copia completa + Docker)
    - reports/ (validation, compilation, test reports)
    """
    
    def __init__(self):
        logger.info("UnifiedStructureManager initialized")
    
    def create_unified_structure(self, project_path: Path, project_name: str) -> Dict[str, Path]:
        """
        🎯 CREATE UNIFIED STRUCTURE - Always the same for all orchestrators
        Returns paths dict for easy access
        """
        clean_name = self._clean_project_name(project_name)
        logger.info(f"📁 Creating unified structure for project: {clean_name}")
        
        # 🎯 UNIFIED PATHS
        structure = {
            "base_path": project_path,
            "project_path": project_path / f"project-{clean_name}",  # Clean code
            "env_test_path": project_path / "env_test",              # Test environment
            "reports_path": project_path / "reports",               # All reports
            "project_name": clean_name,
            "structure_type": "unified"
        }
        
        # Create all directories
        for key, path in structure.items():
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"📂 Created: {path}")
        
        # Clean up any legacy iter-X directories
        self._cleanup_legacy_iterations(project_path)
        
        logger.info(f"✅ Unified structure created: project-{clean_name}/ + env_test/ + reports/")
        return structure
    
    def save_to_unified_structure(self, 
                                structure: Dict[str, Path], 
                                organized_files: Dict[str, str]) -> Tuple[int, int]:
        """
        💾 SAVE TO UNIFIED STRUCTURE - Overwrites previous iterations
        Returns (files_generated, files_modified)
        """
        files_generated = 0
        files_modified = 0
        project_name = structure["project_name"]
        project_prefix = f"project-{project_name}"
        
        logger.info(f"💾 Saving to unified structure: {len(organized_files)} files")
        
        for file_path, content in organized_files.items():
            # Determine target location
            if file_path.startswith("env_test/"):
                # Save to env_test/
                relative_path = file_path[9:]  # Remove "env_test/"
                full_path = structure["env_test_path"] / relative_path
                
            elif file_path.startswith(project_prefix):
                # Save to project-{name}/
                relative_path = file_path[len(project_prefix)+1:]  # Remove "project-{name}/"
                full_path = structure["project_path"] / relative_path
                
            elif file_path in ["requirements.txt", ".env.template", ".gitignore"]:
                # Root support files
                full_path = structure["base_path"] / file_path
                
            else:
                # Default to project path
                full_path = structure["project_path"] / file_path
            
            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists (for counting)
            if full_path.exists():
                files_modified += 1
            else:
                files_generated += 1
            
            # Write file
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.debug(f"💾 Saved: {file_path}")
            except Exception as e:
                logger.error(f"❌ Error saving {file_path}: {e}")
        
        logger.info(f"✅ Unified save complete: {files_generated} generated, {files_modified} modified")
        return files_generated, files_modified
    
    def load_from_unified_structure(self, structure: Dict[str, Path]) -> Optional[Dict[str, str]]:
        """
        📖 LOAD FROM UNIFIED STRUCTURE - Always from project-{name}/
        Returns dict of relative_path -> content
        """
        project_path = structure["project_path"]
        
        if not project_path.exists():
            logger.warning(f"Project path not found: {project_path}")
            return None
        
        files = {}
        try:
            for file_path in project_path.rglob("*"):
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(project_path))
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            files[relative_path] = f.read()
                        logger.debug(f"📖 Loaded: {relative_path}")
                    except Exception as e:
                        logger.warning(f"Could not read {relative_path}: {e}")
            
            logger.info(f"✅ Loaded {len(files)} files from unified structure")
            return files
            
        except Exception as e:
            logger.error(f"❌ Error loading from unified structure: {e}")
            return None
    
    def get_structure_info(self, structure: Dict[str, Path]) -> Dict[str, Any]:
        """
        📊 GET STRUCTURE INFO - Statistics and validation
        """
        info = {
            "structure_type": "unified",
            "project_name": structure["project_name"],
            "paths": {},
            "file_counts": {},
            "total_size_mb": 0.0
        }
        
        # Check each path
        for key, path in structure.items():
            if isinstance(path, Path):
                info["paths"][key] = str(path)
                
                if path.exists():
                    if path.is_dir():
                        file_count = len(list(path.rglob("*")))
                        info["file_counts"][key] = file_count
                        
                        # Calculate size
                        try:
                            total_size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
                            info["total_size_mb"] += total_size / (1024 * 1024)
                        except:
                            pass
                else:
                    info["file_counts"][key] = 0
        
        info["total_size_mb"] = round(info["total_size_mb"], 2)
        return info
    
    def cleanup_structure(self, structure: Dict[str, Path], keep_reports: bool = True) -> Dict[str, Any]:
        """
        🗑️ CLEANUP STRUCTURE - Remove files but keep structure
        """
        logger.info("🗑️ Cleaning up unified structure")
        
        cleanup_result = {
            "cleaned_paths": [],
            "kept_reports": keep_reports,
            "errors": []
        }
        
        try:
            # Clean project code (but keep directory)
            project_path = structure["project_path"]
            if project_path.exists():
                for item in project_path.iterdir():
                    try:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                        cleanup_result["cleaned_paths"].append(str(item))
                    except Exception as e:
                        cleanup_result["errors"].append(f"Error cleaning {item}: {e}")
            
            # Clean env_test (but keep directory)
            env_test_path = structure["env_test_path"]
            if env_test_path.exists():
                for item in env_test_path.iterdir():
                    try:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                        cleanup_result["cleaned_paths"].append(str(item))
                    except Exception as e:
                        cleanup_result["errors"].append(f"Error cleaning {item}: {e}")
            
            # Clean reports (conditionally)
            if not keep_reports:
                reports_path = structure["reports_path"]
                if reports_path.exists():
                    for item in reports_path.iterdir():
                        try:
                            item.unlink()
                            cleanup_result["cleaned_paths"].append(str(item))
                        except Exception as e:
                            cleanup_result["errors"].append(f"Error cleaning {item}: {e}")
            
            logger.info(f"✅ Cleanup complete: {len(cleanup_result['cleaned_paths'])} items removed")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
            cleanup_result["errors"].append(str(e))
        
        return cleanup_result
    
    def _clean_project_name(self, project_name: str) -> str:
        """Clean project name for directory usage"""
        clean_name = re.sub(r'[^a-zA-Z0-9\-_]', '', str(project_name).lower())
        if not clean_name:
            clean_name = "generated-project"
        return clean_name
    
    def _cleanup_legacy_iterations(self, project_path: Path):
        """Remove any old iter-X directories"""
        try:
            for item in project_path.iterdir():
                if item.is_dir() and item.name.startswith("iter-"):
                    logger.info(f"🗑️ Removing legacy iteration: {item}")
                    shutil.rmtree(item)
        except Exception as e:
            logger.warning(f"Could not cleanup legacy iterations: {e}")
    
    def validate_structure(self, structure: Dict[str, Path]) -> Dict[str, Any]:
        """
        ✅ VALIDATE STRUCTURE - Check if structure is correct
        """
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "structure_type": "unified"
        }
        
        required_paths = ["base_path", "project_path", "env_test_path", "reports_path"]
        
        # Check required paths exist
        for path_key in required_paths:
            if path_key not in structure:
                validation["errors"].append(f"Missing required path: {path_key}")
                validation["valid"] = False
                continue
            
            path = structure[path_key]
            if not isinstance(path, Path):
                validation["errors"].append(f"Path {path_key} is not a Path object")
                validation["valid"] = False
                continue
            
            if not path.exists():
                validation["warnings"].append(f"Path does not exist: {path}")
        
        # Check project name
        if "project_name" not in structure:
            validation["errors"].append("Missing project_name in structure")
            validation["valid"] = False
        
        # Check for legacy iter-X directories
        try:
            base_path = structure["base_path"]
            legacy_dirs = [d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("iter-")]
            if legacy_dirs:
                validation["warnings"].append(f"Found {len(legacy_dirs)} legacy iter-X directories")
        except:
            pass
        
        logger.info(f"✅ Structure validation: {'VALID' if validation['valid'] else 'INVALID'}")
        return validation