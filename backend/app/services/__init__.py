# backend/app/services/__init__.py

# Servizi esistenti
from .llm_service import LLMService
from .code_generator import CodeGenerator
from .test_generator import TestGenerator
from .test_runner import TestRunner
from .orchestrator import OrchestratorAgent

# 🔥 NUOVI SERVIZI
from .code_validator import CodeValidator
from .compilation_checker import CompilationChecker
from .iteration_manager import IterationManager
from .enhanced_test_agent import EnhancedTestAgent
from .updated_orchestrator import UpdatedOrchestratorAgent
from .requirements_analyzer import RequirementsAnalyzer

__all__ = [
    'LLMService',
    'CodeGenerator', 
    'TestGenerator',
    'TestRunner',
    'OrchestratorAgent',
    # Nuovi servizi
    'CodeValidator',
    'CompilationChecker', 
    'IterationManager',
    'EnhancedTestAgent',
    'UpdatedOrchestratorAgent',
    'RequirementsAnalyzer'
]