# backend/app/tasks/celery_app.py
from celery import Celery
from celery.signals import task_revoked  # Aggiungere questo import
from pathlib import Path
import json
import yaml
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime  # Aggiungere questo import

from app.core.config import settings

# Create Celery app
celery = Celery('tasks',
                broker=settings.REDIS_URL,
                backend=settings.REDIS_URL)

# Configurazione
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    worker_cancel_long_running_tasks_on_connection_loss=True,
    
    # 🔥 FIX per deprecation warning Celery 6.0
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_connection_retry_delay=5.0,
    
    # 🔥 BONUS: Configurazioni per reliability
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    
    # 🔥 TIMEOUT: Configurazioni timeout
    task_soft_time_limit=3600,
    task_time_limit=3900,
    worker_disable_rate_limits=True,
    
    # 🔥 RESULT: Configurazioni result backend
    result_expires=3600,
    result_persistent=True,
)

# Gestione dell'interruzione dei task
@task_revoked.connect
def handle_revoked_task(sender=None, request=None, terminated=None, signum=None, expired=None, **kwargs):
    """
    Gestisce il segnale quando un task viene interrotto/revocato.
    Aggiorna lo stato del progetto nel database.
    """
    # Ottieni l'ID del task revocato
    task_id = sender.request.id if sender and sender.request else None
    
    # Cerca il project_id dagli argomenti del task
    if request and request.kwargs:
        project_id = request.kwargs.get('project_id')
        if project_id:
            project_path = Path(f"output/{project_id}")
            
            # Aggiorna lo stato del progetto
            with open(project_path / "project.json", 'r') as f:
                project_data = json.load(f)
            
            project_data["status"] = "failed"
            project_data["stopped_by_user"] = True
            project_data["stopped_at"] = datetime.now().isoformat()
            
            with open(project_path / "project.json", 'w') as f:
                json.dump(project_data, f, indent=2)
            
            logging.info(f"Task {task_id} per il progetto {project_id} è stato revocato/fermato dall'utente.")
    else:
        logging.warning(f"Task {task_id} è stato revocato, ma non è stato possibile identificare il progetto associato.")

@celery.task(bind=True)
def process_multi_agent_generation(self,
                                  project_id: str,
                                  llm_provider: str,
                                  max_iterations: int = 10):
    """Task per la generazione di codice utilizzando il sistema multi-agent"""
    
    from app.services.llm_service import LLMService
    from app.services.multi_agent_orchestrator import MultiAgentOrchestrator
    
    project_path = Path(f"output/{project_id}")
    
    try:
        # Inizializza i servizi
        llm_service = LLMService()
        orchestrator = MultiAgentOrchestrator(llm_service)
        
        # Carica i requisiti
        with open(project_path / "requirements.yaml", 'r') as f:
            import yaml
            requirements = yaml.safe_load(f)
        
        # Aggiorna lo stato del progetto
        update_project_status(project_path, "processing")
        
        # Salva l'ID del task nel file project.json
        with open(project_path / "project.json", 'r') as f:
            project_data = json.load(f)
        
        project_data["task_id"] = self.request.id
        project_data["generation_mode"] = "multi_agent"
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        # Funzione di callback per aggiornare lo stato
        def progress_callback(iteration: int, status: str):
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': iteration,
                    'total': max_iterations,
                    'status': status
                }
            )
        
        # Esegui la generazione multi-agent
        result = asyncio.run(
            orchestrator.generate_multi_agent_application(
                requirements=requirements,
                provider=llm_provider,
                max_iterations=max_iterations,
                project_path=project_path,
                progress_callback=progress_callback
            )
        )
        
        # Aggiorna lo stato finale
        if result["status"] == "completed":
            update_project_status(project_path, "completed", result["iteration"])
        elif result["status"] == "completed_with_warnings":
            update_project_status(project_path, "completed", result["iteration"])
        elif result["status"] == "stopped":
            update_project_status(project_path, "failed", result.get("iteration", 0))
        else:
            update_project_status(project_path, "error")
        
        return result
        
    except Exception as e:
        logging.error(f"Multi-agent process error: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Error details: {error_details}")
        
        try:
            with open(project_path / "project.json", 'r') as f:
                project_data = json.load(f)
                current_iteration = project_data.get("current_iteration", 0)
        except:
            current_iteration = None
            
        update_project_status(project_path, "error", current_iteration)
        return {
            "status": "error",
            "error": str(e),
            "project_id": project_id,
            "current_iteration": current_iteration
        }

# In app/tasks/celery_app.py

# In backend/app/tasks/celery_app.py

# 🔥 NUOVO TASK ENHANCED che sostituisce process_agent_generation per smart generation
@celery.task(bind=True)
def process_enhanced_code_generation(self,
                                   project_id: str,
                                   llm_provider: str,
                                   max_iterations: int = 10,
                                   agent_mode: str = "updated_orchestrator"):
    """
    Enhanced task che usa il nuovo orchestratore basato su agent_mode.
    Questo task viene chiamato dalla smart generation.
    """
    
    project_path = Path(f"output/{project_id}")
    
    try:
        logger = logging.getLogger(__name__)
        logger.info(f"Starting enhanced generation for {project_id} with {agent_mode} mode")
        
        # Load project data
        with open(project_path / "project.json", 'r') as f:
            project_data = json.load(f)
        
        requirements = project_data.get('requirements', {})
        
        # Update project status
        project_data["status"] = "processing"
        project_data["task_id"] = self.request.id
        project_data["generation_mode"] = "enhanced_v2"
        project_data["agent_mode"] = agent_mode
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        # Progress callback
        def progress_callback(iteration: int, status: str):
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': iteration,
                    'total': max_iterations,
                    'status': status,
                    'agent_mode': agent_mode
                }
            )
        
        # 🎯 DECISION LOGIC: Scegli orchestratore basato su agent_mode
        if agent_mode == "original":
            # 🔄 BACKWARD COMPATIBILITY: Usa il vecchio sistema solo per "original"
            logger.info("Using original orchestrator for backward compatibility")
            
            from app.services.orchestrator import OrchestratorAgent
            from app.services.llm_service import LLMService
            
            llm_service = LLMService()
            orchestrator = OrchestratorAgent(llm_service)
            
            result = asyncio.run(
                orchestrator.generate_application_with_orchestration(
                    requirements=requirements,
                    provider=llm_provider,
                    max_iterations=max_iterations,
                    project_path=project_path,
                    progress_callback=progress_callback
                )
            )
        
        else:
            # 🔥 NUOVO: Usa enhanced orchestrator per tutti gli altri modi
            logger.info(f"Using enhanced orchestrator for {agent_mode} mode")
            
            from app.services.updated_orchestrator import UpdatedOrchestratorAgent
            from app.services.llm_service import LLMService
            
            llm_service = LLMService()
            orchestrator = UpdatedOrchestratorAgent(llm_service)
            
            # Adatta max_iterations basato su agent_mode
            if agent_mode == "enhanced_generator":
                max_iterations = min(max_iterations, 5)  # Limita iterazioni per generatore singolo
            elif agent_mode == "updated_orchestrator":
                max_iterations = min(max_iterations, 10)  # Iterazioni medie
            # multi_agent mantiene max_iterations originale
            
            result = asyncio.run(
                orchestrator.generate_application_with_enhanced_flow(
                    requirements=requirements,
                    provider=llm_provider,
                    max_iterations=max_iterations,
                    project_path=project_path,
                    progress_callback=progress_callback
                )
            )
            
            # Generate final project se completato con successo
            if result["status"] in ["completed", "completed_with_issues", "completed_with_improvements"]:
                logger.info("Generating final consolidated project")
                try:
                    final_result = asyncio.run(
                        orchestrator.generate_final_project(
                            project_path, result.get("project_name", project_id)
                        )
                    )
                    result["final_project"] = final_result
                    logger.info("Final project generated successfully")
                except Exception as e:
                    logger.warning(f"Could not generate final project: {e}")
                    result["final_project"] = {"success": False, "error": str(e)}
        
        # Update final status
        project_data['status'] = result["status"]
        project_data['final_result'] = result
        project_data['completed_at'] = datetime.now().isoformat()
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        logger.info(f"Enhanced generation completed for {project_id}: {result['status']}")
        return result
        
    except Exception as e:
        logger.error(f"Enhanced process error for {project_id}: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error details: {error_details}")
        
        try:
            # Update project status to failed
            with open(project_path / "project.json", 'r') as f:
                project_data = json.load(f)
            
            project_data['status'] = 'failed'
            project_data['error'] = str(e)
            project_data['failed_at'] = datetime.now().isoformat()
            
            with open(project_path / "project.json", 'w') as f:
                json.dump(project_data, f, indent=2)
        except:
            pass
        
        return {
            "status": "error",
            "error": str(e),
            "project_id": project_id
        }
    
@celery.task(bind=True)
def process_agent_generation(self, project_id, llm_provider="openai", max_iterations=10, agent_mode="multi_agent"):
    """
    Task Celery per gestire la generazione di codice tramite sistema di agenti.
    """
    try:
        # Importazioni necessarie
        import json
        import logging
        import asyncio
        from pathlib import Path
        
        logger = logging.getLogger(__name__)
        logger.info(f"Starting agent-based code generation for project {project_id}")
        
        # Percorso del progetto
        project_path = Path(f"output/{project_id}")
        if not project_path.exists():
            logger.error(f"Project path not found: {project_path}")
            return {"error": "Project not found"}
        
        # Carica i dati del progetto
        try:
            with open(project_path / "project.json", 'r') as f:
                project_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading project data: {e}")
            return {"error": f"Error loading project data: {str(e)}"}
        
        # Estrai i requirements
        requirements = project_data.get('requirements', {})
        
        # Aggiorna lo stato
        project_data['status'] = 'processing'
        project_data['agent_mode'] = agent_mode
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        # Inizializza i servizi necessari
        from app.services.llm_service import LLMService
        llm_service = LLMService()
        
        # Funzione di callback per aggiornare lo stato
        def progress_callback(iteration: int, status: str):
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': iteration,
                    'total': max_iterations,
                    'status': status
                }
            )
        
        # Determine which agent system to use and execute
        result = None
        
        if agent_mode == "multi_agent":
            # Sistema multi-agente completo
            from app.services.multi_agent_orchestrator import MultiAgentOrchestrator
            orchestrator = MultiAgentOrchestrator(llm_service)
            
            # Usa il metodo corretto generate_multi_agent_application
            result = asyncio.run(
                orchestrator.generate_multi_agent_application(
                    requirements=requirements,
                    provider=llm_provider,
                    max_iterations=max_iterations,
                    project_path=project_path,
                    progress_callback=progress_callback
                )
            )
            
        elif agent_mode == "updated_orchestrator":
            # Sistema con orchestratore migliorato
            from app.services.updated_orchestrator import EnhancedOrchestrator
            orchestrator = EnhancedOrchestrator(llm_service)
            
            # Usa il metodo corretto
            result = asyncio.run(
                orchestrator.generate_application_with_orchestration(
                    requirements=requirements,
                    provider=llm_provider,
                    max_iterations=max_iterations,
                    project_path=project_path,
                    progress_callback=progress_callback
                )
            )
            
        elif agent_mode == "enhanced_generator":
            # Generator singolo migliorato
            from app.services.enhanced_code_generator import EnhancedCodeGenerator
            generator = EnhancedCodeGenerator(llm_service)
            
            # Usa il metodo corretto
            result = asyncio.run(
                generator.generate_complete_project(
                    project_id=project_id,
                    requirements=requirements,
                    provider=llm_provider,
                    max_iterations=max_iterations
                )
            )
            
        elif agent_mode == "original":
            # Sistema originale
            from app.services.code_generator import CodeGenerator
            generator = CodeGenerator(llm_service=llm_service)
            
            # Usa il metodo corretto
            result = asyncio.run(
                generator.generate_application_with_testing(
                    requirements=requirements,
                    provider=llm_provider,
                    max_iterations=max_iterations,
                    project_path=project_path,
                    progress_callback=progress_callback
                )
            )
            
        else:
            logger.error(f"Unknown agent mode: {agent_mode}")
            return {"error": f"Unknown agent mode: {agent_mode}"}
        
        # Aggiorna lo stato del progetto a completato
        project_data['status'] = 'completed'
        if result:
            if isinstance(result, dict):
                for key, value in result.items():
                    project_data[key] = value
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        logger.info(f"Completed agent-based generation for project {project_id}")
        return {
            "project_id": project_id,
            "status": "completed",
            "agent_mode": agent_mode,
            "message": f"Code generation completed using {agent_mode} agent system"
        }
    
    except Exception as e:
        import traceback
        logger.error(f"Error in process_agent_generation: {e}")
        logger.error(traceback.format_exc())
        
        # Aggiorna lo stato del progetto a fallito
        try:
            project_path = Path(f"output/{project_id}")
            with open(project_path / "project.json", 'r') as f:
                project_data = json.load(f)
            
            project_data['status'] = 'failed'
            project_data['error'] = str(e)
            
            with open(project_path / "project.json", 'w') as f:
                json.dump(project_data, f, indent=2)
        except:
            pass
        
        return {"error": str(e)}
    
@celery.task(bind=True)
def process_code_generation(self,
                          project_id: str,
                          llm_provider: str,
                          max_iterations: int = 10):
    """Main task for code generation with orchestrated testing"""
    
    from app.services.llm_service import LLMService
    from app.services.orchestrator import OrchestratorAgent
    
    project_path = Path(f"output/{project_id}")
    
    try:
        # Initialize services
        llm_service = LLMService()
        orchestrator = OrchestratorAgent(llm_service)
        
        # Load requirements
        with open(project_path / "requirements.yaml", 'r') as f:
            requirements = yaml.safe_load(f)
        
        # Update project status
        update_project_status(project_path, "processing")
        
        # Salva l'ID del task nel file project.json
        with open(project_path / "project.json", 'r') as f:
            project_data = json.load(f)
        
        project_data["task_id"] = self.request.id
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        # Semplice funzione di progress_callback che aggiorna solo lo stato
        def progress_callback(iteration: int, status: str):
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': iteration,
                    'total': max_iterations,
                    'status': status
                }
            )
        
        # Use orchestrator instead of manual loop
        result = asyncio.run(
            orchestrator.generate_application_with_orchestration(
                requirements=requirements,
                provider=llm_provider,
                max_iterations=max_iterations,
                project_path=project_path,
                progress_callback=progress_callback
            )
        )
        
        # Update final status
        if result["status"] == "completed":
            update_project_status(project_path, "completed", result["iteration"])
        elif result["status"] == "failed":
            update_project_status(project_path, "failed", result.get("iterations", max_iterations))
        else:
            update_project_status(project_path, "error")
        
        return result
        
    except Exception as e:
        logging.error(f"Process error: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Error details: {error_details}")
        
        try:
            with open(project_path / "project.json", 'r') as f:
                project_data = json.load(f)
                current_iteration = project_data.get("current_iteration", 0)
        except:
            current_iteration = None
            
        update_project_status(project_path, "error", current_iteration)
        return {
            "status": "error",
            "error": str(e),
            "project_id": project_id,
            "current_iteration": current_iteration
        }

def update_project_status(project_path: Path, status: str, iteration: int = None):
    """Update project status in metadata file"""
    
    # Mappa gli stati interni agli stati dell'enum
    status_mapping = {
        "generating_code": "processing",
        "generating_tests": "processing",
        "running_tests": "processing",
        "completed": "completed",
        "failed": "failed",
        "error": "error"
    }
    
    # Usa lo stato mappato se disponibile
    enum_status = status_mapping.get(status, status)
    
    with open(project_path / "project.json", 'r') as f:
        project_data = json.load(f)
    
    project_data["status"] = enum_status
    # Aggiungi anche lo stato interno per debugging
    project_data["detailed_status"] = status
    
    if iteration:
        project_data["completed_iteration"] = iteration
        # Aggiungi anche l'iterazione corrente
        project_data["current_iteration"] = iteration
    
    with open(project_path / "project.json", 'w') as f:
        json.dump(project_data, f, indent=2)