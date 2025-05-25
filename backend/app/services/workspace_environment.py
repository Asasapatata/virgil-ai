# backend/app/services/workspace_environment.py
import subprocess
import shutil
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class WorkspaceEnvironment:
    """Gestisce ambiente di lavoro isolato per generazione e test"""
    
    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.generation_path = workspace_path / "generation"
        self.testing_path = workspace_path / "testing"
        
    def clean_and_prepare(self):
        """Prepara ambiente pulito per nuova iterazione"""
        if self.workspace_path.exists():
            shutil.rmtree(self.workspace_path)
        
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.generation_path.mkdir(parents=True, exist_ok=True)
        self.testing_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Prepared clean workspace at {self.workspace_path}")
    
    def save_generated_code(self, code_files: Dict[str, str]) -> Path:
        """Salva codice generato in ambiente di generazione"""
        for file_path, content in code_files.items():
            full_path = self.generation_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
        
        logger.info(f"Generated {len(code_files)} files in {self.generation_path}")
        return self.generation_path
    
    def prepare_testing_environment(self, code_files: Dict[str, str]) -> 'TestingEnvironment':
        """Prepara ambiente isolato per test con dipendenze"""
        
        # Copia codice in ambiente test
        for file_path, content in code_files.items():
            full_path = self.testing_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
        
        logger.info(f"Copied {len(code_files)} files to testing environment")
        
        # Crea ambiente testing specializzato
        testing_env = TestingEnvironment(self.testing_path)
        testing_env.setup_dependencies()
        
        return testing_env


class TestingEnvironment:
    """Ambiente isolato per esecuzione test con gestione dipendenze"""
    
    def __init__(self, testing_path: Path):
        self.testing_path = testing_path
        self.venv_path = testing_path / ".venv"
        self.node_modules_path = testing_path / "node_modules"
        self.deps_setup_complete = False
        
    def setup_dependencies(self):
        """Setup dipendenze in ambiente isolato"""
        logger.info("Setting up dependencies in isolated testing environment")
        
        try:
            # Setup Python virtual environment se ci sono file Python
            if self._has_python_files():
                self._setup_python_env()
            
            # Setup Node.js dependencies se ci sono file Node
            if self._has_node_files():
                self._setup_node_env()
            
            # Setup test frameworks specifici
            self._setup_test_frameworks()
            
            self.deps_setup_complete = True
            logger.info("Dependencies setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error setting up dependencies: {e}")
            self.deps_setup_complete = False
    
    def _has_python_files(self) -> bool:
        """Verifica se ci sono file Python nel progetto"""
        python_files = list(self.testing_path.rglob("*.py"))
        requirements_file = self.testing_path / "requirements.txt"
        return len(python_files) > 0 or requirements_file.exists()
    
    def _has_node_files(self) -> bool:
        """Verifica se ci sono file Node.js nel progetto"""
        js_files = list(self.testing_path.rglob("*.js")) + list(self.testing_path.rglob("*.ts"))
        jsx_files = list(self.testing_path.rglob("*.jsx")) + list(self.testing_path.rglob("*.tsx"))
        package_json = self.testing_path / "package.json"
        return len(js_files) > 0 or len(jsx_files) > 0 or package_json.exists()
    
    def _setup_python_env(self):
        """Setup ambiente Python isolato"""
        logger.info("Setting up Python virtual environment")
        
        try:
            # Crea virtual environment se non esiste
            if not self.venv_path.exists():
                result = subprocess.run([
                    "python", "-m", "venv", str(self.venv_path)
                ], check=True, capture_output=True, text=True, timeout=60)
                
                logger.info("Python virtual environment created")
            
            # Determina python executable
            python_exe = self._get_venv_python()
            
            if not python_exe or not python_exe.exists():
                raise Exception("Could not find Python executable in virtual environment")
            
            # Upgrade pip
            subprocess.run([
                str(python_exe), "-m", "pip", "install", "--upgrade", "pip"
            ], check=True, capture_output=True, text=True, timeout=60)
            
            # Installa dipendenze base per test
            test_packages = ["pytest", "pytest-asyncio", "pytest-mock"]
            subprocess.run([
                str(python_exe), "-m", "pip", "install"
            ] + test_packages, check=True, capture_output=True, text=True, timeout=120)
            
            logger.info("Installed base Python test packages")
            
            # Installa dipendenze progetto se esistono
            requirements_file = self.testing_path / "requirements.txt"
            if requirements_file.exists():
                logger.info("Installing project Python dependencies")
                subprocess.run([
                    str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)
                ], check=True, capture_output=True, text=True, timeout=300)
                
                logger.info("Project Python dependencies installed")
            
            # Verifica installazione
            result = subprocess.run([
                str(python_exe), "-c", "import pytest; print('pytest available')"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("Python environment verification successful")
            else:
                logger.warning("Python environment verification failed")
                
        except subprocess.TimeoutExpired:
            logger.error("Python environment setup timed out")
            raise Exception("Python environment setup timed out")
        except subprocess.CalledProcessError as e:
            logger.error(f"Python environment setup failed: {e}")
            logger.error(f"Command output: {e.stdout}")
            logger.error(f"Command error: {e.stderr}")
            raise Exception(f"Python environment setup failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Python setup: {e}")
            raise
    
    def _setup_node_env(self):
        """Setup ambiente Node.js isolato"""
        logger.info("Setting up Node.js environment")
        
        try:
            package_json = self.testing_path / "package.json"
            
            # Se non esiste package.json, creane uno minimale
            if not package_json.exists():
                self._create_minimal_package_json()
            
            # Se node_modules non esiste, installa dipendenze
            if not self.node_modules_path.exists():
                logger.info("Installing Node.js dependencies")
                
                # npm install con timeout
                result = subprocess.run([
                    "npm", "install", "--no-audit", "--no-fund"
                ], cwd=self.testing_path, check=True, capture_output=True, text=True, timeout=300)
                
                logger.info("Node.js dependencies installed")
            
            # Installa test frameworks se non presenti in package.json
            self._ensure_test_frameworks_installed()
            
            # Verifica installazione
            result = subprocess.run([
                "npm", "list", "jest"
            ], cwd=self.testing_path, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("Node.js environment verification successful")
            else:
                logger.warning("Jest not found, but continuing...")
                
        except subprocess.TimeoutExpired:
            logger.error("Node.js environment setup timed out")
            raise Exception("Node.js environment setup timed out")
        except subprocess.CalledProcessError as e:
            logger.error(f"Node.js environment setup failed: {e}")
            logger.error(f"Command output: {e.stdout}")
            logger.error(f"Command error: {e.stderr}")
            raise Exception(f"Node.js environment setup failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Node.js setup: {e}")
            raise
    
    def _create_minimal_package_json(self):
        """Crea un package.json minimale per testing"""
        minimal_package = {
            "name": "test-environment",
            "version": "1.0.0",
            "description": "Temporary testing environment",
            "scripts": {
                "test": "jest --watchAll=false",
                "test:coverage": "jest --coverage --watchAll=false"
            },
            "devDependencies": {}
        }
        
        package_json_path = self.testing_path / "package.json"
        with open(package_json_path, 'w') as f:
            import json
            json.dump(minimal_package, f, indent=2)
        
        logger.info("Created minimal package.json for testing")
    
    def _ensure_test_frameworks_installed(self):
        """Assicura che i framework di test siano installati"""
        logger.info("Ensuring test frameworks are installed")
        
        # Lista di pacchetti test da installare se mancanti
        test_packages = []
        
        # Controlla se jest è già presente
        try:
            subprocess.run([
                "npm", "list", "jest"
            ], cwd=self.testing_path, check=True, capture_output=True, timeout=30)
        except:
            test_packages.append("jest")
        
        # Se ci sono file React, aggiungi testing library
        react_files = list(self.testing_path.rglob("*.jsx")) + list(self.testing_path.rglob("*.tsx"))
        if react_files:
            try:
                subprocess.run([
                    "npm", "list", "@testing-library/react"
                ], cwd=self.testing_path, check=True, capture_output=True, timeout=30)
            except:
                test_packages.extend([
                    "@testing-library/react",
                    "@testing-library/jest-dom",
                    "@testing-library/user-event"
                ])
        
        # Installa pacchetti mancanti
        if test_packages:
            logger.info(f"Installing missing test packages: {', '.join(test_packages)}")
            try:
                subprocess.run([
                    "npm", "install", "--save-dev", "--no-audit", "--no-fund"
                ] + test_packages, 
                cwd=self.testing_path, check=True, capture_output=True, text=True, timeout=180)
                
                logger.info("Test frameworks installed successfully")
            except Exception as e:
                logger.warning(f"Could not install test frameworks: {e}")
                # Non è critico, continua comunque
    
    def _setup_test_frameworks(self):
        """Setup configurazioni aggiuntive per framework di test"""
        logger.info("Setting up test framework configurations")
        
        # Setup Jest config se necessario
        if self._has_node_files():
            self._setup_jest_config()
        
        # Setup pytest config se necessario
        if self._has_python_files():
            self._setup_pytest_config()
    
    def _setup_jest_config(self):
        """Setup configurazione Jest"""
        jest_config_path = self.testing_path / "jest.config.js"
        
        if not jest_config_path.exists():
            # Configurazione Jest minimale
            jest_config = """module.exports = {
  testEnvironment: 'node',
  testMatch: [
    '**/__tests__/**/*.(js|jsx|ts|tsx)',
    '**/*.(test|spec).(js|jsx|ts|tsx)'
  ],
  transform: {
    '^.+\\.(js|jsx|ts|tsx): 'babel-jest',
  },
  moduleFileExtensions: ['js', 'jsx', 'ts', 'tsx', 'json'],
  collectCoverageFrom: [
    'src/**/*.(js|jsx|ts|tsx)',
    '!src/**/*.d.ts',
  ],
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
  testTimeout: 10000,
  verbose: true
};
"""
            
            # Se ci sono file React, usa configurazione React
            react_files = list(self.testing_path.rglob("*.jsx")) + list(self.testing_path.rglob("*.tsx"))
            if react_files:
                jest_config = """module.exports = {
  testEnvironment: 'jsdom',
  testMatch: [
    '**/__tests__/**/*.(js|jsx|ts|tsx)',
    '**/*.(test|spec).(js|jsx|ts|tsx)'
  ],
  transform: {
    '^.+\\.(js|jsx|ts|tsx): 'babel-jest',
  },
  moduleFileExtensions: ['js', 'jsx', 'ts', 'tsx', 'json'],
  setupFilesAfterEnv: ['@testing-library/jest-dom'],
  collectCoverageFrom: [
    'src/**/*.(js|jsx|ts|tsx)',
    '!src/**/*.d.ts',
  ],
  testTimeout: 10000,
  verbose: true,
  moduleNameMapping: {
    '\\.(css|less|scss|sass): 'identity-obj-proxy',
  }
};
"""
            
            jest_config_path.write_text(jest_config)
            logger.info("Created Jest configuration")
    
    def _setup_pytest_config(self):
        """Setup configurazione pytest"""
        pytest_ini_path = self.testing_path / "pytest.ini"
        
        if not pytest_ini_path.exists():
            pytest_config = """[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
"""
            pytest_ini_path.write_text(pytest_config)
            logger.info("Created pytest configuration")
    
    def _get_venv_python(self) -> Optional[Path]:
        """Ottieni il percorso dell'eseguibile Python nel virtual environment"""
        # Unix/Linux/macOS
        python_unix = self.venv_path / "bin" / "python"
        if python_unix.exists():
            return python_unix
        
        # Windows
        python_windows = self.venv_path / "Scripts" / "python.exe"
        if python_windows.exists():
            return python_windows
        
        return None
    
    def get_execution_context(self) -> Dict[str, Any]:
        """Ritorna contesto per esecuzione test"""
        context = {
            "testing_path": str(self.testing_path),
            "dependencies_ready": self.deps_setup_complete,
            "environment_vars": {
                "NODE_ENV": "test",
                "CI": "true",
                "FORCE_COLOR": "0",  # Disable colors in CI
                "NO_WATCH": "true"   # Disable watch mode
            }
        }
        
        # Aggiungi contesto Python se disponibile
        if self._has_python_files():
            python_exe = self._get_venv_python()
            context.update({
                "python_executable": str(python_exe) if python_exe else None,
                "python_path": str(self.testing_path),
                "has_python": True
            })
            
            # Aggiungi PYTHONPATH all'environment
            context["environment_vars"]["PYTHONPATH"] = str(self.testing_path)
        
        # Aggiungi contesto Node se disponibile
        if self._has_node_files():
            context.update({
                "node_cwd": str(self.testing_path),
                "has_node": True,
                "node_modules_available": self.node_modules_path.exists()
            })
        
        return context
    
    def verify_environment(self) -> Dict[str, Any]:
        """Verifica che l'ambiente sia correttamente configurato"""
        verification = {
            "python_ready": False,
            "node_ready": False,
            "dependencies_installed": self.deps_setup_complete,
            "issues": []
        }
        
        # Verifica Python
        if self._has_python_files():
            python_exe = self._get_venv_python()
            if python_exe and python_exe.exists():
                try:
                    result = subprocess.run([
                        str(python_exe), "-c", "import pytest; print('OK')"
                    ], capture_output=True, text=True, timeout=10)
                    
                    verification["python_ready"] = result.returncode == 0
                    if not verification["python_ready"]:
                        verification["issues"].append("Python pytest not available")
                except:
                    verification["issues"].append("Python environment verification failed")
            else:
                verification["issues"].append("Python executable not found")
        else:
            verification["python_ready"] = True  # Non needed
        
        # Verifica Node
        if self._has_node_files():
            try:
                result = subprocess.run([
                    "node", "--version"
                ], cwd=self.testing_path, capture_output=True, text=True, timeout=10)
                
                verification["node_ready"] = result.returncode == 0
                if not verification["node_ready"]:
                    verification["issues"].append("Node.js not available")
                
                # Verifica npm
                if verification["node_ready"]:
                    result = subprocess.run([
                        "npm", "list", "--depth=0"
                    ], cwd=self.testing_path, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode != 0:
                        verification["issues"].append("npm dependencies not properly installed")
                
            except:
                verification["node_ready"] = False
                verification["issues"].append("Node.js environment verification failed")
        else:
            verification["node_ready"] = True  # Not needed
        
        verification["overall_ready"] = (
            verification["python_ready"] and 
            verification["node_ready"] and 
            verification["dependencies_installed"]
        )
        
        if verification["overall_ready"]:
            logger.info("Testing environment verification successful")
        else:
            logger.warning(f"Testing environment issues: {verification['issues']}")
        
        return verification
    
    def cleanup(self):
        """Pulisce l'ambiente di test (chiamato da OutputManager)"""
        try:
            if self.testing_path.exists():
                # Rimuovi solo file temporanei, mantieni log se necessario
                temp_dirs = [self.venv_path, self.node_modules_path]
                for temp_dir in temp_dirs:
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir)
                
                logger.info("Testing environment cleaned up")
        except Exception as e:
            logger.warning(f"Error cleaning up testing environment: {e}")
    
    def get_test_command(self, test_type: str) -> Optional[List[str]]:
        """Ottieni comando per eseguire test di un tipo specifico"""
        
        if test_type == "python" and self._has_python_files():
            python_exe = self._get_venv_python()
            if python_exe:
                return [str(python_exe), "-m", "pytest", "-v", "--tb=short"]
        
        elif test_type == "node" and self._has_node_files():
            # Prova prima npm test, poi jest direttamente
            if (self.testing_path / "package.json").exists():
                return ["npm", "test", "--", "--watchAll=false"]
            else:
                return ["npx", "jest", "--watchAll=false"]
        
        elif test_type == "node_coverage" and self._has_node_files():
            return ["npm", "run", "test:coverage"]
        
        return None
    
    def save_test_files(self, test_files: Dict[str, str]):
        """Salva file di test nell'ambiente"""
        for file_path, content in test_files.items():
            full_path = self.testing_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
        
        logger.info(f"Saved {len(test_files)} test files to testing environment")