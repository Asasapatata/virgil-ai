import traceback
import sys
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import yaml
import uuid
from pathlib import Path
import json
from datetime import datetime
import shutil

from app.core.config import settings
from app.services.llm_service import LLMService
from app.services.code_generator import CodeGenerator
from app.services.project_merger import ProjectMerger  # NUOVO
from app.services.test_generator import TestGenerator
from app.services.test_runner import TestRunner
from app.tasks.celery_app import process_code_generation, process_enhanced_code_generation
from app.models.project import Project, ProjectStatus 
from celery.result import AsyncResult

# Importa i nuovi endpoint basati su agenti
from app.services.endpoints_agent import router as agent_router, generate_with_agents, AgentGenerateRequest
from app.api.smart_generation import router as smart_router


# Import per i nuovi agenti
from app.services.agent_system import SystemAgent
from app.services.agent_integration import IntegrationAgent 
from app.services.endpoints_agent import EndpointsAgent
from app.services.endpoints_agent import router as agent_router
from app.services.multi_agent_orchestrator import MultiAgentOrchestrator



# Configurazione logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Classe per la serializzazione degli oggetti datetime
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app = FastAPI(title="Virgil AI API")

app.include_router(agent_router)
app.include_router(smart_router, prefix="/api")


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inizializza i servizi ENHANCED
llm_service = LLMService()
project_merger = ProjectMerger(base_output_path="output")
system_agent = SystemAgent(llm_service)
integration_agent = IntegrationAgent(llm_service)
multi_agent_orchestrator = MultiAgentOrchestrator(llm_service)

class GenerateRequest(BaseModel):
    project_id: str
    llm_provider: str = "openai"  # openai, anthropic, deepseek
    max_iterations: int = 10

# NUOVO: Modello per il metodo enhanced
class EnhancedGenerateRequest(BaseModel):
    project_id: str
    llm_provider: str = "openai"
    max_iterations: int = 10
    use_enhanced: bool = True  # Flag per scegliere il metodo

class ProjectResponse(BaseModel):
    project_id: str
    status: str
    current_iteration: int
    test_results: Optional[Dict[str, Any]] = None
    output_path: str

@app.get("/")
async def root():
    return {"message": "Virgil AI API", "version": "2.0.0"}

def load_project_data(project_path: Path) -> Dict[str, Any]:
    """
    Carica i dati del progetto in modo sicuro con gestione errori
    """
    project_json_path = project_path / "project.json"
    
    if not project_json_path.exists():
        raise HTTPException(status_code=404, detail="File progetto non trovato")
    
    if project_json_path.stat().st_size == 0:
        raise HTTPException(status_code=500, detail="File progetto corrotto (vuoto)")
    
    try:
        with open(project_json_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"File progetto corrotto: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore caricamento progetto: {str(e)}")


# Mantieni il tuo endpoint esistente INVARIATO
@app.post("/upload-requirements")
async def upload_requirements(file: UploadFile = File(...), project_name: Optional[str] = None):
    """Upload YAML requirements file"""
    try:
        # Logging iniziale
        logger.info(f"Upload started for file: {file.filename}")
        
        # Validate file type
        if not file.filename.endswith('.yaml') and not file.filename.endswith('.yml'):
            logger.warning(f"Invalid file type: {file.filename}")
            raise HTTPException(status_code=400, detail="File must be YAML format")
        
        # Generate unique project ID
        project_id = str(uuid.uuid4())
        logger.info(f"Generated project ID: {project_id}")
        
        # Create output directory
        output_path = Path(f"output/{project_id}")
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {output_path}")
        except Exception as e:
            logger.error(f"Failed to create directory: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create directory: {str(e)}")
        
        # Save requirements file
        requirements_path = output_path / "requirements.yaml"
        logger.info(f"Reading file content...")
        
        try:
            content = await file.read()
            logger.info(f"Read {len(content)} bytes")
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
        
        # Validate YAML
        try:
            logger.info("Parsing YAML...")
            requirements = yaml.safe_load(content)
            logger.info("YAML parsing successful")
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")
        
        # Save validated requirements
        try:
            logger.info(f"Writing requirements to {requirements_path}")
            with open(requirements_path, 'wb') as f:
                f.write(content)
            logger.info("Requirements saved successfully")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
        # Create project record
        try:
            logger.info("Creating project record...")
            # E sostituiscila con questa versione modificata
            # Il nome personalizzato ha sempre la priorità se specificato
            if project_name and project_name.strip():
                project_name = project_name.strip()  # Usa il nome personalizzato fornito
                logger.info(f"Using custom project name: {project_name}")
            else:
                # Altrimenti, cerca il nome nei requirements o usa un nome generico
                project_name = requirements.get('project', {}).get('name', f'Progetto {project_id[:8]}')
                logger.info(f"Using project name from requirements: {project_name}")
            
            project = Project(
                id=project_id,
                name=project_name,
                requirements=requirements,
                status=ProjectStatus.CREATED
            )
            
            # Save project metadata
            project_json_path = output_path / "project.json"
            logger.info(f"Saving project metadata to {project_json_path}")
            with open(project_json_path, 'w') as f:
                # Usa DateTimeEncoder per gestire la serializzazione degli oggetti datetime
                json.dump(project.dict(), f, indent=2, cls=DateTimeEncoder)
            logger.info("Project metadata saved successfully")
        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")
        
        logger.info("Upload complete, returning response")
        return {
            "project_id": project_id,
            "project_name": project.name,
            "status": "requirements_uploaded",
            "output_path": str(output_path)
        }
        
    except Exception as e:
        logger.error(f"Uncaught exception: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# MANTIENI il metodo esistente
@app.post("/generate")
async def generate_code(request: GenerateRequest):
    """Start code generation process (metodo esistente)"""
    try:
        # Verify project exists
        project_path = Path(f"output/{request.project_id}")
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Load project
        with open(project_path / "project.json", 'r') as f:
            project_data = json.load(f)
        
        # Start async task
        task = process_code_generation.delay(
            project_id=request.project_id,
            llm_provider=request.llm_provider,
            max_iterations=request.max_iterations
        )
        
        # Update project status
        project_data['status'] = 'processing'
        project_data['task_id'] = task.id
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        return {
            "project_id": request.project_id,
            "task_id": task.id,
            "status": "processing",
            "message": "Code generation started"
        }
        
    except Exception as e:
        logger.error(f"Generate error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/generate-enhanced-v2")
async def generate_enhanced_v2(request: GenerateRequest):
    """Nuova generazione con flusso enhanced"""
    try:
        # Verifica progetto
        project_path = Path(f"output/{request.project_id}")
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Avvia task enhanced
        task = process_enhanced_code_generation.delay(
            project_id=request.project_id,
            llm_provider=request.llm_provider,
            max_iterations=request.max_iterations
        )
        
        # Aggiorna progetto
        with open(project_path / "project.json", 'r') as f:
            project_data = json.load(f)
        
        project_data['status'] = 'processing'
        project_data['task_id'] = task.id
        project_data['generation_mode'] = 'enhanced_v2'
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        return {
            "project_id": request.project_id,
            "task_id": task.id,
            "status": "processing",
            "mode": "enhanced_v2",
            "message": "Enhanced generation started with validation and compilation checks"
        }
        
    except Exception as e:
        logger.error(f"Enhanced generate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/project/{project_id}/health")
async def get_project_health(project_id: str):
    """Ottieni report salute progetto"""
    try:
        from app.services.updated_orchestrator import UpdatedOrchestratorAgent
        from app.services.llm_service import LLMService
        
        project_path = Path(f"output/{project_id}")
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        llm_service = LLMService()
        orchestrator = UpdatedOrchestratorAgent(llm_service)
        
        health_report = await orchestrator.get_project_health_report(project_path)
        
        return health_report
        
    except Exception as e:
        logger.error(f"Health report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-with-agents")
async def generate_with_agents_wrapper(request: GenerateRequest):
    """
    Start code generation using the agent-based system
    (Wrapper per integrazione facile con il frontend esistente)
    """
    try:
        # Crea una richiesta di tipo AgentGenerateRequest
        agent_request = AgentGenerateRequest(
            project_id=request.project_id,
            llm_provider=request.llm_provider,
            max_iterations=request.max_iterations,
            agent_mode="multi_agent"  # Default to multi-agent system
        )
        # Chiama direttamente la funzione, non un metodo dell'oggetto
        return await generate_with_agents(agent_request)
    except Exception as e:
        logger.error(f"Generate with agents error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent-info")
async def get_agent_info():
    """Get information about available agent systems"""
    return {
        "available_agents": [
            {
                "id": "multi_agent",
                "name": "Multi-Agent System",
                "description": "Uses specialized agents for architecture, frontend/backend development, and testing",
                "recommended_for": "Complex projects with both frontend and backend components"
            },
            {
                "id": "updated_orchestrator",
                "name": "Enhanced Orchestrator",
                "description": "Uses an improved orchestrator with better planning and analysis capabilities",
                "recommended_for": "Projects requiring careful planning and architecture design"
            },
            {
                "id": "enhanced_generator",
                "name": "Enhanced Generator",
                "description": "Uses a single enhanced code generator with sophisticated prompting",
                "recommended_for": "Simpler projects or focused components"
            },
            {
                "id": "original",
                "name": "Original System",
                "description": "Uses the original code generation system",
                "recommended_for": "Compatibility with existing projects"
            }
        ],
        "default_agent": "multi_agent",
        "recommended_provider": "anthropic"
    }

# NUOVO: Metodo enhanced per la generazione completa
@app.post("/generate-enhanced")
async def generate_enhanced_code(request: EnhancedGenerateRequest):
    """Generate complete project with automatic merging"""
    try:
        # Verify project exists
        project_path = Path(f"output/{request.project_id}")
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Load project and requirements
        with open(project_path / "project.json", 'r') as f:
            project_data = json.load(f)
        
        requirements = project_data.get('requirements', {})
        
        logger.info(f"Starting enhanced generation for {request.project_id}")
        
        # Usa l'enhanced generator
        result = await enhanced_generator.generate_complete_project(
            project_id=request.project_id,
            requirements=requirements,
            provider=request.llm_provider,
            max_iterations=request.max_iterations
        )
        
        # Update project status
        project_data['status'] = 'completed'
        project_data['iterations_completed'] = result['iterations_made']
        project_data['final_path'] = str(result['final_path'])
        project_data['file_count'] = len(result['final_files'])
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2, cls=DateTimeEncoder)
        
        return {
            "project_id": request.project_id,
            "status": "completed",
            "iterations_completed": len(result['iterations_made']),
            "final_path": str(result['final_path']),
            "file_count": len(result['final_files']),
            "download_url": f"/project/{request.project_id}/download-final",
            "message": f"Project generated with {len(result['iterations_made'])} iterations"
        }
        
    except Exception as e:
        logger.error(f"Enhanced generate error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/project/{project_id}/status")
async def get_project_status(project_id: str):
    """Get current project status - compatibile con entrambe le strutture"""
    try:
        project_path = Path(f"output/{project_id}")
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = load_project_data(project_path)
        
        # 🔥 RILEVA STRUTTURA: Controlla generation_mode
        generation_mode = project_data.get('generation_mode', 'original')
        
        if generation_mode == 'enhanced_v2':
            # 🔥 NUOVA STRUTTURA
            return await get_enhanced_project_status(project_id, project_path, project_data)
        else:
            # 🔄 STRUTTURA ORIGINALE (codice esistente unchanged)
            iterations = list(project_path.glob("iter-*"))
            current_iteration = len(iterations)
            
            has_final = (project_path / "final").exists()
            
            test_results = None
            if current_iteration > 0:
                latest_iter = project_path / f"iter-{current_iteration}"
                test_results_path = latest_iter / "test_results.json"
                if test_results_path.exists():
                    try:
                        with open(test_results_path, 'r') as f:
                            test_results = json.load(f)
                    except json.JSONDecodeError:
                        test_results = {"error": "Invalid test results data"}
            
            return {
                "project_id": project_id,
                "project_name": project_data.get('name', f'Project {project_id[:8]}'),
                "status": project_data.get('status', 'unknown'),
                "generation_mode": "original",
                "current_iteration": current_iteration,
                "has_final": has_final,
                "test_results": test_results,
                "output_path": str(project_path),
                "final_path": str(project_path / "final") if has_final else None,
                "file_count": project_data.get('file_count', 0)
            }
            
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
async def get_enhanced_project_status(project_id: str, project_path: Path, project_data: Dict):
    """Status per progetti con nuova struttura enhanced"""
    
    # Trova iterazioni con nuova struttura
    iterations = []
    for item in project_path.iterdir():
        if item.is_dir() and item.name.startswith("iter-"):
            try:
                iter_num = int(item.name.split("-")[1])
                
                # Carica iteration summary se esiste
                summary_path = item / "iteration_summary.json"
                iteration_info = {
                    "iteration": iter_num,
                    "has_summary": summary_path.exists()
                }
                
                if summary_path.exists():
                    try:
                        with open(summary_path, 'r') as f:
                            summary = json.load(f)
                        iteration_info.update({
                            "success": summary.get("success", False),
                            "validation_errors": summary.get("validation_report", {}).get("summary", {}).get("error", 0),
                            "compilation_success": summary.get("compilation_report", {}).get("success", False),
                            "test_success": summary.get("test_results", {}).get("success", False),
                            "files_generated": summary.get("files_generated", 0)
                        })
                    except Exception as e:
                        logger.warning(f"Could not load iteration summary for iter-{iter_num}: {e}")
                        iteration_info["error"] = str(e)
                
                iterations.append(iteration_info)
            except ValueError:
                continue
    
    # Ordina per numero iterazione
    iterations.sort(key=lambda x: x["iteration"])
    
    # Controlla progetto finale
    final_path = project_path / "final"
    has_final = final_path.exists()
    
    return {
        "project_id": project_id,
        "project_name": project_data.get('name', f'Project {project_id[:8]}'),
        "status": project_data.get('status', 'unknown'),
        "generation_mode": "enhanced_v2",
        "agent_mode": project_data.get('selected_agent_mode', 'unknown'),
        "current_iteration": len(iterations),
        "iterations": iterations,
        "has_final": has_final,
        "final_path": str(final_path) if has_final else None,
        "enhanced_features": {
            "validation_reports": True,
            "compilation_checks": True,
            "structured_tests": True,
            "detailed_analysis": True,
            "error_tracking": True,
            "health_monitoring": True
        },
        "analysis": project_data.get('analysis', {}),
        "final_result": project_data.get('final_result', {})
    }

@app.put("/project/{project_id}/update-name")
async def update_project_name(project_id: str, request: dict):
    """Update project name"""
    try:
        project_path = Path(f"output/{project_id}")
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get the new name from request
        new_name = request.get("project_name")
        if not new_name or not isinstance(new_name, str) or not new_name.strip():
            raise HTTPException(status_code=400, detail="Invalid project name")
        
        new_name = new_name.strip()
        
        # Load project data
        project_json_path = project_path / "project.json"
        project_data = load_project_data(project_path)
        
        # Update project name
        project_data["name"] = new_name
        
        # Save project data
        with open(project_json_path, 'w') as f:
            json.dump(project_data, f, indent=2, cls=DateTimeEncoder)
        
        return {
            "project_id": project_id,
            "project_name": new_name,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error updating project name: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Mantieni il download esistente
@app.get("/project/{project_id}/download")
async def download_project(project_id: str, iteration: Optional[int] = None):
    """Download generated code for a specific iteration"""
    try:
        project_path = Path(f"output/{project_id}")
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Determine which iteration to download
        if iteration is None:
            iterations = list(project_path.glob("iter-*"))
            if not iterations:
                raise HTTPException(status_code=404, detail="No iterations found")
            iteration = len(iterations)
        
        iter_path = project_path / f"iter-{iteration}"
        if not iter_path.exists():
            raise HTTPException(status_code=404, detail=f"Iteration {iteration} not found")
        
        # Create zip file
        zip_path = project_path / f"code_iter_{iteration}.zip"
        shutil.make_archive(str(zip_path.with_suffix('')), 'zip', iter_path)
        
        from fastapi.responses import FileResponse
        return FileResponse(
            zip_path,
            media_type='application/zip',
            filename=f"{project_id}_iter_{iteration}.zip"
        )
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# NUOVO: Download del progetto finale completo
@app.get("/project/{project_id}/download-final")
async def download_final_project(project_id: str):
    """Download the complete final project"""
    try:
        project_path = Path(f"output/{project_id}")
        final_path = project_path / "final"
        
        if not final_path.exists():
            raise HTTPException(status_code=404, detail="Final project not found")
        
        # Create zip file of final project
        zip_path = project_path / f"{project_id}_final.zip"
        shutil.make_archive(str(zip_path.with_suffix('')), 'zip', final_path)
        
        from fastapi.responses import FileResponse
        return FileResponse(
            zip_path,
            media_type='application/zip',
            filename=f"{project_id}_final.zip"
        )
        
    except Exception as e:
        logger.error(f"Final download error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/project/{project_id}/merge")
async def merge_project(project_id: str):
    """Merge all iterations into final project"""
    try:
        # Importa solo quando serve
        from app.services.project_merger import ProjectMerger
        
        project_path = Path(f"output/{project_id}")
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Trova tutte le iterazioni
        iterations = []
        for iter_dir in project_path.glob("iter-*"):
            if iter_dir.is_dir():
                iter_num = int(iter_dir.name.split("-")[1])
                iterations.append(iter_num)
        
        if not iterations:
            raise HTTPException(status_code=404, detail="No iterations found")
        
        # Crea il merger e combina le iterazioni
        project_merger = ProjectMerger(base_output_path="output")
        project_merger.merge_all_iterations(project_id, sorted(iterations))
        
        return {
            "success": True,
            "message": f"Merged {len(iterations)} iterations successfully",
            "final_path": f"output/{project_id}/final"
        }
        
    except Exception as e:
        logger.error(f"Merge error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
     
# NUOVO: Cleanup endpoint
@app.delete("/project/{project_id}/cleanup")
async def cleanup_project(project_id: str, keep_final: bool = True):
    """Clean up intermediate iterations"""
    try:
        project_merger.cleanup_iterations(project_id, keep_final)
        
        return {
            "success": True,
            "message": f"Cleaned up iterations for {project_id}",
            "kept_final": keep_final
        }
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mantieni il tuo endpoint esistente
@app.get("/llm-providers")
async def get_llm_providers():
    """Get available LLM providers"""
    return {
        "providers": [
            {
                "id": "openai",
                "name": "ChatGPT (OpenAI)",
                "model": "gpt-4",
                "description": "General purpose code generation"
            },
            {
                "id": "anthropic",
                "name": "Claude (Anthropic)",
                "model": "claude-3-opus",
                "description": "Complex architectures and systems"
            },
            {
                "id": "deepseek",
                "name": "DeepSeek (RunPod)",
                "model": "deepseek-coder",
                "description": "Specialized for coding tasks"
            }
        ]
    }

@app.post("/project/{project_id}/stop")
async def stop_project_generation(project_id: str):
    """
    Ferma la generazione in corso per un progetto specifico.
    """
    try:
        project_path = Path(f"output/{project_id}")
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        
        project_data = load_project_data(project_path)
        
        # Verifica se il progetto è in fase di generazione
        status = project_data.get("status")
        if status not in ["processing", "generating_code", "generating_tests", "running_tests"]:
            raise HTTPException(status_code=400, detail=f"Il progetto è in stato '{status}' e non può essere fermato")
        
        # Ottieni l'ID del task Celery
        task_id = project_data.get("task_id")
        if not task_id:
            raise HTTPException(status_code=404, detail="ID del task non trovato")
        
        # Crea un file di segnalazione per indicare che il task deve essere fermato
        stop_file = project_path / "STOP_REQUESTED"
        with open(stop_file, "w") as f:
            f.write(f"Stop requested at {datetime.now().isoformat()}")
        
        # Aggiorna lo stato del progetto
        project_data["status"] = "failed"
        project_data["stopped_by_user"] = True
        project_data["stopped_at"] = datetime.now().isoformat()
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        # Tenta comunque di revocare il task Celery come prima
        try:
            from app.tasks.celery_app import celery
            celery.control.revoke(task_id, terminate=True, signal='SIGTERM')
            logger.info(f"Task {task_id} revoked successfully")
        except Exception as revoke_error:
            logger.warning(f"Failed to revoke task, but stop file created: {revoke_error}")
        
        return {
            "success": True,
            "message": "Generazione fermata con successo",
            "project_id": project_id
        }
    except Exception as e:
        logger.error(f"Errore durante lo stop della generazione: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))   

@app.get("/project/{project_id}/can-stop")
async def can_stop_generation(project_id: str):
    """
    Verifica se la generazione può essere fermata per un progetto.
    """
    try:
        project_path = Path(f"output/{project_id}")
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        
        # 🔧 FIX: Controlla se il file esiste E non è vuoto
        project_json_path = project_path / "project.json"
        if not project_json_path.exists():
            raise HTTPException(status_code=404, detail="File progetto non trovato")
        
        # 🔧 FIX: Controlla se il file è vuoto
        if project_json_path.stat().st_size == 0:
            raise HTTPException(status_code=500, detail="File progetto corrotto (vuoto)")
        
        
        project_data = load_project_data(project_path)
        
        # Resto del codice rimane identico...
        status = project_data.get("status")
        can_stop = status in ["processing", "generating_code", "generating_tests", "running_tests"]
        task_id = project_data.get("task_id")
        
        # Verifica lo stato del task
        if can_stop and task_id:
            from app.tasks.celery_app import celery
            task = AsyncResult(task_id, app=celery)
            if task.state in ['PENDING', 'STARTED', 'PROGRESS']:
                return {
                    "can_stop": True,
                    "reason": f"Il progetto è in fase di {status} e può essere fermato",
                    "task_id": task_id,
                    "task_state": task.state
                }
            else:
                return {
                    "can_stop": False,
                    "reason": f"Il task è in stato {task.state} e non può essere fermato",
                    "task_id": task_id,
                    "task_state": task.state
                }
        
        # Risposta in base allo stato
        if can_stop:
            return {
                "can_stop": True,
                "reason": f"Il progetto è in fase di {status} e può essere fermato"
            }
        else:
            return {
                "can_stop": False,
                "reason": f"Il progetto è in stato '{status}' e non può essere fermato"
            }
    except Exception as e:
        logger.error(f"Errore durante la verifica dello stop: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)