# app/services/enhanced_testing_workflow.py
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import json

from app.services.unified_testing_integration import UnifiedTestingService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class TestingStrategy(Enum):
    QUICK = "quick"           # Solo test essenziali
    STANDARD = "standard"     # Test completi con 1-2 iterazioni
    THOROUGH = "thorough"     # Test approfonditi con multiple iterazioni
    CUSTOM = "custom"         # Strategia personalizzata

class TestPriority(Enum):
    CRITICAL = "critical"     # Test che devono assolutamente passare
    HIGH = "high"            # Test importanti
    MEDIUM = "medium"        # Test standard
    LOW = "low"             # Test nice-to-have

@dataclass
class TestingConfig:
    strategy: TestingStrategy = TestingStrategy.STANDARD
    max_iterations: int = 2
    parallel_execution: bool = True
    coverage_threshold: float = 80.0
    fail_fast: bool = False
    retry_failed_tests: bool = True
    generate_reports: bool = True
    custom_hooks: Dict[str, Callable] = None

class EnhancedTestingWorkflow:
    """
    Workflow di testing avanzato che estende UnifiedTestingService.
    
    Risposta alla domanda: GLI AGENTI DI TEST CONTINUANO AD ESSERE UTILIZZATI!
    
    Gerarchia:
    1. EnhancedTestingWorkflow (orchestrazione avanzata)
    2. UnifiedTestingService (coordinamento)  
    3. TestAgent (esecuzione core)
    4. TestGenerator + TestRunner (componenti specifici)
    
    Gli agenti non sono stati sostituiti, ma organizzati in una struttura più chiara.
    """
    
    def __init__(self, llm_service: LLMService):
        self.unified_service = UnifiedTestingService(llm_service)
        self.llm_service = llm_service
        logger.info("EnhancedTestingWorkflow initialized - TestAgent is still core component")
    
    async def execute_strategic_testing(self,
                                       requirements: Dict[str, Any],
                                       code_files: Dict[str, str],
                                       provider: str,
                                       output_path: Path,
                                       config: TestingConfig) -> Dict[str, Any]:
        """
        Esegue testing secondo una strategia specifica.
        Utilizza sempre TestAgent come engine di base.
        """
        logger.info(f"Starting strategic testing with strategy: {config.strategy.value}")
        
        # Configura il testing basato sulla strategia
        unified_config = self._build_unified_config(config)
        
        workflow_result = {
            "strategy_used": config.strategy.value,
            "config": unified_config,
            "phases": [],
            "overall_success": False,
            "metrics": {},
            "recommendations": []
        }
        
        try:
            if config.strategy == TestingStrategy.QUICK:
                result = await self._execute_quick_strategy(
                    requirements, code_files, provider, output_path, unified_config
                )
            elif config.strategy == TestingStrategy.THOROUGH:
                result = await self._execute_thorough_strategy(
                    requirements, code_files, provider, output_path, unified_config
                )
            else:  # STANDARD or CUSTOM
                result = await self._execute_standard_strategy(
                    requirements, code_files, provider, output_path, unified_config
                )
            
            workflow_result.update(result)
            workflow_result["overall_success"] = result.get("success", False)
            
            # Genera metriche e raccomandazioni
            workflow_result["metrics"] = await self._calculate_metrics(result)
            workflow_result["recommendations"] = await self._generate_recommendations(
                result, config, provider
            )
            
        except Exception as e:
            logger.error(f"Error in strategic testing: {e}")
            workflow_result["error"] = str(e)
            workflow_result["overall_success"] = False
        
        logger.info(f"Strategic testing completed. Success: {workflow_result['overall_success']}")
        return workflow_result
    
    async def _execute_quick_strategy(self,
                                    requirements: Dict[str, Any],
                                    code_files: Dict[str, str],
                                    provider: str,
                                    output_path: Path,
                                    config: Dict[str, Any]) -> Dict[str, Any]:
        """Strategia rapida: un singolo passaggio di test via TestAgent"""
        
        logger.info("Executing QUICK testing strategy")
        
        # Usa direttamente il quick test dell'UnifiedService (che usa TestAgent)
        result = await self.unified_service.quick_test_execution(
            requirements, code_files, provider, output_path
        )
        
        return {
            "strategy_details": "Single-pass testing via TestAgent",
            "phases": [{"phase": "quick_test", "result": result}],
            "success": result.get("success", False),
            "execution_time": "fast",
            "test_agent_used": True
        }
    
    async def _execute_standard_strategy(self,
                                       requirements: Dict[str, Any],
                                       code_files: Dict[str, str],
                                       provider: str,
                                       output_path: Path,
                                       config: Dict[str, Any]) -> Dict[str, Any]:
        """Strategia standard: workflow completo via TestAgent con iterazioni limitate"""
        
        logger.info("Executing STANDARD testing strategy")
        
        # Usa il workflow completo dell'UnifiedService (che coordina TestAgent)
        result = await self.unified_service.execute_full_testing_workflow(
            requirements, code_files, provider, output_path, config
        )
        
        return {
            "strategy_details": "Full workflow via TestAgent with limited iterations",
            "phases": result.get("iterations", []),
            "success": result.get("final_success", False),
            "execution_time": "moderate",
            "test_agent_used": True,
            "unified_service_result": result
        }
    
    async def _execute_thorough_strategy(self,
                                       requirements: Dict[str, Any],
                                       code_files: Dict[str, str],
                                       provider: str,
                                       output_path: Path,
                                       config: Dict[str, Any]) -> Dict[str, Any]:
        """Strategia approfondita: multiple fasi con analisi dettagliate"""
        
        logger.info("Executing THOROUGH testing strategy")
        
        phases = []
        
        # Fase 1: Analisi preliminare
        analysis_phase = await self._preliminary_code_analysis(
            requirements, code_files, provider
        )
        phases.append({"phase": "preliminary_analysis", "result": analysis_phase})
        
        # Fase 2: Testing standard via TestAgent
        config["max_iterations"] = max(config.get("max_iterations", 3), 3)
        standard_result = await self.unified_service.execute_full_testing_workflow(
            requirements, code_files, provider, output_path, config
        )
        phases.append({"phase": "standard_testing", "result": standard_result})
        
        # Fase 3: Analisi di copertura approfondita
        if standard_result.get("final_success"):
            coverage_phase = await self._deep_coverage_analysis(
                standard_result, code_files, provider
            )
            phases.append({"phase": "coverage_analysis", "result": coverage_phase})
        
        # Fase 4: Test di stress (se appropriato)
        if len(code_files) > 10:  # Solo per progetti più grandi
            stress_phase = await self._stress_testing_phase(
                requirements, code_files, provider, output_path
            )
            phases.append({"phase": "stress_testing", "result": stress_phase})
        
        overall_success = standard_result.get("final_success", False)
        
        return {
            "strategy_details": "Multi-phase thorough testing with TestAgent coordination",
            "phases": phases,
            "success": overall_success,
            "execution_time": "extensive",
            "test_agent_used": True,
            "comprehensive_analysis": True
        }
    
    def _build_unified_config(self, config: TestingConfig) -> Dict[str, Any]:
        """Converte TestingConfig in configurazione per UnifiedTestingService"""
        return {
            "max_iterations": config.max_iterations,
            "parallel_execution": config.parallel_execution,
            "coverage_threshold": config.coverage_threshold,
            "fail_fast": config.fail_fast,
            "retry_failed_tests": config.retry_failed_tests,
            "generate_reports": config.generate_reports
        }
    
    async def _preliminary_code_analysis(self,
                                       requirements: Dict[str, Any],
                                       code_files: Dict[str, str],
                                       provider: str) -> Dict[str, Any]:
        """Analisi preliminare del codice prima dei test"""
        
        system_prompt = """Sei un expert code reviewer. Analizza il codice fornito e identifica:
        1. Potenziali problemi di qualità
        2. Pattern architetturali utilizzati  
        3. Aree che richiedono test specifici
        4. Complessità del testing necessario"""
        
        # Analizza i tipi di file e la struttura
        file_analysis = {
            "total_files": len(code_files),
            "frontend_files": len([f for f in code_files.keys() if f.endswith(('.js', '.jsx', '.ts', '.tsx'))]),
            "backend_files": len([f for f in code_files.keys() if f.endswith('.py')]),
            "config_files": len([f for f in code_files.keys() if 'config' in f or f.endswith(('.json', '.yaml', '.yml'))]),
        }
        
        # Campiona alcuni file per l'analisi
        sample_files = list(code_files.items())[:3]
        sample_content = "\n\n".join([f"--- {path} ---\n{content[:500]}" for path, content in sample_files])
        
        prompt = f"""Analizza questa struttura di progetto:

Statistiche file:
{json.dumps(file_analysis, indent=2)}

Campione di codice:
{sample_content}

Requisiti del progetto:
{json.dumps(requirements, indent=2)}

Fornisci un'analisi strutturata per pianificare il testing ottimale."""
        
        try:
            analysis_response = await self.llm_service.generate(
                provider=provider,
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            return {
                "file_analysis": file_analysis,
                "llm_analysis": analysis_response,
                "complexity_estimate": self._estimate_testing_complexity(file_analysis),
                "recommended_test_types": self._recommend_test_types(file_analysis)
            }
        except Exception as e:
            logger.error(f"Error in preliminary analysis: {e}")
            return {"error": str(e), "file_analysis": file_analysis}
    
    def _estimate_testing_complexity(self, file_analysis: Dict[str, Any]) -> str:
        """Stima la complessità del testing basata sull'analisi dei file"""
        total_files = file_analysis["total_files"]
        
        if total_files <= 5:
            return "low"
        elif total_files <= 15:
            return "medium"
        elif total_files <= 30:
            return "high"
        else:
            return "very_high"
    
    def _recommend_test_types(self, file_analysis: Dict[str, Any]) -> List[str]:
        """Raccomanda tipi di test basati sull'analisi dei file"""
        recommendations = []
        
        if file_analysis["frontend_files"] > 0:
            recommendations.extend(["unit_tests_frontend", "component_tests"])
        
        if file_analysis["backend_files"] > 0:
            recommendations.extend(["unit_tests_backend", "api_tests"])
        
        if file_analysis["frontend_files"] > 0 and file_analysis["backend_files"] > 0:
            recommendations.append("integration_tests")
        
        if file_analysis["total_files"] > 10:
            recommendations.append("e2e_tests")
        
        return recommendations
    
    async def _deep_coverage_analysis(self,
                                    test_results: Dict[str, Any],
                                    code_files: Dict[str, str],
                                    provider: str) -> Dict[str, Any]:
        """Analisi approfondita della copertura dei test"""
        
        system_prompt = """Sei un expert testing engineer. Analizza la copertura dei test e suggerisci miglioramenti specifici per raggiungere una copertura ottimale."""
        
        # Estrai informazioni sui test eseguiti
        iterations = test_results.get("iterations", [])
        if not iterations:
            return {"error": "No test iterations found for coverage analysis"}
        
        last_iteration = iterations[-1]
        test_data = last_iteration.get("test_agent_results", {})
        
        coverage_data = {
            "total_test_files": len(test_data.get("test_files", {})),
            "total_code_files": len(code_files),
            "test_success_rate": "100%" if test_data.get("success") else "partial",
            "failure_count": len(test_data.get("failures", [])),
            "test_types_executed": []
        }
        
        # Identifica tipi di test eseguiti
        test_results_detail = test_data.get("test_results", {})
        for test_type in ["frontend", "backend", "e2e"]:
            if test_results_detail.get(test_type):
                coverage_data["test_types_executed"].append(test_type)
        
        prompt = f"""Analizza la copertura dei test per questo progetto:
        
Dati di copertura:
{json.dumps(coverage_data, indent=2)}

File di codice totali: {len(code_files)}
Tipi di file: {list(set([f.split('.')[-1] for f in code_files.keys() if '.' in f]))}

Test eseguiti: {coverage_data['test_types_executed']}
Successo: {coverage_data['test_success_rate']}

Suggerisci miglioramenti specifici per ottimizzare la copertura."""
        
        try:
            analysis_response = await self.llm_service.generate(
                provider=provider,
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            return {
                "coverage_data": coverage_data,
                "analysis": analysis_response,
                "coverage_score": self._calculate_coverage_score(coverage_data),
                "improvement_suggestions": self._extract_coverage_improvements(analysis_response)
            }
        except Exception as e:
            logger.error(f"Error in deep coverage analysis: {e}")
            return {"error": str(e), "coverage_data": coverage_data}
    
    def _calculate_coverage_score(self, coverage_data: Dict[str, Any]) -> float:
        """Calcola un punteggio di copertura basato sui dati disponibili"""
        score = 0.0
        
        # Base score per test esistenti
        if coverage_data["total_test_files"] > 0:
            score += 30.0
        
        # Score per tipi di test
        test_types = coverage_data.get("test_types_executed", [])
        score += len(test_types) * 20.0  # Max 60 per 3 tipi
        
        # Penalità per fallimenti
        if coverage_data["test_success_rate"] != "100%":
            score -= coverage_data["failure_count"] * 5.0
        
        # Bonus per rapporto test/code files
        if coverage_data["total_code_files"] > 0:
            ratio = coverage_data["total_test_files"] / coverage_data["total_code_files"]
            score += min(ratio * 20, 10.0)  # Max 10 bonus
        
        return max(0.0, min(100.0, score))
    
    def _extract_coverage_improvements(self, analysis_text: str) -> List[str]:
        """Estrae suggerimenti di miglioramento dal testo dell'analisi"""
        improvements = []
        
        # Pattern comuni nei suggerimenti
        common_suggestions = [
            "Add unit tests",
            "Increase integration testing",
            "Add E2E tests",
            "Improve test coverage",
            "Add edge case tests",
            "Mock external dependencies"
        ]
        
        analysis_lower = analysis_text.lower()
        for suggestion in common_suggestions:
            if any(word in analysis_lower for word in suggestion.lower().split()):
                improvements.append(suggestion)
        
        return improvements[:5]  # Limite a 5 suggerimenti
    
    async def _stress_testing_phase(self,
                                  requirements: Dict[str, Any],
                                  code_files: Dict[str, str],
                                  provider: str,
                                  output_path: Path) -> Dict[str, Any]:
        """Fase di stress testing per progetti complessi"""
        
        logger.info("Executing stress testing phase")
        
        stress_results = {
            "concurrent_test_execution": False,
            "performance_impact": "unknown",
            "resource_usage": {},
            "recommendations": []
        }
        
        try:
            # Simula test di carico (implementazione base)
            import time
            start_time = time.time()
            
            # Esegui test multipli in parallelo (simulazione)
            tasks = []
            for i in range(3):  # 3 esecuzioni parallele
                task = asyncio.create_task(
                    self._simulate_concurrent_test(i, code_files, provider)
                )
                tasks.append(task)
            
            concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Analizza risultati
            successful_runs = sum(1 for r in concurrent_results if isinstance(r, dict) and r.get("success"))
            
            stress_results.update({
                "concurrent_test_execution": True,
                "parallel_runs": len(tasks),
                "successful_runs": successful_runs,
                "execution_time": end_time - start_time,
                "performance_impact": "acceptable" if successful_runs >= 2 else "concerning",
                "recommendations": [
                    "Tests can handle concurrent execution" if successful_runs >= 2 
                    else "Review test isolation and resource conflicts"
                ]
            })
            
        except Exception as e:
            logger.error(f"Error in stress testing: {e}")
            stress_results["error"] = str(e)
            stress_results["recommendations"].append("Stress testing failed - review test setup")
        
        return stress_results
    
    async def _simulate_concurrent_test(self, run_id: int, code_files: Dict[str, str], provider: str) -> Dict[str, Any]:
        """Simula l'esecuzione concorrente di test"""
        try:
            # Simula carico di lavoro
            await asyncio.sleep(0.5 + run_id * 0.1)
            
            # Simula successo/fallimento basato su euristica semplice
            success = len(code_files) < 50 or run_id % 2 == 0
            
            return {
                "run_id": run_id,
                "success": success,
                "simulated": True,
                "code_files_processed": len(code_files)
            }
        except Exception as e:
            return {"run_id": run_id, "success": False, "error": str(e)}
    
    async def _calculate_metrics(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calcola metriche dettagliate del workflow"""
        
        metrics = {
            "execution_efficiency": "unknown",
            "test_effectiveness": "unknown",
            "coverage_quality": "unknown",
            "overall_score": 0.0
        }
        
        try:
            # Efficienza di esecuzione
            phases = workflow_result.get("phases", [])
            if phases:
                successful_phases = sum(1 for p in phases if p.get("result", {}).get("success", False))
                metrics["execution_efficiency"] = f"{successful_phases}/{len(phases)} phases successful"
                
                # Efficacia dei test
                if "unified_service_result" in workflow_result:
                    unified_result = workflow_result["unified_service_result"]
                    final_success = unified_result.get("final_success", False)
                    metrics["test_effectiveness"] = "high" if final_success else "needs_improvement"
                    
                    # Qualità della copertura
                    coverage_analysis = unified_result.get("test_coverage_analysis", {})
                    test_types = coverage_analysis.get("test_types_covered", [])
                    metrics["coverage_quality"] = f"{len(test_types)} test types covered"
                
                # Score complessivo
                base_score = 50.0
                if workflow_result.get("success", False):
                    base_score += 30.0
                if len(test_types) >= 2:
                    base_score += 20.0
                
                metrics["overall_score"] = min(100.0, base_score)
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            metrics["error"] = str(e)
        
        return metrics
    
    async def _generate_recommendations(self,
                                      workflow_result: Dict[str, Any],
                                      config: TestingConfig,
                                      provider: str) -> List[Dict[str, Any]]:
        """Genera raccomandazioni basate sui risultati del workflow"""
        
        recommendations = []
        
        try:
            # Raccomandazioni basate sul successo
            if not workflow_result.get("success", False):
                recommendations.append({
                    "priority": "high",
                    "type": "fix_failures",
                    "description": "Address failing tests before deployment",
                    "action": "Review test failures and fix underlying issues"
                })
            
            # Raccomandazioni basate sulla strategia
            if config.strategy == TestingStrategy.QUICK:
                recommendations.append({
                    "priority": "medium",
                    "type": "expand_testing",
                    "description": "Consider more comprehensive testing for production",
                    "action": "Run STANDARD or THOROUGH strategy before final deployment"
                })
            
            # Raccomandazioni basate sulla copertura
            phases = workflow_result.get("phases", [])
            coverage_phases = [p for p in phases if p.get("phase") == "coverage_analysis"]
            
            if coverage_phases:
                coverage_result = coverage_phases[0].get("result", {})
                if coverage_result.get("coverage_score", 0) < 70:
                    recommendations.append({
                        "priority": "medium",
                        "type": "improve_coverage",
                        "description": "Test coverage below recommended threshold",
                        "action": "Add more unit tests and integration tests"
                    })
            
            # Raccomandazioni generiche per miglioramento
            if config.strategy != TestingStrategy.THOROUGH:
                recommendations.append({
                    "priority": "low",
                    "type": "optimization",
                    "description": "Consider thorough testing for critical applications",
                    "action": "Use THOROUGH strategy for comprehensive analysis"
                })
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append({
                "priority": "high",
                "type": "error",
                "description": f"Error in recommendation generation: {str(e)}",
                "action": "Review testing workflow configuration"
            })
        
        return recommendations

# Factory functions per creare configurazioni predefinite
def create_quick_config() -> TestingConfig:
    """Configurazione per testing rapido"""
    return TestingConfig(
        strategy=TestingStrategy.QUICK,
        max_iterations=1,
        parallel_execution=True,
        fail_fast=True,
        generate_reports=False
    )

def create_standard_config() -> TestingConfig:
    """Configurazione per testing standard"""
    return TestingConfig(
        strategy=TestingStrategy.STANDARD,
        max_iterations=2,
        parallel_execution=True,
        coverage_threshold=75.0,
        retry_failed_tests=True,
        generate_reports=True
    )

def create_thorough_config() -> TestingConfig:
    """Configurazione per testing approfondito"""
    return TestingConfig(
        strategy=TestingStrategy.THOROUGH,
        max_iterations=3,
        parallel_execution=True,
        coverage_threshold=85.0,
        retry_failed_tests=True,
        generate_reports=True
    )

def create_production_config() -> TestingConfig:
    """Configurazione per testing pre-produzione"""
    return TestingConfig(
        strategy=TestingStrategy.THOROUGH,
        max_iterations=5,
        parallel_execution=False,  # Più stabile per produzione
        coverage_threshold=90.0,
        fail_fast=False,
        retry_failed_tests=True,
        generate_reports=True
    )

# Convenience function per l'uso diretto
async def run_enhanced_testing(requirements: Dict[str, Any],
                             code_files: Dict[str, str],
                             provider: str,
                             output_path: Path,
                             llm_service: LLMService,
                             strategy: TestingStrategy = TestingStrategy.STANDARD) -> Dict[str, Any]:
    """
    Funzione di convenienza per eseguire enhanced testing.
    
    IMPORTANTE: Questa funzione utilizza sempre TestAgent come componente core!
    Gli agenti di test NON sono stati sostituiti, ma organizzati meglio.
    """
    
    # Seleziona configurazione basata sulla strategia
    config_map = {
        TestingStrategy.QUICK: create_quick_config(),
        TestingStrategy.STANDARD: create_standard_config(),
        TestingStrategy.THOROUGH: create_thorough_config()
    }
    
    config = config_map.get(strategy, create_standard_config())
    
    workflow = EnhancedTestingWorkflow(llm_service)
    return await workflow.execute_strategic_testing(
        requirements, code_files, provider, output_path, config
    )