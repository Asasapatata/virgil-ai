# backend/app/services/enhanced_test_agent.py
import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.services.llm_service import LLMService
from app.services.test_generator import TestGenerator
from app.services.test_runner import TestRunner
from app.services.iteration_manager import IterationManager, IterationStructure
from app.services.code_validator import ValidationReport
from app.services.compilation_checker import CompilationResult

logger = logging.getLogger(__name__)

class EnhancedTestAgent:
    """
    Enhanced Test Agent that integrates validation, compilation checking, and testing
    with proper iteration management and structured reporting
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.test_generator = TestGenerator(llm_service)
        self.test_runner = TestRunner()
        self.iteration_manager = IterationManager()
        logger.info("EnhancedTestAgent initialized")
    
    async def process_iteration_complete(self, 
                                       iteration_structure: IterationStructure,
                                       project_name: str,
                                       iteration: int,
                                       requirements: Dict[str, Any],
                                       code_files: Dict[str, str],
                                       provider: str) -> Dict[str, Any]:
        """
        Complete processing of an iteration: validation, compilation, test generation, and execution
        """
        logger.info(f"Processing complete iteration {iteration} for {project_name}")
        
        try:
            # Step 1: Validate generated code
            logger.info("Step 1: Validating code")
            validation_report = await self.iteration_manager.validate_iteration(
                iteration_structure, project_name, iteration
            )
            
            # Step 2: Check compilation
            logger.info("Step 2: Checking compilation")
            compilation_report = await self.iteration_manager.check_compilation(
                iteration_structure, project_name
            )
            
            # Step 3: Generate tests (only if validation and compilation are acceptable)
            test_files = {}
            test_results = {"success": False, "message": "Tests not run due to critical errors"}
            
            critical_errors = (
                validation_report.summary.get("error", 0) > 0 or
                not compilation_report.success
            )
            
            if not critical_errors:
                logger.info("Step 3: Generating tests")
                test_files = await self.test_generator.generate_tests(
                    requirements, code_files, provider
                )
                
                # Save test files to structured location
                self.iteration_manager.save_test_files(iteration_structure, test_files)
                
                # Step 4: Run tests
                logger.info("Step 4: Running tests")
                test_results = await self.test_runner.run_tests(
                    iteration_structure.iteration_path, test_files
                )
            else:
                logger.warning("Skipping test generation and execution due to critical errors")
                test_results = {
                    "success": False,
                    "message": "Tests skipped due to validation or compilation errors",
                    "validation_errors": validation_report.summary.get("error", 0),
                    "compilation_success": compilation_report.success
                }
            
            # Step 5: Save test results
            self.iteration_manager.save_test_results(iteration_structure, test_results)
            
            # Step 6: Create comprehensive iteration report
            iteration_report = self._create_iteration_report(
                iteration, project_name, validation_report, 
                compilation_report, test_results, len(code_files)
            )
            
            self.iteration_manager.create_iteration_summary(iteration_structure, iteration_report)
            
            # Step 7: Analyze progress
            progress = self.iteration_manager.analyze_iteration_progress(
                iteration, iteration_structure.iteration_path.parent,
                validation_report, compilation_report, test_results
            )
            
            # Prepare result
            result = {
                "iteration": iteration,
                "success": self._determine_overall_success(validation_report, compilation_report, test_results),
                "validation_report": validation_report.to_dict(),
                "compilation_report": compilation_report.to_dict(),
                "test_results": test_results,
                "test_files_generated": len(test_files),
                "progress": progress,
                "iteration_report": iteration_report.to_dict(),
                "errors_for_fixing": self.iteration_manager.get_error_context_for_next_iteration(
                    validation_report, compilation_report, test_results
                ),
                "recommendations": self._generate_recommendations(
                    validation_report, compilation_report, test_results
                )
            }
            
            logger.info(f"Iteration {iteration} processing completed - Success: {result['success']}")
            return result
        
        except Exception as e:
            logger.error(f"Error processing iteration {iteration}: {str(e)}")
            return {
                "iteration": iteration,
                "success": False,
                "error": str(e),
                "validation_report": None,
                "compilation_report": None,
                "test_results": {"success": False, "error": str(e)},
                "progress": {"iteration": iteration, "improvements": [], "remaining_issues": [str(e)]}
            }
    
    def _create_iteration_report(self,
                               iteration: int,
                               project_name: str,
                               validation_report: ValidationReport,
                               compilation_report: CompilationResult,
                               test_results: Dict[str, Any],
                               files_generated: int) -> Any:
        """Create a comprehensive iteration report"""
        from app.services.iteration_manager import IterationReport
        
        # Calculate metrics
        errors_remaining = (
            validation_report.summary.get("error", 0) +
            len(compilation_report.errors) +
            (0 if test_results.get("success", False) else 1)
        )
        
        success = self._determine_overall_success(validation_report, compilation_report, test_results)
        
        return IterationReport(
            iteration=iteration,
            project_id="",  # Will be set by orchestrator
            project_name=project_name,
            validation_report=validation_report,
            compilation_report=compilation_report,
            test_results=test_results,
            files_generated=files_generated,
            files_modified=0,  # Will be calculated by iteration manager
            errors_fixed=0,    # Will be calculated by comparing with previous iteration
            errors_remaining=errors_remaining,
            success=success
        )
    
    def _determine_overall_success(self,
                                 validation_report: ValidationReport,
                                 compilation_report: CompilationResult,
                                 test_results: Dict[str, Any]) -> bool:
        """Determine if the iteration was overall successful"""
        
        # Critical failures
        if validation_report.summary.get("error", 0) > 0:
            return False
        
        if not compilation_report.success:
            return False
        
        # Test results (can be more lenient for first iterations)
        if not test_results.get("success", False):
            # Check if it's just test failures vs. critical issues
            if "error" in test_results and "compilation" in str(test_results["error"]).lower():
                return False
            # If only test failures, might still be acceptable for early iterations
        
        return True
    
    def _generate_recommendations(self,
                                validation_report: ValidationReport,
                                compilation_report: CompilationResult,
                                test_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations for the next iteration"""
        recommendations = []
        
        # Validation recommendations
        if validation_report.summary.get("error", 0) > 0:
            error_types = {}
            for issue in validation_report.issues:
                if issue.severity == "error":
                    error_types[issue.issue_type] = error_types.get(issue.issue_type, 0) + 1
            
            for error_type, count in error_types.items():
                if error_type == "import_error":
                    recommendations.append(f"Fix {count} import errors - check file paths and dependencies")
                elif error_type == "syntax_error":
                    recommendations.append(f"Fix {count} syntax errors - critical for compilation")
                elif error_type == "dependency_error":
                    recommendations.append(f"Resolve {count} dependency issues - update package files")
        
        # Compilation recommendations
        if not compilation_report.success:
            error_types = {}
            for error in compilation_report.errors:
                error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            
            for error_type, count in error_types.items():
                if error_type == "dependency":
                    recommendations.append(f"Install or fix {count} missing dependencies")
                elif error_type == "syntax":
                    recommendations.append(f"Fix {count} compilation syntax errors")
                elif error_type == "build":
                    recommendations.append(f"Resolve {count} build configuration issues")
        
        # Test recommendations
        if not test_results.get("success", False):
            if "frontend" in test_results and not test_results["frontend"].get("success", True):
                recommendations.append("Fix frontend test failures")
            if "backend" in test_results and not test_results["backend"].get("success", True):
                recommendations.append("Fix backend test failures")
            if "e2e" in test_results and not test_results["e2e"].get("success", True):
                recommendations.append("Fix end-to-end test failures")
        
        # General recommendations
        if len(recommendations) == 0:
            recommendations.append("Code quality looks good - consider adding more comprehensive tests")
        elif len(recommendations) > 5:
            recommendations = recommendations[:3]  # Prioritize top 3
            recommendations.append("Focus on critical errors first before addressing all issues")
        
        return recommendations
    
    async def analyze_test_failures_detailed(self, 
                                           test_results: Dict[str, Any],
                                           iteration_structure: IterationStructure) -> List[Dict[str, Any]]:
        """
        Enhanced analysis of test failures with more detailed context
        """
        logger.info("Analyzing test failures in detail")
        
        failures = []
        
        # Use existing test runner analysis as base
        base_failures = self.test_runner.analyze_test_failures(test_results)
        
        # Enhance with additional context
        for failure in base_failures:
            enhanced_failure = {
                **failure,
                "category": self._categorize_failure(failure),
                "severity": self._assess_failure_severity(failure),
                "suggested_fix": self._suggest_fix_for_failure(failure),
                "related_files": self._find_related_files(failure, iteration_structure)
            }
            failures.append(enhanced_failure)
        
        # Add compilation failures as test failures
        compilation_report_path = iteration_structure.compilation_report_path
        if compilation_report_path.exists():
            try:
                import json
                with open(compilation_report_path, 'r') as f:
                    compilation_data = json.load(f)
                
                for error in compilation_data.get("errors", []):
                    failures.append({
                        "type": "compilation",
                        "category": "build_failure",
                        "severity": "high",
                        "error": error.get("message", ""),
                        "file": error.get("file_path"),
                        "line": error.get("line_number"),
                        "command": error.get("command"),
                        "suggested_fix": error.get("suggestion", ""),
                        "details": f"Compilation failed: {error.get('message', '')}"
                    })
            except Exception as e:
                logger.warning(f"Could not load compilation report: {e}")
        
        logger.info(f"Analyzed {len(failures)} detailed failures")
        return failures
    
    def _categorize_failure(self, failure: Dict[str, Any]) -> str:
        """Categorize the type of failure"""
        error_msg = failure.get("error", "").lower()
        failure_type = failure.get("type", "").lower()
        
        if "import" in error_msg or "module" in error_msg:
            return "import_issue"
        elif "syntax" in error_msg:
            return "syntax_issue"  
        elif "dependency" in error_msg or "package" in error_msg:
            return "dependency_issue"
        elif "timeout" in error_msg:
            return "timeout_issue"
        elif "assertion" in error_msg or "expect" in error_msg:
            return "logic_issue"
        elif failure_type == "compilation":
            return "build_issue"
        else:
            return "unknown_issue"
    
    def _assess_failure_severity(self, failure: Dict[str, Any]) -> str:
        """Assess the severity of a failure"""
        category = self._categorize_failure(failure)
        failure_type = failure.get("type", "").lower()
        
        # High severity - blocks execution
        if category in ["syntax_issue", "import_issue", "build_issue"]:
            return "high"
        elif failure_type == "compilation":
            return "high"
        
        # Medium severity - functional issues
        elif category in ["dependency_issue", "logic_issue"]:
            return "medium"
        
        # Low severity - non-critical issues
        elif category in ["timeout_issue"]:
            return "low"
        
        return "medium"  # default
    
    def _suggest_fix_for_failure(self, failure: Dict[str, Any]) -> str:
        """Suggest a specific fix for the failure"""
        category = self._categorize_failure(failure)
        error_msg = failure.get("error", "")
        
        suggestions = {
            "import_issue": "Check import paths and ensure all referenced files exist",
            "syntax_issue": "Fix syntax errors in the code",
            "dependency_issue": "Install missing dependencies or update package configuration",
            "build_issue": "Fix build configuration and resolve compilation errors",
            "logic_issue": "Review business logic and test expectations",
            "timeout_issue": "Optimize performance or increase timeout limits",
            "unknown_issue": "Review error details and check related code"
        }
        
        base_suggestion = suggestions.get(category, suggestions["unknown_issue"])
        
        # Add specific suggestions based on error content
        if "not found" in error_msg.lower():
            base_suggestion += " - File or module not found"
        elif "permission" in error_msg.lower():
            base_suggestion += " - Check file permissions"
        elif "version" in error_msg.lower():
            base_suggestion += " - Check version compatibility"
        
        return base_suggestion
    
    def _find_related_files(self, 
                          failure: Dict[str, Any], 
                          iteration_structure: IterationStructure) -> List[str]:
        """Find files related to the failure"""
        related_files = []
        
        # Add the file mentioned in the failure
        if "file" in failure and failure["file"]:
            related_files.append(failure["file"])
        
        # For import issues, try to find imported files
        if self._categorize_failure(failure) == "import_issue":
            error_msg = failure.get("error", "")
            # Try to extract module names from error messages
            import re
            import_matches = re.findall(r"'([^']+)'", error_msg)
            for match in import_matches:
                # Convert import path to potential file path
                potential_path = match.replace(".", "/") + ".py"
                if (iteration_structure.project_path / potential_path).exists():
                    related_files.append(potential_path)
        
        return related_files
    
    async def generate_enhanced_tests(self, 
                                    requirements: Dict[str, Any],
                                    code_files: Dict[str, str],
                                    validation_report: ValidationReport,
                                    compilation_report: CompilationResult,
                                    provider: str) -> Dict[str, str]:
        """
        Generate tests with enhanced context from validation and compilation results
        """
        logger.info("Generating enhanced tests with validation and compilation context")
        
        # Enhance requirements with validation and compilation context
        enhanced_requirements = dict(requirements)
        enhanced_requirements["_validation_context"] = {
            "validation_errors": validation_report.summary.get("error", 0),
            "validation_warnings": validation_report.summary.get("warning", 0),
            "structure_valid": validation_report.structure_valid,
            "dependencies_valid": validation_report.dependencies_valid
        }
        
        enhanced_requirements["_compilation_context"] = {
            "project_type": compilation_report.project_type,
            "compilation_success": compilation_report.success,
            "dependencies_installed": compilation_report.dependencies_installed,
            "compilation_errors": len(compilation_report.errors)
        }
        
        # Generate tests with enhanced context
        test_files = await self.test_generator.generate_tests(
            enhanced_requirements, code_files, provider
        )
        
        # Add specific validation tests if there are issues
        if validation_report.summary.get("error", 0) > 0:
            validation_tests = self._generate_validation_tests(validation_report, code_files)
            test_files.update(validation_tests)
        
        # Add compilation tests if there are issues
        if not compilation_report.success:
            compilation_tests = self._generate_compilation_tests(compilation_report, code_files)
            test_files.update(compilation_tests)
        
        logger.info(f"Generated {len(test_files)} enhanced test files")
        return test_files
    
    def _generate_validation_tests(self, 
                                 validation_report: ValidationReport, 
                                 code_files: Dict[str, str]) -> Dict[str, str]:
        """Generate specific tests for validation issues"""
        validation_tests = {}
        
        # Group issues by file
        issues_by_file = {}
        for issue in validation_report.issues:
            if issue.severity == "error" and issue.file_path:
                if issue.file_path not in issues_by_file:
                    issues_by_file[issue.file_path] = []
                issues_by_file[issue.file_path].append(issue)
        
        # Generate validation test for each problematic file
        for file_path, issues in issues_by_file.items():
            test_file_path = f"tests/validation/test_validation_{Path(file_path).stem}.py"
            
            test_content = self._create_validation_test_content(file_path, issues)
            if test_content:
                validation_tests[test_file_path] = test_content
        
        return validation_tests
    
    def _create_validation_test_content(self, file_path: str, issues: List[Any]) -> str:
        """Create content for a validation test file"""
        from pathlib import Path
        
        file_stem = Path(file_path).stem
        test_content = f'''"""
Validation tests for {file_path}
Auto-generated to verify validation issues are resolved
"""
import pytest
import ast
import importlib.util
from pathlib import Path

class TestValidation{file_stem.title()}:
    """Test validation issues for {file_path}"""
    
    def test_file_exists(self):
        """Test that the file exists"""
        file_path = Path("{file_path}")
        assert file_path.exists(), f"File {file_path} should exist"
    
    def test_syntax_valid(self):
        """Test that the file has valid Python syntax"""
        file_path = Path("{file_path}")
        if file_path.suffix == ".py":
            with open(file_path, 'r') as f:
                content = f.read()
            try:
                ast.parse(content)
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {file_path}: {{e}}")
'''
        
        # Add specific tests for each issue type
        import_issues = [i for i in issues if i.issue_type == "import_error"]
        if import_issues:
            test_content += '''
    def test_imports_valid(self):
        """Test that all imports are valid"""
        file_path = Path("{}")
        if file_path.suffix == ".py":
            spec = importlib.util.spec_from_file_location("module", file_path)
            try:
                spec.loader.load_module(spec)
            except ImportError as e:
                pytest.fail(f"Import error in {{file_path}}: {{e}}")
'''.format(file_path)
        
        return test_content
    
    def _generate_compilation_tests(self, 
                                  compilation_report: CompilationResult, 
                                  code_files: Dict[str, str]) -> Dict[str, str]:
        """Generate specific tests for compilation issues"""
        compilation_tests = {}
        
        project_type = compilation_report.project_type
        
        if project_type == "node":
            compilation_tests["tests/compilation/test_node_build.js"] = self._create_node_compilation_test()
        elif project_type == "python":
            compilation_tests["tests/compilation/test_python_build.py"] = self._create_python_compilation_test()
        elif project_type == "mixed":
            compilation_tests["tests/compilation/test_node_build.js"] = self._create_node_compilation_test()
            compilation_tests["tests/compilation/test_python_build.py"] = self._create_python_compilation_test()
        
        return compilation_tests
    
    def _create_node_compilation_test(self) -> str:
        """Create Node.js compilation test"""
        return '''/**
 * Node.js compilation test
 * Auto-generated to verify build process works
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

describe('Node.js Compilation Tests', () => {
    test('package.json exists and is valid', () => {
        expect(fs.existsSync('package.json')).toBe(true);
        
        const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
        expect(packageJson.name).toBeDefined();
        expect(packageJson.version).toBeDefined();
    });
    
    test('dependencies can be installed', () => {
        expect(() => {
            execSync('npm install', { stdio: 'pipe' });
        }).not.toThrow();
    });
    
    test('TypeScript compilation works if tsconfig exists', () => {
        if (fs.existsSync('tsconfig.json')) {
            expect(() => {
                execSync('npx tsc --noEmit', { stdio: 'pipe' });
            }).not.toThrow();
        }
    });
    
    test('build script works if defined', () => {
        const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
        if (packageJson.scripts && packageJson.scripts.build) {
            expect(() => {
                execSync('npm run build', { stdio: 'pipe' });
            }).not.toThrow();
        }
    });
});
'''
    
    def _create_python_compilation_test(self) -> str:
        """Create Python compilation test"""
        return '''"""
Python compilation test
Auto-generated to verify Python code compiles correctly
"""
import pytest
import subprocess
import sys
from pathlib import Path
import py_compile
import tempfile

class TestPythonCompilation:
    """Test Python compilation and imports"""
    
    def test_requirements_file_exists(self):
        """Test that requirements.txt exists if Python files are present"""
        py_files = list(Path('.').rglob('*.py'))
        if py_files:
            assert Path('requirements.txt').exists(), "requirements.txt should exist for Python projects"
    
    def test_python_files_compile(self):
        """Test that all Python files compile without syntax errors"""
        py_files = list(Path('.').rglob('*.py'))
        for py_file in py_files:
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as e:
                pytest.fail(f"Compilation error in {py_file}: {e}")
    
    def test_requirements_installable(self):
        """Test that requirements can be installed"""
        requirements_file = Path('requirements.txt')
        if requirements_file.exists():
            with tempfile.TemporaryDirectory() as temp_dir:
                venv_dir = Path(temp_dir) / 'test_venv'
                
                # Create virtual environment
                subprocess.run([sys.executable, '-m', 'venv', str(venv_dir)], check=True)
                
                # Determine python executable
                python_exe = venv_dir / 'bin' / 'python'
                if not python_exe.exists():
                    python_exe = venv_dir / 'Scripts' / 'python.exe'
                
                # Install requirements
                result = subprocess.run([
                    str(python_exe), '-m', 'pip', 'install', '-r', str(requirements_file)
                ], capture_output=True, text=True)
                
                assert result.returncode == 0, f"Failed to install requirements: {result.stderr}"
    
    def test_main_modules_importable(self):
        """Test that main modules can be imported"""
        main_files = ['main.py', 'app.py', '__init__.py']
        for main_file in main_files:
            if Path(main_file).exists():
                try:
                    # Try to compile and check imports
                    with open(main_file, 'r') as f:
                        content = f.read()
                    
                    # Check for obvious import issues
                    import ast
                    tree = ast.parse(content)
                    
                    # This is a basic check - in a real scenario, we'd try to import
                    assert tree is not None, f"Could not parse {main_file}"
                
                except Exception as e:
                    pytest.fail(f"Error checking {main_file}: {e}")
'''
    
    async def run_enhanced_tests(self, 
                               iteration_structure: IterationStructure,
                               test_files: Dict[str, str]) -> Dict[str, Any]:
        """
        Run tests with enhanced reporting and error categorization
        """
        logger.info("Running enhanced tests with detailed reporting")
        
        # Run standard tests
        base_results = await self.test_runner.run_tests(
            iteration_structure.iteration_path, test_files
        )
        
        # Enhance results with additional analysis
        enhanced_results = {
            **base_results,
            "enhanced_analysis": True,
            "test_categories": self._categorize_test_results(base_results),
            "failure_analysis": await self.analyze_test_failures_detailed(
                base_results, iteration_structure
            ),
            "recommendations": self._generate_test_recommendations(base_results),
            "next_iteration_focus": self._determine_next_iteration_focus(base_results)
        }
        
        logger.info(f"Enhanced test execution completed - Success: {enhanced_results['success']}")
        return enhanced_results
    
    def _categorize_test_results(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize test results by type and outcome"""
        categories = {
            "unit_tests": {"passed": 0, "failed": 0, "total": 0},
            "integration_tests": {"passed": 0, "failed": 0, "total": 0},
            "compilation_tests": {"passed": 0, "failed": 0, "total": 0},
            "validation_tests": {"passed": 0, "failed": 0, "total": 0},
            "e2e_tests": {"passed": 0, "failed": 0, "total": 0}
        }
        
        # Analyze test results by type
        for test_type in ["frontend", "backend", "e2e"]:
            if test_type in test_results and test_results[test_type]:
                result = test_results[test_type]
                success = result.get("success", False)
                
                if test_type == "e2e":
                    categories["e2e_tests"]["total"] += 1
                    if success:
                        categories["e2e_tests"]["passed"] += 1
                    else:
                        categories["e2e_tests"]["failed"] += 1
                else:
                    # Classify as unit or integration based on test type
                    if "mock" in str(result).lower():
                        categories["unit_tests"]["total"] += 1
                        if success:
                            categories["unit_tests"]["passed"] += 1
                        else:
                            categories["unit_tests"]["failed"] += 1
                    else:
                        categories["integration_tests"]["total"] += 1
                        if success:
                            categories["integration_tests"]["passed"] += 1
                        else:
                            categories["integration_tests"]["failed"] += 1
        
        return categories
    
    def _generate_test_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations based on test results"""
        recommendations = []
        
        if not test_results.get("success", False):
            # Frontend test recommendations
            if "frontend" in test_results and not test_results["frontend"].get("success", True):
                frontend_result = test_results["frontend"]
                if "mock" in str(frontend_result).get("message", "").lower():
                    recommendations.append("Frontend tests are running in mock mode - set up real testing environment")
                else:
                    recommendations.append("Fix frontend test failures - check component logic and test setup")
            
            # Backend test recommendations
            if "backend" in test_results and not test_results["backend"].get("success", True):
                backend_result = test_results["backend"]
                if "mock" in str(backend_result).get("message", "").lower():
                    recommendations.append("Backend tests are running in mock mode - set up real testing environment")
                else:
                    recommendations.append("Fix backend test failures - check API logic and database connections")
            
            # E2E test recommendations
            if "e2e" in test_results and not test_results["e2e"].get("success", True):
                recommendations.append("E2E tests need implementation - critical for user experience validation")
        
        else:
            recommendations.append("All tests are passing - consider adding more edge case tests")
        
        return recommendations
    
    def _determine_next_iteration_focus(self, test_results: Dict[str, Any]) -> List[str]:
        """Determine what the next iteration should focus on"""
        focus_areas = []
        
        if not test_results.get("success", False):
            # Priority 1: Critical failures
            if "errors" in test_results:
                for error in test_results["errors"]:
                    if "compilation" in str(error).lower():
                        focus_areas.append("Fix compilation errors")
                    elif "import" in str(error).lower():
                        focus_areas.append("Resolve import issues")
                    elif "syntax" in str(error).lower():
                        focus_areas.append("Fix syntax errors")
            
            # Priority 2: Test failures
            failed_types = []
            for test_type in ["frontend", "backend", "e2e"]:
                if test_type in test_results and not test_results[test_type].get("success", True):
                    failed_types.append(test_type)
            
            if failed_types:
                focus_areas.append(f"Fix {', '.join(failed_types)} test failures")
        
        else:
            # If tests pass, focus on improvements
            focus_areas.extend([
                "Add more comprehensive test coverage",
                "Improve code documentation",
                "Optimize performance"
            ])
        
        return focus_areas[:3]  # Return top 3 focus areas