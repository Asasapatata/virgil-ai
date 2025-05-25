# backend/app/services/enhanced_code_generator.py
import json
import re
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class EnhancedCodeGenerator:
    """
    Enhanced code generator that implements sophisticated prompting and
    specialized roles for different aspects of code generation.
    
    🔥 AGGIORNATO: Aggiunge metodi specifici per integrazione con sistema enhanced_v2
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        logger.info("EnhancedCodeGenerator initialized")
    
    # 🔥 NUOVO: Metodo principale per integrazione con enhanced_v2 system
    async def generate_complete_project_enhanced(self,
                                               requirements: Dict[str, Any],
                                               provider: str,
                                               max_iterations: int = 5) -> Dict[str, Any]:
        """
        Genera un progetto completo usando il flusso enhanced con validazione e compilazione.
        Questo è il metodo entry point per l'integrazione con il sistema enhanced_v2.
        """
        logger.info("Starting complete enhanced project generation")
        
        try:
            # Analizza l'architettura del progetto
            architecture_plan = await self._create_architecture_plan(requirements, provider)
            
            # Genera il codice base con piano architetturale
            base_code = await self.generate_with_architecture(requirements, architecture_plan, provider)
            
            # Applica miglioramenti iterativi
            enhanced_code = await self._apply_iterative_enhancements(
                base_code, requirements, provider, max_iterations
            )
            
            return {
                "success": True,
                "code_files": enhanced_code,
                "architecture_plan": architecture_plan,
                "iterations_applied": min(max_iterations, 3),  # Limit per enhanced generator
                "generation_strategy": "enhanced_single_agent",
                "file_count": len(enhanced_code)
            }
        
        except Exception as e:
            logger.error(f"Error in enhanced project generation: {e}")
            return {
                "success": False,
                "error": str(e),
                "code_files": {},
                "generation_strategy": "enhanced_single_agent"
            }
    
    async def _create_architecture_plan(self, requirements: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """
        Crea un piano architetturale dettagliato per il progetto
        """
        logger.info("Creating architecture plan")
        
        system_prompt = """
        You are an expert software architect. Create a comprehensive architecture plan 
        that will guide the code generation process. Focus on:
        1. System architecture patterns
        2. Component organization
        3. Data flow design
        4. Technology integration
        5. Scalability considerations
        """
        
        prompt = f"""
        Create a detailed architecture plan for this project:
        
        {json.dumps(requirements, indent=2)}
        
        The plan should include:
        1. Overall architecture pattern (MVC, Component-based, etc.)
        2. Directory structure and file organization
        3. Component breakdown and responsibilities
        4. Data flow and API design
        5. Integration points and dependencies
        6. Technology-specific recommendations
        
        Provide the plan in JSON format with clear sections.
        """
        
        try:
            response = await self.llm_service.generate(provider, prompt, system_prompt)
            
            # Try to extract JSON
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            else:
                # Create basic plan from requirements
                return self._create_basic_plan(requirements)
        
        except Exception as e:
            logger.warning(f"Failed to create detailed architecture plan: {e}")
            return self._create_basic_plan(requirements)
    
    def _create_basic_plan(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un piano architetturale di base
        """
        tech_stack = requirements.get("tech_stack", {})
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        return {
            "architecture_pattern": "Component-based MVC",
            "project_type": project_type,
            "tech_stack": tech_stack,
            "components": {
                "frontend": {
                    "framework": tech_stack.get("frontend", "React"),
                    "structure": ["components", "pages", "hooks", "utils", "services"]
                },
                "backend": {
                    "framework": tech_stack.get("backend", "Node.js"),
                    "structure": ["routes", "controllers", "models", "middleware", "config"]
                },
                "database": {
                    "type": tech_stack.get("database", "PostgreSQL"),
                    "structure": ["models", "migrations", "seeds"]
                }
            },
            "file_organization": {
                "frontend_root": "frontend/src",
                "backend_root": "backend/src",
                "shared": "shared",
                "config": "config"
            },
            "integration_points": ["API routes", "Database connections", "Authentication"]
        }
    
    async def _apply_iterative_enhancements(self,
                                          base_code: Dict[str, str],
                                          requirements: Dict[str, Any],
                                          provider: str,
                                          max_iterations: int) -> Dict[str, str]:
        """
        Applica miglioramenti iterativi al codice base
        """
        logger.info(f"Applying iterative enhancements (max {max_iterations} iterations)")
        
        current_code = dict(base_code)
        
        # Limita le iterazioni per Enhanced Generator (è un singolo agente)
        actual_iterations = min(max_iterations, 3)
        
        for iteration in range(1, actual_iterations + 1):
            logger.info(f"Enhancement iteration {iteration}")
            
            # Determina focus per questa iterazione
            focus_areas = self._get_enhancement_focus(iteration, requirements)
            
            try:
                # Applica miglioramenti
                enhanced_code = await self.enhance_code_quality(
                    current_code, focus_areas, provider
                )
                
                # Aggiorna il codice corrente
                current_code = enhanced_code
                
                logger.info(f"Applied enhancements with focus: {', '.join(focus_areas)}")
            
            except Exception as e:
                logger.warning(f"Enhancement iteration {iteration} failed: {e}")
                break
        
        return current_code
    
    def _get_enhancement_focus(self, iteration: int, requirements: Dict[str, Any]) -> List[str]:
        """
        Determina il focus per ogni iterazione di miglioramento
        """
        # Focus diversi per ogni iterazione
        iteration_focus = {
            1: ["security", "error_handling"],
            2: ["performance", "optimization"],
            3: ["documentation", "code_quality"]
        }
        
        base_focus = iteration_focus.get(iteration, ["code_quality"])
        
        # Aggiungi focus specifici basati sui requisiti
        if "authentication" in str(requirements).lower():
            base_focus.append("security")
        if "database" in str(requirements).lower():
            base_focus.append("performance")
        if "api" in str(requirements).lower():
            base_focus.append("api_design")
        
        return list(set(base_focus))  # Rimuovi duplicati
    
    # 🔥 NUOVO: Metodo per generazione rapida senza architettura complessa
    async def generate_streamlined_code(self,
                                      requirements: Dict[str, Any],
                                      provider: str) -> Dict[str, str]:
        """
        Genera codice in modo streamlined per progetti semplici/moderati.
        Usato quando non serve l'overhead completo dell'analisi architetturale.
        """
        logger.info("Generating streamlined code for moderate complexity project")
        
        project_type = requirements.get("project", {}).get("type", "fullstack")
        tech_stack = requirements.get("tech_stack", {})
        
        # Crea prompt ottimizzato per generazione rapida ma di qualità
        system_prompt = """
        You are an expert full-stack developer. Generate clean, production-ready code 
        following best practices for the specified technology stack. Focus on:
        1. Clean, maintainable code structure
        2. Proper error handling and validation
        3. Security best practices
        4. Performance optimization
        5. Comprehensive documentation
        """
        
        prompt = self._create_streamlined_prompt(requirements, project_type, tech_stack)
        
        try:
            response = await self.llm_service.generate(provider, prompt, system_prompt)
            files = self._extract_files(response)
            
            logger.info(f"Generated {len(files)} files in streamlined mode")
            return files
        
        except Exception as e:
            logger.error(f"Error in streamlined generation: {e}")
            # Fallback to basic generation
            return await self._generate_basic_fallback(requirements, provider)
    
    def _create_streamlined_prompt(self, 
                                 requirements: Dict[str, Any],
                                 project_type: str,
                                 tech_stack: Dict[str, Any]) -> str:
        """
        Crea un prompt ottimizzato per generazione streamlined
        """
        # Extract key information
        features = requirements.get("features", [])
        security = requirements.get("security", [])
        database_schema = requirements.get("database_schema", {})
        
        prompt = f"""
        # Streamlined Code Generation
        
        Generate a complete {project_type} application with these specifications:
        
        ## Technology Stack
        - Frontend: {tech_stack.get('frontend', 'React')}
        - Backend: {tech_stack.get('backend', 'Node.js')}
        - Database: {tech_stack.get('database', 'PostgreSQL')}
        - API: {tech_stack.get('api', 'RESTful')}
        - Auth: {tech_stack.get('auth', 'JWT')}
        
        ## Features to Implement
        {self._format_features(features)}
        
        ## Security Requirements
        {self._format_security(security)}
        
        ## Database Schema
        {json.dumps(database_schema, indent=2) if database_schema else 'Design appropriate schema'}
        
        ## Complete Project Requirements
        {json.dumps(requirements, indent=2)}
        
        ## Instructions
        
        Generate a complete, production-ready codebase with:
        
        1. **Frontend** ({tech_stack.get('frontend', 'React')}):
           - Component-based architecture
           - Routing and navigation
           - State management
           - API integration
           - Authentication handling
           - Responsive design
        
        2. **Backend** ({tech_stack.get('backend', 'Node.js')}):
           - RESTful API endpoints
           - Database integration
           - Authentication middleware
           - Input validation
           - Error handling
           - Security measures
        
        3. **Configuration**:
           - Package management files
           - Environment configuration
           - Docker setup
           - Development scripts
        
        ## Response Format
        
        For each file, use this exact format:
        
        FILE: path/to/file.ext
        ```language
        [complete file content]
        ```
        
        Generate ALL necessary files for a working application.
        Include proper error handling, validation, and security measures.
        Follow best practices for the chosen technology stack.
        """
        
        return prompt
    
    def _format_features(self, features: List[Any]) -> str:
        """
        Formatta le features per il prompt
        """
        if not features:
            return "- Basic CRUD operations\n- User authentication\n- Data management"
        
        formatted = []
        for feature in features:
            if isinstance(feature, dict):
                for name, details in feature.items():
                    formatted.append(f"- {name}: {self._extract_feature_description(details)}")
            elif isinstance(feature, str):
                formatted.append(f"- {feature}")
            else:
                formatted.append(f"- {str(feature)}")
        
        return "\n".join(formatted)
    
    def _format_security(self, security: List[Any]) -> str:
        """
        Formatta i requisiti di sicurezza per il prompt
        """
        if not security:
            return "- JWT authentication\n- Password hashing\n- Input validation\n- CORS protection"
        
        formatted = []
        for item in security:
            if isinstance(item, str):
                formatted.append(f"- {item}")
            else:
                formatted.append(f"- {str(item)}")
        
        return "\n".join(formatted)
    
    def _extract_feature_description(self, details: Any) -> str:
        """
        Estrae una descrizione della feature
        """
        if isinstance(details, dict):
            desc = details.get("description", "")
            if desc:
                return desc
            # Try to create description from components or other fields
            components = details.get("components", [])
            if components:
                return f"Includes {', '.join(components[:3])}"
        
        return str(details)[:100]  # Truncate long descriptions
    
    async def _generate_basic_fallback(self, requirements: Dict[str, Any], provider: str) -> Dict[str, str]:
        """
        Fallback di base se tutto il resto fallisce
        """
        logger.warning("Using basic fallback generation")
        
        # Import basic generator for fallback
        try:
            from app.services.code_generator import CodeGenerator
            basic_gen = CodeGenerator(self.llm_service)
            
            project_type = requirements.get("project", {}).get("type", "fullstack")
            
            if project_type == "frontend":
                return await basic_gen.generate_react_app(requirements, provider)
            elif project_type == "backend":
                return await basic_gen.generate_backend_api(requirements, provider)
            else:
                return await basic_gen.generate_code(requirements, provider, 1)
        
        except Exception as e:
            logger.error(f"Even basic fallback failed: {e}")
            return {}
    
    # 🔥 MIGLIORATO: Metodo fix_issues con better error handling
    async def fix_issues_enhanced(self,
                                code_files: Dict[str, str],
                                issues: List[Dict[str, Any]],
                                provider: str,
                                context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Versione migliorata di fix_issues con context aggiuntivo
        """
        logger.info(f"Fixing {len(issues)} issues with enhanced context")
        
        if not issues:
            logger.info("No issues to fix, returning original files")
            return code_files
        
        # Group issues by priority and type
        prioritized_issues = self._prioritize_issues(issues)
        
        # Fix issues in order of priority
        fixed_files = dict(code_files)
        
        for priority_group in prioritized_issues:
            try:
                batch_fixes = await self._fix_issue_batch(
                    fixed_files, priority_group, provider, context
                )
                fixed_files.update(batch_fixes)
                
                logger.info(f"Fixed {len(priority_group)} {priority_group[0].get('priority', 'medium')} priority issues")
            
            except Exception as e:
                logger.warning(f"Failed to fix priority group: {e}")
                continue
        
        return fixed_files
    
    def _prioritize_issues(self, issues: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Raggruppa e prioritizza gli issues
        """
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for issue in issues:
            priority = issue.get("priority", "medium")
            issue_type = issue.get("type", "unknown")
            
            # Critical issues: compilation, syntax errors
            if priority == "high" or issue_type in ["compilation", "syntax", "import"]:
                high_priority.append(issue)
            elif priority == "low" or issue_type in ["style", "warning"]:
                low_priority.append(issue)
            else:
                medium_priority.append(issue)
        
        return [group for group in [high_priority, medium_priority, low_priority] if group]
    
    async def _fix_issue_batch(self,
                             code_files: Dict[str, str],
                             issues: List[Dict[str, Any]],
                             provider: str,
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Fixa un batch di issues correlati
        """
        if not issues:
            return {}
        
        # Group issues by file
        issues_by_file = {}
        for issue in issues:
            file_path = issue.get('file', 'unknown')
            if file_path not in issues_by_file:
                issues_by_file[file_path] = []
            issues_by_file[file_path].append(issue)
        
        fixed_files = {}
        
        for file_path, file_issues in issues_by_file.items():
            if file_path == 'unknown' or file_path not in code_files:
                continue
            
            try:
                fixed_content = await self._fix_single_file_enhanced(
                    file_path, code_files[file_path], file_issues, provider, context
                )
                
                if fixed_content:
                    fixed_files[file_path] = fixed_content
            
            except Exception as e:
                logger.warning(f"Failed to fix file {file_path}: {e}")
                continue
        
        return fixed_files
    
    async def _fix_single_file_enhanced(self,
                                      file_path: str,
                                      content: str,
                                      issues: List[Dict[str, Any]],
                                      provider: str,
                                      context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Fixa un singolo file con context enhancement
        """
        # Create enhanced prompt with context
        prompt = self._create_enhanced_fixing_prompt(file_path, content, issues, context)
        
        system_prompt = """
        You are an expert software engineer specializing in debugging and code fixing.
        Your task is to fix specific issues while maintaining code functionality and quality.
        
        Key principles:
        1. Fix only the reported issues
        2. Maintain existing functionality
        3. Improve code quality where possible
        4. Add helpful comments for complex fixes
        5. Ensure fixes don't introduce new problems
        """
        
        try:
            response = await self.llm_service.generate(provider, prompt, system_prompt)
            
            # Extract fixed file content
            files = self._extract_files(response)
            
            if file_path in files:
                return files[file_path]
            elif len(files) == 1:
                return list(files.values())[0]
            else:
                # Try to extract content directly
                return self._extract_direct_content(response)
        
        except Exception as e:
            logger.error(f"Error fixing file {file_path}: {e}")
            return None
    
    def _create_enhanced_fixing_prompt(self,
                                     file_path: str,
                                     content: str,
                                     issues: List[Dict[str, Any]],
                                     context: Optional[Dict[str, Any]] = None) -> str:
        """
        Crea un prompt enhanced per il fixing con context
        """
        # Format issues with priorities
        issues_text = ""
        for i, issue in enumerate(issues, 1):
            priority = issue.get('priority', 'medium')
            issue_type = issue.get('type', 'unknown')
            message = issue.get('message', 'No description')
            line = issue.get('line', 'unknown')
            suggestion = issue.get('suggestion', '')
            
            issues_text += f"{i}. [{priority.upper()}] {issue_type} at line {line}\n"
            issues_text += f"   Error: {message}\n"
            if suggestion:
                issues_text += f"   Suggestion: {suggestion}\n"
            issues_text += "\n"
        
        # Add context information if available
        context_text = ""
        if context:
            if "related_files" in context:
                context_text += f"Related files: {', '.join(context['related_files'])}\n"
            if "project_type" in context:
                context_text += f"Project type: {context['project_type']}\n"
            if "tech_stack" in context:
                context_text += f"Tech stack: {context['tech_stack']}\n"
        
        return f"""
        # Enhanced Code Fixing Task
        
        Fix the following issues in this file while maintaining functionality and improving code quality.
        
        ## File Information
        Path: {file_path}
        {context_text}
        
        ## Issues to Fix (in priority order)
        {issues_text}
        
        ## Current File Content
        ```
        {content}
        ```
        
        ## Instructions
        
        1. Fix each issue in priority order (HIGH → MEDIUM → LOW)
        2. For each fix, ensure it doesn't break existing functionality
        3. Add brief comments explaining complex fixes
        4. Improve code quality where appropriate
        5. Maintain consistent code style
        
        ## Response Format
        
        Provide the complete fixed file content:
        
        FILE: {file_path}
        ```
        [complete fixed file content]
        ```
        
        Focus on fixing critical issues first, then improve overall code quality.
        """
    
    def _extract_direct_content(self, response: str) -> Optional[str]:
        """
        Estrae il contenuto direttamente dalla risposta se non ci sono tag FILE
        """
        # Try to find code blocks
        code_blocks = re.findall(r'```(?:\w+)?\s*\n(.*?)\n```', response, re.DOTALL)
        
        if code_blocks:
            # Return the largest code block (likely the main content)
            return max(code_blocks, key=len).strip()
        
        # If no code blocks, try to extract meaningful content
        lines = response.split('\n')
        content_lines = []
        
        for line in lines:
            # Skip obvious metadata lines
            if not any(skip in line.lower() for skip in ['file:', 'fixed', 'here is', 'the following']):
                content_lines.append(line)
        
        if content_lines:
            return '\n'.join(content_lines).strip()
        
        return None
    
    # Mantieni tutti i metodi esistenti del file originale
    async def generate_with_architecture(self, 
                                       requirements: Dict[str, Any],
                                       architecture_plan: Dict[str, Any],
                                       provider: str) -> Dict[str, str]:
        """
        Generate code based on requirements and an architecture plan
        """
        logger.info("Generating code with architecture plan")
        
        # Create prompt for code generation with architecture context
        prompt = self._create_architecture_based_prompt(requirements, architecture_plan)
        
        # Generate code
        system_prompt = """
        You are an expert software engineer tasked with implementing code according to requirements
        and a specific architecture plan. Your code should be clean, well-documented, maintainable,
        and follow best practices for the selected tech stack.
        """
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Extract files from response
        files = self._extract_files(response)
        logger.info(f"Generated {len(files)} files based on architecture plan")
        
        return files
    
    async def generate_specific_component(self,
                                        requirements: Dict[str, Any],
                                        component_spec: Dict[str, Any],
                                        existing_files: Dict[str, str],
                                        provider: str) -> Dict[str, str]:
        """
        Generate code for a specific component, considering the existing codebase
        """
        logger.info(f"Generating component: {component_spec.get('name', 'Unnamed')}")
        
        # Create prompt for component generation
        prompt = self._create_component_prompt(requirements, component_spec, existing_files)
        
        # Generate component code
        system_prompt = """
        You are an expert software component developer. Your task is to implement a specific
        component that integrates with an existing codebase. Your component should be:
        1. Focused on the specific functionality required
        2. Well-integrated with the existing code
        3. Following the established patterns and conventions
        4. Well-documented and maintainable
        """
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Extract files from response
        files = self._extract_files(response)
        logger.info(f"Generated {len(files)} files for component")
        
        return files
    
    async def enhance_code_quality(self,
                                 code_files: Dict[str, str],
                                 quality_focus: List[str],
                                 provider: str) -> Dict[str, str]:
        """
        Enhance the quality of existing code focusing on specific aspects like
        performance, security, documentation, etc.
        """
        logger.info(f"Enhancing code quality with focus on: {', '.join(quality_focus)}")
        
        # Prepare files for analysis (select a subset to avoid token limits)
        important_files = self._select_files_for_quality_enhancement(code_files, quality_focus)
        
        # Create prompt for code quality enhancement
        prompt = self._create_quality_enhancement_prompt(important_files, quality_focus)
        
        # Generate enhanced code
        system_prompt = """
        You are an expert code reviewer and quality engineer. Your task is to improve
        the quality of the provided code focusing on specific aspects like security,
        performance, documentation, or testing.
        
        For each file, you should:
        1. Identify issues and areas for improvement
        2. Make specific enhancements to address these issues
        3. Maintain the functional behavior of the code
        4. Add appropriate comments explaining significant changes
        """
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Extract enhanced files
        enhanced_files = self._extract_files(response)
        logger.info(f"Enhanced {len(enhanced_files)} files")
        
        # Merge with original files, only updating the ones that were enhanced
        merged_files = dict(code_files)
        merged_files.update(enhanced_files)
        
        return merged_files
    
    async def fix_issues(self,
                      code_files: Dict[str, str],
                      issues: List[Dict[str, Any]],
                      provider: str) -> Dict[str, str]:
        """
        Fix specific issues in the code based on testing results or review comments
        """
        logger.info(f"Fixing {len(issues)} issues in codebase")
        
        # Group issues by file
        issues_by_file = {}
        for issue in issues:
            file_path = issue.get('file', 'unknown')
            if file_path not in issues_by_file:
                issues_by_file[file_path] = []
            issues_by_file[file_path].append(issue)
        
        # For each file with issues, create a targeted prompt
        fixed_files = {}
        
        for file_path, file_issues in issues_by_file.items():
            # Skip files that don't exist in the codebase
            if file_path not in code_files and file_path != 'unknown':
                logger.warning(f"Issues reported for non-existent file: {file_path}")
                continue
            
            # Create prompt for fixing this file
            content = code_files.get(file_path, "")
            prompt = self._create_issue_fixing_prompt(file_path, content, file_issues)
            
            # Generate fixed code
            system_prompt = """
            You are an expert software developer tasked with fixing specific issues in code.
            For each issue:
            1. Understand the root cause
            2. Implement a proper fix
            3. Ensure the fix doesn't introduce new problems
            4. Add comments explaining the fix if appropriate
            
            Return the complete fixed file, not just the changes.
            """
            
            response = await self.llm_service.generate(
                provider=provider,
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            # Extract the fixed file
            fixed_file = self._extract_files(response)
            
            # Check if we got a valid response
            if file_path in fixed_file:
                fixed_files[file_path] = fixed_file[file_path]
            elif len(fixed_file) == 1:
                # If there's only one file returned, assume it's the one we wanted
                fixed_files[file_path] = list(fixed_file.values())[0]
            else:
                logger.warning(f"Failed to get fixed version of {file_path}")
        
        # Merge with original files
        merged_files = dict(code_files)
        merged_files.update(fixed_files)
        
        return merged_files
    
    async def analyze_code(self,
                       code_files: Dict[str, str],
                       analysis_type: str,
                       provider: str) -> Dict[str, Any]:
        """
        Analyze code for various purposes: architecture understanding,
        quality assessment, security audit, etc.
        """
        logger.info(f"Analyzing code for: {analysis_type}")
        
        # Select appropriate files for analysis
        important_files = self._select_files_for_analysis(code_files, analysis_type)
        
        # Create prompt for code analysis
        prompt = self._create_code_analysis_prompt(important_files, analysis_type)
        
        # Generate analysis
        system_prompt = """
        You are an expert code analyst with deep understanding of software architecture,
        design patterns, security best practices, and performance optimization.
        
        Analyze the provided code according to the requested analysis type and provide:
        1. A structured overview of the findings
        2. Detailed observations for each important aspect
        3. Recommendations for improvement where applicable
        4. A summary of strengths and weaknesses
        
        Your analysis should be thorough, precise, and actionable.
        """
        
        response = await self.llm_service.generate(
            provider=provider,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Parse the analysis from the response
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                analysis_result = json.loads(json_match.group(1))
            else:
                # If no JSON found, create a structured result from the text
                analysis_result = {
                    "analysis_type": analysis_type,
                    "content": response,
                    "summary": self._extract_summary(response)
                }
        except json.JSONDecodeError:
            logger.warning("Failed to parse analysis as JSON, using text response")
            analysis_result = {
                "analysis_type": analysis_type,
                "content": response,
                "summary": self._extract_summary(response)
            }
        
        return analysis_result
    
    def _create_architecture_based_prompt(self, 
                                       requirements: Dict[str, Any],
                                       architecture_plan: Dict[str, Any]) -> str:
        """
        Create a prompt for generating code based on requirements and architecture plan
        """
        # Convert dictionaries to formatted strings
        req_str = json.dumps(requirements, indent=2)
        arch_str = json.dumps(architecture_plan, indent=2)
        
        return f"""
        # Architecture-Driven Code Generation
        
        I need you to generate code based on detailed requirements and an architecture plan.
        
        ## Project Requirements
        ```json
        {req_str}
        ```
        
        ## Architecture Plan
        ```json
        {arch_str}
        ```
        
        ## Instructions
        
        1. Generate all necessary code files according to the architecture plan.
        2. Include proper documentation, comments, and type hints.
        3. Implement functionality as specified in the requirements.
        4. Ensure all components are properly integrated.
        5. Include appropriate configuration files, package managers, etc.
        
        ## Response Format
        
        For each file, use the following format:
        
        FILE: path/to/file
        ```language
        [complete file content]
        ```
        
        Be thorough and follow best practices for the specific tech stack.
        """
    
    def _create_component_prompt(self,
                              requirements: Dict[str, Any],
                              component_spec: Dict[str, Any],
                              existing_files: Dict[str, str]) -> str:
        """
        Create a prompt for generating a specific component within an existing codebase
        """
        # Convert dictionaries to formatted strings
        req_str = json.dumps(requirements, indent=2)
        comp_str = json.dumps(component_spec, indent=2)
        
        # Select relevant existing files to provide as context
        context_files = self._select_context_files(existing_files, component_spec)
        
        # Create file context section
        context_section = ""
        for file_path, content in context_files.items():
            # Truncate very large files
            if len(content) > 3000:
                truncated = content[:1500] + "\n...[content truncated]...\n" + content[-1500:]
                context_section += f"\nFILE: {file_path}\n```\n{truncated}\n```\n"
            else:
                context_section += f"\nFILE: {file_path}\n```\n{content}\n```\n"
        
        return f"""
        # Component-Specific Code Generation
        
        I need you to implement a specific component that integrates with an existing codebase.
        
        ## Project Requirements
        ```json
        {req_str}
        ```
        
        ## Component Specification
        ```json
        {comp_str}
        ```
        
        ## Existing Codebase Context
        {context_section}
        
        ## Instructions
        
        1. Generate the necessary files for this component.
        2. Ensure the component integrates properly with the existing code.
        3. Follow the established patterns and conventions.
        4. Include proper documentation and type information.
        5. Implement the functionality as specified.
        
        ## Response Format
        
        For each file you create or modify, use the following format:
        
        FILE: path/to/file
        ```language
        [complete file content]
        ```
        
        Be thorough and follow best practices for the specific tech stack.
        """
    
    def _create_quality_enhancement_prompt(self, 
                                        files: Dict[str, str],
                                        quality_focus: List[str]) -> str:
        """
        Create a prompt for enhancing code quality focusing on specific aspects
        """
        # Create file section
        files_section = ""
        for file_path, content in files.items():
            files_section += f"\nFILE: {file_path}\n```\n{content}\n```\n"
        
        # Create focus areas section
        focus_areas = "\n".join([f"- {focus}" for focus in quality_focus])
        
        return f"""
        # Code Quality Enhancement
        
        I need you to enhance the quality of the following code, focusing specifically on:
        
        {focus_areas}
        
        ## Code to Enhance
        {files_section}
        
        ## Instructions
        
        1. Analyze each file for issues related to the focus areas.
        2. Make specific improvements to address these issues.
        3. Maintain the functional behavior of the code.
        4. Add comments explaining significant changes.
        
        ## Response Format
        
        For each file you enhance, use the following format:
        
        FILE: path/to/file
        ```language
        [complete enhanced file content]
        ```
        
        Only include files that you have enhanced. For each file, provide the complete
        content, not just the changes.
        """
    
    def _create_issue_fixing_prompt(self,
                                 file_path: str,
                                 content: str,
                                 issues: List[Dict[str, Any]]) -> str:
        """
        Create a prompt for fixing specific issues in a file
        """
        # Format issues into a structured list
        issues_list = ""
        for i, issue in enumerate(issues, 1):
            issue_type = issue.get('type', 'Unknown')
            message = issue.get('message', 'No description')
            line = issue.get('line', 'Unknown')
            issues_list += f"{i}. {issue_type} at line {line}: {message}\n"
        
        return f"""
        # Code Issue Fixing
        
        I need you to fix the following issues in this file:
        
        ## File to Fix
        {file_path}
        
        ## Issues to Fix
        {issues_list}
        
        ## Current Code
        ```
        {content}
        ```
        
        ## Instructions
        
        1. Fix each issue one by one.
        2. Ensure your fixes don't introduce new problems.
        3. Add comments explaining your fixes if appropriate.
        
        ## Response Format
        
        Provide the complete fixed file content:
        
        FILE: {file_path}
        ```
        [complete fixed file content]
        ```
        """
    
    def _create_code_analysis_prompt(self,
                                  files: Dict[str, str],
                                  analysis_type: str) -> str:
        """
        Create a prompt for analyzing code
        """
        # Create file section
        files_section = ""
        for file_path, content in files.items():
            # Truncate large files
            if len(content) > 5000:
                truncated = content[:2000] + "\n...[content truncated]...\n" + content[-2000:]
                files_section += f"\nFILE: {file_path}\n```\n{truncated}\n```\n"
            else:
                files_section += f"\nFILE: {file_path}\n```\n{content}\n```\n"
        
        analysis_instructions = ""
        if analysis_type == "architecture":
            analysis_instructions = """
            1. Identify the overall architecture pattern being used
            2. Map out the component structure and interactions
            3. Evaluate the separation of concerns
            4. Assess the modularity and extensibility
            5. Identify potential architecture issues or anti-patterns
            """
        elif analysis_type == "security":
            analysis_instructions = """
            1. Identify potential security vulnerabilities
            2. Check for proper input validation and sanitization
            3. Assess authentication and authorization mechanisms
            4. Look for sensitive data handling issues
            5. Evaluate security best practices compliance
            """
        elif analysis_type == "performance":
            analysis_instructions = """
            1. Identify potential performance bottlenecks
            2. Assess algorithm efficiency and complexity
            3. Check for resource-intensive operations
            4. Evaluate caching strategies
            5. Look for areas to optimize
            """
        else:
            analysis_instructions = """
            1. Provide a general analysis of the code quality
            2. Assess adherence to best practices
            3. Evaluate documentation and readability
            4. Identify strengths and areas for improvement
            5. Suggest specific enhancements
            """
        
        return f"""
        # Code Analysis: {analysis_type.title()}
        
        I need you to perform a detailed {analysis_type} analysis of the following code.
        
        ## Code to Analyze
        {files_section}
        
        ## Analysis Instructions
        {analysis_instructions}
        
        ## Response Format
        
        Provide your analysis in a structured format:
        
        ```json
        {{
          "analysis_type": "{analysis_type}",
          "overview": "Overall assessment of the codebase",
          "findings": [
            {{
              "category": "Category name",
              "observations": ["Observation 1", "Observation 2", ...],
              "recommendations": ["Recommendation 1", "Recommendation 2", ...]
            }},
            ...
          ],
          "summary": {{
            "strengths": ["Strength 1", "Strength 2", ...],
            "weaknesses": ["Weakness 1", "Weakness 2", ...],
            "overall_rating": "Rating on a scale of 1-10"
          }}
        }}
        ```
        
        Be thorough, specific, and provide actionable insights.
        """
    
    def _select_files_for_quality_enhancement(self, 
                                           files: Dict[str, str],
                                           quality_focus: List[str]) -> Dict[str, str]:
        """
        Select the most relevant files for quality enhancement based on focus areas
        """
        # If there are very few files, include all of them
        if len(files) <= 5:
            return files
        
        selected_files = {}
        
        # Based on quality focus, select relevant file types
        focus_to_patterns = {
            "security": [r'auth', r'login', r'password', r'user', r'permission'],
            "performance": [r'database', r'api', r'query', r'service', r'process'],
            "documentation": [r'\.md', r'README', r'docs'],
            "testing": [r'test', r'spec'],
            "maintainability": [r'utils', r'helpers', r'common', r'shared'],
            "accessibility": [r'component', r'ui', r'view', r'page'],
            "error_handling": [r'error', r'exception', r'handler'],
            "api_design": [r'api', r'route', r'endpoint', r'controller'],
            "optimization": [r'service', r'util', r'helper', r'performance']
        }
        
        # Get patterns for our focus areas
        relevant_patterns = []
        for focus in quality_focus:
            if focus in focus_to_patterns:
                relevant_patterns.extend(focus_to_patterns[focus])
        
        # Add files matching the patterns
        for file_path, content in files.items():
            if any(re.search(pattern, file_path, re.IGNORECASE) for pattern in relevant_patterns):
                selected_files[file_path] = content
        
        # If we selected too few files, add some important ones
        if len(selected_files) < 3 and len(files) > 3:
            # Add core files
            for file_path in self._identify_core_files(files):
                if file_path not in selected_files:
                    selected_files[file_path] = files[file_path]
                    if len(selected_files) >= 5:
                        break
        
        # If still too few, add more randomly until we have enough (up to 10)
        if len(selected_files) < min(5, len(files)):
            remaining = set(files.keys()) - set(selected_files.keys())
            for file_path in list(remaining)[:10 - len(selected_files)]:
                selected_files[file_path] = files[file_path]
        
        return selected_files
    
    def _select_context_files(self, 
                           files: Dict[str, str], 
                           component_spec: Dict[str, Any]) -> Dict[str, str]:
        """
        Select the most relevant files to provide context for component generation
        """
        # If there are very few files, include all of them
        if len(files) <= 5:
            return files
        
        selected_files = {}
        
        # Extract any file paths or patterns mentioned in the component spec
        spec_str = json.dumps(component_spec)
        file_mentions = re.findall(r'[\w\-./]+\.[a-zA-Z]+', spec_str)
        
        # Add files that match the mentions
        for file_path in files:
            for mention in file_mentions:
                if mention in file_path:
                    selected_files[file_path] = files[file_path]
                    break
        
        # For components, it's important to include examples of similar components
        component_name = component_spec.get('name', '').lower()
        component_type = component_spec.get('type', '').lower()
        
        # Add files that might be similar components
        if component_type or component_name:
            for file_path, content in files.items():
                name_match = component_name and component_name in file_path.lower()
                type_match = component_type and component_type in file_path.lower()
                
                if name_match or type_match:
                    selected_files[file_path] = content
        
        # Add core files that would be useful for context
        core_files = self._identify_core_files(files)
        for file_path in core_files:
            if file_path not in selected_files:
                selected_files[file_path] = files[file_path]
                if len(selected_files) >= 10:  # Limit to 10 files
                    break
        
        # Ensure we don't have too many files
        if len(selected_files) > 10:
            # Keep the 10 smallest files to avoid token limits
            file_sizes = [(path, len(content)) for path, content in selected_files.items()]
            sorted_files = sorted(file_sizes, key=lambda x: x[1])
            selected_paths = [path for path, _ in sorted_files[:10]]
            
            selected_files = {path: files[path] for path in selected_paths}
        
        return selected_files
    
    def _select_files_for_analysis(self,
                               files: Dict[str, str],
                               analysis_type: str) -> Dict[str, str]:
        """
        Select the most relevant files for the requested analysis type
        """
        # If there are very few files, include all of them
        if len(files) <= 5:
            return files
        
        selected_files = {}
        
        # Different file patterns for different analysis types
        analysis_patterns = {
            "architecture": [r'setup', r'config', r'main', r'index', r'app', r'\.md'],
            "security": [r'auth', r'login', r'user', r'api', r'route', r'controller'],
            "performance": [r'database', r'service', r'util', r'helper', r'process'],
            "quality": [r'component', r'service', r'model', r'controller'],
        }
        
        # Get patterns for our analysis type (default to quality)
        patterns = analysis_patterns.get(analysis_type, analysis_patterns["quality"])
        
        # Add files matching the patterns
        for file_path, content in files.items():
            if any(re.search(pattern, file_path, re.IGNORECASE) for pattern in patterns):
                selected_files[file_path] = content
                if len(selected_files) >= 10:  # Limit to 10 files
                    break
        
        # If we have too few, add some core files
        if len(selected_files) < 5:
            core_files = self._identify_core_files(files)
            for file_path in core_files:
                if file_path not in selected_files:
                    selected_files[file_path] = files[file_path]
                    if len(selected_files) >= 10:
                        break
        
        return selected_files
    
    def _identify_core_files(self, files: Dict[str, str]) -> List[str]:
        """
        Identify core files in the codebase that are critical for understanding
        """
        # Patterns for important files, ordered by priority
        core_patterns = [
            r'package\.json',
            r'requirements\.txt',
            r'setup\.py', 
            r'tsconfig\.json',
            r'README\.md',
            r'main\.py',
            r'app\.py',
            r'index\.[jt]sx?',
            r'App\.[jt]sx?',
            r'settings\.py',
            r'config\.[jt]s',
            r'urls\.py',
            r'router\.[jt]s'
        ]
        
        core_files = []
        
        # First pass - find exact matches to patterns
        for pattern in core_patterns:
            for file_path in files:
                if re.search(pattern, file_path):
                    core_files.append(file_path)
        
        # Second pass - add important directories with index or main files
        for file_path in files:
            parts = file_path.split('/')
            if len(parts) >= 2:
                filename = parts[-1]
                if filename in ['index.js', 'index.ts', 'index.tsx', 'main.py', '__init__.py']:
                    core_files.append(file_path)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(core_files))
    
    def _extract_files(self, response: str) -> Dict[str, str]:
        """Extract files from LLM response with improved pattern matching"""
        files = {}
        
        # Primary pattern: FILE: path followed by code block
        pattern = r'FILE:\s*([^\n]+)\s*\n```(?:\w+)?\s*\n(.*?)\n```'
        matches = re.finditer(pattern, response, re.DOTALL)
        
        for match in matches:
            file_path, content = match.groups()
            file_path = file_path.strip()
            
            # Normalize file path
            if file_path.startswith('./'):
                file_path = file_path[2:]
            
            # Skip invalid paths
            if not file_path or '..' in file_path:
                continue
            
            # Normalize slashes
            file_path = file_path.replace('\\', '/')
            
            files[file_path] = content.strip()
        
        # Fallback pattern for simpler format without code blocks
        if not files:
            alt_pattern = r'FILE:\s*([^\n]+)\s*\nCODE:\s*\n(.*?)\nEND'
            matches = re.finditer(alt_pattern, response, re.DOTALL)
            
            for match in matches:
                file_path, content = match.groups()
                file_path = file_path.strip()
                
                if not file_path or '..' in file_path:
                    continue
                
                # Normalize slashes
                file_path = file_path.replace('\\', '/')
                
                files[file_path] = content.strip()
        
        return files
    
    def _extract_summary(self, text: str) -> Dict[str, Any]:
        """Extract a summary from text analysis"""
        # Try to find a "Summary" or "Conclusion" section
        summary_match = re.search(r'(?:Summary|Conclusion)(?::|)\s*(.*?)(?:\n\n|\n#|\Z)', text, re.DOTALL | re.IGNORECASE)
        
        strengths = []
        weaknesses = []
        
        # Try to find "Strengths" section
        strengths_match = re.search(r'(?:Strengths|Pros|Positive\s+Points)(?::|)\s*(.*?)(?:\n\n|\n#|\Z|\n\s*(?:Weaknesses|Cons|Negative))', text, re.DOTALL | re.IGNORECASE)
        if strengths_match:
            # Extract bullet points
            strength_points = re.findall(r'[-*+]\s+(.*?)(?:\n|$)', strengths_match.group(1))
            strengths = [point.strip() for point in strength_points if point.strip()]
        
        # Try to find "Weaknesses" section
        weaknesses_match = re.search(r'(?:Weaknesses|Cons|Negative\s+Points)(?::|)\s*(.*?)(?:\n\n|\n#|\Z)', text, re.DOTALL | re.IGNORECASE)
        if weaknesses_match:
            # Extract bullet points
            weakness_points = re.findall(r'[-*+]\s+(.*?)(?:\n|$)', weaknesses_match.group(1))
            weaknesses = [point.strip() for point in weakness_points if point.strip()]
        
        # Try to find a rating
        rating_match = re.search(r'(?:Rating|Score|Overall):\s*(\d+(?:\.\d+)?)\s*(?:\/\s*\d+)?', text, re.IGNORECASE)
        
        # Create a summary dictionary
        summary = {
            "overview": summary_match.group(1).strip() if summary_match else "No summary provided",
            "strengths": strengths if strengths else ["Not explicitly mentioned"],
            "weaknesses": weaknesses if weaknesses else ["Not explicitly mentioned"],
            "rating": rating_match.group(1) if rating_match else "N/A"
        }
        
        return summary