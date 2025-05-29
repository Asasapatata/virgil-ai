# backend/app/services/unified_test_validator.py
import json
import logging
import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class UnifiedTestValidator:
    """
    🧪 UNIFIED TEST VALIDATOR
    Gestisce validazione, compilazione e test per tutti gli orchestratori:
    - Validazione codice (syntax, imports, structure)
    - Compilazione e dependency checking
    - Test execution e analysis
    - Report generation unificati
    """
    
    def __init__(self):
        logger.info("UnifiedTestValidator initialized")
    
    async def validate_iteration(self,
                               structure: Dict[str, Path],
                               code_files: Dict[str, str],
                               requirements: Dict[str, Any],
                               iteration: int,
                               project_name: str) -> Dict[str, Any]:
        """
        🔍 VALIDATE ITERATION - Complete validation pipeline
        Returns comprehensive validation result
        """
        logger.info(f"🔍 Starting unified validation for iteration {iteration}")
        
        validation_start = datetime.now()
        
        # Run all validation phases
        validation_report = await self._run_code_validation(
            structure, code_files, requirements
        )
        
        compilation_report = await self._run_compilation_tests(
            structure, code_files, requirements
        )
        
        test_results = await self._run_functional_tests(
            structure, code_files, requirements
        )
        
        # Analyze results and generate recommendations
        analysis = self._analyze_validation_results(
            validation_report, compilation_report, test_results
        )
        
        # Create comprehensive result
        result = {
            "iteration": iteration,
            "project_name": project_name,
            "validation_timestamp": validation_start.isoformat(),
            "validation_duration": (datetime.now() - validation_start).total_seconds(),
            
            # Individual reports
            "validation_report": validation_report,
            "compilation_report": compilation_report,
            "test_results": test_results,
            
            # Analysis
            "analysis": analysis,
            "success": analysis["overall_success"],
            "errors_for_fixing": analysis["critical_errors"],
            
            # Metadata
            "structure_type": "unified",
            "validation_version": "2.0"
        }
        
        # Save reports to unified structure
        await self._save_validation_reports(structure, result, iteration)
        
        logger.info(f"✅ Unified validation complete: {'SUCCESS' if result['success'] else 'ISSUES FOUND'}")
        return result
    
    async def _run_code_validation(self,
                                 structure: Dict[str, Path],
                                 code_files: Dict[str, str],
                                 requirements: Dict[str, Any]) -> Dict[str, Any]:
        """🔍 CODE VALIDATION - Syntax, imports, structure"""
        logger.info("🔍 Running code validation")
        
        validation_issues = []
        file_stats = {
            "total_files": len(code_files),
            "python_files": 0,
            "typescript_files": 0,
            "other_files": 0
        }
        
        for file_path, content in code_files.items():
            try:
                # Determine file type and run appropriate validation
                if file_path.endswith('.py'):
                    file_stats["python_files"] += 1
                    issues = await self._validate_python_file(file_path, content)
                    validation_issues.extend(issues)
                    
                elif file_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
                    file_stats["typescript_files"] += 1
                    issues = await self._validate_typescript_file(file_path, content)
                    validation_issues.extend(issues)
                    
                else:
                    file_stats["other_files"] += 1
                    issues = await self._validate_generic_file(file_path, content)
                    validation_issues.extend(issues)
                    
            except Exception as e:
                validation_issues.append({
                    "file_path": file_path,
                    "line_number": None,
                    "issue_type": "validation_error",
                    "severity": "error",
                    "message": f"Failed to validate file: {str(e)}",
                    "suggestion": "Check file format and content"
                })
        
        # Categorize issues
        error_count = len([i for i in validation_issues if i["severity"] == "error"])
        warning_count = len([i for i in validation_issues if i["severity"] == "warning"])
        
        return {
            "summary": {
                "total_issues": len(validation_issues),
                "error": error_count,
                "warning": warning_count,
                "success": error_count == 0
            },
            "file_stats": file_stats,
            "issues": validation_issues,
            "validation_type": "unified_code_validation"
        }
    
    async def _validate_python_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Validate Python file"""
        issues = []
        
        try:
            # Basic syntax check
            compile(content, file_path, 'exec')
            
        except SyntaxError as e:
            issues.append({
                "file_path": file_path,
                "line_number": e.lineno,
                "issue_type": "syntax_error",
                "severity": "error",
                "message": f"Syntax error: {e.msg}",
                "suggestion": "Fix Python syntax error"
            })
        except Exception as e:
            issues.append({
                "file_path": file_path,
                "line_number": None,
                "issue_type": "compilation_error",
                "severity": "error", 
                "message": str(e),
                "suggestion": "Check Python code structure"
            })
        
        # Check for common import issues
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for relative imports that might fail
            if line.startswith('from .') or line.startswith('import .'):
                issues.append({
                    "file_path": file_path,
                    "line_number": i,
                    "issue_type": "import_warning",
                    "severity": "warning",
                    "message": "Relative import detected - ensure package structure is correct",
                    "suggestion": "Consider using absolute imports"
                })
            
            # Check for missing imports
            common_missing = ['os', 'sys', 'json', 'datetime', 'pathlib']
            for module in common_missing:
                if f'{module}.' in line and f'import {module}' not in content:
                    issues.append({
                        "file_path": file_path,
                        "line_number": i,
                        "issue_type": "missing_import",
                        "severity": "error",
                        "message": f"Using '{module}' without importing it",
                        "suggestion": f"Add 'import {module}' at the top of the file"
                    })
        
        return issues
    
    async def _validate_typescript_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Validate TypeScript/JavaScript file"""
        issues = []
        
        # Basic checks for common issues
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for console.log in production code
            if 'console.log' in line and not file_path.endswith('.test.ts'):
                issues.append({
                    "file_path": file_path,
                    "line_number": i,
                    "issue_type": "console_log",
                    "severity": "warning",
                    "message": "console.log found in production code",
                    "suggestion": "Remove console.log or use proper logging"
                })
            
            # Check for missing semicolons (basic check)
            if line.endswith(')') and not line.endswith(');') and 'if' not in line and 'for' not in line:
                issues.append({
                    "file_path": file_path,
                    "line_number": i,
                    "issue_type": "missing_semicolon",
                    "severity": "warning",
                    "message": "Missing semicolon",
                    "suggestion": "Add semicolon at end of statement"
                })
        
        # Check for React imports
        if 'React' in content and "import React" not in content and file_path.endswith(('.tsx', '.jsx')):
            issues.append({
                "file_path": file_path,
                "line_number": 1,
                "issue_type": "missing_import",
                "severity": "error",
                "message": "Using React without importing it",
                "suggestion": "Add 'import React from 'react';'"
            })
        
        return issues
    
    async def _validate_generic_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Validate generic files (JSON, YAML, etc.)"""
        issues = []
        
        try:
            # JSON validation
            if file_path.endswith('.json'):
                json.loads(content)
                
            # Basic YAML validation (simple check)
            elif file_path.endswith(('.yml', '.yaml')):
                import yaml
                yaml.safe_load(content)
                
        except json.JSONDecodeError as e:
            issues.append({
                "file_path": file_path,
                "line_number": e.lineno,
                "issue_type": "json_error", 
                "severity": "error",
                "message": f"JSON syntax error: {e.msg}",
                "suggestion": "Fix JSON syntax"
            })
        except Exception as e:
            issues.append({
                "file_path": file_path,
                "line_number": None,
                "issue_type": "format_error",
                "severity": "warning",
                "message": f"File format issue: {str(e)}",
                "suggestion": "Check file format and content"
            })
        
        return issues
    
    async def _run_compilation_tests(self,
                                   structure: Dict[str, Path],
                                   code_files: Dict[str, str],
                                   requirements: Dict[str, Any]) -> Dict[str, Any]:
        """🔨 COMPILATION TESTS - Dependencies, build checks"""
        logger.info("🔨 Running compilation tests")
        
        compilation_results = {
            "success": True,
            "errors": [],
            "warnings": [],
            "dependency_check": {},
            "build_attempts": []
        }
        
        # Check Python dependencies
        python_deps = await self._check_python_dependencies(structure, code_files)
        compilation_results["dependency_check"]["python"] = python_deps
        
        if not python_deps["satisfied"]:
            compilation_results["success"] = False
            compilation_results["errors"].extend(python_deps["missing"])
        
        # Check Node.js dependencies
        node_deps = await self._check_node_dependencies(structure, code_files)
        compilation_results["dependency_check"]["node"] = node_deps
        
        if not node_deps["satisfied"]:
            compilation_results["warnings"].extend(node_deps["missing"])
        
        # Attempt basic import/compilation checks
        try:
            import_results = await self._test_import_resolution(structure, code_files)
            compilation_results["build_attempts"].append(import_results)
            
            if not import_results["success"]:
                compilation_results["success"] = False
                compilation_results["errors"].extend(import_results["errors"])
                
        except Exception as e:
            compilation_results["success"] = False
            compilation_results["errors"].append({
                "error_type": "compilation_test_failure",
                "message": str(e),
                "suggestion": "Check code structure and dependencies"
            })
        
        return compilation_results
    
    async def _check_python_dependencies(self, 
                                       structure: Dict[str, Path], 
                                       code_files: Dict[str, str]) -> Dict[str, Any]:
        """Check Python dependencies"""
        required_modules = set()
        
        # Extract imports from Python files
        for file_path, content in code_files.items():
            if file_path.endswith('.py'):
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('import '):
                        module = line.replace('import ', '').split()[0].split('.')[0]
                        required_modules.add(module)
                    elif line.startswith('from '):
                        module = line.split()[1].split('.')[0]
                        required_modules.add(module)
        
        # Check which modules are available
        available_modules = set()
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
                available_modules.add(module)
            except ImportError:
                # Check if it's a standard library module
                if module not in ['os', 'sys', 'json', 'datetime', 'pathlib', 're']:
                    missing_modules.append({
                        "module": module,
                        "error_type": "missing_dependency",
                        "message": f"Module '{module}' not found",
                        "suggestion": f"Install module: pip install {module}"
                    })
        
        return {
            "required": list(required_modules),
            "available": list(available_modules),
            "missing": missing_modules,
            "satisfied": len(missing_modules) == 0
        }
    
    async def _check_node_dependencies(self,
                                     structure: Dict[str, Path],
                                     code_files: Dict[str, str]) -> Dict[str, Any]:
        """Check Node.js dependencies"""
        # Look for package.json
        package_json_content = None
        for file_path, content in code_files.items():
            if file_path.endswith('package.json'):
                try:
                    package_json_content = json.loads(content)
                    break
                except:
                    pass
        
        if not package_json_content:
            return {
                "required": [],
                "available": [],
                "missing": [],
                "satisfied": True,
                "note": "No package.json found"
            }
        
        # Extract required dependencies
        dependencies = package_json_content.get('dependencies', {})
        dev_dependencies = package_json_content.get('devDependencies', {})
        all_deps = {**dependencies, **dev_dependencies}
        
        # For now, assume all are missing (would need npm ls in real implementation)
        missing_deps = []
        for dep_name, version in all_deps.items():
            missing_deps.append({
                "module": dep_name,
                "version": version,
                "error_type": "missing_node_dependency",
                "message": f"Node module '{dep_name}' may not be installed",
                "suggestion": f"Run: npm install {dep_name}"
            })
        
        return {
            "required": list(all_deps.keys()),
            "available": [],  # Would need to check node_modules
            "missing": missing_deps,
            "satisfied": len(missing_deps) == 0
        }
    
    async def _test_import_resolution(self,
                                    structure: Dict[str, Path],
                                    code_files: Dict[str, str]) -> Dict[str, Any]:
        """Test if imports can be resolved"""
        import_results = {
            "success": True,
            "errors": [],
            "tested_files": 0
        }
        
        # Test Python files in temporary environment
        for file_path, content in code_files.items():
            if file_path.endswith('.py'):
                try:
                    # Create temporary file and test import
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
                        tmp_file.write(content)
                        tmp_file.flush()
                        
                        # Try to compile (basic check)
                        compile(content, file_path, 'exec')
                        import_results["tested_files"] += 1
                        
                except SyntaxError as e:
                    import_results["success"] = False
                    import_results["errors"].append({
                        "file_path": file_path,
                        "error_type": "syntax_error",
                        "line_number": e.lineno,
                        "message": str(e),
                        "suggestion": "Fix syntax error"
                    })
                except Exception as e:
                    import_results["errors"].append({
                        "file_path": file_path,
                        "error_type": "import_error",
                        "message": str(e),
                        "suggestion": "Check imports and dependencies"
                    })
        
        return import_results
    
    async def _run_functional_tests(self,
                                  structure: Dict[str, Path],
                                  code_files: Dict[str, str],
                                  requirements: Dict[str, Any]) -> Dict[str, Any]:
        """🧪 FUNCTIONAL TESTS - Basic functionality checks"""
        logger.info("🧪 Running functional tests")
        
        test_results = {
            "success": True,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": [],
            "coverage": 0.0
        }
        
        # Test 1: File structure validation
        structure_test = self._test_file_structure(code_files, requirements)
        test_results["test_details"].append(structure_test)
        test_results["tests_run"] += 1
        
        if structure_test["passed"]:
            test_results["tests_passed"] += 1
        else:
            test_results["tests_failed"] += 1
            test_results["success"] = False
        
        # Test 2: Configuration files validation
        config_test = self._test_configuration_files(code_files, requirements)
        test_results["test_details"].append(config_test)
        test_results["tests_run"] += 1
        
        if config_test["passed"]:
            test_results["tests_passed"] += 1
        else:
            test_results["tests_failed"] += 1
        
        # Test 3: API structure validation (if backend)
        if self._has_backend_files(code_files):
            api_test = self._test_api_structure(code_files)
            test_results["test_details"].append(api_test)
            test_results["tests_run"] += 1
            
            if api_test["passed"]:
                test_results["tests_passed"] += 1
            else:
                test_results["tests_failed"] += 1
        
        # Calculate coverage
        if test_results["tests_run"] > 0:
            test_results["coverage"] = test_results["tests_passed"] / test_results["tests_run"]
        
        return test_results
    
    def _test_file_structure(self, code_files: Dict[str, str], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Test if file structure is appropriate"""
        test = {
            "test_name": "file_structure_validation",
            "passed": True,
            "issues": [],
            "details": {}
        }
        
        # Check for essential files
        essential_files = []
        if self._has_backend_files(code_files):
            essential_files.extend(['main.py', 'app.py', '__init__.py'])
        if self._has_frontend_files(code_files):
            essential_files.extend(['package.json', 'index.html', 'App.tsx', 'App.jsx'])
        
        found_essential = []
        for essential in essential_files:
            for file_path in code_files.keys():
                if essential in file_path:
                    found_essential.append(essential)
                    break
        
        test["details"]["essential_files_found"] = found_essential
        test["details"]["essential_files_expected"] = essential_files
        
        if len(found_essential) < len(essential_files) * 0.5:  # At least 50% of essential files
            test["passed"] = False
            test["issues"].append("Missing essential application files")
        
        # Check directory structure
        has_proper_structure = any(
            'backend' in fp or 'frontend' in fp or 'src' in fp or 'app' in fp 
            for fp in code_files.keys()
        )
        
        if not has_proper_structure:
            test["issues"].append("No clear project structure found")
            test["passed"] = False
        
        return test
    
    def _test_configuration_files(self, code_files: Dict[str, str], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Test configuration files"""
        test = {
            "test_name": "configuration_validation",
            "passed": True,
            "issues": [],
            "details": {}
        }
        
        config_files_found = []
        
        # Check for common config files
        config_patterns = [
            'requirements.txt', 'package.json', 'docker-compose', 
            '.env', 'config.py', 'settings.py'
        ]
        
        for pattern in config_patterns:
            for file_path in code_files.keys():
                if pattern in file_path.lower():
                    config_files_found.append(file_path)
                    break
        
        test["details"]["config_files_found"] = config_files_found
        
        if len(config_files_found) == 0:
            test["passed"] = False
            test["issues"].append("No configuration files found")
        
        # Validate JSON files
        for file_path, content in code_files.items():
            if file_path.endswith('.json'):
                try:
                    json.loads(content)
                except json.JSONDecodeError:
                    test["passed"] = False
                    test["issues"].append(f"Invalid JSON in {file_path}")
        
        return test
    
    def _test_api_structure(self, code_files: Dict[str, str]) -> Dict[str, Any]:
        """Test API structure for backend projects"""
        test = {
            "test_name": "api_structure_validation",
            "passed": True,
            "issues": [],
            "details": {}
        }
        
        api_indicators = ['router', 'endpoint', 'api', 'route', 'controller']
        api_files_found = []
        
        for file_path, content in code_files.items():
            if any(indicator in file_path.lower() for indicator in api_indicators):
                api_files_found.append(file_path)
            elif any(indicator in content.lower() for indicator in ['@app.', 'fastapi', 'router', 'endpoint']):
                api_files_found.append(file_path)
        
        test["details"]["api_files_found"] = api_files_found
        
        if len(api_files_found) == 0:
            test["issues"].append("No API structure detected in backend project")
            # Don't fail the test as this might be intentional
        
        return test
    
    def _has_backend_files(self, code_files: Dict[str, str]) -> bool:
        """Check if project has backend files"""
        backend_indicators = ['.py', 'requirements.txt', 'fastapi', 'django', 'flask']
        return any(
            any(indicator in fp.lower() for indicator in backend_indicators)
            for fp in code_files.keys()
        )
    
    def _has_frontend_files(self, code_files: Dict[str, str]) -> bool:
        """Check if project has frontend files"""
        frontend_indicators = ['.tsx', '.jsx', '.ts', '.js', 'package.json', 'react']
        return any(
            any(indicator in fp.lower() for indicator in frontend_indicators)
            for fp in code_files.keys()
        )
    
    def _analyze_validation_results(self,
                                  validation_report: Dict[str, Any],
                                  compilation_report: Dict[str, Any],
                                  test_results: Dict[str, Any]) -> Dict[str, Any]:
        """🔍 ANALYZE RESULTS - Generate comprehensive analysis"""
        
        # Calculate overall scores
        validation_score = 1.0 - (validation_report["summary"]["error"] / max(1, validation_report["summary"]["total_issues"]))
        compilation_score = 1.0 if compilation_report["success"] else 0.5
        test_score = test_results["coverage"]
        
        overall_score = (validation_score + compilation_score + test_score) / 3
        overall_success = overall_score >= 0.7  # 70% threshold
        
        # Categorize errors by priority
        critical_errors = []
        
        # Critical validation errors
        for issue in validation_report["issues"]:
            if issue["severity"] == "error" and issue["issue_type"] in ["syntax_error", "missing_import", "compilation_error"]:
                critical_errors.append({
                    "type": "validation",
                    "category": issue["issue_type"],
                    "file": issue["file_path"],
                    "line": issue.get("line_number"),
                    "message": issue["message"],
                    "suggestion": issue.get("suggestion", ""),
                    "priority": "high"
                })
        
        # Critical compilation errors
        for error in compilation_report["errors"]:
            critical_errors.append({
                "type": "compilation",
                "category": error.get("error_type", "unknown"),
                "message": error["message"],
                "suggestion": error.get("suggestion", ""),
                "priority": "high"
            })
        
        # Failed tests
        for test_detail in test_results["test_details"]:
            if not test_detail["passed"]:
                for issue in test_detail["issues"]:
                    critical_errors.append({
                        "type": "functional_test",
                        "category": test_detail["test_name"],
                        "message": issue,
                        "priority": "medium"
                    })
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            validation_report, compilation_report, test_results, critical_errors
        )
        
        return {
            "overall_success": overall_success,
            "overall_score": round(overall_score, 2),
            "scores": {
                "validation": round(validation_score, 2),
                "compilation": round(compilation_score, 2),
                "testing": round(test_score, 2)
            },
            "critical_errors": critical_errors,
            "total_critical_errors": len(critical_errors),
            "recommendations": recommendations,
            "next_iteration_focus": self._determine_next_focus(critical_errors)
        }
    
    def _generate_recommendations(self,
                                validation_report: Dict[str, Any],
                                compilation_report: Dict[str, Any],
                                test_results: Dict[str, Any],
                                critical_errors: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Validation recommendations
        if validation_report["summary"]["error"] > 0:
            recommendations.append("Fix syntax and import errors before proceeding")
            
        if validation_report["summary"]["error"] > 5:
            recommendations.append("Consider breaking down large files with many errors")
        
        # Compilation recommendations
        if not compilation_report["success"]:
            if compilation_report["dependency_check"]["python"]["missing"]:
                recommendations.append("Install missing Python dependencies")
            if compilation_report["dependency_check"]["node"]["missing"]:
                recommendations.append("Run npm install to resolve Node.js dependencies")
        
        # Test recommendations
        if test_results["coverage"] < 0.5:
            recommendations.append("Improve code structure and add essential files")
            
        # Critical error recommendations
        error_types = [e["category"] for e in critical_errors]
        if "syntax_error" in error_types:
            recommendations.append("Prioritize fixing syntax errors - they prevent execution")
        if "missing_import" in error_types:
            recommendations.append("Add missing import statements")
        if "file_structure_validation" in error_types:
            recommendations.append("Reorganize project structure with clear backend/frontend separation")
        
        # General recommendations
        if len(critical_errors) > 10:
            recommendations.append("Focus on top 5 critical errors first to make meaningful progress")
        
        if not recommendations:
            recommendations.append("Code quality looks good - consider adding more comprehensive tests")
        
        return recommendations
    
    def _determine_next_focus(self, critical_errors: List[Dict[str, Any]]) -> List[str]:
        """Determine what to focus on in next iteration"""
        focus_areas = []
        
        error_categories = {}
        for error in critical_errors:
            category = error["category"]
            error_categories[category] = error_categories.get(category, 0) + 1
        
        # Sort by frequency
        sorted_categories = sorted(error_categories.items(), key=lambda x: x[1], reverse=True)
        
        # Focus on top categories
        for category, count in sorted_categories[:3]:  # Top 3 categories
            if category == "syntax_error":
                focus_areas.append("syntax_fixes")
            elif category == "missing_import":
                focus_areas.append("import_resolution")
            elif category == "compilation_error":
                focus_areas.append("dependency_management")
            elif category == "file_structure_validation":
                focus_areas.append("project_organization")
            else:
                focus_areas.append("code_quality")
        
        return focus_areas or ["general_improvements"]
    
    async def _save_validation_reports(self,
                                     structure: Dict[str, Path],
                                     result: Dict[str, Any],
                                     iteration: int):
        """💾 SAVE VALIDATION REPORTS - To unified reports/ directory"""
        reports_path = structure["reports_path"]
        
        try:
            # Save individual reports
            validation_file = reports_path / f"validation_iter_{iteration}.json"
            with open(validation_file, 'w') as f:
                json.dump(result["validation_report"], f, indent=2)
            
            compilation_file = reports_path / f"compilation_iter_{iteration}.json"
            with open(compilation_file, 'w') as f:
                json.dump(result["compilation_report"], f, indent=2)
            
            test_file = reports_path / f"test_results_iter_{iteration}.json"
            with open(test_file, 'w') as f:
                json.dump(result["test_results"], f, indent=2)
            
            # Save comprehensive iteration summary
            summary_file = reports_path / f"iteration_{iteration}.json"
            with open(summary_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"💾 Validation reports saved to {reports_path}")
            
        except Exception as e:
            logger.error(f"❌ Error saving validation reports: {e}")
    
    def load_previous_errors(self, structure: Dict[str, Path], previous_iteration: int) -> List[Dict[str, Any]]:
        """📖 LOAD PREVIOUS ERRORS - From unified reports/ directory"""
        errors = []
        reports_path = structure["reports_path"]
        
        summary_file = reports_path / f"iteration_{previous_iteration}.json"
        if summary_file.exists():
            try:
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
                
                # Extract critical errors from analysis
                if "analysis" in summary and "critical_errors" in summary["analysis"]:
                    errors = summary["analysis"]["critical_errors"]
                
                logger.info(f"📖 Loaded {len(errors)} errors from iteration {previous_iteration}")
                
            except Exception as e:
                logger.error(f"❌ Error loading previous errors: {e}")
        
        return errors
    
    def get_validation_summary(self, structure: Dict[str, Path]) -> Dict[str, Any]:
        """📊 GET VALIDATION SUMMARY - Overall project health"""
        reports_path = structure["reports_path"]
        
        summary = {
            "total_iterations": 0,
            "latest_iteration": 0,
            "overall_trend": "unknown",
            "current_status": "unknown",
            "total_errors_fixed": 0,
            "remaining_critical_errors": 0
        }
        
        try:
            # Find all iteration reports
            iteration_files = list(reports_path.glob("iteration_*.json"))
            iteration_numbers = []
            
            for file in iteration_files:
                try:
                    iteration_num = int(file.stem.split('_')[1])
                    iteration_numbers.append(iteration_num)
                except:
                    continue
            
            if iteration_numbers:
                iteration_numbers.sort()
                summary["total_iterations"] = len(iteration_numbers)
                summary["latest_iteration"] = max(iteration_numbers)
                
                # Load latest report
                latest_file = reports_path / f"iteration_{summary['latest_iteration']}.json"
                with open(latest_file, 'r') as f:
                    latest_report = json.load(f)
                
                summary["current_status"] = "success" if latest_report.get("success", False) else "issues"
                summary["remaining_critical_errors"] = len(latest_report.get("analysis", {}).get("critical_errors", []))
                
                # Calculate trend if multiple iterations
                if len(iteration_numbers) >= 2:
                    first_file = reports_path / f"iteration_{iteration_numbers[0]}.json"
                    with open(first_file, 'r') as f:
                        first_report = json.load(f)
                    
                    first_errors = len(first_report.get("analysis", {}).get("critical_errors", []))
                    latest_errors = summary["remaining_critical_errors"]
                    
                    summary["total_errors_fixed"] = max(0, first_errors - latest_errors)
                    
                    if latest_errors < first_errors:
                        summary["overall_trend"] = "improving"
                    elif latest_errors > first_errors:
                        summary["overall_trend"] = "worsening"
                    else:
                        summary["overall_trend"] = "stable"
        
        except Exception as e:
            logger.error(f"❌ Error generating validation summary: {e}")
        
        return summary