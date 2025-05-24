# backend/app/services/code_generator.py
import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class CodeGenerator:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        logger.info("Using REAL CodeGenerator with improved prompts")
    
    async def generate_code(self, 
                          requirements: Dict[str, Any], 
                          provider: str,
                          iteration: int,
                          previous_errors: Optional[List[Dict[str, Any]]] = None,
                          existing_files: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Generate code based on requirements using LLMs with improved prompts"""
        logger.info(f"Generating code for iteration {iteration} with provider {provider}")
        
        # Build the appropriate prompt based on iteration and context
        if iteration == 1:
            prompt = self._build_initial_prompt(requirements)
        else:
            prompt = self._build_iterative_prompt(requirements, previous_errors, existing_files, iteration)
        
        # Call LLM API to generate code
        response = await self.llm_service.generate_text(prompt, provider)
        
        # Process response to extract code files
        code_files = self._extract_files(response)
        
        logger.info(f"Generated {len(code_files)} files for iteration {iteration}")
        return code_files
    
    def _build_initial_prompt(self, requirements: Dict[str, Any]) -> str:
        """Build initial prompt for first iteration"""
        project_name = requirements.get("project", {}).get("name", "Application")
        focus = requirements.get("focus", "fullstack")
        
        prompt = f"""# Expert Code Generation Task: {project_name}

You are an expert software architect and full-stack developer. Create a complete, production-ready application based on the requirements below.

## Core Principles
- Write clean, maintainable, well-documented code
- Follow industry best practices and design patterns  
- Ensure type safety and proper error handling
- Create modular, reusable components
- Implement responsive designs by default

## Project Requirements
{json.dumps(requirements, indent=2)}

## Technology Stack & Guidelines
"""
        
        if focus == "frontend" or focus == "fullstack":
            prompt += """
### Frontend (Next.js + TypeScript + Material-UI)
- Use Next.js 14+ with App Router and TypeScript
- Implement Material-UI v5 for consistent UI components
- Create responsive layouts (mobile-first approach)
- Use proper state management (React Context/Zustand)
- Implement form validation with react-hook-form + zod
- Add loading states and error boundaries
- Include proper SEO metadata
- Structure: src/app/, src/components/, src/lib/, src/types/
"""
        
        if focus == "backend" or focus == "fullstack":
            prompt += """
### Backend (FastAPI + Python)
- Use FastAPI with async/await patterns
- Implement proper request/response models with Pydantic
- Add comprehensive input validation and error handling
- Use dependency injection for services
- Include proper CORS configuration
- Add health check endpoints
- Structure: app/api/, app/models/, app/services/, app/schemas/
- Implement proper logging throughout
"""
        
        prompt += """
## File Output Format
Provide ALL necessary files in this EXACT format:

FILE: path/to/file.ext
```language
[complete file content]
```

Example:
FILE: src/app/page.tsx
```typescript
import React from 'react';

export default function HomePage() {
  return <div>Hello World</div>;
}
```

## Critical Requirements
1. Provide COMPLETE files - no placeholders or comments like "// rest of implementation"
2. Ensure all imports have corresponding files
3. Include configuration files (package.json, tsconfig.json, etc.)
4. Add README.md with setup instructions
5. Include error handling and loading states
6. Make the application immediately runnable

## Quality Checklist
Before outputting, verify:
- [ ] All TypeScript types are properly defined
- [ ] All imports reference actual files you're creating
- [ ] Forms have proper validation
- [ ] Error boundaries are implemented
- [ ] Loading states are handled
- [ ] Code follows consistent naming conventions
- [ ] Components are properly separated and reusable

Begin implementation now. Create a beautiful, functional application that exceeds expectations.
"""
        
        return prompt
    
    def _build_iterative_prompt(self, 
                               requirements: Dict[str, Any],
                               previous_errors: List[Dict[str, Any]],
                               existing_files: Optional[Dict[str, str]],
                               iteration: int) -> str:
        """Build prompt for iterative improvements"""
        project_name = requirements.get("project", {}).get("name", "Application")
        
        prompt = f"""# Code Improvement Task - Iteration {iteration}: {project_name}

You are debugging and improving an existing codebase. Make MINIMAL changes to fix issues while preserving all working functionality.

## Error Analysis
The following errors occurred in the previous iteration:
"""
        
        # Group errors by type for better understanding
        error_groups = self._group_errors_by_type(previous_errors)
        for error_type, errors in error_groups.items():
            prompt += f"\n### {error_type} Errors:\n"
            for error in errors:
                file = error.get('file', 'Unknown')
                message = error.get('message', 'Unknown error')
                line = error.get('line', 'Unknown')
                prompt += f"- {file}:{line} - {message}\n"
        
        prompt += """
## Debugging Strategy
1. **Identify Root Causes**: Analyze each error and its underlying cause
2. **Minimal Changes**: Fix only what's broken, don't rewrite working code
3. **Preserve Functionality**: Maintain all existing features and behavior
4. **Verify Dependencies**: Ensure all imports and references are valid

## Current Codebase Structure
"""
        
        if existing_files:
            prompt += "Existing files in the project:\n"
            for file_path in sorted(existing_files.keys()):
                prompt += f"- {file_path}\n"
            
            prompt += "\n## Key Files to Consider\n"
            # Highlight potentially problematic files
            error_files = {error.get('file', '') for error in previous_errors}
            for file in error_files:
                if file and file in existing_files:
                    prompt += f"\n### {file}\n```\n{existing_files[file][:500]}...\n```\n"
        
        prompt += """
## Response Format
Only provide files that need to be CHANGED or ADDED. Use this format:

FILE: path/to/file.ext
```language
[complete corrected file content]
```

## Fixing Guidelines
- Import errors: Check file paths and ensure imported modules exist
- Type errors: Add proper TypeScript types and interfaces
- Syntax errors: Fix JavaScript/TypeScript syntax issues
- Missing dependencies: Add required package imports
- Configuration errors: Update config files as needed

## Quality Assurance
Before responding:
- [ ] Each error has been addressed
- [ ] All imports reference existing files
- [ ] TypeScript types are correct
- [ ] No new errors introduced
- [ ] Minimal changes made

Focus on surgical fixes - don't rebuild what's working correctly.
"""
        
        return prompt
    
    def _group_errors_by_type(self, errors: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group errors by their type for better prompt organization"""
        groups = {
            "Import/Module": [],
            "TypeScript": [],
            "Syntax": [],
            "Runtime": [],
            "Other": []
        }
        
        for error in errors:
            message = error.get('message', '').lower()
            if any(keyword in message for keyword in ['import', 'module', 'cannot find']):
                groups["Import/Module"].append(error)
            elif any(keyword in message for keyword in ['type', 'property', 'does not exist']):
                groups["TypeScript"].append(error)
            elif any(keyword in message for keyword in ['syntax', 'unexpected', 'expected']):
                groups["Syntax"].append(error)
            elif any(keyword in message for keyword in ['runtime', 'reference', 'undefined']):
                groups["Runtime"].append(error)
            else:
                groups["Other"].append(error)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _extract_files(self, response: str) -> Dict[str, str]:
        """Extract files from LLM response with improved parsing"""
        files = {}
        
        # Primary pattern: FILE: path followed by code block
        pattern = r'FILE:\s*([^\n]+)\s*\n```(?:\w+)?\s*\n(.*?)\n```'
        matches = re.finditer(pattern, response, re.DOTALL)
        
        for match in matches:
            file_path, content = match.groups()
            file_path = self._clean_file_path(file_path)
            if file_path:
                files[file_path] = content.strip()
        
        # Fallback pattern for simpler format
        if not files:
            alt_pattern = r'FILE:\s*([^\n]+)\s*\nCODE:\s*\n(.*?)\nEND'
            matches = re.finditer(alt_pattern, response, re.DOTALL)
            
            for match in matches:
                file_path, content = match.groups()
                file_path = self._clean_file_path(file_path)
                if file_path:
                    files[file_path] = content.strip()
        
        logger.info(f"Extracted {len(files)} files from LLM response")
        return files
    
    def _clean_file_path(self, file_path: str) -> Optional[str]:
        """Clean and validate file path"""
        file_path = file_path.strip()
        
        # Remove leading './'
        if file_path.startswith('./'):
            file_path = file_path[2:]
        
        # Validate path
        if not file_path or len(file_path) > 255 or '..' in file_path:
            return None
            
        # Ensure Unix-style paths
        file_path = file_path.replace('\\', '/')
        
        return file_path
    
    async def generate_react_app(self, requirements: Dict[str, Any], provider: str) -> Dict[str, str]:
        """Generate React application with improved prompts"""
        requirements_with_frontend = {**requirements, "focus": "frontend"}
        code_files = await self.generate_code(requirements_with_frontend, provider, 1)
        
        # Add essential frontend configuration if missing
        code_files = self._ensure_frontend_configs(code_files, requirements)
        
        return code_files
    
    async def generate_backend_api(self, requirements: Dict[str, Any], provider: str) -> Dict[str, str]:
        """Generate backend API with improved prompts"""
        requirements_with_backend = {**requirements, "focus": "backend"}
        code_files = await self.generate_code(requirements_with_backend, provider, 1)
        
        # Apply backend-specific fixes and additions
        fixed_files = self._fix_backend_imports(code_files)
        self._add_backend_support_files(fixed_files)
        
        return fixed_files
    
    def _ensure_frontend_configs(self, code_files: Dict[str, str], requirements: Dict[str, Any]) -> Dict[str, str]:
        """Ensure essential frontend configuration files are present"""
        project_name = requirements.get("project", {}).get("name", "app")
        
        # Add package.json if missing
        if "package.json" not in code_files:
            code_files["package.json"] = self._generate_package_json(project_name)
        
        # Add tsconfig.json if missing
        if "tsconfig.json" not in code_files:
            code_files["tsconfig.json"] = self._generate_tsconfig()
        
        # Add next.config.js if missing (for Next.js projects)
        if "next.config.js" not in code_files and any("next" in content.lower() for content in code_files.values()):
            code_files["next.config.js"] = self._generate_next_config()
        
        return code_files
    
    def _generate_package_json(self, project_name: str) -> str:
        """Generate basic package.json for frontend"""
        package_json = {
            "name": project_name.lower().replace(" ", "-"),
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint"
            },
            "dependencies": {
                "next": "^14.0.0",
                "react": "^18.0.0",
                "react-dom": "^18.0.0",
                "@mui/material": "^5.14.0",
                "@emotion/react": "^11.11.0",
                "@emotion/styled": "^11.11.0",
                "react-hook-form": "^7.45.0",
                "@hookform/resolvers": "^3.3.0",
                "zod": "^3.22.0"
            },
            "devDependencies": {
                "typescript": "^5.0.0",
                "@types/node": "^20.0.0",
                "@types/react": "^18.0.0",
                "@types/react-dom": "^18.0.0",
                "eslint": "^8.0.0",
                "eslint-config-next": "^14.0.0"
            }
        }
        return json.dumps(package_json, indent=2)
    
    def _generate_tsconfig(self) -> str:
        """Generate TypeScript configuration"""
        tsconfig = {
            "compilerOptions": {
                "lib": ["dom", "dom.iterable", "es6"],
                "allowJs": True,
                "skipLibCheck": True,
                "strict": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "plugins": [{"name": "next"}],
                "baseUrl": ".",
                "paths": {
                    "@/*": ["./src/*"]
                }
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
            "exclude": ["node_modules"]
        }
        return json.dumps(tsconfig, indent=2)
    
    def _generate_next_config(self) -> str:
        """Generate Next.js configuration"""
        return """/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
}

module.exports = nextConfig
"""
    
    def _fix_backend_imports(self, code_files: Dict[str, str]) -> Dict[str, str]:
        """Fix import statements in backend files"""
        fixed_files = dict(code_files)
        
        # Import fixes for common patterns
        import_fixes = {
            "from api.": "from app.api.",
            "from core.": "from app.core.",
            "from db.": "from app.db.",
            "from models.": "from app.models.",
            "from schemas.": "from app.schemas.",
            "from services.": "from app.services.",
            "from utils.": "from app.utils.",
        }
        
        for file_path, content in code_files.items():
            if file_path.endswith('.py'):
                for old_import, new_import in import_fixes.items():
                    content = content.replace(old_import, new_import)
                fixed_files[file_path] = content
        
        # Add __init__.py files for Python packages
        self._add_init_files(fixed_files)
        
        return fixed_files
    
    def _add_init_files(self, code_files: Dict[str, str]):
        """Add __init__.py files for Python packages"""
        directories = set()
        
        # Find all directories that contain Python files
        for file_path in code_files.keys():
            if file_path.endswith('.py') and '/' in file_path:
                parts = file_path.split('/')
                for i in range(1, len(parts)):
                    directory = '/'.join(parts[:i])
                    directories.add(directory)
        
        # Add __init__.py to each directory
        for directory in directories:
            init_file = f"{directory}/__init__.py"
            if init_file not in code_files:
                code_files[init_file] = '"""Package initialization file."""\n'
    
    def _add_backend_support_files(self, code_files: Dict[str, str]):
        """Add support files for the backend"""
        
        # Add startup script
        if "run_app.sh" not in code_files:
            code_files["run_app.sh"] = """#!/bin/bash
# Script to start the FastAPI application
export PYTHONPATH=$PYTHONPATH:$(pwd)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
"""
        
        # Add requirements.txt if missing
        if "requirements.txt" not in code_files:
            code_files["requirements.txt"] = """fastapi==0.104.0
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
alembic==1.12.1
pytest==7.4.3
pytest-asyncio==0.21.1
"""
        
        # Add .env example
        if ".env.example" not in code_files:
            code_files[".env.example"] = """# Database Configuration
DATABASE_URL=sqlite:///./app.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
DEBUG=True
"""
        
        # Add Dockerfile if missing
        if "Dockerfile" not in code_files:
            code_files["Dockerfile"] = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
"""

    async def generate_iterative_improvement(self,
                                           requirements: Dict[str, Any],
                                           provider: str,
                                           iteration: int,
                                           previous_errors: List[Dict[str, Any]],
                                           existing_files: Dict[str, str]) -> Tuple[Dict[str, str], List[str]]:
        """Generate iterative improvements with file change tracking"""
        
        # Determine which files need changes based on errors
        files_to_modify = self._identify_files_to_modify(previous_errors, existing_files)
        
        # Generate improvements for specific files
        improved_files = await self.generate_code(
            requirements, provider, iteration, previous_errors, existing_files
        )
        
        # Track what changed
        changes_made = []
        for file_path in improved_files:
            if file_path in existing_files:
                if improved_files[file_path] != existing_files[file_path]:
                    changes_made.append(f"Modified: {file_path}")
            else:
                changes_made.append(f"Created: {file_path}")
        
        logger.info(f"Iteration {iteration}: Made {len(changes_made)} changes")
        return improved_files, changes_made
    
    def _identify_files_to_modify(self, 
                                 errors: List[Dict[str, Any]], 
                                 existing_files: Dict[str, str]) -> List[str]:
        """Identify which files need modification based on errors"""
        files_to_modify = set()
        
        for error in errors:
            file_path = error.get('file', '')
            if file_path:
                files_to_modify.add(file_path)
                
                # Also consider related files
                if file_path.endswith('.tsx') or file_path.endswith('.ts'):
                    # Look for related component files
                    base_name = file_path.replace('.tsx', '').replace('.ts', '')
                    for existing_file in existing_files:
                        if base_name in existing_file:
                            files_to_modify.add(existing_file)
        
        return list(files_to_modify)