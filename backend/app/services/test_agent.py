# backend/app/services/test_agent.py
import asyncio
import logging
from typing import Dict, Any, List
from pathlib import Path

from app.services.test_generator import TestGenerator
from app.services.test_runner import TestRunner
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class TestAgent:
    def __init__(self, llm_service: LLMService):
        self.test_generator = TestGenerator(llm_service)
        self.test_runner = TestRunner()
        logger.info("TestAgent initialized")
    
    async def analyze_and_test_code(self, 
                                   requirements: Dict[str, Any],
                                   code_files: Dict[str, str],
                                   provider: str,
                                   output_path: Path) -> Dict[str, Any]:
        """
        Complete analysis cycle: generate tests, run them, analyze results
        This replaces the manual coordination of TestGenerator + TestRunner
        """
        logger.info(f"Starting test analysis for {len(code_files)} files")
        
        try:
            # 1. Generate tests using existing TestGenerator
            test_files = await self.test_generator.generate_tests(
                requirements, code_files, provider
            )
            logger.info(f"Generated {len(test_files)} test files")
            
            # 2. Run tests using existing TestRunner
            test_results = await self.test_runner.run_tests(output_path, test_files)
            logger.info(f"Test execution completed")
            
            # 3. Analyze failures using existing TestRunner method
            failures = self.test_runner.analyze_test_failures(test_results)
            logger.info(f"Found {len(failures)} test failures")
            
            return {
                "test_files": test_files,
                "test_results": test_results,
                "failures": failures,
                "success": test_results.get("success", False),
                "summary": {
                    "total_tests": len(test_files),
                    "failures_count": len(failures),
                    "passed": test_results.get("success", False)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in test analysis: {str(e)}")
            return {
                "test_files": {},
                "test_results": {"success": False, "error": str(e)},
                "failures": [{"error": str(e)}],
                "success": False,
                "summary": {"total_tests": 0, "failures_count": 1, "passed": False}
            }