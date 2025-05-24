# app/services/test_generator.py
import asyncio
import logging
from typing import Dict, Any, List
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class TestGenerator:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    async def generate_tests(self, 
                           requirements: Dict[str, Any],
                           code_files: Dict[str, str],
                           provider: str) -> Dict[str, str]:
        """Generate test files for the generated code"""
        
        test_files = {}
        
        # Generate backend tests if backend code exists
        backend_files = {k: v for k, v in code_files.items() 
                        if k.endswith('.py') or '/app/' in k or '/backend/' in k}
        
        if backend_files:
            logger.info(f"Generating backend tests for {len(backend_files)} files")
            backend_test_files = await self._generate_backend_tests(
                requirements, backend_files, provider
            )
            test_files.update(backend_test_files)
        
        # Generate frontend tests if frontend code exists
        frontend_files = {k: v for k, v in code_files.items() 
                         if k.endswith('.js') or k.endswith('.jsx') or 
                            k.endswith('.ts') or k.endswith('.tsx') or
                            '/src/' in k or '/frontend/' in k}
        
        if frontend_files:
            logger.info(f"Generating frontend tests for {len(frontend_files)} files")
            frontend_test_files = await self._generate_frontend_tests(
                requirements, frontend_files, provider
            )
            test_files.update(frontend_test_files)
        
        return test_files
    
    async def _generate_backend_tests(self,
                                    requirements: Dict[str, Any],
                                    code_files: Dict[str, str],
                                    provider: str) -> Dict[str, str]:
        """Generate pytest tests for backend code"""
        
        system_prompt = """You are an expert Python test engineer specializing in pytest. 
        Generate comprehensive test files for the given Python code. Include tests for all 
        significant functionality, with proper test setup, mocks, and assertions."""
        
        # Prepare code excerpts to include in the prompt
        code_excerpts = []
        for path, content in code_files.items():
            if '/api/' in path or 'model' in path or 'schema' in path or 'main.py' in path:
                excerpt = f"\n--- {path} ---\n{content[:1000]}...(truncated)"
                code_excerpts.append(excerpt)
                if len(code_excerpts) >= 5:  # Limit to 5 files to avoid token limits
                    break
        
        prompt = f"""Generate pytest test files for the following backend code:

{' '.join(code_excerpts)}

The application has these requirements:
Create test files following these guidelines:
1. Use pytest fixtures for database setup and teardown
2. Mock external services when appropriate
3. Test both success and error cases
4. Include docstrings explaining the purpose of each test
5. Use descriptive test function names following the pattern test_should_*

IMPORTANT: For each file, use EXACTLY this format:
<file path="tests/path/to/test_file.py">
# Test file content
</file>

DO NOT use JSON or code blocks with backticks. Use ONLY the <file> XML-like tags.
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Extract test files using the same pattern as in CodeGenerator
        test_files = self._extract_files_with_tags(response)
        logger.info(f"Generated {len(test_files)} backend test files")
        
        return test_files
    
    async def _generate_frontend_tests(self,
                                     requirements: Dict[str, Any],
                                     code_files: Dict[str, str],
                                     provider: str) -> Dict[str, str]:
        """Generate Jest tests for frontend code"""
        
        system_prompt = """You are an expert React test engineer specializing in Jest and 
        React Testing Library. Generate comprehensive test files for the given React components
        and utilities. Include tests for all significant functionality, with proper test setup,
        mocks, and assertions."""
        
        # Prepare code excerpts to include in the prompt
        code_excerpts = []
        for path, content in code_files.items():
            if ('component' in path.lower() or '/page' in path or '/hook' in path or 
                path.endswith('.tsx') or path.endswith('.jsx')):
                excerpt = f"\n--- {path} ---\n{content[:1000]}...(truncated)"
                code_excerpts.append(excerpt)
                if len(code_excerpts) >= 5:  # Limit to 5 files to avoid token limits
                    break
        
        prompt = f"""Generate Jest test files for the following React components:

{' '.join(code_excerpts)}

The application has these requirements:
Create test files following these guidelines:
1. Use React Testing Library for component testing
2. Test both rendering and interactions
3. Mock API calls and context providers when needed
4. Test edge cases and error states
5. Include descriptive test descriptions

IMPORTANT: For each file, use EXACTLY this format:
<file path="src/path/to/component.test.tsx">
// Test file content
</file>

DO NOT use JSON or code blocks with backticks. Use ONLY the <file> XML-like tags.
"""
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Extract test files using the same pattern as in CodeGenerator
        test_files = self._extract_files_with_tags(response)
        logger.info(f"Generated {len(test_files)} frontend test files")
        
        return test_files
    
    def _extract_files_with_tags(self, response: str) -> Dict[str, str]:
        """Extract files from response using <file> tags"""
        import re
        
        files = {}
        
        # Pattern to match <file path="...">...</file> format
        pattern = r'<file path=[\'"]([^\'"]+)[\'"]>(.*?)</file>'
        matches = re.finditer(pattern, response, re.DOTALL)
        
        for match in matches:
            file_path = match.group(1)
            content = match.group(2).strip()
            files[file_path] = content
        
        return files