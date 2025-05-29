# app/services/orchestrator_testing_integration.py
import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from enum import Enum

from app.services.enhanced_testing_workflow import (
    EnhancedTestingWorkflow, 
    TestingStrategy, 
    TestingConfig,
    create_quick_config,
    create_standard_config,
    create_thorough_config
)
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class OrchestratorTestingMode(Enum):
    DISABLED = "disabled"           # Nessun testing automatico
    QUICK_ONLY = "quick_only"      # Solo test rapidi
    STANDARD = "standard"          # Test standard dopo generazione
    THOROUGH = "thorough"          # Test approfonditi
    ADAPTIVE = "adaptive"          # Adatta basato su progetto
    ON_DEMAND = "on_demand"        # Test solo su richiesta

class TestingIntegrationMixin:
    """
    Mixin per integrare il sistema di testing negli orchestratori esistenti.
    Aggiunge capacità di testing senza modificare la logica core.
    """
    
    def __init_testing__(self, llm_service: LLMService, testing_mode: OrchestratorTestingMode = OrchestratorTestingMode.STANDARD):
        """Inizializza il sistema di testing per l'orchestratore"""
        self.testing_workflow = EnhancedTestingWorkflow(llm_service)
        self.testing_mode = testing_mode
        self.testing_enabled = testing_mode != OrchestratorTestingMode.DISABLED
        logger.info(f"Testing integration initialized with mode: {testing_mode.value}")
    
    async def execute_post_generation_testing(self,
                                            requirements: Dict[str, Any],
                                            generated_code: Dict[str, str],
                                            provider: str,
                                            output_path: Path,
                                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Esegue testing dopo la generazione del codice.
        Chiamato automaticamente dagli orchestratori.
        """
        if not self.testing_enabled:
            return {"testing_skipped": True, "reason": "Testing disabled"}
        
        logger.info(f"Executing post-generation testing with mode: {self.testing_mode.value}")
        
        try:
            # Determina la strategia di testing basata sul modo e contesto
            strategy, config = self._determine_testing_strategy(requirements, generated_code, context)
            
            # Esegui testing
            testing_result = await self.testing_workflow.execute_strategic_testing(
                requirements, generated_code, provider, output_path, config
            )
            
            # Aggiungi metadati
            testing_result["integration_context"] = {
                "orchestrator_mode": self.testing_mode.value,
                "strategy_used": strategy.value,
                "triggered_by": "post_generation",
                "code_files_count": len(generated_code)
            }
            
            return testing_result
            
        except Exception as e:
            logger.error(f"Error in post-generation testing: {e}")
            return {
                "testing_error": str(e),
                "testing_failed": True,
                "integration_context": {
                    "orchestrator_mode": self.testing_mode.value,
                    "error_occurred": True
                }
            }
    
    async def execute_on_demand_testing(self,
                                      requirements: Dict[str, Any],
                                      code_files: Dict[str, str],
                                      provider: str,
                                      output_path: Path,
                                      requested_strategy: Optional[TestingStrategy] = None) -> Dict[str, Any]:
        """
        Esegue testing su richiesta specifica.
        Utilizzato quando l'utente richiede esplicitamente testing.
        """
        logger.info("Executing on-demand testing")
        
        # Usa la strategia richiesta o determina automaticamente
        if requested_strategy:
            strategy = requested_strategy
            config = self._get_config_for_strategy(strategy)
        else:
            strategy, config = self._determine_testing_strategy(requirements, code_files)
        
        testing_result = await self.testing_workflow.execute_strategic_testing(
            requirements, code_files, provider, output_path, config
        )
        
        testing_result["integration_context"] = {
            "orchestrator_mode": self.testing_mode.value,
            "strategy_used": strategy.value,
            "triggered_by": "on_demand",
            "explicitly_requested": True
        }
        
        return testing_result
    
    def _determine_testing_strategy(self,
                                  requirements: Dict[str, Any],
                                  code_files: Dict[str, str],
                                  context: Optional[Dict[str, Any]] = None) -> tuple[TestingStrategy, TestingConfig]:
        """Determina la strategia di testing ottimale"""
        
        context = context or {}
        
        # Se modalità è specifica, usa quella
        if self.testing_mode == OrchestratorTestingMode.QUICK_ONLY:
            return TestingStrategy.QUICK, create_quick_config()
        elif self.testing_mode == OrchestratorTestingMode.THOROUGH:
            return TestingStrategy.THOROUGH, create_thorough_config()
        elif self.testing_mode == OrchestratorTestingMode.STANDARD:
            return TestingStrategy.STANDARD, create_standard_config()
        
        # Modalità ADAPTIVE: determina basato sul progetto
        elif self.testing_mode == OrchestratorTestingMode.ADAPTIVE:
            return self._adaptive_strategy_selection(requirements, code_files, context)
        
        # Default
        return TestingStrategy.STANDARD, create_standard_config()
    
    def _adaptive_strategy_selection(self,
                                   requirements: Dict[str, Any],
                                   code_files: Dict[str, str],
                                   context: Dict[str, Any]) -> tuple[TestingStrategy, TestingConfig]:
        """Selezione adattiva della strategia basata sulle caratteristiche del progetto"""
        
        # Analizza complessità del progetto
        complexity_score = 0
        
        # Numero di file
        file_count = len(code_files)
        if file_count > 20:
            complexity_score += 3
        elif file_count > 10:
            complexity_score += 2
        elif file_count > 5:
            complexity_score += 1
        
        # Tipi di tecnologie
        has_frontend = any(f.endswith(('.js', '.jsx', '.ts', '.tsx')) for f in code_files.keys())
        has_backend = any(f.endswith('.py') for f in code_files.keys())
        has_database = any('model' in f.lower() or 'schema' in f.lower() for f in code_files.keys())
        
        if has_frontend and has_backend:
            complexity_score += 2
        if has_database:
            complexity_score += 1
        
        # Requisiti di qualità
        quality_keywords = ['production', 'enterprise', 'critical', 'secure', 'scalable']
        req_text = str(requirements).lower()
        quality_mentions = sum(1 for keyword in quality_keywords if keyword in req_text)
        complexity_score += quality_mentions
        
        # Contesto dell'orchestratore
        orchestrator_type = context.get('orchestrator_type', 'unknown')
        if orchestrator_type in ['enterprise', 'production']:
            complexity_score += 2
        
        # Determina strategia basata sul punteggio
        if complexity_score >= 6:
            return TestingStrategy.THOROUGH, create_thorough_config()
        elif complexity_score >= 3:
            return TestingStrategy.STANDARD, create_standard_config()
        else:
            return TestingStrategy.QUICK, create_quick_config()
    
    def _get_config_for_strategy(self, strategy: TestingStrategy) -> TestingConfig:
        """Ottiene la configurazione per una strategia specifica"""
        config_map = {
            TestingStrategy.QUICK: create_quick_config(),
            TestingStrategy.STANDARD: create_standard_config(),
            TestingStrategy.THOROUGH: create_thorough_config()
        }
        return config_map.get(strategy, create_standard_config())
    
    def should_run_automatic_testing(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Determina se eseguire testing automatico basato sul contesto"""
        if not self.testing_enabled:
            return False
        
        if self.testing_mode == OrchestratorTestingMode.ON_DEMAND:
            return False
        
        context = context or {}
        
        # Non eseguire test se esplicitamente disabilitato nel contesto
        if context.get('skip_testing', False):
            return False
        
        # Sempre esegui per modalità non on-demand
        return True


class ProjectOrchestratorWithTesting:
    """
    Orchestratore principale enhanced con sistema di testing integrato.
    Estende l'orchestratore esistente senza modificarlo direttamente.
    """
    
    def __init__(self, 
                 llm_service: LLMService,
                 existing_orchestrator: Any,  # Il tuo orchestratore esistente
                 testing_mode: OrchestratorTestingMode = OrchestratorTestingMode.STANDARD):
        
        self.llm_service = llm_service
        self.orchestrator = existing_orchestrator
        self.testing_mode = testing_mode
        
        # Inizializza testing usando il mixin
        self.testing_mixin = TestingIntegrationMixin()
        self.testing_mixin.__init_testing__(llm_service, testing_mode)
        
        logger.info(f"ProjectOrchestrator enhanced with testing mode: {testing_mode.value}")
    
    async def generate_project_with_testing(self,
                                          requirements: Dict[str, Any],
                                          provider: str,
                                          output_path: Path,
                                          testing_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Genera progetto utilizzando l'orchestratore esistente e aggiunge testing.
        Questo è il metodo principale da chiamare.
        """
        logger.info("Starting project generation with integrated testing")
        
        orchestration_result = {
            "generation_phase": {},
            "testing_phase": {},
            "overall_success": False,
            "integration_metadata": {
                "testing_mode": self.testing_mode.value,
                "testing_enabled": self.testing_mixin.testing_enabled
            }
        }
        
        try:
            # Fase 1: Generazione usando orchestratore esistente
            logger.info("Phase 1: Code generation via existing orchestrator")
            
            # Chiama il metodo del tuo orchestratore esistente
            # Adatta questo in base all'interfaccia del tuo orchestratore
            generation_result = await self._call_existing_orchestrator(
                requirements, provider, output_path
            )
            
            orchestration_result["generation_phase"] = generation_result
            
            # Estrai i file generati
            generated_code = self._extract_generated_code(generation_result)
            
            if not generated_code:
                raise ValueError("No code files generated by orchestrator")
            
            # Fase 2: Testing automatico (se abilitato)
            if self.testing_mixin.should_run_automatic_testing(testing_config):
                logger.info("Phase 2: Automatic testing execution")
                
                testing_result = await self.testing_mixin.execute_post_generation_testing(
                    requirements, generated_code, provider, output_path, 
                    context={"orchestrator_type": "enhanced"}
                )
                
                orchestration_result["testing_phase"] = testing_result
                
                # Determina successo complessivo
                generation_success = generation_result.get("success", False)
                testing_success = testing_result.get("overall_success", False)
                
                orchestration_result["overall_success"] = generation_success and testing_success
                
            else:
                logger.info("Phase 2: Testing skipped (disabled or on-demand mode)")
                orchestration_result["testing_phase"] = {"skipped": True}
                orchestration_result["overall_success"] = generation_result.get("success", False)
            
        except Exception as e:
            logger.error(f"Error in integrated orchestration: {e}")
            orchestration_result["error"] = str(e)
            orchestration_result["overall_success"] = False
        
        return orchestration_result
    
    async def run_testing_only(self,
                             requirements: Dict[str, Any],
                             code_files: Dict[str, str],
                             provider: str,
                             output_path: Path,
                             strategy: Optional[TestingStrategy] = None) -> Dict[str, Any]:
        """
        Esegue solo testing su codice esistente.
        Utile per testare codice già generato.
        """
        return await self.testing_mixin.execute_on_demand_testing(
            requirements, code_files, provider, output_path, strategy
        )
    
    async def _call_existing_orchestrator(self,
                                        requirements: Dict[str, Any],
                                        provider: str,
                                        output_path: Path) -> Dict[str, Any]:
        """
        Chiama l'orchestratore esistente.
        ADATTA QUESTO METODO alla tua interfaccia specifica!
        """
        
        # Esempio per orchestratore con metodo generate_project
        if hasattr(self.orchestrator, 'generate_project'):
            return await self.orchestrator.generate_project(requirements, provider, output_path)
        
        # Esempio per orchestratore con metodo orchestrate
        elif hasattr(self.orchestrator, 'orchestrate'):
            return await self.orchestrator.orchestrate(requirements, provider, output_path)
        
        # Esempio per orchestratore con metodo run
        elif hasattr(self.orchestrator, 'run'):
            return await self.orchestrator.run(requirements, provider, output_path)
        
        # Aggiungi altri pattern comuni...
        else:
            raise NotImplementedError(
                f"Unknown orchestrator interface. "
                f"Please adapt _call_existing_orchestrator method for: {type(self.orchestrator)}"
            )
    
    def _extract_generated_code(self, generation_result: Dict[str, Any]) -> Dict[str, str]:
        """
        Estrae i file di codice generati dal risultato dell'orchestratore.
        ADATTA QUESTO METODO al formato del tuo orchestratore!
        """
        
        # Pattern comuni per estrarre codice generato
        possible_keys = ['code_files', 'generated_files', 'files', 'output_files', 'result_files']
        
        for key in possible_keys:
            if key in generation_result:
                files = generation_result[key]
                if isinstance(files, dict):
                    return files
                elif isinstance(files, list):
                    # Converte lista in dict se necessario
                    return {f"file_{i}.py": str(f) for i, f in enumerate(files)}
        
        # Fallback: cerca nei risultati annidati
        if 'result' in generation_result:
            return self._extract_generated_code(generation_result['result'])
        
        logger.warning("Could not extract generated code from orchestrator result")
        return {}


# Factory functions per creare orchestratori con testing
def create_quick_testing_orchestrator(llm_service: LLMService, existing_orchestrator: Any):
    """Crea orchestratore con testing rapido"""
    return ProjectOrchestratorWithTesting(
        llm_service, existing_orchestrator, OrchestratorTestingMode.QUICK_ONLY
    )

def create_standard_testing_orchestrator(llm_service: LLMService, existing_orchestrator: Any):
    """Crea orchestratore con testing standard"""
    return ProjectOrchestratorWithTesting(
        llm_service, existing_orchestrator, OrchestratorTestingMode.STANDARD
    )

def create_thorough_testing_orchestrator(llm_service: LLMService, existing_orchestrator: Any):
    """Crea orchestratore con testing approfondito"""
    return ProjectOrchestratorWithTesting(
        llm_service, existing_orchestrator, OrchestratorTestingMode.THOROUGH
    )

def create_adaptive_testing_orchestrator(llm_service: LLMService, existing_orchestrator: Any):
    """Crea orchestratore con testing adattivo"""
    return ProjectOrchestratorWithTesting(
        llm_service, existing_orchestrator, OrchestratorTestingMode.ADAPTIVE
    )

# Convenienza per retrofit degli orchestratori esistenti
async def add_testing_to_existing_orchestrator(orchestrator_instance: Any,
                                             llm_service: LLMService,
                                             testing_mode: OrchestratorTestingMode = OrchestratorTestingMode.STANDARD):
    """
    Aggiunge capacità di testing a un orchestratore esistente senza modificarlo.
    Usa questo per retrofit rapido.
    """
    
    # Aggiungi testing mixin all'istanza esistente
    if not hasattr(orchestrator_instance, 'testing_mixin'):
        orchestrator_instance.testing_mixin = TestingIntegrationMixin()
        orchestrator_instance.testing_mixin.__init_testing__(llm_service, testing_mode)
        
        # Aggiungi metodi di convenienza
        orchestrator_instance.run_post_generation_testing = orchestrator_instance.testing_mixin.execute_post_generation_testing
        orchestrator_instance.run_on_demand_testing = orchestrator_instance.testing_mixin.execute_on_demand_testing
        
        logger.info(f"Testing capabilities added to existing orchestrator: {type(orchestrator_instance)}")
    
    return orchestrator_instance
