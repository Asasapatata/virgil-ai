from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class ProjectStatus(str, Enum):
    CREATED = "created"
    UPLOADED = "uploaded"  # Aggiunto per file caricati
    IMPORTED = "imported"  # Aggiunto per progetti importati
    PROCESSING = "processing"
    GENERATING_CODE = "generating_code"
    GENERATING_TESTS = "generating_tests"
    RUNNING_TESTS = "running_tests"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"

class AnalysisResult(BaseModel):
    technologies: Optional[List[str]] = Field(default_factory=list)
    estimated_complexity: Optional[str] = None  # 'low', 'medium', 'high'
    suggestions: Optional[List[str]] = Field(default_factory=list)

class Project(BaseModel):
    id: str
    name: str
    requirements: Dict[str, Any]
    status: ProjectStatus
    created_at: datetime = datetime.now()
    updated_at: Optional[datetime] = None
    completed_iteration: Optional[int] = None
    task_id: Optional[str] = None
    
    # Campi per Stop Generation
    stopped_by_user: Optional[bool] = False
    stopped_at: Optional[datetime] = None
    
    # Campi per progetti importati
    imported: Optional[bool] = False
    imported_files: Optional[List[str]] = None
    analysis: Optional[AnalysisResult] = None
    
    # Campi per progetti modificati
    modification_id: Optional[str] = None
    modification_mode: Optional[str] = None  # 'incremental' o 'complete_rewrite'
    
    class Config:
        use_enum_values = True