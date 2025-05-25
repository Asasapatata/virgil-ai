# backend/app/services/project_structure_manager.py
import json
import shutil
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ProjectStructure:
    """Definisce la struttura di un progetto generato"""
    project_id: str
    project_name: str
    base_path: Path
    source_path: Path      # ${project_id}/${project_name} - codice pulito
    tests_path: Path       # ${project_id}/.tests - test isolati
    reports_path: Path     # ${project_id}/.reports - report delle iterazioni
    metadata_path: Path    # ${project_id}/.metadata - metadati del progetto
    snapshots_path: Path   # ${project_id}/.snapshots - snapshot delle iterazioni

class ProjectStructureManager:
    """
    🎯 NUOVO: Gestisce la struttura pulita dei progetti generati
    
    Struttura finale:
    output/
    └── ${project_id}/
        ├── ${project_name}/           # 🎯 CODICE PULITO (quello che conta)
        │   ├── src/
        │   ├── components/
        │   ├── package.json
        │   └── ...
        ├── .tests/                    # 🧪 TEST ISOLATI
        │   ├── unit/
        │   ├── integration/
        │   └── e2e/
        ├── .reports/                  # 📊 REPORT ITERAZIONI
        │   ├── iteration_1.json
        │   ├── iteration_2.json
        │   └── final_report.json
        ├── .metadata/                 # 📋 METADATI
        │   ├── project.json
        │   ├── requirements.yaml
        │   └── generation_log.json
        └── .snapshots/                # 📸 SNAPSHOT ITERAZIONI (opzionale)
            ├── iteration_1/
            ├── iteration_2/
            └── before_iteration_X/
    """
    
    def __init__(self, base_output_path: str = "output"):
        self.base_output_path = Path(base_output_path)
        logger.info("ProjectStructureManager initialized with clean structure approach")
    
    def create_project_structure(self, project_id: str, project_name: str) -> ProjectStructure:
        """
        🎯 Crea la struttura pulita per un nuovo progetto
        """
        logger.info(f"Creating clean project structure for {project_id} / {project_name}")
        
        # Base project directory
        base_path = self.base_output_path / project_id
        
        # Define clean paths
        source_path = base_path / project_name
        tests_path = base_path / ".tests"
        reports_path = base_path / ".reports"
        metadata_path = base_path / ".metadata"
        snapshots_path = base_path / ".snapshots"
        
        # Create directories
        for path in [source_path, tests_path, reports_path, metadata_path, snapshots_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for tests
        (tests_path / "unit").mkdir(exist_ok=True)
        (tests_path / "integration").mkdir(exist_ok=True)
        (tests_path / "e2e").mkdir(exist_ok=True)
        
        structure = ProjectStructure(
            project_id=project_id,
            project_name=project_name,
            base_path=base_path,
            source_path=source_path,
            tests_path=tests_path,
            reports_path=reports_path,
            metadata_path=metadata_path,
            snapshots_path=snapshots_path
        )
        
        logger.info(f"Created clean structure at {base_path}")
        return structure
    
    def save_source_code(self, 
                        structure: ProjectStructure, 
                        code_files: Dict[str, str],
                        iteration: int) -> Tuple[int, int]:
        """
        🎯 Salva il codice nella directory source pulita
        
        Args:
            structure: Struttura del progetto
            code_files: File di codice da salvare
            iteration: Numero iterazione corrente
            
        Returns:
            Tuple[files_created, files_modified]
        """
        logger.info(f"Saving source code for iteration {iteration}")
        
        # 📸 Optional: Create snapshot before modifying
        if iteration > 1:
            self._create_iteration_snapshot(structure, iteration)
        
        files_created = 0
        files_modified = 0
        
        # Save code files to clean source directory
        for file_path, content in code_files.items():
            # Skip test files - they go to tests directory
            if self._is_test_file(file_path):
                continue
                
            full_path = structure.source_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists
            if full_path.exists():
                files_modified += 1
                logger.debug(f"Modified: {file_path}")
            else:
                files_created += 1
                logger.debug(f"Created: {file_path}")
            
            # Write file with error handling
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error writing {file_path}: {e}")
        
        logger.info(f"Source code saved: {files_created} created, {files_modified} modified")
        return files_created, files_modified
    
    def save_test_files(self, 
                       structure: ProjectStructure, 
                       test_files: Dict[str, str]) -> int:
        """
        🧪 Salva i test nella directory tests isolata
        """
        logger.info(f"Saving {len(test_files)} test files")
        
        saved_count = 0
        
        for file_path, content in test_files.items():
            # Determine test category and path
            test_category = self._determine_test_category(file_path)
            clean_path = self._clean_test_path(file_path)
            
            full_path = structure.tests_path / test_category / clean_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                saved_count += 1
                logger.debug(f"Saved test: {full_path}")
            except Exception as e:
                logger.error(f"Error saving test {file_path}: {e}")
        
        logger.info(f"Saved {saved_count} test files")
        return saved_count
    
    def save_iteration_report(self, 
                             structure: ProjectStructure,
                             iteration: int,
                             report_data: Dict[str, Any]) -> None:
        """
        📊 Salva il report di un'iterazione
        """
        logger.info(f"Saving iteration {iteration} report")
        
        report_file = structure.reports_path / f"iteration_{iteration}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
            logger.info(f"Saved iteration report: {report_file}")
        except Exception as e:
            logger.error(f"Error saving iteration report: {e}")
    
    def save_project_metadata(self, 
                             structure: ProjectStructure,
                             project_data: Dict[str, Any]) -> None:
        """
        📋 Salva i metadati del progetto
        """
        logger.info("Saving project metadata")
        
        # Save main project.json
        project_file = structure.metadata_path / "project.json"
        try:
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving project metadata: {e}")
        
        # Save requirements if available
        if "requirements" in project_data:
            requirements_file = structure.metadata_path / "requirements.yaml"
            try:
                import yaml
                with open(requirements_file, 'w', encoding='utf-8') as f:
                    yaml.dump(project_data["requirements"], f, default_flow_style=False)
            except Exception as e:
                logger.warning(f"Could not save requirements.yaml: {e}")
    
    def get_current_source_files(self, structure: ProjectStructure) -> Dict[str, str]:
        """
        📖 Legge tutti i file sorgente attuali dalla directory pulita
        """
        logger.info("Loading current source files")
        
        files = {}
        
        try:
            for file_path in structure.source_path.rglob("*"):
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(structure.source_path))
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            files[relative_path] = f.read()
                    except Exception as e:
                        logger.warning(f"Could not read {relative_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading source files: {e}")
        
        logger.info(f"Loaded {len(files)} source files")
        return files
    
    def create_final_report(self, 
                           structure: ProjectStructure,
                           final_data: Dict[str, Any]) -> None:
        """
        📋 Crea il report finale del progetto
        """
        logger.info("Creating final project report")
        
        # Collect all iteration reports
        iteration_reports = []
        for report_file in structure.reports_path.glob("iteration_*.json"):
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    iteration_reports.append(json.load(f))
            except Exception as e:
                logger.warning(f"Could not load {report_file}: {e}")
        
        # Count source files
        source_files = list(structure.source_path.rglob("*"))
        source_file_count = len([f for f in source_files if f.is_file()])
        
        # Count test files
        test_files = list(structure.tests_path.rglob("*"))
        test_file_count = len([f for f in test_files if f.is_file()])
        
        final_report = {
            "project_id": structure.project_id,
            "project_name": structure.project_name,
            "generation_completed_at": datetime.now().isoformat(),
            "final_status": final_data.get("status", "unknown"),
            "total_iterations": len(iteration_reports),
            "statistics": {
                "source_files": source_file_count,
                "test_files": test_file_count,
                "total_files": source_file_count + test_file_count
            },
            "structure": {
                "source_path": str(structure.source_path),
                "tests_path": str(structure.tests_path),
                "reports_path": str(structure.reports_path)
            },
            "iteration_summary": iteration_reports,
            "final_data": final_data
        }
        
        final_report_file = structure.reports_path / "final_report.json"
        try:
            with open(final_report_file, 'w', encoding='utf-8') as f:
                json.dump(final_report, f, indent=2, default=str)
            logger.info(f"Final report saved: {final_report_file}")
        except Exception as e:
            logger.error(f"Error saving final report: {e}")
    
    def create_project_zip(self, structure: ProjectStructure, include_tests: bool = False) -> Path:
        """
        📦 Crea un ZIP del progetto (solo source o con test)
        """
        logger.info(f"Creating project ZIP (include_tests={include_tests})")
        
        import zipfile
        
        zip_name = f"{structure.project_name}.zip"
        if include_tests:
            zip_name = f"{structure.project_name}_with_tests.zip"
        
        zip_path = structure.base_path / zip_name
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add source files
                for file_path in structure.source_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(structure.source_path)
                        zf.write(file_path, arcname)
                
                # Add tests if requested
                if include_tests:
                    for file_path in structure.tests_path.rglob("*"):
                        if file_path.is_file():
                            arcname = Path("tests") / file_path.relative_to(structure.tests_path)
                            zf.write(file_path, arcname)
            
            logger.info(f"Created ZIP: {zip_path}")
            return zip_path
        
        except Exception as e:
            logger.error(f"Error creating ZIP: {e}")
            raise
    
    def cleanup_project(self, 
                       structure: ProjectStructure,
                       keep_snapshots: bool = False,
                       keep_reports: bool = True) -> None:
        """
        🧹 Pulisce il progetto mantenendo solo l'essenziale
        """
        logger.info("Cleaning up project")
        
        try:
            # Remove snapshots if not needed
            if not keep_snapshots and structure.snapshots_path.exists():
                shutil.rmtree(structure.snapshots_path)
                logger.info("Removed snapshots directory")
            
            # Remove old reports if not needed
            if not keep_reports and structure.reports_path.exists():
                shutil.rmtree(structure.reports_path)
                logger.info("Removed reports directory")
            
            logger.info("Project cleanup completed")
        
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_project_statistics(self, structure: ProjectStructure) -> Dict[str, Any]:
        """
        📊 Ottiene statistiche del progetto
        """
        stats = {
            "project_id": structure.project_id,
            "project_name": structure.project_name,
            "structure_valid": structure.source_path.exists(),
            "source_files": 0,
            "test_files": 0,
            "reports": 0,
            "size_mb": 0.0
        }
        
        try:
            # Count source files
            if structure.source_path.exists():
                source_files = [f for f in structure.source_path.rglob("*") if f.is_file()]
                stats["source_files"] = len(source_files)
            
            # Count test files
            if structure.tests_path.exists():
                test_files = [f for f in structure.tests_path.rglob("*") if f.is_file()]
                stats["test_files"] = len(test_files)
            
            # Count reports
            if structure.reports_path.exists():
                report_files = list(structure.reports_path.glob("*.json"))
                stats["reports"] = len(report_files)
            
            # Calculate total size
            total_size = 0
            for path in [structure.source_path, structure.tests_path, structure.reports_path, structure.metadata_path]:
                if path.exists():
                    for file_path in path.rglob("*"):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
            
            stats["size_mb"] = round(total_size / (1024 * 1024), 2)
        
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
        
        return stats
    
    # === HELPER METHODS ===
    
    def _is_test_file(self, file_path: str) -> bool:
        """Determina se un file è un test"""
        path_lower = file_path.lower()
        test_indicators = [
            '.test.', '_test.', 'test_', '/tests/', '/test/',
            '.spec.', '_spec.', 'spec_', '/specs/', '/spec/',
            'cypress', 'e2e', 'playwright'
        ]
        return any(indicator in path_lower for indicator in test_indicators)
    
    def _determine_test_category(self, file_path: str) -> str:
        """Determina la categoria del test"""
        path_lower = file_path.lower()
        
        if 'e2e' in path_lower or 'cypress' in path_lower or 'playwright' in path_lower:
            return "e2e"
        elif 'integration' in path_lower:
            return "integration"
        else:
            return "unit"
    
    def _clean_test_path(self, file_path: str) -> str:
        """Pulisce il percorso del test rimuovendo prefissi non necessari"""
        # Remove common test directory prefixes
        clean_path = file_path
        
        prefixes_to_remove = ['tests/', 'test/', '__tests__/', 'specs/', 'spec/']
        for prefix in prefixes_to_remove:
            if clean_path.startswith(prefix):
                clean_path = clean_path[len(prefix):]
                break
        
        return clean_path
    
    def _create_iteration_snapshot(self, structure: ProjectStructure, iteration: int) -> None:
        """📸 Crea uno snapshot prima di modificare il codice"""
        logger.debug(f"Creating snapshot before iteration {iteration}")
        
        snapshot_dir = structure.snapshots_path / f"before_iteration_{iteration}"
        
        try:
            if structure.source_path.exists() and any(structure.source_path.iterdir()):
                shutil.copytree(structure.source_path, snapshot_dir, dirs_exist_ok=True)
                logger.debug(f"Snapshot created: {snapshot_dir}")
        except Exception as e:
            logger.warning(f"Could not create snapshot: {e}")
    
    # === MIGRATION METHODS ===
    
    def migrate_from_old_structure(self, 
                                  project_id: str, 
                                  project_name: str,
                                  old_project_path: Path) -> ProjectStructure:
        """
        🔄 Migra un progetto dalla vecchia struttura (iter-1, iter-2...) alla nuova
        """
        logger.info(f"Migrating project {project_id} from old structure")
        
        # Create new structure
        structure = self.create_project_structure(project_id, project_name)
        
        try:
            # Find latest iteration
            iter_dirs = list(old_project_path.glob("iter-*"))
            if not iter_dirs:
                logger.warning("No iteration directories found in old structure")
                return structure
            
            # Get the latest iteration number
            latest_iter = max(iter_dirs, key=lambda x: int(x.name.split("-")[1]))
            logger.info(f"Using latest iteration: {latest_iter}")
            
            # Copy source files
            source_files = {}
            test_files = {}
            
            for file_path in latest_iter.rglob("*"):
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(latest_iter))
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if self._is_test_file(relative_path):
                            test_files[relative_path] = content
                        else:
                            source_files[relative_path] = content
                    
                    except Exception as e:
                        logger.warning(f"Could not read {relative_path}: {e}")
            
            # Save files to new structure
            self.save_source_code(structure, source_files, 1)
            self.save_test_files(structure, test_files)
            
            # Migrate project metadata if exists
            old_project_json = old_project_path / "project.json"
            if old_project_json.exists():
                try:
                    with open(old_project_json, 'r', encoding='utf-8') as f:
                        project_data = json.load(f)
                    self.save_project_metadata(structure, project_data)
                except Exception as e:
                    logger.warning(f"Could not migrate project metadata: {e}")
            
            logger.info(f"Migration completed: {len(source_files)} source files, {len(test_files)} test files")
        
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            raise
        
        return structure