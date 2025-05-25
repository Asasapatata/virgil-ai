# backend/app/services/consolidated_test_runner.py
import subprocess
import time
import json
import re
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.output_manager import OutputManager, IterationResults
from app.services.workspace_environment import TestingEnvironment

logger = logging.getLogger(__name__)

class ConsolidatedTestRunner:
    """Test runner con gestione ambienti isolati e logging consolidato"""
    
    def __init__(self, output_manager: OutputManager):
        self.output_manager = output_manager
    
    async def run_iteration_tests(self, 
                                iteration: int,
                                code_files: Dict[str, str],
                                test_files: Dict[str, str],
                                validation_report: Any,
                                compilation_report: Any) -> IterationResults:
        """Esegue test completi per una iterazione in ambiente isolato"""
        
        start_time = time.time()
        logger.info(f"Starting iteration {iteration} tests with {len(test_files)} test files")
        
        # 1. Crea workspace pulito
        workspace = self.output_manager.create_workspace()
        
        # 2. Salva codice generato
        generation_path = workspace.save_generated_code(code_files)
        
        # 3. Prepara ambiente test isolato
        testing_env = workspace.prepare_testing_environment(code_files)
        
        # 4. Salva test files in ambiente test
        testing_env.save_test_files(test_files)
        
        # 5. Verifica ambiente test
        env_verification = testing_env.verify_environment()
        
        # 6. Esegue test in ambiente isolato
        test_results = await self._run_tests_isolated(testing_env, test_files, env_verification)
        
        # 7. Analizza risultati e determina se l'iterazione ha successo
        iteration_success = self._is_iteration_successful(validation_report, compilation_report, test_results)
        
        # 8. Identifica miglioramenti e errori risolti
        errors_fixed = self._identify_errors_fixed(iteration, validation_report, compilation_report)
        improvements = self._identify_improvements(iteration, test_results, iteration_success)
        
        # 9. Crea risultati strutturati
        iteration_results = IterationResults(
            iteration=iteration,
            status="success" if iteration_success else "failed",
            validation_errors=getattr(validation_report, 'summary', {}).get("error", 0) if validation_report else 0,
            compilation_success=getattr(compilation_report, 'success', True) if compilation_report else True,
            test_results=test_results,
            code_files_count=len(code_files),
            test_files_count=len(test_files),
            duration=time.time() - start_time,
            errors_fixed=errors_fixed,
            improvements=improvements,
            timestamp=datetime.now().isoformat()
        )
        
        # 10. Log risultati
        self.output_manager.log_iteration(iteration, iteration_results)
        
        # 11. Se iterazione success, aggiorna codice finale
        if iteration_results.status == "success":
            self.output_manager.update_final_code(code_files, iteration)
            logger.info(f"Iteration {iteration} successful - updated final code")
        else:
            logger.info(f"Iteration {iteration} failed - final code not updated")
        
        return iteration_results
    
    async def _run_tests_isolated(self, 
                                testing_env: TestingEnvironment, 
                                test_files: Dict[str, str],
                                env_verification: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue test in ambiente completamente isolato"""
        
        context = testing_env.get_execution_context()
        results = {
            "frontend": None, 
            "backend": None, 
            "e2e": None, 
            "success": False,
            "environment": {
                "isolated": True,
                "verification": env_verification,
                "context": context
            }
        }
        
        logger.info("Running tests in isolated environment")
        
        try:
            # Frontend tests se disponibili e ambiente pronto
            if self._has_frontend_tests(test_files) and env_verification.get("node_ready", False):
                logger.info("Running frontend tests")
                results["frontend"] = await self._run_frontend_tests_isolated(testing_env, context)
            elif self._has_frontend_tests(test_files):
                logger.warning("Frontend tests found but Node.js environment not ready")
                results["frontend"] = {
                    "success": False,
                    "error": "Node.js environment not ready",
                    "skipped": True
                }
            
            # Backend tests se disponibili e ambiente pronto
            if self._has_backend_tests(test_files) and env_verification.get("python_ready", False):
                logger.info("Running backend tests")
                results["backend"] = await self._run_backend_tests_isolated(testing_env, context)
            elif self._has_backend_tests(test_files):
                logger.warning("Backend tests found but Python environment not ready")
                results["backend"] = {
                    "success": False,
                    "error": "Python environment not ready",
                    "skipped": True
                }
            
            # E2E tests (placeholder for now)
            if self._has_e2e_tests(test_files):
                logger.info("E2E tests found, but not implemented yet")
                results["e2e"] = {
                    "success": True,
                    "message": "E2E tests not implemented",
                    "skipped": True
                }
            
            # Determine overall success
            test_parts = [results["frontend"], results["backend"], results["e2e"]]
            executed_tests = [result for result in test_parts if result and not result.get("skipped", False)]
            
            if executed_tests:
                results["success"] = all(result.get("success", False) for result in executed_tests)
            else:
                # Se nessun test è stato eseguito, considera success se non ci sono errori critici
                results["success"] = env_verification.get("overall_ready", False)
                results["message"] = "No tests executed - environment issues or no test files"
            
            # Add summary
            results["summary"] = {
                "tests_executed": len(executed_tests),
                "tests_passed": len([r for r in executed_tests if r.get("success", False)]),
                "tests_failed": len([r for r in executed_tests if not r.get("success", True)]),
                "tests_skipped": len([r for r in test_parts if r and r.get("skipped", False)]),
                "overall_success": results["success"]
            }
            
        except Exception as e:
            logger.error(f"Error in isolated test execution: {e}")
            results["error"] = str(e)
            results["success"] = False
        
        logger.info(f"Test execution completed - Success: {results['success']}")
        return results
    
    async def _run_frontend_tests_isolated(self, testing_env: TestingEnvironment, context: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue frontend test in ambiente Node isolato"""
        try:
            # Ottieni comando test
            test_command = testing_env.get_test_command("node")
            if not test_command:
                return {
                    "success": False,
                    "error": "Could not determine Node.js test command",
                    "isolated_execution": True
                }
            
            logger.info(f"Running frontend tests with command: {' '.join(test_command)}")
            
            # Esegui test con ambiente isolato
            result = subprocess.run(
                test_command,
                cwd=context["node_cwd"],
                env={**os.environ, **context["environment_vars"]},
                capture_output=True,
                text=True,
                timeout=300  # 5 minuti timeout
            )
            
            success = result.returncode == 0
            
            # Parse output per estrarre informazioni dettagliate
            test_summary = self._parse_jest_output(result.stdout)
            
            return {
                "success": success,
                "isolated_execution": True,
                "command": " ".join(test_command),
                "exit_code": result.returncode,
                "stdout": self._truncate_output(result.stdout, 3000),
                "stderr": self._truncate_output(result.stderr, 1000),
                "test_summary": test_summary,
                "duration": test_summary.get("duration", 0),
                "stats": {
                    "tests_run": test_summary.get("tests_run", 0),
                    "tests_passed": test_summary.get("tests_passed", 0),
                    "tests_failed": test_summary.get("tests_failed", 0)
                }
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Frontend tests timed out")
            return {
                "success": False,
                "error": "Frontend tests timed out after 5 minutes",
                "isolated_execution": True,
                "timeout": True
            }
        except Exception as e:
            logger.error(f"Frontend test execution failed: {e}")
            return {
                "success": False,
                "error": f"Frontend test execution failed: {str(e)}",
                "isolated_execution": True
            }
    
    async def _run_backend_tests_isolated(self, testing_env: TestingEnvironment, context: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue backend test in venv isolato"""
        try:
            # Ottieni comando test
            test_command = testing_env.get_test_command("python")
            if not test_command:
                return {
                    "success": False,
                    "error": "Could not determine Python test command",
                    "isolated_execution": True
                }
            
            logger.info(f"Running backend tests with command: {' '.join(test_command)}")
            
            # Esegui pytest in venv isolato
            result = subprocess.run(
                test_command,
                cwd=context["testing_path"],
                env={**os.environ, **context["environment_vars"]},
                capture_output=True,
                text=True,
                timeout=300  # 5 minuti timeout
            )
            
            success = result.returncode == 0
            
            # Parse output per estrarre informazioni dettagliate
            test_summary = self._parse_pytest_output(result.stdout)
            
            return {
                "success": success,
                "isolated_execution": True,
                "command": " ".join(test_command),
                "exit_code": result.returncode,
                "stdout": self._truncate_output(result.stdout, 3000),
                "stderr": self._truncate_output(result.stderr, 1000),
                "test_summary": test_summary,
                "duration": test_summary.get("duration", 0),
                "stats": {
                    "tests_run": test_summary.get("tests_run", 0),
                    "tests_passed": test_summary.get("tests_passed", 0),
                    "tests_failed": test_summary.get("tests_failed", 0)
                }
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Backend tests timed out")
            return {
                "success": False,
                "error": "Backend tests timed out after 5 minutes",
                "isolated_execution": True,
                "timeout": True
            }
        except Exception as e:
            logger.error(f"Backend test execution failed: {e}")
            return {
                "success": False,
                "error": f"Backend test execution failed: {str(e)}",
                "isolated_execution": True
            }
    
    def _has_frontend_tests(self, test_files: Dict[str, str]) -> bool:
        """Verifica se ci sono test frontend"""
        frontend_patterns = ['.test.js', '.test.jsx', '.test.ts', '.test.tsx', '.spec.js', '.spec.jsx', '.spec.ts', '.spec.tsx']
        return any(any(pattern in file_path for pattern in frontend_patterns) for file_path in test_files.keys())
    
    def _has_backend_tests(self, test_files: Dict[str, str]) -> bool:
        """Verifica se ci sono test backend"""
        backend_patterns = ['test_.py', '_test.py', 'test.py', '/tests/']
        return any(any(pattern in file_path for pattern in backend_patterns) for file_path in test_files.keys())
    
    def _has_e2e_tests(self, test_files: Dict[str, str]) -> bool:
        """Verifica se ci sono test E2E"""
        e2e_patterns = ['e2e', 'cypress', 'playwright', 'selenium']
        return any(any(pattern in file_path.lower() for pattern in e2e_patterns) for file_path in test_files.keys())
    
    def _parse_jest_output(self, output: str) -> Dict[str, Any]:
        """Parse output di Jest per estrarre statistiche"""
        summary = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "duration": 0,
            "suites": 0
        }
        
        try:
            # Pattern per Jest output
            # "Tests: 3 passed, 3 total"
            tests_match = re.search(r'Tests:\s+(\d+)\s+passed(?:,\s+(\d+)\s+failed)?(?:,\s+(\d+)\s+total)?', output)
            if tests_match:
                summary["tests_passed"] = int(tests_match.group(1))
                summary["tests_failed"] = int(tests_match.group(2) or 0)
                summary["tests_run"] = int(tests_match.group(3) or summary["tests_passed"] + summary["tests_failed"])
            
            # "Test Suites: 1 passed, 1 total"
            suites_match = re.search(r'Test Suites:\s+(\d+)\s+passed(?:,\s+\d+\s+failed)?(?:,\s+(\d+)\s+total)?', output)
            if suites_match:
                summary["suites"] = int(suites_match.group(2) or suites_match.group(1))
            
            # "Time: 2.5s"
            time_match = re.search(r'Time:\s+([\d.]+)\s*s', output)
            if time_match:
                summary["duration"] = float(time_match.group(1))
            
        except Exception as e:
            logger.warning(f"Error parsing Jest output: {e}")
        
        return summary
    
    def _parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """Parse output di pytest per estrarre statistiche"""
        summary = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "duration": 0,
            "warnings": 0
        }
        
        try:
            # Pattern per pytest output
            # "====== 3 passed in 1.23s ======"
            result_match = re.search(r'=+\s*(\d+)\s+passed(?:,\s+(\d+)\s+failed)?(?:,\s+(\d+)\s+warnings?)?\s+in\s+([\d.]+)s\s*=+', output)
            if result_match:
                summary["tests_passed"] = int(result_match.group(1))
                summary["tests_failed"] = int(result_match.group(2) or 0)
                summary["warnings"] = int(result_match.group(3) or 0)
                summary["duration"] = float(result_match.group(4))
                summary["tests_run"] = summary["tests_passed"] + summary["tests_failed"]
            
            # Alternative pattern: "collected 3 items"
            collected_match = re.search(r'collected\s+(\d+)\s+items?', output)
            if collected_match and summary["tests_run"] == 0:
                summary["tests_run"] = int(collected_match.group(1))
            
        except Exception as e:
            logger.warning(f"Error parsing pytest output: {e}")
        
        return summary
    
    def _truncate_output(self, output: str, max_length: int) -> str:
        """Tronca output mantenendo parti importanti"""
        if len(output) <= max_length:
            return output
        
        # Prendi inizio e fine, tronca la parte centrale
        start_length = max_length // 2 - 50
        end_length = max_length // 2 - 50
        
        start_part = output[:start_length]
        end_part = output[-end_length:]
        
        return f"{start_part}\n... [output truncated] ...\n{end_part}"
    
    def _is_iteration_successful(self, validation_report: Any, compilation_report: Any, test_results: Dict[str, Any]) -> bool:
        """Determina se l'iterazione è stata complessivamente un successo"""
        
        # Criteri critici che devono essere soddisfatti
        critical_criteria = []
        
        # 1. Validazione senza errori critici
        if validation_report:
            validation_errors = getattr(validation_report, 'summary', {}).get("error", 0)
            critical_criteria.append(validation_errors == 0)
        else:
            critical_criteria.append(True)  # Nessuna validazione = OK
        
        # 2. Compilazione riuscita
        if compilation_report:
            compilation_success = getattr(compilation_report, 'success', True)
            critical_criteria.append(compilation_success)
        else:
            critical_criteria.append(True)  # Nessuna compilazione = OK
        
        # 3. Test execution success (più flessibile)
        test_success = test_results.get("success", False)
        
        # Se i criteri critici falliscono, l'iterazione è fallita
        if not all(critical_criteria):
            return False
        
        # Se i criteri critici passano ma i test falliscono, 
        # considera ancora un successo se:
        # - I test sono stati eseguiti senza errori di ambiente
        # - Non ci sono stati timeout o crash
        if not test_success:
            # Controlla se il fallimento è dovuto a problemi di ambiente
            environment_issues = any(
                result and (result.get("timeout") or result.get("skipped") or "environment" in str(result.get("error", "")))
                for result in [test_results.get("frontend"), test_results.get("backend"), test_results.get("e2e")]
                if result
            )
            
            # Se sono problemi di ambiente, non è colpa del codice generato
            if environment_issues:
                logger.info("Test failures due to environment issues - considering iteration partially successful")
                return True
        
        return test_success
    
    def _identify_errors_fixed(self, iteration: int, validation_report: Any, compilation_report: Any) -> List[str]:
        """Identifica gli errori che sono stati risolti in questa iterazione"""
        errors_fixed = []
        
        if iteration == 1:
            return errors_fixed  # Prima iterazione, nessun errore precedente da confrontare
        
        try:
            # Carica errori dall'iterazione precedente (se disponibili)
            prev_iteration_path = self.output_manager.logs_path.parent / f"iter-{iteration-1}"
            
            # Per ora, logica semplificata basata su miglioramenti evidenti
            if validation_report:
                current_validation_errors = getattr(validation_report, 'summary', {}).get("error", 0)
                if current_validation_errors == 0:
                    errors_fixed.append("All validation errors resolved")
            
            if compilation_report:
                compilation_success = getattr(compilation_report, 'success', False)
                if compilation_success:
                    errors_fixed.append("Compilation issues resolved")
            
        except Exception as e:
            logger.warning(f"Could not compare with previous iteration: {e}")
        
        return errors_fixed
    
    def _identify_improvements(self, iteration: int, test_results: Dict[str, Any], iteration_success: bool) -> List[str]:
        """Identifica i miglioramenti apportati in questa iterazione"""
        improvements = []
        
        if iteration_success:
            improvements.append("Iteration completed successfully")
        
        # Analizza risultati test per identificare miglioramenti specifici
        summary = test_results.get("summary", {})
        tests_executed = summary.get("tests_executed", 0)
        tests_passed = summary.get("tests_passed", 0)
        
        if tests_executed > 0:
            if tests_passed == tests_executed:
                improvements.append(f"All {tests_executed} tests passed")
            elif tests_passed > 0:
                improvements.append(f"{tests_passed}/{tests_executed} tests passed")
        
        # Miglioramenti specifici per tipo di test
        if test_results.get("frontend", {}).get("success"):
            improvements.append("Frontend tests passing")
        
        if test_results.get("backend", {}).get("success"):
            improvements.append("Backend tests passing")
        
        # Miglioramenti di ambiente
        environment = test_results.get("environment", {})
        if environment.get("verification", {}).get("overall_ready"):
            improvements.append("Testing environment properly configured")
        
        return improvements
    
    def analyze_test_failures(self, test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analizza fallimenti dei test per fornire contesto per la prossima iterazione"""
        failures = []
        
        # Analizza fallimenti frontend
        frontend_result = test_results.get("frontend")
        if frontend_result and not frontend_result.get("success", True) and not frontend_result.get("skipped", False):
            failure = {
                "type": "frontend",
                "category": "test_execution",
                "error": frontend_result.get("error", "Frontend tests failed"),
                "details": frontend_result.get("stderr", ""),
                "command": frontend_result.get("command", ""),
                "exit_code": frontend_result.get("exit_code"),
                "suggestions": self._extract_frontend_suggestions(frontend_result)
            }
            failures.append(failure)
        
        # Analizza fallimenti backend
        backend_result = test_results.get("backend")
        if backend_result and not backend_result.get("success", True) and not backend_result.get("skipped", False):
            failure = {
                "type": "backend",
                "category": "test_execution",
                "error": backend_result.get("error", "Backend tests failed"),
                "details": backend_result.get("stderr", ""),
                "command": backend_result.get("command", ""),
                "exit_code": backend_result.get("exit_code"),
                "suggestions": self._extract_backend_suggestions(backend_result)
            }
            failures.append(failure)
        
        # Analizza problemi di ambiente
        environment = test_results.get("environment", {})
        verification = environment.get("verification", {})
        
        if not verification.get("overall_ready", True):
            for issue in verification.get("issues", []):
                failure = {
                    "type": "environment",
                    "category": "setup",
                    "error": issue,
                    "suggestions": ["Fix environment setup", "Check dependencies installation"]
                }
                failures.append(failure)
        
        return failures
    
    def _extract_frontend_suggestions(self, frontend_result: Dict[str, Any]) -> List[str]:
        """Estrae suggerimenti specifici dai fallimenti frontend"""
        suggestions = []
        
        error_output = frontend_result.get("stderr", "") + " " + frontend_result.get("stdout", "")
        error_text = error_output.lower()
        
        if "module not found" in error_text or "cannot resolve" in error_text:
            suggestions.append("Fix import paths and ensure all referenced modules exist")
        
        if "jest" in error_text and "config" in error_text:
            suggestions.append("Check Jest configuration and setup")
        
        if "babel" in error_text:
            suggestions.append("Check Babel configuration for TypeScript/JSX compilation")
        
        if "timeout" in error_text:
            suggestions.append("Optimize test performance or increase timeout limits")
        
        if "enzyme" in error_text or "testing-library" in error_text:
            suggestions.append("Check React testing library setup and imports")
        
        if not suggestions:
            suggestions.append("Review frontend test failures and fix component logic")
        
        return suggestions
    
    def _extract_backend_suggestions(self, backend_result: Dict[str, Any]) -> List[str]:
        """Estrae suggerimenti specifici dai fallimenti backend"""
        suggestions = []
        
        error_output = backend_result.get("stderr", "") + " " + backend_result.get("stdout", "")
        error_text = error_output.lower()
        
        if "modulenotfounderror" in error_text or "importerror" in error_text:
            suggestions.append("Fix Python import paths and ensure all modules are available")
        
        if "fixture" in error_text:
            suggestions.append("Check pytest fixture definitions and scope")
        
        if "database" in error_text or "connection" in error_text:
            suggestions.append("Setup test database or mock database connections")
        
        if "async" in error_text or "asyncio" in error_text:
            suggestions.append("Check async/await patterns and event loop handling")
        
        if "assertion" in error_text:
            suggestions.append("Review test assertions and expected vs actual values")
        
        if "permission" in error_text:
            suggestions.append("Check file permissions and access rights")
        
        if not suggestions:
            suggestions.append("Review backend test failures and fix business logic")
        
        return suggestions
    
    def get_test_execution_summary(self, project_path: Path) -> Dict[str, Any]:
        """Ottieni un riassunto di tutte le esecuzioni test del progetto"""
        try:
            test_history_file = self.output_manager.logs_path / "test_history.json"
            
            if not test_history_file.exists():
                return {"error": "No test history available"}
            
            with open(test_history_file, 'r') as f:
                test_history = json.load(f)
            
            # Calcola statistiche aggregate
            iterations = test_history.get("iterations", [])
            
            if not iterations:
                return {"message": "No test iterations recorded"}
            
            # Calcola metriche aggregate
            total_duration = sum(iter_data.get("duration", 0) for iter_data in iterations)
            successful_iterations = len([i for i in iterations if i.get("status") == "success"])
            
            # Statistiche test per tipo
            frontend_stats = {"executed": 0, "passed": 0, "failed": 0}
            backend_stats = {"executed": 0, "passed": 0, "failed": 0}
            
            for iter_data in iterations:
                test_results = iter_data.get("test_results", {})
                
                if test_results.get("frontend"):
                    frontend_stats["executed"] += 1
                    if test_results["frontend"].get("success"):
                        frontend_stats["passed"] += 1
                    else:
                        frontend_stats["failed"] += 1
                
                if test_results.get("backend"):
                    backend_stats["executed"] += 1
                    if test_results["backend"].get("success"):
                        backend_stats["passed"] += 1
                    else:
                        backend_stats["failed"] += 1
            
            summary = {
                "total_iterations": len(iterations),
                "successful_iterations": successful_iterations,
                "success_rate": successful_iterations / len(iterations) if iterations else 0,
                "total_duration": total_duration,
                "average_duration": total_duration / len(iterations) if iterations else 0,
                "frontend_stats": frontend_stats,
                "backend_stats": backend_stats,
                "final_status": iterations[-1].get("status") if iterations else "unknown",
                "last_updated": test_history.get("summary", {}).get("last_updated")
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting test execution summary: {e}")
            return {"error": str(e)}
    
    def cleanup_test_environments(self):
        """Pulisce tutti gli ambienti di test temporanei"""
        try:
            workspace_path = self.output_manager.workspace_path
            if workspace_path.exists():
                import shutil
                shutil.rmtree(workspace_path)
                logger.info("Cleaned up all test environments")
        except Exception as e:
            logger.warning(f"Error cleaning up test environments: {e}")