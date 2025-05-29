# backend/app/services/enhanced_orchestrator_wrapper.py
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from app.services.llm_service import LLMService
from app.services.code_generator import CodeGenerator
from app.services.test_agent import TestAgent
from app.services.unified_orchestration_manager import UnifiedOrchestrationManager

logger = logging.getLogger(__name__)

class EnhancedGeneratorWrapper:
    """
    🔥 ENHANCED GENERATOR WRAPPER - Using Unified Components
    
    Specializes in single-agent enhanced code generation with architectural planning.
    Uses unified components for all structure management, file organization, and validation.
    
    Focus: Simple to moderate projects with architectural analysis and quality enhancement
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.basic_generator = CodeGenerator(llm_service)  # Fallback
        self.test_agent = TestAgent(llm_service)
        
        # 🎯 UNIFIED COMPONENTS
        self.unified_manager = UnifiedOrchestrationManager()
        
        self.stop_requested = False
        
        # Enhanced Code Generator
        try:
            from app.services.enhanced_code_generator import EnhancedCodeGenerator
            self.enhanced_generator = EnhancedCodeGenerator(llm_service)
            self.has_enhanced_generator = True
        except ImportError:
            self.enhanced_generator = None
            self.has_enhanced_generator = False
            
        logger.info("EnhancedGeneratorWrapper initialized with unified components")
    
    async def generate_application_with_enhanced_flow(self, 
                                                    requirements: Dict[str, Any],
                                                    provider: str,
                                                    max_iterations: int,
                                                    project_path: Path,
                                                    progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        🚀 GENERATE WITH ENHANCED SINGLE-AGENT FLOW
        
        This method focuses on enhanced single-agent generation with architecture analysis,
        while delegating all structure, organization, and validation to unified components.
        """
        
        # Check for stop request
        stop_file = project_path / "STOP_REQUESTED"
        if stop_file.exists():
            logger.info(f"Stop file found for project {project_path.name}, stopping generation")
            return {"status": "stopped", "reason": "user_requested"}
        
        logger.info(f"🚀 Starting enhanced single-agent generation with {max_iterations} max iterations")
        
        # Extract and clean project name
        project_name = requirements.get("project", {}).get("name", project_path.name)
        if not project_name or project_name == project_path.name:
            project_name = f"project_{project_path.name}"
        
        # 🎯 CREATE UNIFIED STRUCTURE
        structure = self.unified_manager.create_project_structure(project_path, project_name)
        logger.info(f"🏗️ Unified structure created for: {structure['project_name']}")
        
        # Track project state
        project_state = {
            "iterations_completed": 0,
            "total_errors_fixed": 0,
            "remaining_issues": [],
            "final_success": False,
            "generation_strategy": "enhanced_single_agent_unified",
            "structure_type": "unified",
            "architecture_analysis_completed": False
        }
        
        # 🎯 ARCHITECTURAL ANALYSIS (enhanced generator specialty)
        if progress_callback:
            progress_callback(0, 'analyzing_architecture')
        
        architecture_plan = await self._analyze_project_architecture(requirements, provider)
        project_state["architecture_analysis_completed"] = True
        logger.info("🏛️ Architecture analysis completed")
        
        # Main iteration loop
        for iteration in range(1, max_iterations + 1):
            logger.info(f"🔄 Starting enhanced single-agent iteration {iteration} for {structure['project_name']}")
            
            # Check for stop request
            if stop_file.exists() or self.stop_requested:
                logger.info("Stop requested, interrupting generation")
                return {
                    "status": "stopped",
                    "reason": "user_requested",
                    "iteration": iteration - 1,
                    "project_id": project_path.name,
                    "project_state": project_state,
                    "output_path": str(structure["project_path"])
                }
            
            try:
                # Update current iteration in project.json
                self._update_current_iteration(project_path, iteration)
                
                # Progress callback
                if progress_callback:
                    progress_callback(iteration, f'enhanced_single_agent_iteration_{iteration}')
                
                # 🔧 GENERATE CODE (enhanced single-agent logic)
                if progress_callback:
                    progress_callback(iteration, 'generating_enhanced_single_agent_code')
                
                code_files = await self._generate_code_for_enhanced_single_agent_iteration(
                    requirements, provider, iteration, structure, architecture_plan
                )
                
                # 📁 ORGANIZE AND SAVE (unified system)
                files_generated, files_modified = self.unified_manager.organize_and_save_files(
                    structure, code_files, requirements
                )
                
                logger.info(f"✅ Enhanced single-agent iteration {iteration}: Generated {files_generated} files, modified {files_modified}")
                
                # 🔍 VALIDATE (unified system)
                if progress_callback:
                    progress_callback(iteration, 'enhanced_single_agent_validation')
                
                validation_result = await self.unified_manager.validate_iteration(
                    structure, requirements, iteration
                )
                
                # Update project state
                project_state["iterations_completed"] = iteration
                project_state["remaining_issues"] = validation_result.get("errors_for_fixing", [])
                
                # Check if iteration was successful
                if validation_result["success"]:
                    logger.info(f"🎉 Enhanced single-agent iteration {iteration} completed successfully!")
                    project_state["final_success"] = True
                    
                    return {
                        "status": "completed",
                        "iteration": iteration,
                        "project_id": project_path.name,
                        "project_name": structure["project_name"],
                        "output_path": str(structure["project_path"]),
                        "project_state": project_state,
                        "final_result": validation_result,
                        "generation_strategy": "enhanced_single_agent_unified",
                        "structure_type": "unified",
                        "architecture_plan": architecture_plan
                    }
                
                # Continue to next iteration with error tracking
                logger.info(f"🔄 Enhanced single-agent iteration {iteration} had issues, continuing to iteration {iteration + 1}")
                
                # Update error tracking
                prev_errors = len(project_state["remaining_issues"])
                current_errors = len(validation_result.get("errors_for_fixing", []))
                
                if current_errors < prev_errors:
                    project_state["total_errors_fixed"] += (prev_errors - current_errors)
                
                # Check progress (enhanced single-agent is usually more effective)
                if iteration > 1 and current_errors >= prev_errors:
                    logger.warning(f"⚠️ No progress in enhanced single-agent iteration {iteration}, errors: {current_errors}")
                
            except Exception as e:
                logger.error(f"❌ Error in enhanced single-agent iteration {iteration}: {str(e)}")
                
                # If this is the last iteration, return failure
                if iteration == max_iterations:
                    return {
                        "status": "failed",
                        "reason": "iteration_error",
                        "error": str(e),
                        "iteration": iteration,
                        "project_id": project_path.name,
                        "project_state": project_state,
                        "structure_type": "unified"
                    }
                
                # Otherwise, try to continue
                logger.info(f"🔄 Attempting to continue after error in enhanced single-agent iteration {iteration}")
                continue
        
        # Max iterations reached
        logger.warning(f"⏱️ Max iterations ({max_iterations}) reached for enhanced single-agent generation")
        
        final_status = "completed_with_issues"
        if project_state["total_errors_fixed"] > 0:
            final_status = "completed_with_improvements"
        
        return {
            "status": final_status,
            "reason": "max_iterations_reached",
            "iterations": max_iterations,
            "project_id": project_path.name,
            "project_name": structure["project_name"],
            "project_state": project_state,
            "output_path": str(structure["project_path"]),
            "generation_strategy": "enhanced_single_agent_unified",
            "structure_type": "unified",
            "architecture_plan": architecture_plan
        }
    
    async def _analyze_project_architecture(self, requirements: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """
        🏛️ ANALYZE PROJECT ARCHITECTURE
        
        Enhanced Generator specialty: architectural analysis and planning
        """
        logger.info("🏛️ Analyzing project architecture with enhanced generator")
        
        # Create architecture analysis prompt
        analysis_prompt = f"""
        Analyze the following project requirements and create a comprehensive architecture plan:
        
        {json.dumps(requirements, indent=2)}
        
        Create an architecture plan that includes:
        1. Overall system architecture pattern
        2. Component breakdown and responsibilities
        3. Data flow and integration points
        4. Technology stack recommendations
        5. File structure and organization
        6. Key design patterns to follow
        7. Scalability considerations
        8. Security considerations
        
        Provide the analysis in JSON format with clear structure.
        """
        
        system_prompt = """
        You are an expert software architect specializing in modern application design.
        Analyze the requirements and create a detailed architecture plan that will guide 
        the enhanced code generation process. Focus on:
        - Scalability and maintainability
        - Best practices for the specified technology stack
        - Clear separation of concerns
        - Modern architectural patterns
        - Security and performance considerations
        """
        
        try:
            response = await self.llm_service.generate(
                provider=provider,
                prompt=analysis_prompt,
                system_prompt=system_prompt
            )
            
            # Try to extract JSON from response
            import re
            import json
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                architecture_plan = json.loads(json_match.group(1))
            else:
                # Fallback: create structured plan from text response
                architecture_plan = {
                    "analysis_type": "enhanced_architecture",
                    "overview": response[:500],
                    "components": self._extract_components_from_text(response),
                    "patterns": self._extract_patterns_from_text(response),
                    "tech_stack": requirements.get("tech_stack", {}),
                    "recommendations": self._extract_recommendations_from_text(response)
                }
            
            # Enhance with project-specific details
            architecture_plan["project_type"] = requirements.get("project", {}).get("type", "fullstack")
            architecture_plan["complexity_level"] = self._assess_complexity_level(requirements)
            architecture_plan["enhanced_features"] = self._identify_enhanced_features(requirements)
            
            logger.info(f"✅ Architecture analysis complete: {architecture_plan.get('analysis_type', 'basic')}")
            return architecture_plan
            
        except Exception as e:
            logger.error(f"Error in architecture analysis: {e}")
            return self._create_fallback_architecture_plan(requirements)
    
    def _assess_complexity_level(self, requirements: Dict[str, Any]) -> str:
        """Assess project complexity level for enhanced generation"""
        features = requirements.get("features", [])
        tech_stack = requirements.get("tech_stack", {})
        
        complexity_indicators = 0
        
        # Count complexity indicators
        if len(features) > 5:
            complexity_indicators += 1
        if "authentication" in str(requirements).lower():
            complexity_indicators += 1
        if "database" in str(requirements).lower():
            complexity_indicators += 1
        if len(tech_stack) > 3:
            complexity_indicators += 1
        if "api" in str(requirements).lower():
            complexity_indicators += 1
        
        if complexity_indicators <= 2:
            return "simple"
        elif complexity_indicators <= 4:
            return "moderate"
        else:
            return "complex"
    
    def _identify_enhanced_features(self, requirements: Dict[str, Any]) -> List[str]:
        """Identify features that benefit from enhanced generation"""
        enhanced_features = []
        req_str = str(requirements).lower()
        
        if "real-time" in req_str or "websocket" in req_str:
            enhanced_features.append("real_time_communication")
        if "auth" in req_str or "login" in req_str:
            enhanced_features.append("authentication_system")
        if "upload" in req_str or "file" in req_str:
            enhanced_features.append("file_management")
        if "search" in req_str:
            enhanced_features.append("search_functionality")
        if "notification" in req_str:
            enhanced_features.append("notification_system")
        if "payment" in req_str or "billing" in req_str:
            enhanced_features.append("payment_integration")
        
        return enhanced_features
    
    def _extract_components_from_text(self, text: str) -> List[str]:
        """Extract main components from architecture analysis text"""
        import re
        component_patterns = [
            r'(\w+)\s+component',
            r'(\w+)\s+service',
            r'(\w+)\s+controller',
            r'(\w+)\s+model',
            r'(\w+)\s+module'
        ]
        
        components = set()
        for pattern in component_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            components.update(matches)
        
        return list(components)[:10]  # Limit to 10 main components
    
    def _extract_patterns_from_text(self, text: str) -> List[str]:
        """Extract design patterns from architecture analysis"""
        common_patterns = [
            "MVC", "MVP", "MVVM", "Repository", "Factory", "Observer", 
            "Singleton", "Strategy", "Command", "Decorator", "Adapter"
        ]
        
        found_patterns = []
        text_lower = text.lower()
        for pattern in common_patterns:
            if pattern.lower() in text_lower:
                found_patterns.append(pattern)
        
        return found_patterns or ["MVC", "Repository"]  # Default patterns
    
    def _extract_recommendations_from_text(self, text: str) -> List[str]:
        """Extract recommendations from architecture analysis"""
        # Simple extraction of sentences containing recommendation keywords
        recommendation_keywords = ["recommend", "suggest", "should", "consider", "use"]
        sentences = text.split('.')
        
        recommendations = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in recommendation_keywords):
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 20:  # Filter out very short sentences
                    recommendations.append(clean_sentence)
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _create_fallback_architecture_plan(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic architecture plan if analysis fails"""
        tech_stack = requirements.get("tech_stack", {})
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        return {
            "analysis_type": "fallback_architecture",
            "overview": f"Basic {project_type} application architecture",
            "components": ["frontend", "backend", "database", "api"],
            "patterns": ["MVC", "Component-based", "RESTful API"],
            "tech_stack": tech_stack,
            "project_type": project_type,
            "complexity_level": self._assess_complexity_level(requirements),
            "recommendations": [
                "Follow separation of concerns",
                "Implement proper error handling",
                "Use consistent naming conventions",
                "Add comprehensive logging"
            ]
        }
    
    async def _generate_code_for_enhanced_single_agent_iteration(self,
                                                               requirements: Dict[str, Any],
                                                               provider: str,
                                                               iteration: int,
                                                               structure: Dict[str, Path],
                                                               architecture_plan: Dict[str, Any]) -> Dict[str, str]:
        """
        🔧 GENERATE CODE FOR ENHANCED SINGLE-AGENT ITERATION
        
        This method focuses on enhanced single-agent code generation with architectural guidance.
        """
        logger.info(f"🔧 Generating enhanced single-agent code for iteration {iteration}")
        
        if iteration == 1:
            # First iteration: generate with architecture plan
            return await self._generate_initial_code_with_architecture(
                requirements, provider, architecture_plan
            )
        else:
            # Subsequent iterations: load previous and apply intelligent fixes
            existing_files = self.unified_manager.load_previous_files(structure)
            previous_errors = self.unified_manager.load_previous_errors(structure, iteration - 1)
            
            if previous_errors and existing_files:
                logger.info(f"🔧 Found {len(previous_errors)} errors from previous iteration")
                return await self._generate_intelligent_fixes(
                    requirements, provider, previous_errors, existing_files, architecture_plan, iteration
                )
            else:
                logger.info("🎨 No previous errors found, applying quality enhancements")
                return await self._generate_quality_enhancements(
                    requirements, provider, existing_files or {}, architecture_plan, iteration
                )

    async def _generate_initial_code_with_architecture(self,
                                                     requirements: Dict[str, Any],
                                                     provider: str,
                                                     architecture_plan: Dict[str, Any]) -> Dict[str, str]:
        """Generate initial code guided by architecture plan"""
        logger.info("🏗️ Generating initial code with architectural guidance")
        
        # Use enhanced generator if available
        if self.has_enhanced_generator:
            logger.info("⚡ Using Enhanced Generator with architecture plan")
            try:
                enhanced_result = await self.enhanced_generator.generate_with_architecture(
                    requirements=requirements,
                    architecture_plan=architecture_plan,
                    provider=provider
                )
                
                if enhanced_result and isinstance(enhanced_result, dict):
                    logger.info("✅ Enhanced Generator with architecture produced code successfully")
                    return enhanced_result
                    
            except AttributeError:
                logger.info("Enhanced Generator doesn't have generate_with_architecture method, using standard method")
                try:
                    enhanced_result = await self.enhanced_generator.generate_complete_project_enhanced(
                        requirements=requirements,
                        provider=provider,
                        max_iterations=1
                    )
                    
                    if enhanced_result["success"]:
                        return enhanced_result["code_files"]
                        
                except Exception as e:
                    logger.warning(f"Enhanced Generator standard method failed: {e}")
            except Exception as e:
                logger.warning(f"Enhanced Generator with architecture failed: {e}")
        
        # Fallback to basic generator with architecture context
        logger.info("🔧 Using basic generator with architecture context")
        return await self._generate_with_basic_generator_and_architecture(
            requirements, provider, architecture_plan
        )

    async def _generate_with_basic_generator_and_architecture(self,
                                                            requirements: Dict[str, Any],
                                                            provider: str,
                                                            architecture_plan: Dict[str, Any]) -> Dict[str, str]:
        """Generate code using basic generator with architecture context"""
        
        # Enhance requirements with architecture insights
        enhanced_requirements = dict(requirements)
        enhanced_requirements["_architecture_context"] = {
            "components": architecture_plan.get("components", []),
            "patterns": architecture_plan.get("patterns", []),
            "complexity_level": architecture_plan.get("complexity_level", "moderate"),
            "recommendations": architecture_plan.get("recommendations", [])
        }
        
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        if project_type == "frontend":
            return await self.basic_generator.generate_react_app(enhanced_requirements, provider)
        elif project_type == "backend":
            return await self.basic_generator.generate_backend_api(enhanced_requirements, provider)
        else:
            return await self.basic_generator.generate_code(enhanced_requirements, provider, 1)

    async def _generate_intelligent_fixes(self,
                                        requirements: Dict[str, Any],
                                        provider: str,
                                        errors: List[Dict[str, Any]],
                                        existing_files: Dict[str, str],
                                        architecture_plan: Dict[str, Any],
                                        iteration: int) -> Dict[str, str]:
        """Generate intelligent fixes using enhanced capabilities"""
        logger.info(f"🔧 Generating intelligent fixes for {len(errors)} errors")
        
        # Use enhanced generator for intelligent fixing if available
        if self.has_enhanced_generator:
            try:
                fixed_files = await self.enhanced_generator.fix_issues(
                    code_files=existing_files,
                    issues=errors,
                    provider=provider,
                    context={
                        "iteration": iteration,
                        "architecture_plan": architecture_plan,
                        "project_type": requirements.get("project", {}).get("type", "fullstack"),
                        "tech_stack": requirements.get("tech_stack", {}),
                        "structure_type": "unified",
                        "generation_mode": "enhanced_single_agent"
                    }
                )
                logger.info("✅ Enhanced Generator applied intelligent fixes")
                return fixed_files
                
            except Exception as e:
                logger.warning(f"Enhanced Generator intelligent fixing failed: {e}")
        
        # Fallback to standard fixing
        return await self.basic_generator.generate_iterative_improvement(
            requirements, provider, iteration, errors, existing_files
        )

    async def _generate_quality_enhancements(self,
                                           requirements: Dict[str, Any],
                                           provider: str,
                                           existing_files: Dict[str, str],
                                           architecture_plan: Dict[str, Any],
                                           iteration: int) -> Dict[str, str]:
        """Generate quality enhancements without specific errors"""
        logger.info(f"🎨 Generating quality enhancements for iteration {iteration}")
        
        # Determine enhancement focus based on architecture and iteration
        enhancement_focus = self._determine_enhancement_focus(
            requirements, architecture_plan, iteration
        )
        
        # Use enhanced generator for quality improvements if available
        if self.has_enhanced_generator:
            try:
                enhanced_files = await self.enhanced_generator.enhance_code_quality(
                    code_files=existing_files,
                    quality_focus=enhancement_focus,
                    provider=provider
                )
                logger.info(f"✅ Enhanced Generator applied quality improvements: {', '.join(enhancement_focus)}")
                return enhanced_files
                
            except Exception as e:
                logger.warning(f"Enhanced Generator quality enhancement failed: {e}")
        
        # Fallback to standard improvements
        return await self.basic_generator.generate_iterative_improvement(
            requirements, provider, iteration, [], existing_files
        )

    def _determine_enhancement_focus(self,
                                   requirements: Dict[str, Any],
                                   architecture_plan: Dict[str, Any],
                                   iteration: int) -> List[str]:
        """Determine quality enhancement focus areas"""
        
        # Base focus by iteration
        iteration_focus = {
            2: ["code_organization", "error_handling"],
            3: ["performance", "security"],
            4: ["documentation", "testing"],
            5: ["maintainability", "scalability"]
        }
        
        focus_areas = iteration_focus.get(iteration, ["code_quality"])
        
        # Add architecture-based focus
        complexity = architecture_plan.get("complexity_level", "moderate")
        if complexity == "complex":
            focus_areas.extend(["modularization", "separation_of_concerns"])
        
        enhanced_features = architecture_plan.get("enhanced_features", [])
        if "authentication_system" in enhanced_features:
            focus_areas.append("security")
        if "real_time_communication" in enhanced_features:
            focus_areas.append("performance")
        
        # Add requirements-based focus
        req_str = str(requirements).lower()
        if "api" in req_str:
            focus_areas.append("documentation")
        if "database" in req_str:
            focus_areas.append("data_validation")
        
        return list(set(focus_areas))  # Remove duplicates
    
    def _update_current_iteration(self, project_path: Path, iteration: int):
        """Update current iteration in project.json"""
        try:
            project_json_path = project_path / "project.json"
            if project_json_path.exists():
                import json
                with open(project_json_path, 'r') as f:
                    project_data = json.load(f)
                
                project_data["current_iteration"] = iteration
                project_data["structure_type"] = "unified"
                project_data["generation_mode"] = "enhanced_single_agent"
                
                with open(project_json_path, 'w') as f:
                    json.dump(project_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error updating project.json: {str(e)}")
    
    def request_stop(self):
        """Request stop for the enhanced generator wrapper"""
        logger.info("Stop requested for EnhancedGeneratorWrapper")
        self.stop_requested = True