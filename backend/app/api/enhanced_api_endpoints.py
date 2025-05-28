# backend/app/api/generate.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import logging

from app.services.enhanced_code_generator import EnhancedCodeGenerator
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter()

class GenerateRequest(BaseModel):
    project: Dict[str, Any]
    requirements: Dict[str, Any]
    provider: str = "claude"
    max_iterations: int = 10

class GenerateResponse(BaseModel):
    success: bool
    project_id: str
    message: str
    iterations_completed: int
    final_path: str
    file_count: int
    download_url: Optional[str] = None

# Inizializza i servizi
llm_service = LLMService()
enhanced_generator = EnhancedCodeGenerator(llm_service)

@router.post("/generate-complete", response_model=GenerateResponse)
async def generate_complete_project(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Endpoint principale per generare un progetto completo con iterazioni multiple
    """
    try:
        # Genera un ID unico per il progetto
        project_id = f"project-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Starting complete project generation: {project_id}")
        
        # Combina tutti i requirements
        full_requirements = {
            "project": request.project,
            **request.requirements
        }
        
        # Genera il progetto completo usando EnhancedCodeGenerator
        result = await enhanced_generator.generate_complete_project_enhanced(
            project_id=project_id,
            requirements=full_requirements,
            provider=request.provider,
            max_iterations=request.max_iterations
        )
        
        # Prepara la risposta
        return GenerateResponse(
            success=True,
            project_id=project_id,
            message=f"Project generated successfully with {result['iterations_made'][-1]} iterations",
            iterations_completed=len(result['iterations_made']),
            final_path=str(result['final_path']),
            file_count=len(result['final_files']),
            download_url=f"/api/download/{project_id}"
        )
        
    except Exception as e:
        logger.error(f"Error generating project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-single", response_model=GenerateResponse)
async def generate_single_iteration(request: GenerateRequest):
    """
    Endpoint per generare solo una singola iterazione (per compatibilità con il sistema esistente)
    """
    try:
        project_id = f"project-{uuid.uuid4().hex[:8]}"
        
        # Usa il CodeGenerator base per una singola iterazione
        from app.services.code_generator import CodeGenerator
        basic_generator = CodeGenerator(llm_service)
        
        # Determina il focus
        focus = request.requirements.get("focus", "fullstack")
        
        # Genera codice
        if focus == "frontend":
            code_files = await basic_generator.generate_react_app(request.requirements, request.provider)
        elif focus == "backend":
            code_files = await basic_generator.generate_backend_api(request.requirements, request.provider)
        else:
            code_files = await basic_generator.generate_code(request.requirements, request.provider, 1)
        
        # Salva in iter-1 e copia in final per compatibilità
        enhanced_generator._save_iteration(project_id, 1, code_files)
        
        # Crea anche la versione finale
        from app.services.project_merger import ProjectMerger
        merger = ProjectMerger()
        final_files = merger.merge_all_iterations(project_id, [1])
        
        return GenerateResponse(
            success=True,
            project_id=project_id,
            message="Single iteration completed",
            iterations_completed=1,
            final_path=str(merger.get_final_project_path(project_id)),
            file_count=len(code_files),
            download_url=f"/api/download/{project_id}"
        )
        
    except Exception as e:
        logger.error(f"Error in single iteration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{project_id}")
async def download_project(project_id: str):
    """
    Endpoint per scaricare il progetto finale come ZIP
    """
    try:
        import zipfile
        import io
        from fastapi.responses import StreamingResponse
        
        # Ottieni il percorso del progetto finale
        from app.services.project_merger import ProjectMerger
        merger = ProjectMerger()
        final_path = merger.get_final_project_path(project_id)
        
        if not final_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Crea ZIP in memoria
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in final_path.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(final_path)
                    zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={project_id}.zip"}
        )
        
    except Exception as e:
        logger.error(f"Error downloading project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{project_id}")
async def get_project_status(project_id: str):
    """
    Endpoint per ottenere lo status di un progetto
    """
    try:
        from app.services.project_merger import ProjectMerger
        from pathlib import Path
        
        merger = ProjectMerger()
        project_path = Path(merger.output_path) / project_id
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Conta le iterazioni
        iterations = []
        for iter_dir in project_path.glob("iter-*"):
            if iter_dir.is_dir():
                iter_num = int(iter_dir.name.split("-")[1])
                iterations.append(iter_num)
        
        # Verifica se esiste il progetto finale
        final_path = project_path / "final"
        has_final = final_path.exists()
        
        # Conta i file finali
        final_file_count = 0
        if has_final:
            final_file_count = len(list(final_path.rglob("*")))
        
        return {
            "project_id": project_id,
            "iterations": sorted(iterations),
            "has_final": has_final,
            "final_file_count": final_file_count,
            "final_path": str(final_path) if has_final else None
        }
        
    except Exception as e:
        logger.error(f"Error getting project status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup/{project_id}")
async def cleanup_project(project_id: str, keep_final: bool = True):
    """
    Endpoint per fare cleanup delle iterazioni intermedie
    """
    try:
        from app.services.project_merger import ProjectMerger
        merger = ProjectMerger()
        merger.cleanup_iterations(project_id, keep_final)
        
        return {
            "success": True,
            "message": f"Cleaned up iterations for {project_id}",
            "kept_final": keep_final
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))