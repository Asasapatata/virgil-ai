# app/services/unified_testing_integration.py
import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from app.services.test_agent import TestAgent
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class UnifiedTestingService:
    """
    Servizio unificato per la gestione completa del testing.
    Coordina TestAgent e fornisce un'interfaccia semplificata.
    
    Gli agenti di test CONTINUANO ad essere utilizzati, ma in modo più strutturato:
    - TestAgent rimane il coordinatore principale
    - Questo servizio aggiunge orchestrazione di alto livello
    - Supporta workflow avanzati e analisi iterative
    """
    
    def __init__(self, llm_service: LLMService):
        self.test_agent = TestAgent(llm_service)
        self.llm_service = llm_service
        logger.info("UnifiedTestingService initialized with TestAgent")
    
    async def execute_full_testing_workflow(self,
                                          requirements: Dict[str, Any],
                                          code_files: Dict[str, str],
                                          provider: str,
                                          output_path: Path,
                                          config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Workflow completo di testing che utilizza TestAgent come core engine.
        
        Fasi:
        1. Analisi preliminare del codice
        2. Generazione test via TestAgent
        3. Esecuzione test via TestAgent
        4. Analisi risultati e suggerimenti miglioramenti
        5. Iterazione se necessario
        """
        config = config or {}
        max_iterations = config.get('max_iterations', 2)
        
        logger.info(f"Starting full testing workflow with max {max_iterations} iterations")
        
        workflow_results = {
            "iterations": [],
            "final_success": False,
            "improvements_suggested": [],
            "test_coverage_analysis": {},
            "summary": {}
        }
        
        for iteration in range(max_iterations):
            logger.info(f"Starting testing iteration {iteration + 1}")
            
            # Usa TestAgent per l'analisi completa
            iteration_result = await self.test_agent.analyze_and_test_code(
                requirements, code_files, provider, output_path
            )
            
            # Analizza i risultati dell'iterazione
            analysis = await self._analyze_iteration_results(
                iteration_result, iteration, provider
            )
            
            iteration_data = {
                "iteration": iteration + 1,
                "test_agent_results": iteration_result,
                "analysis": analysis,
                "success": iteration_result.get("success", False)
            }
            
            workflow_results["iterations"].append(iteration_data)
            
            # Se tutti i test passano, termina
            if iteration_result.get("success", False):
                workflow_results["final_success"] = True
                logger.info(f"All tests passed in iteration {iteration + 1}")
                break
            
            # Se non è l'ultima iterazione, cerca di migliorare il codice
            if iteration < max_iterations - 1:
                code_improvements = await self._suggest_code_improvements(
                    iteration_result, code_files, provider
                )
                workflow_results["improvements_suggested"].extend(code_improvements)
                
                # Applica miglioramenti se possibile
                if code_improvements:
                    code_files = await self._apply_code_improvements(
                        code_files, code_improvements, provider
                    )
        
        # Analisi finale
        workflow_results["test_coverage_analysis"] = await self._analyze_test_coverage(
            workflow_results["iterations"], provider
        )
        
        workflow_results["summary"] = self._create_workflow_summary(workflow_results)
        
        logger.info(f"Testing workflow completed. Final success: {workflow_results['final_success']}")
        return workflow_results
    
    async def quick_test_execution(self,
                                 requirements: Dict[str, Any],
                                 code_files: Dict[str, str],
                                 provider: str,
                                 output_path: Path) -> Dict[str, Any]:
        """
        Esecuzione rapida dei test usando direttamente TestAgent.
        Ideale per test veloci durante lo sviluppo.
        """
        logger.info("Executing quick test via TestAgent")
        return await self.test_agent.analyze_and_test_code(
            requirements, code_files, provider, output_path
        )
    
    async def _analyze_iteration_results(self,
                                       iteration_result: Dict[str, Any],
                                       iteration: int,
                                       provider: str) -> Dict[str, Any]:
        """Analizza i risultati di un'iterazione di test usando LLM"""
        
        if not iteration_result.get("failures"):
            return {"status": "success", "analysis": "All tests passed successfully"}
        
        system_prompt = """Sei un esperto analista di test software. 
        Analizza i risultati dei test falliti e fornisci insight su:
        1. Cause probabili dei fallimenti
        2. Pattern comuni nei fallimenti
        3. Priorità dei fix necessari
        4. Suggerimenti per miglioramenti"""
        
        failures_summary = []
        for failure in iteration_result.get("failures", []):
            failures_summary.append({
                "type": failure.get("type", "unknown"),
                "error": failure.get("error", "")[:200],  # Limita la lunghezza
                "details": failure.get("details", "")[:300]
            })
        
        prompt = f"""Analizza questi risultati di test (iterazione {iteration + 1}):

Fallimenti trovati: {len(failures_summary)}
Dettagli fallimenti: {json.dumps(failures_summary, indent=2)}

Test totali: {iteration_result.get('summary', {}).get('total_tests', 0)}
Successo generale: {iteration_result.get('success', False)}

Fornisci un'analisi strutturata dei problemi principali e suggerimenti specifici."""
        
        try:
            analysis_response = await self.llm_service.generate(
                provider=provider,
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            return {
                "status": "analyzed",
                "analysis": analysis_response,
                "failure_count": len(failures_summary),
                "patterns_identified": self._extract_failure_patterns(failures_summary)
            }
        except Exception as e:
            logger.error(f"Error analyzing iteration results: {e}")
            return {
                "status": "error", 
                "analysis": f"Analysis failed: {str(e)}",
                "failure_count": len(failures_summary)
            }
    
    def _extract_failure_patterns(self, failures: List[Dict[str, Any]]) -> List[str]:
        """Estrae pattern comuni dai fallimenti"""
        patterns = []
        
        # Analizza tipi di errore
        error_types = {}
        for failure in failures:
            error_type = failure.get("type", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        if error_types:
            patterns.append(f"Error distribution: {error_types}")
        
        # Cerca pattern comuni nei messaggi di errore
        common_terms = ["import", "module", "undefined", "null", "assertion"]
        for term in common_terms:
            count = sum(1 for f in failures if term.lower() in str(f.get("error", "")).lower())
            if count > 0:
                patterns.append(f"{term} related errors: {count}")
        
        return patterns
    
    async def _suggest_code_improvements(self,
                                       test_results: Dict[str, Any],
                                       code_files: Dict[str, str],
                                       provider: str) -> List[Dict[str, Any]]:
        """Suggerisce miglioramenti al codice basati sui test falliti"""
        
        if not test_results.get("failures"):
            return []
        
        system_prompt = """Sei un expert software engineer. Basandoti sui fallimenti dei test,
        suggerisci miglioramenti specifici al codice. Concentrati su fix pratici e implementabili."""
        
        # Prendi i primi 3 fallimenti più significativi
        key_failures = test_results["failures"][:3]
        
        prompt = f"""Analizza questi fallimenti di test e suggerisci fix specifici:

Fallimenti chiave:
{json.dumps(key_failures, indent=2)}

File di codice disponibili: {list(code_files.keys())}

Per ogni fallimento, suggerisci:
1. File da modificare
2. Tipo di modifica necessaria
3. Codice specifico da aggiungere/modificare
4. Priorità del fix (alta/media/bassa)

Formato risposta JSON:
{
  "suggestions": [
    {
      "file": "path/to/file",
      "description": "cosa modificare",
      "priority": "alta|media|bassa",
      "modification_type": "add|modify|remove",
      "code_snippet": "codice suggerito"
    }
  ]
}"""
        
        try:
            response = await self.llm_service.generate(
                provider=provider,
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            # Prova a parsare come JSON
            import json
            suggestions_data = json.loads(response)
            return suggestions_data.get("suggestions", [])
        
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Could not parse improvement suggestions: {e}")
            return [{
                "file": "general",
                "description": "Review test failures and fix manually",
                "priority": "alta",
                "modification_type": "review",
                "code_snippet": response[:200] if response else "No suggestions generated"
            }]
    
    async def _apply_code_improvements(self,
                                     code_files: Dict[str, str],
                                     improvements: List[Dict[str, Any]],
                                     provider: str) -> Dict[str, str]:
        """Applica miglioramenti al codice (implementazione base)"""
        
        # Per ora, restituisce i file originali
        # In futuro, si potrebbe implementare l'applicazione automatica dei fix
        logger.info(f"Code improvements suggested: {len(improvements)}")
        for improvement in improvements:
            logger.info(f"- {improvement.get('file', 'unknown')}: {improvement.get('description', 'no description')}")
        
        return code_files
    
    async def _analyze_test_coverage(self,
                                   iterations: List[Dict[str, Any]],
                                   provider: str) -> Dict[str, Any]:
        """Analizza la copertura dei test attraverso le iterazioni"""
        
        if not iterations:
            return {"coverage": "unknown", "analysis": "No iterations completed"}
        
        last_iteration = iterations[-1]
        test_results = last_iteration.get("test_agent_results", {})
        
        coverage_analysis = {
            "iterations_completed": len(iterations),
            "final_test_count": test_results.get("summary", {}).get("total_tests", 0),
            "final_success_rate": "100%" if test_results.get("success") else f"{max(0, 100 - len(test_results.get('failures', [])) * 10)}%",
            "test_types_covered": [],
            "recommendations": []
        }
        
        # Analizza tipi di test coperti
        if test_results.get("test_results", {}).get("frontend"):
            coverage_analysis["test_types_covered"].append("frontend")
        if test_results.get("test_results", {}).get("backend"):
            coverage_analysis["test_types_covered"].append("backend")
        if test_results.get("test_results", {}).get("e2e"):
            coverage_analysis["test_types_covered"].append("e2e")
        
        # Raccomandazioni base
        if not coverage_analysis["test_types_covered"]:
            coverage_analysis["recommendations"].append("Add basic unit tests")
        if "e2e" not in coverage_analysis["test_types_covered"]:
            coverage_analysis["recommendations"].append("Consider adding E2E tests")
        
        return coverage_analysis
    
    def _create_workflow_summary(self, workflow_results: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un riassunto del workflow di testing"""
        
        iterations = workflow_results.get("iterations", [])
        if not iterations:
            return {"status": "no_iterations", "message": "No testing iterations completed"}
        
        last_iteration = iterations[-1]
        
        return {
            "total_iterations": len(iterations),
            "final_success": workflow_results.get("final_success", False),
            "total_tests": last_iteration.get("test_agent_results", {}).get("summary", {}).get("total_tests", 0),
            "total_failures": len(last_iteration.get("test_agent_results", {}).get("failures", [])),
            "improvements_count": len(workflow_results.get("improvements_suggested", [])),
            "test_types": workflow_results.get("test_coverage_analysis", {}).get("test_types_covered", []),
            "status": "success" if workflow_results.get("final_success") else "partial_success",
            "message": self._generate_summary_message(workflow_results)
        }
    
    def _generate_summary_message(self, workflow_results: Dict[str, Any]) -> str:
        """Genera un messaggio riassuntivo human-friendly"""
        
        iterations_count = len(workflow_results.get("iterations", []))
        final_success = workflow_results.get("final_success", False)
        
        if final_success:
            return f"Testing completed successfully after {iterations_count} iteration(s). All tests are passing."
        else:
            failures = 0
            if workflow_results.get("iterations"):
                last_iteration = workflow_results["iterations"][-1]
                failures = len(last_iteration.get("test_agent_results", {}).get("failures", []))
            
            return f"Testing completed with {failures} remaining issues after {iterations_count} iteration(s). Manual review recommended."

# Convenience function per backward compatibility
async def run_unified_testing(requirements: Dict[str, Any],
                            code_files: Dict[str, str],
                            provider: str,
                            output_path: Path,
                            llm_service: LLMService,
                            config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Funzione di convenienza per eseguire testing unificato.
    Utilizza TestAgent internamente.
    """
    service = UnifiedTestingService(llm_service)
    return await service.execute_full_testing_workflow(
        requirements, code_files, provider, output_path, config
    )