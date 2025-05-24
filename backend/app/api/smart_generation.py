# backend/app/api/smart_generation.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import logging
from pathlib import Path

from app.services.requirements_analyzer import RequirementsAnalyzer, ProjectComplexity, AgentMode
from app.tasks.celery_app import process_enhanced_code_generation  # 🔥 CAMBIATO: usa il nuovo task

logger = logging.getLogger(__name__)
router = APIRouter()

class SmartGenerateRequest(BaseModel):
    project_id: str
    llm_provider: str = "anthropic"
    override_agent_mode: Optional[str] = None  # Allow manual override
    override_max_iterations: Optional[int] = None  # Allow manual override

class SmartGenerateResponse(BaseModel):
    project_id: str
    task_id: str
    status: str
    analysis: Dict[str, Any]
    message: str

@router.post("/smart-generate", response_model=SmartGenerateResponse)
async def smart_generate_code(request: SmartGenerateRequest):
    """
    Intelligently analyze requirements and route to appropriate agent system
    🔥 AGGIORNATO: Ora usa il nuovo enhanced orchestrator per tutti i modi eccetto "original"
    """
    try:
        # Verify project exists
        project_path = Path(f"output/{request.project_id}")
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Load project data
        try:
            with open(project_path / "project.json", 'r') as f:
                project_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading project data: {e}")
            raise HTTPException(status_code=500, detail=f"Error loading project data: {str(e)}")
        
        # Extract requirements
        requirements = project_data.get('requirements', {})
        
        # Analyze requirements
        analyzer = RequirementsAnalyzer()
        analysis = analyzer.analyze_project(requirements)
        
        # Determine agent mode (allow override)
        agent_mode = request.override_agent_mode or analysis["agent_mode"]
        max_iterations = request.override_max_iterations or analysis["max_iterations"]
        
        logger.info(f"Smart generation for {request.project_id}: {analysis['complexity']} -> {agent_mode}")
        
        # 🔥 NUOVO: Determina quale sistema usare
        use_enhanced_system = agent_mode != "original"
        generation_mode = "enhanced_v2" if use_enhanced_system else "original"
        
        # Update project status with analysis
        project_data['status'] = 'processing'
        project_data['analysis'] = analysis
        project_data['selected_agent_mode'] = agent_mode
        project_data['selected_max_iterations'] = max_iterations
        project_data['generation_mode'] = generation_mode  # 🔥 NUOVO: Marca il tipo di sistema
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        # 🔥 AGGIORNATO: Usa sempre il nuovo task enhanced
        # Il task stesso decide internamente quale orchestratore usare
        task = process_enhanced_code_generation.delay(
            project_id=request.project_id,
            llm_provider=request.llm_provider,
            max_iterations=max_iterations,
            agent_mode=agent_mode
        )
        
        # Update project with task ID
        project_data['task_id'] = task.id
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_data, f, indent=2)
        
        # Create response message
        complexity = analysis["complexity"]
        features_count = len(analysis["features_detected"])
        estimated_duration = analysis["estimated_duration"]
        
        # 🔥 AGGIORNATO: Messaggio più informativo
        system_type = "Enhanced System with validation & compilation checks" if use_enhanced_system else "Original System"
        message = f"Analyzed as {complexity} project with {features_count} features. Using {agent_mode} agent ({system_type}). Estimated duration: {estimated_duration}"
        
        return SmartGenerateResponse(
            project_id=request.project_id,
            task_id=task.id,
            status="processing",
            analysis=analysis,
            message=message
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Smart generation error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyze-requirements/{project_id}")
async def analyze_requirements_only(project_id: str):
    """
    Just analyze requirements without starting generation
    """
    try:
        # Verify project exists
        project_path = Path(f"output/{project_id}")
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Load project data
        with open(project_path / "project.json", 'r') as f:
            project_data = json.load(f)
        
        # Extract requirements
        requirements = project_data.get('requirements', {})
        
        # Analyze requirements
        analyzer = RequirementsAnalyzer()
        analysis = analyzer.analyze_project(requirements)
        
        return {
            "project_id": project_id,
            "analysis": analysis,
            "recommendations": {
                "agent_mode": analysis["agent_mode"],
                "max_iterations": analysis["max_iterations"],
                "estimated_files": analysis["estimated_files"],
                "estimated_duration": analysis["estimated_duration"]
            },
            "system_info": {
                "will_use_enhanced": analysis["agent_mode"] != "original",
                "enhanced_features": [
                    "Code validation",
                    "Compilation checking", 
                    "Structured project layout",
                    "Detailed error analysis",
                    "Comprehensive reporting"
                ] if analysis["agent_mode"] != "original" else []
            }
        }
        
    except Exception as e:
        logger.error(f"Requirements analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent-modes")
async def get_agent_modes_info():
    """
    Get information about available agent modes and when to use them
    🔥 AGGIORNATO: Aggiunge info su enhanced system
    """
    return {
        "agent_modes": [
            {
                "id": "original",
                "name": "Single Agent (Original)",
                "description": "Basic code generator, fast and simple",
                "system": "original",  # 🔥 NUOVO
                "enhanced_features": False,  # 🔥 NUOVO
                "best_for": [
                    "Static websites",
                    "Simple landing pages",
                    "Quick prototypes",
                    "Single-page applications"
                ],
                "complexity": "simple",
                "avg_duration": "1-3 minutes",
                "typical_files": "5-15 files",
                "features": [
                    "Basic code generation",
                    "Simple file structure",
                    "Minimal testing",
                    "Fast execution"
                ]
            },
            {
                "id": "enhanced_generator",
                "name": "Enhanced Single Agent",
                "description": "Improved code generator with validation and compilation checks",
                "system": "enhanced_v2",  # 🔥 NUOVO
                "enhanced_features": True,  # 🔥 NUOVO
                "best_for": [
                    "Frontend applications with some complexity",
                    "Interactive websites",
                    "Component libraries",
                    "Medium-complexity SPAs"
                ],
                "complexity": "simple-moderate", 
                "avg_duration": "3-8 minutes",
                "typical_files": "10-25 files",
                "features": [
                    "Enhanced code quality",
                    "Code validation & compilation checks",  # 🔥 AGGIORNATO
                    "Structured project layout",  # 🔥 NUOVO
                    "Better error handling",
                    "Comprehensive testing"  # 🔥 AGGIORNATO
                ]
            },
            {
                "id": "updated_orchestrator",
                "name": "Enhanced Orchestrator",
                "description": "Planning-based approach with full validation pipeline",
                "system": "enhanced_v2",  # 🔥 NUOVO
                "enhanced_features": True,  # 🔥 NUOVO
                "best_for": [
                    "Full-stack applications",
                    "Applications requiring careful architecture",
                    "Projects with specific performance requirements",
                    "Apps with moderate backend complexity"
                ],
                "complexity": "moderate-complex",
                "avg_duration": "8-25 minutes", 
                "typical_files": "25-50 files",
                "features": [
                    "Requirements analysis",
                    "Architecture planning",
                    "Code validation & compilation checks",  # 🔥 NUOVO
                    "Iterative improvement with error tracking",  # 🔥 AGGIORNATO
                    "Comprehensive testing pipeline",  # 🔥 AGGIORNATO
                    "Performance optimization"
                ]
            },
            {
                "id": "multi_agent",
                "name": "Multi-Agent System",
                "description": "Specialized agents with full enhanced pipeline",
                "system": "enhanced_v2",  # 🔥 NUOVO
                "enhanced_features": True,  # 🔥 NUOVO
                "best_for": [
                    "Complex full-stack applications",
                    "Enterprise applications", 
                    "Apps with multiple integrations",
                    "Microservices architectures",
                    "Production-ready applications"
                ],
                "complexity": "complex-enterprise",
                "avg_duration": "15-60 minutes",
                "typical_files": "40-100+ files",
                "features": [
                    "Specialized agent coordination",
                    "Full validation & compilation pipeline",  # 🔥 NUOVO
                    "System configuration generation",
                    "External service integrations",
                    "Comprehensive API development",
                    "Advanced testing strategies with error analysis",  # 🔥 AGGIORNATO
                    "Production deployment configs",
                    "Detailed project health reporting"  # 🔥 NUOVO
                ]
            }
        ],
        "system_comparison": {  # 🔥 NUOVO
            "original": {
                "validation": False,
                "compilation_checks": False,
                "structured_layout": False,
                "error_analysis": "Basic",
                "testing": "Basic",
                "reporting": "Minimal"
            },
            "enhanced_v2": {
                "validation": True,
                "compilation_checks": True,
                "structured_layout": True,
                "error_analysis": "Advanced",
                "testing": "Comprehensive", 
                "reporting": "Detailed"
            }
        },
        "complexity_levels": [
            {
                "level": "simple",
                "description": "Static sites, landing pages, minimal interactivity",
                "examples": ["Landing page", "Portfolio site", "Documentation site"],
                "recommended_agents": ["original", "enhanced_generator"],
                "enhanced_benefit": "Low - Original system sufficient"  # 🔥 NUOVO
            },
            {
                "level": "moderate",
                "description": "Dynamic frontend with some backend features",
                "examples": ["Blog with CMS", "Dashboard with API", "E-commerce frontend"],
                "recommended_agents": ["enhanced_generator", "updated_orchestrator"],
                "enhanced_benefit": "High - Validation prevents common errors"  # 🔥 NUOVO
            },
            {
                "level": "complex",
                "description": "Full-stack applications with multiple features",
                "examples": ["Social platform", "SaaS application", "E-commerce platform"],
                "recommended_agents": ["updated_orchestrator", "multi_agent"],
                "enhanced_benefit": "Critical - Prevents deployment failures"  # 🔥 NUOVO
            },
            {
                "level": "enterprise",
                "description": "Large-scale applications with advanced requirements",
                "examples": ["Enterprise software", "Microservices platform", "Financial systems"],
                "recommended_agents": ["multi_agent"],
                "enhanced_benefit": "Essential - Required for production readiness"  # 🔥 NUOVO
            }
        ],
        "selection_criteria": {
            "features_that_increase_complexity": [
                "Authentication system",
                "Database integration",
                "External API integrations",
                "Payment processing",
                "Real-time features",
                "File uploads",
                "Multi-user functionality",
                "Admin dashboards",
                "Complex routing",
                "Microservices architecture"
            ],
            "auto_selection_rules": [
                "Projects with 0-2 features → Single Agent",
                "Projects with 3-5 features → Enhanced Generator/Orchestrator",
                "Projects with 6+ features → Multi-Agent",
                "Any microservices → Multi-Agent",
                "Static/landing page → Single Agent",
                "Full-stack with auth + database → Multi-Agent"
            ],
            "enhanced_system_triggers": [  # 🔥 NUOVO
                "Projects with compilation requirements (Node.js, Python)",
                "Projects requiring structured testing",
                "Projects with multiple integrations",
                "Projects needing error analysis and fixing"
            ]
        }
    }

# Resto dei metodi rimane identico...
@router.get("/complexity-analysis/{project_id}")
async def get_complexity_breakdown(project_id: str):
    # ... tutto il codice esistente rimane identico ...
    pass

def _get_alternative_recommendations(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    # ... tutto il codice esistente rimane identico ...
    pass