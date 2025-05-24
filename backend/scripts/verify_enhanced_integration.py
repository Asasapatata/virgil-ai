#!/usr/bin/env python3
# backend/scripts/verify_enhanced_integration.py
"""
Script per verificare che l'integrazione enhanced sia configurata correttamente
"""

import sys
import os
import importlib
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_imports():
    """Verifica che tutti i moduli necessari siano importabili"""
    
    print("🔍 Checking imports...")
    
    required_modules = [
        "app.services.code_validator",
        "app.services.compilation_checker", 
        "app.services.iteration_manager",
        "app.services.enhanced_test_agent",
        "app.services.updated_orchestrator",
        "app.services.requirements_analyzer",
        "app.api.smart_generation",
        "app.tasks.celery_app"
    ]
    
    success = True
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
            print(f"  ✅ {module_name}")
        except ImportError as e:
            print(f"  ❌ {module_name}: {e}")
            success = False
    
    return success

def check_task_exists():
    """Verifica che il nuovo task Celery esista"""
    
    print("\n🔍 Checking Celery tasks...")
    
    try:
        from app.tasks.celery_app import process_enhanced_code_generation
        print("  ✅ process_enhanced_code_generation task exists")
        return True
    except ImportError as e:
        print(f"  ❌ process_enhanced_code_generation task missing: {e}")
        return False

def check_smart_generation_endpoint():
    """Verifica che l'endpoint smart generation sia configurato"""
    
    print("\n🔍 Checking smart generation endpoint...")
    
    try:
        from app.api.smart_generation import smart_generate_code
        print("  ✅ smart_generate_code endpoint exists")
        return True
    except ImportError as e:
        print(f"  ❌ smart_generate_code endpoint missing: {e}")
        return False

def check_requirements_analyzer():
    """Verifica che RequirementsAnalyzer abbia il sistema mapping"""
    
    print("\n🔍 Checking RequirementsAnalyzer...")
    
    try:
        from app.services.requirements_analyzer import RequirementsAnalyzer
        
        analyzer = RequirementsAnalyzer()
        
        # Check system mapping exists
        if hasattr(analyzer, 'SYSTEM_MAPPING'):
            print("  ✅ SYSTEM_MAPPING exists")
            
            # Check mapping values
            expected_mappings = {
                "original": "original",
                "enhanced_generator": "enhanced_v2",
                "updated_orchestrator": "enhanced_v2", 
                "multi_agent": "enhanced_v2"
            }
            
            for key, expected in expected_mappings.items():
                if analyzer.SYSTEM_MAPPING.get(key) == expected:
                    print(f"    ✅ {key} -> {expected}")
                else:
                    print(f"    ❌ {key} -> {analyzer.SYSTEM_MAPPING.get(key)} (expected {expected})")
                    return False
            
            return True
        else:
            print("  ❌ SYSTEM_MAPPING missing")
            return False
            
    except Exception as e:
        print(f"  ❌ RequirementsAnalyzer check failed: {e}")
        return False

def check_orchestrator_integration():
    """Verifica che l'orchestratore enhanced sia integrato"""
    
    print("\n🔍 Checking orchestrator integration...")
    
    try:
        from app.services.updated_orchestrator import UpdatedOrchestratorAgent
        from app.services.llm_service import LLMService
        
        # Mock LLM service
        class MockLLMService:
            pass
        
        mock_llm = MockLLMService()
        orchestrator = UpdatedOrchestratorAgent(mock_llm)
        
        # Check required methods exist
        required_methods = [
            'generate_application_with_enhanced_flow',
            'generate_final_project', 
            'get_project_health_report'
        ]
        
        for method_name in required_methods:
            if hasattr(orchestrator, method_name):
                print(f"  ✅ {method_name} method exists")
            else:
                print(f"  ❌ {method_name} method missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Orchestrator integration check failed: {e}")
        return False

def check_file_structure():
    """Verifica che tutti i file necessari esistano"""
    
    print("\n🔍 Checking file structure...")
    
    backend_path = Path(__file__).parent.parent
    
    required_files = [
        "app/services/code_validator.py",
        "app/services/compilation_checker.py",
        "app/services/iteration_manager.py", 
        "app/services/enhanced_test_agent.py",
        "app/services/updated_orchestrator.py",
        "app/services/requirements_analyzer.py",
        "app/api/smart_generation.py",
        "app/tasks/celery_app.py"
    ]
    
    success = True
    for file_path in required_files:
        full_path = backend_path / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} missing")
            success = False
    
    return success

def run_integration_test():
    """Esegue un test di integrazione veloce"""
    
    print("\n🔍 Running integration test...")
    
    try:
        from app.services.requirements_analyzer import RequirementsAnalyzer
        
        # Test analysis
        analyzer = RequirementsAnalyzer()
        
        test_requirements = {
            "project": {"type": "fullstack", "name": "Test App"},
            "features": [
                {"authentication": {"providers": ["email", "google"]}},
                {"database": {"type": "postgresql"}}
            ]
        }
        
        analysis = analyzer.analyze_project(test_requirements)
        
        # Check analysis results
        required_keys = ["project_type", "complexity", "agent_mode", "system_type", "enhanced_features"]
        
        for key in required_keys:
            if key in analysis:
                print(f"  ✅ Analysis includes {key}: {analysis[key]}")
            else:
                print(f"  ❌ Analysis missing {key}")
                return False
        
        # Check system mapping logic
        if analysis["agent_mode"] != "original":
            if analysis["system_type"] == "enhanced_v2" and analysis["enhanced_features"]:
                print("  ✅ System mapping logic works correctly")
                return True
            else:
                print("  ❌ System mapping logic failed")
                return False
        else:
            print("  ✅ Original system correctly identified")
            return True
    
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False

def main():
    """Main verification function"""
    
    print("🚀 Verifying Enhanced System Integration")
    print("=" * 50)
    
    checks = [
        ("File Structure", check_file_structure),
        ("Imports", check_imports),
        ("Celery Task", check_task_exists),
        ("Smart Generation Endpoint", check_smart_generation_endpoint),
        ("Requirements Analyzer", check_requirements_analyzer),
        ("Orchestrator Integration", check_orchestrator_integration),
        ("Integration Test", run_integration_test)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 30)
        
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ Enhanced system integration is ready!")
        print("\nNext steps:")
        print("1. Start the backend server")
        print("2. Test smart generation via API")
        print("3. Verify enhanced features work")
        return 0
    else:
        print("❌ SOME CHECKS FAILED!")
        print("🔧 Please fix the issues above before proceeding")
        print("\nCommon fixes:")
        print("1. Ensure all new files are created")
        print("2. Check import statements")
        print("3. Verify task registration in celery_app.py")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)