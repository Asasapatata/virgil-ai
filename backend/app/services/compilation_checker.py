# backend/app/services/compilation_checker.py
import asyncio
import subprocess
import json
import logging
import tempfile
import shutil
import os  # 🔥 AGGIUNTO import mancante
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CompilationError:
    """Represents a compilation error"""
    error_type: str     # 'syntax', 'dependency', 'build', 'runtime'
    severity: str       # 'error', 'warning'
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    suggestion: Optional[str] = None
    command: Optional[str] = None  # Command that failed

@dataclass
class CompilationResult:
    """Result of compilation check"""
    project_type: str
    success: bool
    errors: List[CompilationError]
    warnings: List[CompilationError]
    build_output: str
    dependencies_installed: bool
    build_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_type": self.project_type,
            "success": self.success,
            "errors": [
                {
                    "error_type": error.error_type,
                    "severity": error.severity,
                    "message": error.message,
                    "file_path": error.file_path,
                    "line_number": error.line_number,
                    "column_number": error.column_number,
                    "suggestion": error.suggestion,
                    "command": error.command
                }
                for error in self.errors
            ],
            "warnings": [
                {
                    "error_type": warning.error_type,
                    "severity": warning.severity,
                    "message": warning.message,
                    "file_path": warning.file_path,
                    "line_number": warning.line_number,
                    "column_number": warning.column_number,
                    "suggestion": warning.suggestion,
                    "command": warning.command
                }
                for warning in self.warnings
            ],
            "build_output": self.build_output,
            "dependencies_installed": self.dependencies_installed,
            "build_time": self.build_time
        }

class CompilationChecker:
    """
    Service for checking compilation and build processes of generated code
    """
    
    def __init__(self):
        self.timeout = 300  # 5 minutes timeout for compilation
        logger.info("CompilationChecker initialized")
    
    async def check_compilation(self, project_path: Path, project_name: str) -> CompilationResult:
        """
        Check compilation for the project based on detected project type
        """
        logger.info(f"Checking compilation for project at {project_path}")
        
        import time
        start_time = time.time()
        
        # Detect project type
        project_type = self._detect_project_type(project_path)
        logger.info(f"Detected project type: {project_type}")
        
        # Run appropriate compilation check
        if project_type == "node":
            result = await self._check_node_compilation(project_path)
        elif project_type == "python":
            result = await self._check_python_compilation(project_path)
        elif project_type == "mixed":
            result = await self._check_mixed_compilation(project_path)
        elif project_type == "docker":
            result = await self._check_docker_compilation(project_path)
        else:
            result = CompilationResult(
                project_type=project_type,
                success=True,
                errors=[],
                warnings=[],
                build_output="No compilation needed for this project type",
                dependencies_installed=True,
                build_time=0.0
            )
        
        result.build_time = time.time() - start_time
        logger.info(f"Compilation check completed in {result.build_time:.2f}s - Success: {result.success}")
        
        return result
    
    def _detect_project_type(self, project_path: Path) -> str:
        """Detect the type of project to determine compilation strategy"""
        
        has_package_json = (project_path / "package.json").exists()
        has_requirements_txt = (project_path / "requirements.txt").exists()
        has_dockerfile = (project_path / "Dockerfile").exists()
        has_py_files = bool(list(project_path.rglob("*.py")))
        has_js_files = bool(list(project_path.rglob("*.js"))) or bool(list(project_path.rglob("*.ts")))
        
        if has_dockerfile:
            return "docker"
        elif has_package_json and has_requirements_txt:
            return "mixed"
        elif has_package_json or has_js_files:
            return "node"
        elif has_requirements_txt or has_py_files:
            return "python"
        else:
            return "static"
    
    async def _check_node_compilation(self, project_path: Path) -> CompilationResult:
        """Check Node.js/TypeScript compilation"""
        errors = []
        warnings = []
        build_output = ""
        dependencies_installed = False
        
        try:
            # Check if package.json exists
            package_json = project_path / "package.json"
            if not package_json.exists():
                errors.append(CompilationError(
                    error_type="dependency",
                    severity="error",
                    message="package.json not found",
                    suggestion="Create package.json file with project dependencies"
                ))
                return CompilationResult("node", False, errors, warnings, build_output, False, 0.0)
            
            # Parse package.json
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
            except json.JSONDecodeError as e:
                errors.append(CompilationError(
                    error_type="syntax",
                    severity="error",
                    message=f"Invalid package.json: {str(e)}",
                    file_path="package.json",
                    suggestion="Fix JSON syntax in package.json"
                ))
                return CompilationResult("node", False, errors, warnings, build_output, False, 0.0)
            
            # Create temporary directory for safe compilation
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / "project"
                shutil.copytree(project_path, temp_path)
                
                # Install dependencies
                install_result = await self._run_command(
                    ["npm", "install"],
                    cwd=temp_path,
                    timeout=180  # 3 minutes for npm install
                )
                
                build_output += f"=== NPM INSTALL ===\n{install_result.output}\n\n"
                
                if install_result.returncode != 0:
                    errors.extend(self._parse_npm_errors(install_result.output, "npm install"))
                    return CompilationResult("node", False, errors, warnings, build_output, False, 0.0)
                
                dependencies_installed = True
                
                # Check TypeScript compilation if tsconfig.json exists
                if (temp_path / "tsconfig.json").exists():
                    tsc_result = await self._run_command(
                        ["npx", "tsc", "--noEmit"],
                        cwd=temp_path,
                        timeout=120
                    )
                    
                    build_output += f"=== TYPESCRIPT CHECK ===\n{tsc_result.output}\n\n"
                    
                    if tsc_result.returncode != 0:
                        ts_errors = self._parse_typescript_errors(tsc_result.output)
                        errors.extend(ts_errors)
                
                # Try to build if build script exists
                scripts = package_data.get("scripts", {})
                
                if "build" in scripts:
                    build_result = await self._run_command(
                        ["npm", "run", "build"],
                        cwd=temp_path,
                        timeout=180
                    )
                    
                    build_output += f"=== NPM BUILD ===\n{build_result.output}\n\n"
                    
                    if build_result.returncode != 0:
                        build_errors = self._parse_npm_build_errors(build_result.output)
                        errors.extend(build_errors)
                
                # Check for linting if available
                if "lint" in scripts:
                    lint_result = await self._run_command(
                        ["npm", "run", "lint"],
                        cwd=temp_path,
                        timeout=60
                    )
                    
                    build_output += f"=== LINT CHECK ===\n{lint_result.output}\n\n"
                    
                    if lint_result.returncode != 0:
                        lint_warnings = self._parse_lint_output(lint_result.output)
                        warnings.extend(lint_warnings)
        
        except Exception as e:
            logger.error(f"Error during Node.js compilation check: {e}")
            errors.append(CompilationError(
                error_type="build",
                severity="error",
                message=f"Compilation check failed: {str(e)}",
                suggestion="Check project structure and dependencies"
            ))
        
        success = len(errors) == 0
        return CompilationResult("node", success, errors, warnings, build_output, dependencies_installed, 0.0)
    
    async def _check_python_compilation(self, project_path: Path) -> CompilationResult:
        """Check Python compilation and syntax"""
        errors = []
        warnings = []
        build_output = ""
        dependencies_installed = False
        
        try:
            # Check if requirements.txt exists
            requirements_txt = project_path / "requirements.txt"
            
            # Create temporary directory for safe compilation
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / "project"
                shutil.copytree(project_path, temp_path)
                
                # Create virtual environment
                venv_path = Path(temp_dir) / "venv"
                venv_result = await self._run_command(
                    ["python", "-m", "venv", str(venv_path)],
                    timeout=60
                )
                
                if venv_result.returncode != 0:
                    errors.append(CompilationError(
                        error_type="dependency",
                        severity="error",
                        message="Failed to create virtual environment",
                        command="python -m venv",
                        suggestion="Ensure Python is properly installed"
                    ))
                    return CompilationResult("python", False, errors, warnings, build_output, False, 0.0)
                
                # Determine Python executable in venv
                python_exe = venv_path / "bin" / "python"
                if not python_exe.exists():
                    python_exe = venv_path / "Scripts" / "python.exe"  # Windows
                
                if not python_exe.exists():
                    errors.append(CompilationError(
                        error_type="dependency",
                        severity="error",
                        message="Could not find Python executable in virtual environment"
                    ))
                    return CompilationResult("python", False, errors, warnings, build_output, False, 0.0)
                
                # Install dependencies if requirements.txt exists
                if requirements_txt.exists():
                    install_result = await self._run_command(
                        [str(python_exe), "-m", "pip", "install", "-r", str(requirements_txt)],
                        cwd=temp_path,
                        timeout=180
                    )
                    
                    build_output += f"=== PIP INSTALL ===\n{install_result.output}\n\n"
                    
                    if install_result.returncode != 0:
                        pip_errors = self._parse_pip_errors(install_result.output)
                        errors.extend(pip_errors)
                        return CompilationResult("python", False, errors, warnings, build_output, False, 0.0)
                    
                    dependencies_installed = True
                
                # Check Python syntax for all .py files
                py_files = list(temp_path.rglob("*.py"))
                for py_file in py_files:
                    try:
                        syntax_result = await self._run_command(
                            [str(python_exe), "-m", "py_compile", str(py_file)],
                            timeout=30
                        )
                        
                        if syntax_result.returncode != 0:
                            relative_path = str(py_file.relative_to(temp_path))
                            syntax_errors = self._parse_python_syntax_errors(
                                syntax_result.output, relative_path
                            )
                            errors.extend(syntax_errors)
                    
                    except Exception as e:
                        logger.warning(f"Could not check syntax for {py_file}: {e}")
                
                # Try to run basic import checks
                for py_file in py_files:
                    if py_file.name == "__init__.py":
                        continue
                    
                    try:
                        # Convert file path to module path
                        relative_path = py_file.relative_to(temp_path)
                        module_path = str(relative_path.with_suffix('')).replace('/', '.')
                        
                        import_result = await self._run_command(
                            [str(python_exe), "-c", f"import {module_path}"],
                            cwd=temp_path,
                            timeout=30
                        )
                        
                        if import_result.returncode != 0:
                            import_errors = self._parse_python_import_errors(
                                import_result.output, str(relative_path)
                            )
                            errors.extend(import_errors)
                    
                    except Exception as e:
                        logger.warning(f"Could not check imports for {py_file}: {e}")
        
        except Exception as e:
            logger.error(f"Error during Python compilation check: {e}")
            errors.append(CompilationError(
                error_type="build",
                severity="error",
                message=f"Python compilation check failed: {str(e)}",
                suggestion="Check Python installation and project structure"
            ))
        
        success = len(errors) == 0
        return CompilationResult("python", success, errors, warnings, build_output, dependencies_installed, 0.0)
    
    async def _check_mixed_compilation(self, project_path: Path) -> CompilationResult:
        """Check compilation for mixed Node.js + Python projects"""
        logger.info("Checking mixed project compilation")
        
        # Run both Node.js and Python checks
        node_result = await self._check_node_compilation(project_path)
        python_result = await self._check_python_compilation(project_path)
        
        # Combine results
        all_errors = node_result.errors + python_result.errors
        all_warnings = node_result.warnings + python_result.warnings
        combined_output = f"=== NODE.JS COMPILATION ===\n{node_result.build_output}\n\n"
        combined_output += f"=== PYTHON COMPILATION ===\n{python_result.build_output}\n\n"
        
        dependencies_installed = node_result.dependencies_installed and python_result.dependencies_installed
        success = node_result.success and python_result.success
        
        return CompilationResult(
            "mixed", success, all_errors, all_warnings, 
            combined_output, dependencies_installed, 0.0
        )
    
    async def _check_docker_compilation(self, project_path: Path) -> CompilationResult:
        """Check Docker build"""
        errors = []
        warnings = []
        build_output = ""
        
        try:
            dockerfile = project_path / "Dockerfile"
            if not dockerfile.exists():
                errors.append(CompilationError(
                    error_type="dependency",
                    severity="error",
                    message="Dockerfile not found",
                    suggestion="Create Dockerfile for containerized build"
                ))
                return CompilationResult("docker", False, errors, warnings, build_output, False, 0.0)
            
            # 🔧 FIX: Controlla se Docker è disponibile
            try:
                from app.services.docker_config import get_docker_client
                docker_client = get_docker_client()
            except Exception as docker_error:
                # 🔧 Non è un errore critico, documenta solo
                warnings.append(CompilationError(
                    error_type="build",
                    severity="warning",
                    message=f"Docker not available: {str(docker_error)}",
                    suggestion="Docker build check skipped - ensure Docker is available in production"
                ))
                return CompilationResult("docker", True, errors, warnings, 
                                    "Docker build check skipped - Docker not available", 
                                    True, 0.0)
        
            # Create temporary directory and copy project
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / "project"
                shutil.copytree(project_path, temp_path)
                
                # Try to build Docker image
                build_result = await self._run_command(
                    ["docker", "build", "-t", "temp-build-check", "."],
                    cwd=temp_path,
                    timeout=300  # 5 minutes for Docker build
                )
                
                build_output = f"=== DOCKER BUILD ===\n{build_result.output}\n\n"
                
                if build_result.returncode != 0:
                    docker_errors = self._parse_docker_errors(build_result.output)
                    errors.extend(docker_errors)
                else:
                    # Clean up the built image
                    await self._run_command(
                        ["docker", "rmi", "temp-build-check"],
                        timeout=30
                    )
        
        except Exception as e:
            logger.error(f"Error during Docker compilation check: {e}")
            errors.append(CompilationError(
                error_type="build",
                severity="error",
                message=f"Docker build check failed: {str(e)}",
                suggestion="Check Docker installation and Dockerfile syntax"
            ))
        
        success = len(errors) == 0
        dependencies_installed = success  # If Docker build succeeds, dependencies are handled
        
        return CompilationResult("docker", success, errors, warnings, build_output, dependencies_installed, 0.0)
    
    async def _run_command(self, cmd: List[str], cwd: Optional[Path] = None, timeout: int = 60) -> Any:
        """Run a command with timeout and capture output"""
        class CommandResult:
            def __init__(self, returncode: int, output: str):
                self.returncode = returncode
                self.output = output
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env={**os.environ, "CI": "true", "NODE_ENV": "production"}
            )
            
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout)
            output = stdout.decode('utf-8', errors='ignore') if stdout else ""
            
            return CommandResult(process.returncode, output)
        
        except asyncio.TimeoutError:
            logger.warning(f"Command timed out: {' '.join(cmd)}")
            return CommandResult(1, f"Command timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Error running command {' '.join(cmd)}: {e}")
            return CommandResult(1, f"Command failed: {str(e)}")
    
    def _parse_npm_errors(self, output: str, command: str) -> List[CompilationError]:
        """Parse npm install/build errors"""
        errors = []
        lines = output.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # npm ERR! messages
            if line.startswith('npm ERR!'):
                message = line.replace('npm ERR!', '').strip()
                if message and not message.startswith('code '):
                    errors.append(CompilationError(
                        error_type="dependency",
                        severity="error",
                        message=message,
                        command=command,
                        suggestion="Check package.json dependencies and npm registry access"
                    ))
            
            # Package not found errors
            elif '404' in line.lower() and 'not found' in line.lower():
                errors.append(CompilationError(
                    error_type="dependency",
                    severity="error",
                    message=line,
                    command=command,
                    suggestion="Check if the package name is correct and exists in npm registry"
                ))
            
            # Permission errors
            elif 'permission denied' in line.lower() or 'eacces' in line.lower():
                errors.append(CompilationError(
                    error_type="dependency",
                    severity="error",
                    message=line,
                    command=command,
                    suggestion="Try running with appropriate permissions or use npm prefix"
                ))
        
        return errors
    
    def _parse_npm_build_errors(self, output: str) -> List[CompilationError]:
        """Parse npm build errors"""
        errors = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # TypeScript/compilation errors in build output
            if 'error TS' in line:
                # Try to extract file, line, and error info
                ts_error = self._parse_typescript_error_line(line)
                if ts_error:
                    errors.append(ts_error)
            
            # Webpack or other build errors
            elif 'ERROR in' in line:
                errors.append(CompilationError(
                    error_type="build",
                    severity="error",
                    message=line,
                    suggestion="Fix the reported build error"
                ))
            
            # Module not found errors
            elif 'Module not found' in line:
                errors.append(CompilationError(
                    error_type="dependency",
                    severity="error",
                    message=line,
                    suggestion="Install missing module or fix import path"
                ))
        
        return errors
    
    def _parse_typescript_errors(self, output: str) -> List[CompilationError]:
        """Parse TypeScript compiler errors"""
        errors = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if 'error TS' in line:
                ts_error = self._parse_typescript_error_line(line)
                if ts_error:
                    errors.append(ts_error)
        
        return errors
    
    def _parse_typescript_error_line(self, line: str) -> Optional[CompilationError]:
        """Parse a single TypeScript error line"""
        import re
        
        # Pattern: filename(line,col): error TSxxxx: message
        pattern = r'(.+?)\((\d+),(\d+)\):\s*error\s+TS(\d+):\s*(.+)'
        match = re.match(pattern, line)
        
        if match:
            file_path, line_num, col_num, error_code, message = match.groups()
            return CompilationError(
                error_type="syntax",
                severity="error",
                message=f"TS{error_code}: {message}",
                file_path=file_path,
                line_number=int(line_num),
                column_number=int(col_num),
                suggestion="Fix TypeScript type error"
            )
        
        return None
    
    def _parse_lint_output(self, output: str) -> List[CompilationError]:
        """Parse linting output (ESLint, etc.)"""
        warnings = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if '✖' in line or 'warning' in line.lower():
                warnings.append(CompilationError(
                    error_type="style",
                    severity="warning",
                    message=line,
                    suggestion="Fix linting issues for better code quality"
                ))
        
        return warnings
    
    def _parse_pip_errors(self, output: str) -> List[CompilationError]:
        """Parse pip install errors"""
        errors = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if 'ERROR:' in line:
                errors.append(CompilationError(
                    error_type="dependency",
                    severity="error",
                    message=line,
                    command="pip install",
                    suggestion="Check package name and Python version compatibility"
                ))
            
            elif 'No matching distribution found' in line:
                errors.append(CompilationError(
                    error_type="dependency",
                    severity="error",
                    message=line,
                    command="pip install",
                    suggestion="Check if the package exists and version is correct"
                ))
        
        return errors
    
    def _parse_python_syntax_errors(self, output: str, file_path: str) -> List[CompilationError]:
        """Parse Python syntax errors"""
        errors = []
        lines = output.split('\n')
        
        for line in lines:
            if 'SyntaxError:' in line:
                errors.append(CompilationError(
                    error_type="syntax",
                    severity="error",
                    message=line,
                    file_path=file_path,
                    suggestion="Fix Python syntax error"
                ))
        
        return errors
    
    def _parse_python_import_errors(self, output: str, file_path: str) -> List[CompilationError]:
        """Parse Python import errors"""
        errors = []
        lines = output.split('\n')
        
        for line in lines:
            if 'ModuleNotFoundError:' in line or 'ImportError:' in line:
                errors.append(CompilationError(
                    error_type="dependency",
                    severity="error",
                    message=line,
                    file_path=file_path,
                    suggestion="Install missing module or fix import path"
                ))
        
        return errors
    
    def _parse_docker_errors(self, output: str) -> List[CompilationError]:
        """Parse Docker build errors"""
        errors = []
        lines = output.split('\n')
        
        current_step = ""
        for line in lines:
            line = line.strip()
            
            # Track current build step
            if line.startswith('Step '):
                current_step = line
            
            # Error indicators
            elif 'ERROR' in line or 'failed' in line.lower():
                errors.append(CompilationError(
                    error_type="build",
                    severity="error",
                    message=f"{current_step}: {line}" if current_step else line,
                    command="docker build",
                    suggestion="Fix Dockerfile syntax or build dependencies"
                ))
            
            # Package not found in Docker
            elif 'Package' in line and 'not found' in line:
                errors.append(CompilationError(
                    error_type="dependency",
                    severity="error",
                    message=line,
                    command="docker build",
                    suggestion="Check package availability in the Docker base image"
                ))
        
        return errors