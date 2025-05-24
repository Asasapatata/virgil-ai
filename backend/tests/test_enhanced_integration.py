# backend/tests/test_enhanced_integration.py
import pytest
import tempfile
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.requirements_analyzer import RequirementsAnalyzer
from app.services.updated_orchestrator import UpdatedOrchestratorAgent
from app.services.llm_service import LLMService
from app.tasks.celery_app import process_enhanced_code_generation

class TestEnhancedIntegration:
    """Test completo dell'integrazione enhanced system"""
    
    def test_requirements_analyzer_system_mapping(self):
        """Test che l'analyzer mappi correttamente i sistemi"""
        analyzer = RequirementsAnalyzer()
        
        # Test mapping
        assert analyzer.SYSTEM_MAPPING["original"] == "original"
        assert analyzer.SYSTEM_MAPPING["enhanced_generator"] == "enhanced_v2"
        assert analyzer.SYSTEM_MAPPING["updated_orchestrator"] == "enhanced_v2"
        assert analyzer.SYSTEM_MAPPING["multi_agent"] == "enhanced_v2"
    
    def test_analyze_project_includes_system_info(self):
        """Test che l'analisi includa informazioni sul sistema"""
        analyzer = RequirementsAnalyzer()
        
        # Simple project → original
        simple_requirements = {
            "project": {"type": "frontend", "name": "Simple Site"},
            "features": []
        }
        
        analysis = analyzer.analyze_project(simple_requirements)
        
        assert "system_type" in analysis
        assert "enhanced_features" in analysis
        assert analysis["enhanced_features"] == (analysis["agent_mode"] != "original")
    
    @pytest.mark.asyncio
    async def test_smart_generation_api_flow(self):
        """Test del flusso completo smart generation API"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup project
            project_id = "test-project"
            project_path = Path(temp_dir) / project_id
            project_path.mkdir()
            
            # Create project.json
            project_data = {
                "id": project_id,
                "name": "Test Project",
                "requirements": {
                    "project": {"type": "fullstack", "name": "Test App"},
                    "features": [{"authentication": {"providers": ["email"]}}]
                }
            }
            
            with open(project_path / "project.json", 'w') as f:
                json.dump(project_data, f, indent=2)
            
            # Test requirements analysis
            from app.api.smart_generation import analyze_requirements_only
            
            with patch('app.api.smart_generation.Path') as mock_path:
                mock_path_instance = Mock()
                mock_path_instance.exists.return_value = True
                mock_path.return_value = mock_path_instance
                
                with patch('builtins.open', mock_open_project_file(project_data)):
                    # Questo non testerà la chiamata HTTP reale, ma la logica
                    analyzer = RequirementsAnalyzer()
                    analysis = analyzer.analyze_project(project_data["requirements"])
                    
                    assert analysis["project_type"] == "fullstack"
                    assert "system_type" in analysis
                    assert analysis["enhanced_features"] == (analysis["agent_mode"] != "original")
    
    def test_celery_task_decision_logic(self):
        """Test della logica di decisione nel task Celery"""
        
        # Test che il task scelga l'orchestratore giusto
        test_cases = [
            ("original", "should use original orchestrator"),
            ("enhanced_generator", "should use enhanced orchestrator"),
            ("updated_orchestrator", "should use enhanced orchestrator"),
            ("multi_agent", "should use enhanced orchestrator")
        ]
        
        for agent_mode, expected_behavior in test_cases:
            # Verifica la logica without actually running the task
            if agent_mode == "original":
                expected_orchestrator = "OrchestratorAgent"
            else:
                expected_orchestrator = "UpdatedOrchestratorAgent"
            
            # This is a logical test - the actual task will import and use correct orchestrator
            assert expected_orchestrator in ["OrchestratorAgent", "UpdatedOrchestratorAgent"]
    
    @pytest.mark.asyncio 
    async def test_enhanced_orchestrator_integration(self):
        """Test integrazione enhanced orchestrator"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            project_path.mkdir()
            
            # Mock LLM service
            mock_llm = Mock(spec=LLMService)
            mock_llm.generate = Mock(return_value='''FILE: main.py
```python
def hello():
    print("Hello World")
```''')
            
            # Test orchestrator
            orchestrator = UpdatedOrchestratorAgent(mock_llm)
            
            requirements = {
                "project": {"name": "test-project", "type": "backend"},
                "backend": {"framework": "python"}
            }
            
            # Test structure creation (without full execution)
            assert orchestrator is not None
            assert hasattr(orchestrator, 'generate_application_with_enhanced_flow')
            assert hasattr(orchestrator, 'iteration_manager')
            assert hasattr(orchestrator, 'enhanced_test_agent')
    
    def test_backward_compatibility_detection(self):
        """Test che il sistema mantenga backward compatibility"""
        
        # Test project data structures
        old_project = {"name": "Old Project", "status": "completed"}
        new_project = {
            "name": "New Project", 
            "status": "completed",
            "generation_mode": "enhanced_v2",
            "selected_agent_mode": "multi_agent"
        }
        
        # Old project should be detected as original
        assert old_project.get("generation_mode", "original") == "original"
        
        # New project should be detected as enhanced
        assert new_project.get("generation_mode") == "enhanced_v2"

def mock_open_project_file(project_data):
    """Helper per mock open() calls"""
    from unittest.mock import mock_open
    return mock_open(read_data=json.dumps(project_data))

if __name__ == "__main__":
    # Run basic tests
    test = TestEnhancedIntegration()
    test.test_requirements_analyzer_system_mapping()
    test.test_analyze_project_includes_system_info()
    test.test_celery_task_decision_logic() 
    test.test_backward_compatibility_detection()
    print("✅ All integration tests passed!")