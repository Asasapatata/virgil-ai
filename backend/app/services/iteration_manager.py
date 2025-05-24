# backend/app/services/iteration_manager.py
import json
import logging
import shutil
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from app.services.code_validator import CodeValidator, ValidationReport
from app.services.compilation_checker import CompilationChecker, CompilationResult

logger = logging.getLogger(__name__)

@dataclass
class IterationStructure:
    """Defines the structure for an iteration directory"""
    iteration_path: Path
    project_path: Path
    tests_path: Path
    validation_report_path: Path
    compilation_report_path: Path
    test_results_path: Path
    iteration_summary_path: Path

@dataclass
class IterationReport:
    """Complete report for an iteration"""
    iteration: int
    project_id: str
    project_name: str
    validation_report: ValidationReport
    compilation_report: CompilationResult
    test_results: Optional[Dict[str, Any]] = None
    files_generated: int = 0
    files_modified: int = 0
    errors_fixed: int = 0
    errors_remaining: int = 0
    success: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "validation_report": self.validation_report.to_dict(),
            "compilation_report": self.compilation_report.to_dict(),
            "test_results": self.test_results,
            "files_generated": self.files_generated,
            "files_modified": self.files_modified,
            "errors_fixed": self.errors_fixed,
            "errors_remaining": self.errors_remaining,
            "success": self.success
        }

class IterationManager:
    """
    Manages the structure and validation of code generation iterations
    """
    
    def __init__(self):
        self.code_validator = CodeValidator()
        self.compilation_checker = CompilationChecker()
        logger.info("IterationManager initialized")
    
    def create_iteration_structure(self, 
                                 project_path: Path, 
                                 project_name: str, 
                                 iteration: int) -> IterationStructure:
        """
        Create the directory structure for an iteration
        """
        logger.info(f"Creating iteration {iteration} structure for project {project_name}")
        
        # Main iteration directory
        iteration_path = project_path / f"iter-{iteration}"
        iteration_path.mkdir(parents=True, exist_ok=True)
        
        # Project code directory
        project_code_path = iteration_path / project_name
        project_code_path.mkdir(parents=True, exist_ok=True)
        
        # Tests directory
        tests_path = iteration_path / "tests"
        tests_path.mkdir(parents=True, exist_ok=True)
        
        # Create test subdirectories
        (tests_path / "unit").mkdir(exist_ok=True)
        (tests_path / "integration").mkdir(exist_ok=True)
        (tests_path / "e2e").mkdir(exist_ok=True)
        
        # Report file paths
        validation_report_path = iteration_path / "validation_report.json"
        compilation_report_path = iteration_path / "compilation_report.json"
        test_results_path = iteration_path / "test_results.json"
        iteration_summary_path = iteration_path / "iteration_summary.json"
        
        structure = IterationStructure(
            iteration_path=iteration_path,
            project_path=project_code_path,
            tests_path=tests_path,
            validation_report_path=validation_report_path,
            compilation_report_path=compilation_report_path,
            test_results_path=test_results_path,
            iteration_summary_path=iteration_summary_path
        )
        
        logger.info(f"Created iteration structure at {iteration_path}")
        return structure
    
    def save_generated_code(self, 
                          structure: IterationStructure, 
                          code_files: Dict[str, str],
                          existing_files: Optional[Dict[str, str]] = None) -> Tuple[int, int]:
        """
        Save generated code files to the iteration structure
        Returns: (files_generated, files_modified)
        """
        logger.info(f"Saving {len(code_files)} code files to iteration")
        
        files_generated = 0
        files_modified = 0
        
        for file_path, content in code_files.items():
            # Determine full path in project structure
            full_path = structure.project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file already exists
            if full_path.exists():
                files_modified += 1
                logger.debug(f"Modified: {file_path}")
            else:
                files_generated += 1
                logger.debug(f"Generated: {file_path}")
            
            # Save file
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error saving {file_path}: {e}")
        
        logger.info(f"Saved code files: {files_generated} generated, {files_modified} modified")
        return files_generated, files_modified
    
    def save_test_files(self, 
                       structure: IterationStructure, 
                       test_files: Dict[str, str]) -> int:
        """
        Save test files to the tests directory
        Returns: number of test files saved
        """
        logger.info(f"Saving {len(test_files)} test files")
        
        saved_count = 0
        
        for file_path, content in test_files.items():
            # Determine test category and full path
            test_full_path = self._determine_test_path(structure.tests_path, file_path)
            test_full_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(test_full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                saved_count += 1
                logger.debug(f"Saved test: {test_full_path}")
            except Exception as e:
                logger.error(f"Error saving test {file_path}: {e}")
        
        logger.info(f"Saved {saved_count} test files")
        return saved_count
    
    def _determine_test_path(self, tests_path: Path, file_path: str) -> Path:
        """
        Determine the appropriate path for a test file based on its type
        """
        # Categorize tests by file path patterns
        if 'e2e' in file_path.lower() or 'integration' in file_path.lower():
            if 'e2e' in file_path.lower():
                return tests_path / "e2e" / Path(file_path).name
            else:
                return tests_path / "integration" / Path(file_path).name
        else:
            # Default to unit tests
            return tests_path / "unit" / Path(file_path).name
    
    async def validate_iteration(self, 
                               structure: IterationStructure, 
                               project_name: str, 
                               iteration: int) -> ValidationReport:
        """
        Validate the code in an iteration
        """
        logger.info(f"Validating iteration {iteration}")
        
        # Run code validation
        validation_report = self.code_validator.validate_iteration(
            structure.iteration_path, project_name, iteration
        )
        
        # Save validation report
        try:
            with open(structure.validation_report_path, 'w') as f:
                json.dump(validation_report.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving validation report: {e}")
        
        logger.info(f"Validation completed: {validation_report.summary}")
        return validation_report
    
    async def check_compilation(self, 
                              structure: IterationStructure, 
                              project_name: str) -> CompilationResult:
        """
        Check compilation for the iteration
        """
        logger.info("Checking compilation for iteration")
        
        # Run compilation check
        compilation_report = await self.compilation_checker.check_compilation(
            structure.project_path, project_name
        )
        
        # Save compilation report
        try:
            with open(structure.compilation_report_path, 'w') as f:
                json.dump(compilation_report.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving compilation report: {e}")
        
        logger.info(f"Compilation check completed: Success={compilation_report.success}")
        return compilation_report
    
    def save_test_results(self, 
                         structure: IterationStructure, 
                         test_results: Dict[str, Any]) -> None:
        """
        Save test results to the iteration
        """
        logger.info("Saving test results")
        
        try:
            with open(structure.test_results_path, 'w') as f:
                json.dump(test_results, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving test results: {e}")
    
    def create_iteration_summary(self, 
                               structure: IterationStructure,
                               iteration_report: IterationReport) -> None:
        """
        Create a summary of the iteration
        """
        logger.info(f"Creating summary for iteration {iteration_report.iteration}")
        
        try:
            with open(structure.iteration_summary_path, 'w') as f:
                json.dump(iteration_report.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving iteration summary: {e}")
    
    def analyze_iteration_progress(self, 
                                 current_iteration: int,
                                 project_path: Path,
                                 validation_report: ValidationReport,
                                 compilation_report: CompilationResult,
                                 test_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze progress made in current iteration compared to previous
        """
        logger.info(f"Analyzing progress for iteration {current_iteration}")
        
        progress = {
            "iteration": current_iteration,
            "validation_errors": validation_report.summary.get("error", 0),
            "validation_warnings": validation_report.summary.get("warning", 0),
            "compilation_success": compilation_report.success,
            "compilation_errors": len(compilation_report.errors),
            "test_success": test_results.get("success", False) if test_results else False,
            "improvements": [],
            "remaining_issues": []
        }
        
        # Compare with previous iteration if available
        if current_iteration > 1:
            prev_iteration_path = project_path / f"iter-{current_iteration - 1}"
            prev_validation_path = prev_iteration_path / "validation_report.json"
            prev_compilation_path = prev_iteration_path / "compilation_report.json"
            
            if prev_validation_path.exists():
                try:
                    with open(prev_validation_path, 'r') as f:
                        prev_validation = json.load(f)
                    
                    prev_errors = prev_validation.get("summary", {}).get("error", 0)
                    current_errors = validation_report.summary.get("error", 0)
                    
                    if current_errors < prev_errors:
                        progress["improvements"].append(
                            f"Reduced validation errors from {prev_errors} to {current_errors}"
                        )
                    elif current_errors > prev_errors:
                        progress["remaining_issues"].append(
                            f"Validation errors increased from {prev_errors} to {current_errors}"
                        )
                
                except Exception as e:
                    logger.warning(f"Could not compare with previous validation: {e}")
            
            if prev_compilation_path.exists():
                try:
                    with open(prev_compilation_path, 'r') as f:
                        prev_compilation = json.load(f)
                    
                    prev_success = prev_compilation.get("success", False)
                    current_success = compilation_report.success
                    
                    if current_success and not prev_success:
                        progress["improvements"].append("Fixed compilation issues")
                    elif not current_success and prev_success:
                        progress["remaining_issues"].append("New compilation issues introduced")
                
                except Exception as e:
                    logger.warning(f"Could not compare with previous compilation: {e}")
        
        # Add specific remaining issues
        if validation_report.summary.get("error", 0) > 0:
            progress["remaining_issues"].append(
                f"{validation_report.summary['error']} validation errors need fixing"
            )
        
        if not compilation_report.success:
            progress["remaining_issues"].append("Compilation issues need resolving")
        
        if test_results and not test_results.get("success", False):
            progress["remaining_issues"].append("Test failures need addressing")
        
        logger.info(f"Progress analysis: {len(progress['improvements'])} improvements, "
                   f"{len(progress['remaining_issues'])} issues remaining")
        
        return progress
    
    def get_error_context_for_next_iteration(self, 
                                           validation_report: ValidationReport,
                                           compilation_report: CompilationResult,
                                           test_results: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extract error context to provide to the next iteration for fixing
        """
        logger.info("Extracting error context for next iteration")
        
        errors_for_fixing = []
        
        # Add validation errors
        for issue in validation_report.issues:
            if issue.severity == "error":
                errors_for_fixing.append({
                    "type": "validation",
                    "category": issue.issue_type,
                    "file": issue.file_path,
                    "line": issue.line_number,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                    "priority": "high" if issue.issue_type in ["syntax_error", "import_error"] else "medium"
                })
        
        # Add compilation errors
        for error in compilation_report.errors:
            errors_for_fixing.append({
                "type": "compilation",
                "category": error.error_type,
                "file": error.file_path,
                "line": error.line_number,
                "message": error.message,
                "suggestion": error.suggestion,
                "command": error.command,
                "priority": "high"  # Compilation errors are always high priority
            })
        
        # Add test failures
        if test_results and not test_results.get("success", False):
            # Extract test failures
            if "failures" in test_results:
                for failure in test_results["failures"]:
                    errors_for_fixing.append({
                        "type": "test_failure",
                        "category": failure.get("type", "unknown"),
                        "file": failure.get("file"),
                        "message": failure.get("error", failure.get("message", "")),
                        "details": failure.get("details", ""),
                        "priority": "medium"
                    })
        
        # Sort by priority (high first)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        errors_for_fixing.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))
        
        logger.info(f"Extracted {len(errors_for_fixing)} errors for next iteration")
        return errors_for_fixing
    
    def load_previous_iteration_files(self, 
                                    project_path: Path, 
                                    project_name: str,
                                    iteration: int) -> Optional[Dict[str, str]]:
        """
        Load files from the previous iteration
        """
        if iteration <= 1:
            return None
        
        prev_iteration = iteration - 1
        prev_path = project_path / f"iter-{prev_iteration}" / project_name
        
        if not prev_path.exists():
            logger.warning(f"Previous iteration {prev_iteration} not found")
            return None
        
        logger.info(f"Loading files from iteration {prev_iteration}")
        
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
            logger.error(f"Error loading previous iteration files: {e}")
            return None
        
        logger.info(f"Loaded {len(files)} files from previous iteration")
        return files
    
    def cleanup_iteration(self, 
                         project_path: Path, 
                         iteration: int, 
                         keep_reports: bool = True) -> None:
        """
        Clean up an iteration directory, optionally keeping reports
        """
        logger.info(f"Cleaning up iteration {iteration}")
        
        iteration_path = project_path / f"iter-{iteration}"
        if not iteration_path.exists():
            return
        
        try:
            if keep_reports:
                # Keep only report files
                reports_to_keep = [
                    "validation_report.json",
                    "compilation_report.json", 
                    "test_results.json",
                    "iteration_summary.json"
                ]
                
                # Create temp directory for reports
                temp_reports = iteration_path / "temp_reports"
                temp_reports.mkdir(exist_ok=True)
                
                for report_file in reports_to_keep:
                    source = iteration_path / report_file
                    if source.exists():
                        shutil.copy2(source, temp_reports / report_file)
                
                # Remove all content
                for item in iteration_path.iterdir():
                    if item.name != "temp_reports":
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                
                # Move reports back
                for report_file in temp_reports.iterdir():
                    shutil.move(str(report_file), iteration_path / report_file.name)
                
                # Remove temp directory
                temp_reports.rmdir()
            
            else:
                # Remove entire iteration
                shutil.rmtree(iteration_path)
            
            logger.info(f"Cleaned up iteration {iteration}")
        
        except Exception as e:
            logger.error(f"Error cleaning up iteration {iteration}: {e}")
    
    def get_iteration_statistics(self, project_path: Path) -> Dict[str, Any]:
        """
        Get statistics about all iterations in a project
        """
        logger.info("Gathering iteration statistics")
        
        stats = {
            "total_iterations": 0,
            "successful_iterations": 0,
            "iterations_with_errors": 0,
            "total_files_generated": 0,
            "total_errors_fixed": 0,
            "final_success": False,
            "iteration_details": []
        }
        
        try:
            # Find all iteration directories
            iterations = []
            for item in project_path.iterdir():
                if item.is_dir() and item.name.startswith("iter-"):
                    try:
                        iter_num = int(item.name.split("-")[1])
                        iterations.append(iter_num)
                    except ValueError:
                        continue
            
            iterations.sort()
            stats["total_iterations"] = len(iterations)
            
            # Analyze each iteration
            for iteration in iterations:
                iter_path = project_path / f"iter-{iteration}"
                iter_stats = {
                    "iteration": iteration,
                    "validation_errors": 0,
                    "compilation_success": False,
                    "test_success": False,
                    "files_count": 0
                }
                
                # Load validation report
                validation_path = iter_path / "validation_report.json"
                if validation_path.exists():
                    try:
                        with open(validation_path, 'r') as f:
                            validation_data = json.load(f)
                        iter_stats["validation_errors"] = validation_data.get("summary", {}).get("error", 0)
                        iter_stats["files_count"] = validation_data.get("validated_files", 0)
                    except Exception as e:
                        logger.warning(f"Could not load validation report for iter-{iteration}: {e}")
                
                # Load compilation report
                compilation_path = iter_path / "compilation_report.json"
                if compilation_path.exists():
                    try:
                        with open(compilation_path, 'r') as f:
                            compilation_data = json.load(f)
                        iter_stats["compilation_success"] = compilation_data.get("success", False)
                    except Exception as e:
                        logger.warning(f"Could not load compilation report for iter-{iteration}: {e}")
                
                # Load test results
                test_results_path = iter_path / "test_results.json"
                if test_results_path.exists():
                    try:
                        with open(test_results_path, 'r') as f:
                            test_data = json.load(f)
                        iter_stats["test_success"] = test_data.get("success", False)
                    except Exception as e:
                        logger.warning(f"Could not load test results for iter-{iteration}: {e}")
                
                # Update overall stats
                if iter_stats["validation_errors"] == 0 and iter_stats["compilation_success"] and iter_stats["test_success"]:
                    stats["successful_iterations"] += 1
                
                if iter_stats["validation_errors"] > 0 or not iter_stats["compilation_success"] or not iter_stats["test_success"]:
                    stats["iterations_with_errors"] += 1
                
                stats["total_files_generated"] += iter_stats["files_count"]
                stats["iteration_details"].append(iter_stats)
            
            # Determine final success (last iteration success)
            if stats["iteration_details"]:
                last_iter = stats["iteration_details"][-1]
                stats["final_success"] = (
                    last_iter["validation_errors"] == 0 and 
                    last_iter["compilation_success"] and 
                    last_iter["test_success"]
                )
        
        except Exception as e:
            logger.error(f"Error gathering iteration statistics: {e}")
        
        logger.info(f"Statistics: {stats['total_iterations']} iterations, "
                   f"{stats['successful_iterations']} successful")
        
        return stats
    
    def export_iteration_report(self, 
                              project_path: Path, 
                              iteration: int,
                              format: str = "json") -> Optional[str]:
        """
        Export a comprehensive report for an iteration
        """
        logger.info(f"Exporting iteration {iteration} report in {format} format")
        
        iteration_path = project_path / f"iter-{iteration}"
        if not iteration_path.exists():
            logger.error(f"Iteration {iteration} not found")
            return None
        
        try:
            # Collect all reports
            report_data = {
                "iteration": iteration,
                "timestamp": None,
                "validation": None,
                "compilation": None,
                "tests": None,
                "summary": None
            }
            
            # Load all available reports
            report_files = {
                "validation": "validation_report.json",
                "compilation": "compilation_report.json", 
                "tests": "test_results.json",
                "summary": "iteration_summary.json"
            }
            
            for key, filename in report_files.items():
                file_path = iteration_path / filename
                if file_path.exists():
                    try:
                        with open(file_path, 'r') as f:
                            report_data[key] = json.load(f)
                    except Exception as e:
                        logger.warning(f"Could not load {filename}: {e}")
            
            # Export based on format
            if format.lower() == "json":
                return json.dumps(report_data, indent=2)
            elif format.lower() == "markdown":
                return self._format_report_as_markdown(report_data)
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
        
        except Exception as e:
            logger.error(f"Error exporting iteration report: {e}")
            return None
    
    def _format_report_as_markdown(self, report_data: Dict[str, Any]) -> str:
        """
        Format iteration report as Markdown
        """
        md = f"# Iteration {report_data['iteration']} Report\n\n"
        
        # Validation section
        if report_data["validation"]:
            validation = report_data["validation"]
            md += "## Code Validation\n\n"
            md += f"- **Files Validated**: {validation.get('validated_files', 0)}\n"
            md += f"- **Errors**: {validation.get('summary', {}).get('error', 0)}\n"
            md += f"- **Warnings**: {validation.get('summary', {}).get('warning', 0)}\n"
            md += f"- **Structure Valid**: {validation.get('structure_valid', False)}\n\n"
        
        # Compilation section
        if report_data["compilation"]:
            compilation = report_data["compilation"]
            md += "## Compilation Check\n\n"
            md += f"- **Project Type**: {compilation.get('project_type', 'Unknown')}\n"
            md += f"- **Success**: {compilation.get('success', False)}\n"
            md += f"- **Dependencies Installed**: {compilation.get('dependencies_installed', False)}\n"
            md += f"- **Build Time**: {compilation.get('build_time', 0):.2f}s\n"
            md += f"- **Errors**: {len(compilation.get('errors', []))}\n\n"
        
        # Test results section
        if report_data["tests"]:
            tests = report_data["tests"]
            md += "## Test Results\n\n"
            md += f"- **Overall Success**: {tests.get('success', False)}\n"
            
            for test_type in ["frontend", "backend", "e2e"]:
                if test_type in tests and tests[test_type]:
                    test_result = tests[test_type]
                    md += f"- **{test_type.title()} Tests**: {test_result.get('success', False)}\n"
        
        return md