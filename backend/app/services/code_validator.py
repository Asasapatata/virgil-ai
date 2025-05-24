# backend/app/services/code_validator.py
import ast
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationIssue:
    """Represents a code validation issue"""
    file_path: str
    issue_type: str  # 'import_error', 'syntax_error', 'structure_error', 'dependency_error'
    severity: str    # 'error', 'warning', 'info'
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None

@dataclass
class ValidationReport:
    """Complete validation report for an iteration"""
    iteration: int
    project_path: str
    total_files: int
    validated_files: int
    issues: List[ValidationIssue]
    structure_valid: bool
    dependencies_valid: bool
    summary: Dict[str, int]  # Count by severity
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "project_path": self.project_path,
            "total_files": self.total_files,
            "validated_files": self.validated_files,
            "issues": [
                {
                    "file_path": issue.file_path,
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "message": issue.message,
                    "line_number": issue.line_number,
                    "suggestion": issue.suggestion
                }
                for issue in self.issues
            ],
            "structure_valid": self.structure_valid,
            "dependencies_valid": self.dependencies_valid,
            "summary": self.summary
        }

class CodeValidator:
    """
    Service for validating generated code quality, structure, and dependencies
    """
    
    def __init__(self):
        self.supported_extensions = {
            '.py': self._validate_python_file,
            '.js': self._validate_javascript_file,
            '.ts': self._validate_typescript_file,
            '.tsx': self._validate_tsx_file,
            '.jsx': self._validate_jsx_file,
            '.json': self._validate_json_file,
            '.yaml': self._validate_yaml_file,
            '.yml': self._validate_yaml_file
        }
        logger.info("CodeValidator initialized")
    
    def validate_iteration(self, 
                          iteration_path: Path, 
                          project_name: str,
                          iteration: int) -> ValidationReport:
        """
        Validate all code in an iteration directory
        """
        logger.info(f"Validating iteration {iteration} at {iteration_path}")
        
        issues = []
        project_code_path = iteration_path / project_name
        
        # Get all files to validate
        all_files = list(project_code_path.rglob("*")) if project_code_path.exists() else []
        code_files = [f for f in all_files if f.is_file() and f.suffix in self.supported_extensions]
        
        validated_count = 0
        
        # Validate each file
        for file_path in code_files:
            try:
                file_issues = self._validate_file(file_path, project_code_path)
                issues.extend(file_issues)
                validated_count += 1
            except Exception as e:
                logger.error(f"Error validating {file_path}: {e}")
                issues.append(ValidationIssue(
                    file_path=str(file_path.relative_to(project_code_path)),
                    issue_type="validation_error",
                    severity="error",
                    message=f"Failed to validate file: {str(e)}"
                ))
        
        # Validate project structure
        structure_issues = self._validate_project_structure(project_code_path)
        issues.extend(structure_issues)
        
        # Validate dependencies
        dependency_issues = self._validate_dependencies(project_code_path)
        issues.extend(dependency_issues)
        
        # Create summary
        summary = {
            "error": len([i for i in issues if i.severity == "error"]),
            "warning": len([i for i in issues if i.severity == "warning"]),
            "info": len([i for i in issues if i.severity == "info"])
        }
        
        structure_valid = len(structure_issues) == 0
        dependencies_valid = len([i for i in dependency_issues if i.severity == "error"]) == 0
        
        report = ValidationReport(
            iteration=iteration,
            project_path=str(iteration_path),
            total_files=len(all_files),
            validated_files=validated_count,
            issues=issues,
            structure_valid=structure_valid,
            dependencies_valid=dependencies_valid,
            summary=summary
        )
        
        logger.info(f"Validation completed: {summary['error']} errors, {summary['warning']} warnings")
        return report
    
    def _validate_file(self, file_path: Path, project_root: Path) -> List[ValidationIssue]:
        """Validate a single file based on its extension"""
        issues = []
        
        try:
            extension = file_path.suffix.lower()
            if extension in self.supported_extensions:
                validator_func = self.supported_extensions[extension]
                file_issues = validator_func(file_path, project_root)
                issues.extend(file_issues)
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(file_path.relative_to(project_root)),
                issue_type="validation_error",
                severity="error",
                message=f"Validation error: {str(e)}"
            ))
        
        return issues
    
    def _validate_python_file(self, file_path: Path, project_root: Path) -> List[ValidationIssue]:
        """Validate Python file"""
        issues = []
        relative_path = str(file_path.relative_to(project_root))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Syntax validation
            try:
                ast.parse(content)
            except SyntaxError as e:
                issues.append(ValidationIssue(
                    file_path=relative_path,
                    issue_type="syntax_error",
                    severity="error",
                    message=f"Syntax error: {e.msg}",
                    line_number=e.lineno,
                    suggestion="Fix syntax error before proceeding"
                ))
                return issues  # Can't continue if syntax is invalid
            
            # Import validation
            import_issues = self._validate_python_imports(content, file_path, project_root)
            issues.extend(import_issues)
            
            # Code quality checks
            quality_issues = self._validate_python_quality(content, relative_path)
            issues.extend(quality_issues)
            
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=relative_path,
                issue_type="read_error",
                severity="error",
                message=f"Could not read file: {str(e)}"
            ))
        
        return issues
    
    def _validate_python_imports(self, content: str, file_path: Path, project_root: Path) -> List[ValidationIssue]:
        """Validate Python imports"""
        issues = []
        relative_path = str(file_path.relative_to(project_root))
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        issue = self._check_python_import(alias.name, relative_path, project_root)
                        if issue:
                            issues.append(issue)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        issue = self._check_python_import(node.module, relative_path, project_root, is_from=True)
                        if issue:
                            issues.append(issue)
        
        except Exception as e:
            logger.warning(f"Could not validate imports for {relative_path}: {e}")
        
        return issues
    
    def _check_python_import(self, module_name: str, file_path: str, project_root: Path, is_from: bool = False) -> Optional[ValidationIssue]:
        """Check if a Python import is valid"""
        
        # Skip standard library and known third-party packages
        if self._is_standard_library(module_name) or self._is_known_package(module_name):
            return None
        
        # Check for relative imports within project
        if module_name.startswith('app.') or module_name.startswith('.'):
            # Convert module path to file path
            if module_name.startswith('app.'):
                module_path = module_name.replace('app.', '').replace('.', '/')
                expected_path = project_root / f"{module_path}.py"
                
                if not expected_path.exists():
                    # Try as package (__init__.py)
                    expected_path = project_root / module_path / "__init__.py"
                    
                    if not expected_path.exists():
                        return ValidationIssue(
                            file_path=file_path,
                            issue_type="import_error",
                            severity="error",
                            message=f"Import '{module_name}' not found",
                            suggestion=f"Create {module_path}.py or {module_path}/__init__.py"
                        )
        
        return None
    
    def _validate_python_quality(self, content: str, file_path: str) -> List[ValidationIssue]:
        """Basic Python code quality checks"""
        issues = []
        lines = content.split('\n')
        
        # Check for common issues
        for i, line in enumerate(lines, 1):
            # Long lines
            if len(line) > 120:
                issues.append(ValidationIssue(
                    file_path=file_path,
                    issue_type="style_warning",
                    severity="warning",
                    message="Line too long (>120 characters)",
                    line_number=i,
                    suggestion="Consider breaking long lines"
                ))
            
            # TODO comments (might indicate incomplete code)
            if 'TODO' in line or 'FIXME' in line:
                issues.append(ValidationIssue(
                    file_path=file_path,
                    issue_type="incomplete_code",
                    severity="warning",
                    message="TODO/FIXME comment found",
                    line_number=i,
                    suggestion="Complete implementation or remove comment"
                ))
        
        return issues
    
    def _validate_javascript_file(self, file_path: Path, project_root: Path) -> List[ValidationIssue]:
        """Validate JavaScript file"""
        issues = []
        relative_path = str(file_path.relative_to(project_root))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic syntax checks
            if content.count('{') != content.count('}'):
                issues.append(ValidationIssue(
                    file_path=relative_path,
                    issue_type="syntax_error",
                    severity="error",
                    message="Mismatched braces",
                    suggestion="Check for missing or extra braces"
                ))
            
            # Import/require validation
            import_issues = self._validate_js_imports(content, relative_path, project_root)
            issues.extend(import_issues)
            
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=relative_path,
                issue_type="read_error",
                severity="error",
                message=f"Could not read file: {str(e)}"
            ))
        
        return issues
    
    def _validate_typescript_file(self, file_path: Path, project_root: Path) -> List[ValidationIssue]:
        """Validate TypeScript file"""
        # For now, use JavaScript validation with additional TS-specific checks
        issues = self._validate_javascript_file(file_path, project_root)
        
        relative_path = str(file_path.relative_to(project_root))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for TypeScript-specific issues
            if 'any' in content:
                issues.append(ValidationIssue(
                    file_path=relative_path,
                    issue_type="type_warning",
                    severity="warning",
                    message="Usage of 'any' type found",
                    suggestion="Consider using more specific types"
                ))
        
        except Exception as e:
            logger.warning(f"Could not validate TypeScript file {relative_path}: {e}")
        
        return issues
    
    def _validate_tsx_file(self, file_path: Path, project_root: Path) -> List[ValidationIssue]:
        """Validate TSX file"""
        return self._validate_typescript_file(file_path, project_root)
    
    def _validate_jsx_file(self, file_path: Path, project_root: Path) -> List[ValidationIssue]:
        """Validate JSX file"""
        return self._validate_javascript_file(file_path, project_root)
    
    def _validate_json_file(self, file_path: Path, project_root: Path) -> List[ValidationIssue]:
        """Validate JSON file"""
        issues = []
        relative_path = str(file_path.relative_to(project_root))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            issues.append(ValidationIssue(
                file_path=relative_path,
                issue_type="syntax_error",
                severity="error",
                message=f"Invalid JSON: {e.msg}",
                line_number=e.lineno,
                suggestion="Fix JSON syntax"
            ))
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=relative_path,
                issue_type="read_error",
                severity="error",
                message=f"Could not read JSON file: {str(e)}"
            ))
        
        return issues
    
    def _validate_yaml_file(self, file_path: Path, project_root: Path) -> List[ValidationIssue]:
        """Validate YAML file"""
        issues = []
        relative_path = str(file_path.relative_to(project_root))
        
        try:
            import yaml
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            issues.append(ValidationIssue(
                file_path=relative_path,
                issue_type="syntax_error",
                severity="error",
                message=f"Invalid YAML: {str(e)}",
                suggestion="Fix YAML syntax"
            ))
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=relative_path,
                issue_type="read_error",
                severity="error",
                message=f"Could not read YAML file: {str(e)}"
            ))
        
        return issues
    
    def _validate_js_imports(self, content: str, file_path: str, project_root: Path) -> List[ValidationIssue]:
        """Validate JavaScript/TypeScript imports"""
        issues = []
        
        # Find import statements
        import_pattern = r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
        require_pattern = r'require\([\'"]([^\'"]+)[\'"]\)'
        
        imports = re.findall(import_pattern, content) + re.findall(require_pattern, content)
        
        for import_path in imports:
            # Skip node modules and absolute imports
            if not import_path.startswith('.') and not import_path.startswith('/'):
                continue
            
            # Check relative imports
            if import_path.startswith('./') or import_path.startswith('../'):
                # Convert to absolute path and check if exists
                base_dir = Path(file_path).parent if '/' in file_path else project_root
                resolved_path = (base_dir / import_path).resolve()
                
                # Try different extensions
                possible_paths = [
                    resolved_path,
                    resolved_path.with_suffix('.js'),
                    resolved_path.with_suffix('.ts'),
                    resolved_path.with_suffix('.tsx'),
                    resolved_path.with_suffix('.jsx'),
                    resolved_path / 'index.js',
                    resolved_path / 'index.ts'
                ]
                
                if not any(p.exists() for p in possible_paths if str(p).startswith(str(project_root))):
                    issues.append(ValidationIssue(
                        file_path=file_path,
                        issue_type="import_error",
                        severity="error",
                        message=f"Import '{import_path}' not found",
                        suggestion=f"Create the imported file or fix the import path"
                    ))
        
        return issues
    
    def _validate_project_structure(self, project_path: Path) -> List[ValidationIssue]:
        """Validate overall project structure"""
        issues = []
        
        if not project_path.exists():
            issues.append(ValidationIssue(
                file_path="",
                issue_type="structure_error",
                severity="error",
                message="Project directory does not exist"
            ))
            return issues
        
        # Check for common required files
        required_files = []
        
        # Check for package.json if it's a Node.js project
        if any(project_path.rglob("*.js")) or any(project_path.rglob("*.ts")):
            required_files.append("package.json")
        
        # Check for requirements.txt if it's a Python project
        if any(project_path.rglob("*.py")):
            required_files.append("requirements.txt")
        
        for required_file in required_files:
            if not (project_path / required_file).exists():
                issues.append(ValidationIssue(
                    file_path="",
                    issue_type="structure_error",
                    severity="warning",
                    message=f"Missing {required_file}",
                    suggestion=f"Add {required_file} for dependency management"
                ))
        
        return issues
    
    def _validate_dependencies(self, project_path: Path) -> List[ValidationIssue]:
        """Validate project dependencies"""
        issues = []
        
        # Check package.json dependencies
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                
                deps = package_data.get('dependencies', {})
                dev_deps = package_data.get('devDependencies', {})
                
                # Check for common missing dependencies
                js_files = list(project_path.rglob("*.js")) + list(project_path.rglob("*.ts"))
                if js_files:
                    # Check for React if JSX/TSX files exist
                    jsx_files = list(project_path.rglob("*.jsx")) + list(project_path.rglob("*.tsx"))
                    if jsx_files and 'react' not in deps:
                        issues.append(ValidationIssue(
                            file_path="package.json",
                            issue_type="dependency_error",
                            severity="error",
                            message="React dependency missing but JSX/TSX files found",
                            suggestion="Add 'react' to dependencies"
                        ))
            
            except Exception as e:
                issues.append(ValidationIssue(
                    file_path="package.json",
                    issue_type="dependency_error",
                    severity="error",
                    message=f"Could not parse package.json: {str(e)}"
                ))
        
        # Check requirements.txt
        requirements_txt = project_path / "requirements.txt"
        if requirements_txt.exists():
            try:
                with open(requirements_txt, 'r') as f:
                    content = f.read()
                
                # Basic validation that it's not empty
                if not content.strip():
                    issues.append(ValidationIssue(
                        file_path="requirements.txt",
                        issue_type="dependency_error",
                        severity="warning",
                        message="requirements.txt is empty",
                        suggestion="Add Python dependencies if needed"
                    ))
            
            except Exception as e:
                issues.append(ValidationIssue(
                    file_path="requirements.txt",
                    issue_type="dependency_error",
                    severity="error",
                    message=f"Could not read requirements.txt: {str(e)}"
                ))
        
        return issues
    
    def _is_standard_library(self, module_name: str) -> bool:
        """Check if module is part of Python standard library"""
        standard_modules = {
            'os', 'sys', 'json', 'datetime', 'pathlib', 'typing', 'asyncio',
            'logging', 'uuid', 'hashlib', 'base64', 'urllib', 'http',
            'collections', 'itertools', 'functools', 're', 'math', 'random'
        }
        
        base_module = module_name.split('.')[0]
        return base_module in standard_modules
    
    def _is_known_package(self, module_name: str) -> bool:
        """Check if module is a known third-party package"""
        known_packages = {
            'fastapi', 'pydantic', 'sqlalchemy', 'alembic', 'pytest',
            'requests', 'httpx', 'uvicorn', 'celery', 'redis',
            'react', 'next', 'express', 'lodash', 'axios'
        }
        
        base_module = module_name.split('.')[0]
        return base_module in known_packages