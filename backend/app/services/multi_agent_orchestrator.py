# backend/app/services/multi_agent_orchestrator.py
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Set
from pathlib import Path

from app.services.llm_service import LLMService
from app.services.code_generator import CodeGenerator
from app.services.test_agent import TestAgent
from app.services.unified_orchestration_manager import UnifiedOrchestrationManager

# Multi-agent specific imports
from app.services.agent_system import SystemAgent
from app.services.agent_integration import IntegrationAgent
from app.services.endpoints_agent import EndpointsAgent

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    """
    🔥 MULTI-AGENT ORCHESTRATOR - Using Unified Components
    
    Specializes in enterprise-level multi-agent collaborative code generation.
    Uses unified components for all structure management, file organization, and validation.
    
    Focus: Enterprise projects requiring specialized agents working together
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        
        # Core agents
        self.code_generator = CodeGenerator(llm_service)
        self.test_agent = TestAgent(llm_service)
        
        # Specialized agents
        self.system_agent = SystemAgent(llm_service)
        self.integration_agent = IntegrationAgent(llm_service)
        self.endpoints_agent = EndpointsAgent(llm_service)
        
        # 🎯 UNIFIED COMPONENTS
        self.unified_manager = UnifiedOrchestrationManager()
        
        self.stop_requested = False
        
        # Multi-agent coordination tracking
        self.agent_coordination = {
            "active_agents": [],
            "task_distribution": {},
            "collaboration_history": []
        }
        
        logger.info("MultiAgentOrchestrator initialized with unified components and specialized agents")
    
    async def generate_multi_agent_application(self, 
                                             requirements: Dict[str, Any],
                                             provider: str,
                                             max_iterations: int,
                                             project_path: Path,
                                             progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        🚀 GENERATE MULTI-AGENT APPLICATION
        
        Coordinates multiple specialized agents to generate enterprise-level applications,
        while delegating all structure, organization, and validation to unified components.
        """
        
        # Check for stop request
        stop_file = project_path / "STOP_REQUESTED"
        if stop_file.exists():
            logger.info(f"Stop file found for project {project_path.name}, stopping generation")
            return {"status": "stopped", "reason": "user_requested"}
        
        logger.info(f"🚀 Starting multi-agent collaborative generation with {max_iterations} max iterations")
        
        # Extract and clean project name
        project_name = requirements.get("project", {}).get("name", project_path.name)
        if not project_name or project_name == project_path.name:
            project_name = f"project_{project_path.name}"
        
        # 🎯 CREATE UNIFIED STRUCTURE
        structure = self.unified_manager.create_project_structure(project_path, project_name)
        logger.info(f"🏗️ Unified structure created for: {structure['project_name']}")
        
        # Track multi-agent project state
        project_state = {
            "iterations_completed": 0,
            "total_errors_fixed": 0,
            "remaining_issues": [],
            "final_success": False,
            "generation_strategy": "multi_agent_collaborative_unified",
            "structure_type": "unified",
            "agent_coordination": self.agent_coordination,
            "enterprise_features_implemented": []
        }
        
        # 🎯 MULTI-AGENT ANALYSIS AND PLANNING
        if progress_callback:
            progress_callback(0, 'multi_agent_planning')
        
        multi_agent_plan = await self._create_multi_agent_plan(requirements, provider)
        project_state["multi_agent_plan"] = multi_agent_plan
        logger.info("🤖 Multi-agent planning completed")
        
        # Main iteration loop
        for iteration in range(1, max_iterations + 1):
            logger.info(f"🔄 Starting multi-agent iteration {iteration} for {structure['project_name']}")
            
            # Check for stop request
            if stop_file.exists() or self.stop_requested:
                logger.info("Stop requested, interrupting multi-agent generation")
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
                    progress_callback(iteration, f'multi_agent_collaboration_iteration_{iteration}')
                
                # 🤖 COLLABORATIVE CODE GENERATION (multi-agent specialty)
                if progress_callback:
                    progress_callback(iteration, 'multi_agent_collaborative_generation')
                
                code_files = await self._generate_code_with_multi_agent_collaboration(
                    requirements, provider, iteration, structure, multi_agent_plan
                )
                
                # 📁 ORGANIZE AND SAVE (unified system)
                files_generated, files_modified = self.unified_manager.organize_and_save_files(
                    structure, code_files, requirements
                )
                
                logger.info(f"✅ Multi-agent iteration {iteration}: Generated {files_generated} files, modified {files_modified}")
                
                # 🔍 VALIDATE (unified system)
                if progress_callback:
                    progress_callback(iteration, 'multi_agent_validation')
                
                validation_result = await self.unified_manager.validate_iteration(
                    structure, requirements, iteration
                )
                
                # Update project state
                project_state["iterations_completed"] = iteration
                project_state["remaining_issues"] = validation_result.get("errors_for_fixing", [])
                
                # Check if iteration was successful
                if validation_result["success"]:
                    logger.info(f"🎉 Multi-agent iteration {iteration} completed successfully!")
                    project_state["final_success"] = True
                    
                    return {
                        "status": "completed",
                        "iteration": iteration,
                        "project_id": project_path.name,
                        "project_name": structure["project_name"],
                        "output_path": str(structure["project_path"]),
                        "project_state": project_state,
                        "final_result": validation_result,
                        "generation_strategy": "multi_agent_collaborative_unified",
                        "structure_type": "unified",
                        "multi_agent_plan": multi_agent_plan
                    }
                
                # Continue to next iteration with multi-agent coordination
                logger.info(f"🔄 Multi-agent iteration {iteration} had issues, coordinating agents for iteration {iteration + 1}")
                
                # Update error tracking and agent coordination
                prev_errors = len(project_state["remaining_issues"])
                current_errors = len(validation_result.get("errors_for_fixing", []))
                
                if current_errors < prev_errors:
                    project_state["total_errors_fixed"] += (prev_errors - current_errors)
                
                # Update agent coordination strategy based on errors
                await self._update_agent_coordination_strategy(
                    validation_result.get("errors_for_fixing", []), iteration
                )
                
                # Check progress
                if iteration > 1 and current_errors >= prev_errors:
                    logger.warning(f"⚠️ No progress in multi-agent iteration {iteration}, errors: {current_errors}")
                    # Multi-agent systems should be more resilient, so continue trying
                
            except Exception as e:
                logger.error(f"❌ Error in multi-agent iteration {iteration}: {str(e)}")
                
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
                
                # Otherwise, try to continue with different agent coordination
                logger.info(f"🔄 Attempting to continue with modified agent coordination after error in iteration {iteration}")
                await self._handle_iteration_failure(e, iteration)
                continue
        
        # Max iterations reached
        logger.warning(f"⏱️ Max iterations ({max_iterations}) reached for multi-agent generation")
        
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
            "generation_strategy": "multi_agent_collaborative_unified",
            "structure_type": "unified",
            "multi_agent_plan": multi_agent_plan
        }
    
    async def _create_multi_agent_plan(self, requirements: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """
        🤖 CREATE MULTI-AGENT PLAN
        
        Analyze requirements and create a plan for multi-agent collaboration
        """
        logger.info("🤖 Creating multi-agent collaboration plan")
        
        # Analyze requirements complexity
        complexity_analysis = self._analyze_enterprise_complexity(requirements)
        
        # Determine agent assignment
        agent_assignments = await self._determine_agent_assignments(requirements, provider)
        
        # Create collaboration workflow
        collaboration_workflow = self._create_collaboration_workflow(agent_assignments, complexity_analysis)
        
        multi_agent_plan = {
            "complexity_analysis": complexity_analysis,
            "agent_assignments": agent_assignments,
            "collaboration_workflow": collaboration_workflow,
            "coordination_strategy": self._determine_coordination_strategy(complexity_analysis),
            "enterprise_features": self._identify_enterprise_features(requirements)
        }
        
        logger.info(f"✅ Multi-agent plan created with {len(agent_assignments)} specialized agents")
        return multi_agent_plan
    
    def _analyze_enterprise_complexity(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze enterprise-level complexity indicators"""
        
        features = requirements.get("features", [])
        tech_stack = requirements.get("tech_stack", {})
        req_str = str(requirements).lower()
        
        complexity_indicators = {
            "microservices": "microservice" in req_str or "micro-service" in req_str,
            "authentication": "auth" in req_str or "login" in req_str,
            "real_time": "real-time" in req_str or "websocket" in req_str,
            "api_gateway": "gateway" in req_str or "proxy" in req_str,
            "database_multiple": len([k for k in tech_stack.keys() if "db" in k.lower()]) > 1,
            "integrations": "integration" in req_str or "external" in req_str,
            "monitoring": "monitor" in req_str or "log" in req_str,
            "deployment": "docker" in req_str or "kubernetes" in req_str,
            "testing": "test" in req_str,
            "security": "security" in req_str or "encrypt" in req_str
        }
        
        complexity_score = sum(complexity_indicators.values())
        
        if complexity_score >= 7:
            complexity_level = "enterprise"
        elif complexity_score >= 5:
            complexity_level = "advanced"
        elif complexity_score >= 3:
            complexity_level = "intermediate"
        else:
            complexity_level = "standard"
        
        return {
            "level": complexity_level,
            "score": complexity_score,
            "indicators": complexity_indicators,
            "recommended_agents": self._recommend_agents_for_complexity(complexity_level)
        }
    
    def _recommend_agents_for_complexity(self, complexity_level: str) -> List[str]:
        """Recommend agents based on complexity level"""
        agent_recommendations = {
            "standard": ["system_agent", "code_generator"],
            "intermediate": ["system_agent", "code_generator", "endpoints_agent"],
            "advanced": ["system_agent", "code_generator", "endpoints_agent", "integration_agent"],
            "enterprise": ["system_agent", "code_generator", "endpoints_agent", "integration_agent", "test_agent"]
        }
        
        return agent_recommendations.get(complexity_level, ["system_agent", "code_generator"])
    
    async def _determine_agent_assignments(self, requirements: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Determine which agents handle which parts of the project"""
        
        assignments = {
            "system_agent": {
                "responsibilities": ["core_architecture", "configuration", "environment_setup"],
                "priority": "high",
                "specialization": "System architecture and configuration"
            },
            "code_generator": {
                "responsibilities": ["business_logic", "core_functionality", "base_structure"],
                "priority": "high", 
                "specialization": "Core application logic and structure"
            }
        }
        
        # Determine additional agents based on requirements
        req_str = str(requirements).lower()
        
        if "api" in req_str or "endpoint" in req_str:
            assignments["endpoints_agent"] = {
                "responsibilities": ["api_design", "endpoint_implementation", "routing"],
                "priority": "high",
                "specialization": "API endpoints and routing"
            }
        
        if "integration" in req_str or "external" in req_str:
            assignments["integration_agent"] = {
                "responsibilities": ["external_apis", "third_party_integrations", "data_sync"],
                "priority": "medium",
                "specialization": "External integrations and data synchronization"
            }
        
        if "test" in req_str or len(requirements.get("features", [])) > 5:
            assignments["test_agent"] = {
                "responsibilities": ["test_generation", "test_automation", "quality_assurance"],
                "priority": "medium",
                "specialization": "Testing and quality assurance"
            }
        
        return assignments
    
    def _create_collaboration_workflow(self, agent_assignments: Dict[str, Any], complexity_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create workflow for agent collaboration"""
        
        workflow_phases = [
            {
                "phase": "foundation",
                "description": "Establish core architecture and structure",
                "agents": ["system_agent", "code_generator"],
                "parallel": False,
                "dependencies": []
            }
        ]
        
        # Add API phase if endpoints agent is assigned
        if "endpoints_agent" in agent_assignments:
            workflow_phases.append({
                "phase": "api_development",
                "description": "Develop API endpoints and routing",
                "agents": ["endpoints_agent"],
                "parallel": False,
                "dependencies": ["foundation"]
            })
        
        # Add integration phase if integration agent is assigned
        if "integration_agent" in agent_assignments:
            workflow_phases.append({
                "phase": "integration",
                "description": "Implement external integrations and data sync",
                "agents": ["integration_agent"],
                "parallel": True,  # Can run parallel with API development
                "dependencies": ["foundation"]
            })
        
        # Add testing phase if test agent is assigned
        if "test_agent" in agent_assignments:
            workflow_phases.append({
                "phase": "testing",
                "description": "Generate comprehensive tests and quality assurance",
                "agents": ["test_agent"],
                "parallel": False,
                "dependencies": ["api_development", "integration"] if "integration_agent" in agent_assignments else ["api_development"]
            })
        
        return workflow_phases
    
    def _determine_coordination_strategy(self, complexity_analysis: Dict[str, Any]) -> str:
        """Determine coordination strategy based on complexity"""
        complexity_level = complexity_analysis["level"]
        
        strategy_mapping = {
            "standard": "sequential",      # Agents work one after another
            "intermediate": "hybrid",      # Mix of sequential and parallel
            "advanced": "parallel",       # Agents work in parallel where possible
            "enterprise": "collaborative" # Full collaboration with cross-agent communication
        }
        
        return strategy_mapping.get(complexity_level, "hybrid")
    
    def _identify_enterprise_features(self, requirements: Dict[str, Any]) -> List[str]:
        """Identify enterprise-level features that require special handling"""
        enterprise_features = []
        req_str = str(requirements).lower()
        
        feature_indicators = {
            "microservices_architecture": ["microservice", "micro-service", "distributed"],
            "api_gateway": ["gateway", "proxy", "load balancer"],
            "authentication_system": ["auth", "login", "oauth", "jwt", "session"],
            "real_time_communication": ["websocket", "real-time", "live", "streaming"],
            "data_analytics": ["analytics", "reporting", "dashboard", "metrics"],
            "file_management": ["upload", "file", "storage", "s3", "blob"],
            "notification_system": ["notification", "email", "sms", "push"],
            "payment_processing": ["payment", "billing", "stripe", "paypal"],
            "multi_tenant": ["tenant", "multi-tenant", "saas"],
            "audit_logging": ["audit", "logging", "tracking", "compliance"]
        }
        
        for feature, indicators in feature_indicators.items():
            if any(indicator in req_str for indicator in indicators):
                enterprise_features.append(feature)
        
        return enterprise_features
    
    async def _generate_code_with_multi_agent_collaboration(self,
                                                          requirements: Dict[str, Any],
                                                          provider: str,
                                                          iteration: int,
                                                          structure: Dict[str, Path],
                                                          multi_agent_plan: Dict[str, Any]) -> Dict[str, str]:
        """
        🤖 GENERATE CODE WITH MULTI-AGENT COLLABORATION
        
        This method coordinates multiple agents to generate code collaboratively.
        """
        logger.info(f"🤖 Starting multi-agent collaborative code generation for iteration {iteration}")
        
        if iteration == 1:
            # First iteration: full multi-agent collaboration
            return await self._execute_multi_agent_workflow(
                requirements, provider, multi_agent_plan, structure
            )
        else:
            # Subsequent iterations: collaborative error fixing and improvements
            existing_files = self.unified_manager.load_previous_files(structure)
            previous_errors = self.unified_manager.load_previous_errors(structure, iteration - 1)
            
            if previous_errors and existing_files:
                logger.info(f"🤖 Multi-agent collaborative error fixing: {len(previous_errors)} errors")
                return await self._execute_collaborative_error_fixing(
                    requirements, provider, previous_errors, existing_files, multi_agent_plan, iteration
                )
            else:
                logger.info("🤖 Multi-agent collaborative improvements")
                return await self._execute_collaborative_improvements(
                    requirements, provider, existing_files or {}, multi_agent_plan, iteration
                )

    async def _execute_multi_agent_workflow(self,
                                          requirements: Dict[str, Any],
                                          provider: str,
                                          multi_agent_plan: Dict[str, Any],
                                          structure: Dict[str, Path]) -> Dict[str, str]:
        """Execute the multi-agent workflow for initial generation"""
        
        workflow = multi_agent_plan["collaboration_workflow"]
        agent_assignments = multi_agent_plan["agent_assignments"]
        all_generated_files = {}
        
        # Execute workflow phases
        for phase in workflow:
            logger.info(f"🎯 Executing multi-agent phase: {phase['phase']}")
            
            phase_files = {}
            
            # Execute agents in this phase
            for agent_name in phase["agents"]:
                if agent_name in agent_assignments:
                    try:
                        agent_files = await self._execute_agent_task(
                            agent_name, requirements, provider, all_generated_files
                        )
                        phase_files.update(agent_files)
                        
                        # Track collaboration
                        self.agent_coordination["collaboration_history"].append({
                            "phase": phase["phase"],
                            "agent": agent_name,
                            "files_generated": len(agent_files),
                            "success": True
                        })
                        
                    except Exception as e:
                        logger.error(f"❌ Agent {agent_name} failed in phase {phase['phase']}: {e}")
                        
                        # Track failure
                        self.agent_coordination["collaboration_history"].append({
                            "phase": phase["phase"],
                            "agent": agent_name,
                            "files_generated": 0,
                            "success": False,
                            "error": str(e)
                        })
            
            # Merge phase files
            all_generated_files.update(phase_files)
            logger.info(f"✅ Phase {phase['phase']} completed: {len(phase_files)} files generated")
        
        # Apply multi-agent coordination and conflict resolution
        resolved_files = await self._resolve_multi_agent_conflicts(all_generated_files, requirements)
        
        logger.info(f"🤖 Multi-agent workflow completed: {len(resolved_files)} total files")
        return resolved_files

    async def _execute_agent_task(self,
                                agent_name: str,
                                requirements: Dict[str, Any],
                                provider: str,
                                existing_files: Dict[str, str]) -> Dict[str, str]:
        """Execute a specific agent's task"""
        
        logger.info(f"🔧 Executing {agent_name} task")
        
        # Add existing files context to requirements
        enhanced_requirements = dict(requirements)
        enhanced_requirements["_existing_files"] = list(existing_files.keys())
        enhanced_requirements["_collaboration_context"] = {
            "agent_role": agent_name,
            "coordination_mode": "multi_agent",
            "existing_file_count": len(existing_files)
        }
        
        try:
            if agent_name == "system_agent":
                return await self.system_agent.generate_system_files(enhanced_requirements, provider)
            
            elif agent_name == "code_generator":
                return await self.code_generator.generate_code(enhanced_requirements, provider, 1)
            
            elif agent_name == "endpoints_agent":
                return await self.endpoints_agent.generate_endpoints(enhanced_requirements, provider)
            
            elif agent_name == "integration_agent":
                return await self.integration_agent.generate_integrations(enhanced_requirements, provider)
            
            elif agent_name == "test_agent":
                # Test agent needs existing files to generate tests
                if existing_files:
                    return await self.test_agent.test_generator.generate_tests(
                        enhanced_requirements, existing_files, provider
                    )
                else:
                    logger.warning("Test agent called without existing files, skipping")
                    return {}
            
            else:
                logger.warning(f"Unknown agent: {agent_name}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error executing {agent_name}: {e}")
            return {}

    async def _execute_collaborative_error_fixing(self,
                                                requirements: Dict[str, Any],
                                                provider: str,
                                                errors: List[Dict[str, Any]],
                                                existing_files: Dict[str, str],
                                                multi_agent_plan: Dict[str, Any],
                                                iteration: int) -> Dict[str, str]:
        """Execute collaborative error fixing using multiple agents"""
        
        logger.info(f"🔧 Multi-agent collaborative error fixing: {len(errors)} errors")
        
        # Categorize errors by agent specialty
        error_assignments = self._assign_errors_to_agents(errors, multi_agent_plan["agent_assignments"])
        
        fixed_files = dict(existing_files)
        
        # Each agent handles their assigned errors
        for agent_name, agent_errors in error_assignments.items():
            if agent_errors:  # Only if agent has errors to fix
                try:
                    logger.info(f"🔧 {agent_name} fixing {len(agent_errors)} errors")
                    
                    agent_fixes = await self._get_agent_error_fixes(
                        agent_name, requirements, provider, agent_errors, fixed_files
                    )
                    
                    fixed_files.update(agent_fixes)
                    
                    # Track collaboration
                    self.agent_coordination["collaboration_history"].append({
                        "iteration": iteration,
                        "agent": agent_name,
                        "task": "error_fixing",
                        "errors_handled": len(agent_errors),
                        "files_modified": len(agent_fixes),
                        "success": True
                    })
                    
                except Exception as e:
                    logger.error(f"❌ {agent_name} error fixing failed: {e}")
                    
                    # Track failure
                    self.agent_coordination["collaboration_history"].append({
                        "iteration": iteration,
                        "agent": agent_name,
                        "task": "error_fixing",
                        "errors_handled": len(agent_errors),
                        "files_modified": 0,
                        "success": False,
                        "error": str(e)
                    })
        
        return fixed_files

    def _assign_errors_to_agents(self, errors: List[Dict[str, Any]], agent_assignments: Dict[str, Any]) -> Dict[str, List]:
        """Assign errors to appropriate agents based on their specialization"""
        
        error_assignments = {agent: [] for agent in agent_assignments.keys()}
        
        for error in errors:
            error_category = error.get("category", "unknown")
            error_type = error.get("type", "unknown")
            
            # Assign based on error category and agent specialization
            if error_category in ["api", "endpoint", "routing"] and "endpoints_agent" in error_assignments:
                error_assignments["endpoints_agent"].append(error)
            elif error_category in ["integration", "external"] and "integration_agent" in error_assignments:
                error_assignments["integration_agent"].append(error)
            elif error_category in ["config", "system"] and "system_agent" in error_assignments:
                error_assignments["system_agent"].append(error)
            elif error_type in ["test_failure", "testing"] and "test_agent" in error_assignments:
                error_assignments["test_agent"].append(error)
            else:
                # Default to code_generator for general errors
                error_assignments["code_generator"].append(error)
        
        # Log assignment distribution
        for agent, assigned_errors in error_assignments.items():
            if assigned_errors:
                logger.info(f"📋 {agent}: {len(assigned_errors)} errors assigned")
        
        return error_assignments

    async def _get_agent_error_fixes(self,
                                   agent_name: str,
                                   requirements: Dict[str, Any],
                                   provider: str,
                                   errors: List[Dict[str, Any]],
                                   existing_files: Dict[str, str]) -> Dict[str, str]:
        """Get error fixes from a specific agent"""
        
        # Check if agent has a specialized fix method
        if hasattr(getattr(self, agent_name, None), 'fix_issues'):
            agent = getattr(self, agent_name)
            return await agent.fix_issues(errors, existing_files, provider)
        
        # Fallback to general fixing approach
        enhanced_requirements = dict(requirements)
        enhanced_requirements["_error_context"] = {
            "errors": errors,
            "agent_specialization": agent_name,
            "error_count": len(errors)
        }
        
        if agent_name == "code_generator":
            return await self.code_generator.generate_iterative_improvement(
                enhanced_requirements, provider, 2, errors, existing_files
            )
        else:
            # For specialized agents, use their standard generation with error context
            return await self._execute_agent_task(agent_name, enhanced_requirements, provider, existing_files)

    async def _execute_collaborative_improvements(self,
                                                requirements: Dict[str, Any],
                                                provider: str,
                                                existing_files: Dict[str, str],
                                                multi_agent_plan: Dict[str, Any],
                                                iteration: int) -> Dict[str, str]:
        """Execute collaborative improvements using multiple agents"""
        
        logger.info(f"🎨 Multi-agent collaborative improvements for iteration {iteration}")
        
        # Determine improvement focus for each agent
        improvement_assignments = self._assign_improvements_to_agents(
            requirements, multi_agent_plan, iteration
        )
        
        improved_files = dict(existing_files)
        
        # Each agent applies their specialized improvements
        for agent_name, improvement_focus in improvement_assignments.items():
            if improvement_focus:  # Only if agent has improvements to make
                try:
                    logger.info(f"🎨 {agent_name} applying improvements: {', '.join(improvement_focus)}")
                    
                    agent_improvements = await self._get_agent_improvements(
                        agent_name, requirements, provider, improvement_focus, improved_files
                    )
                    
                    improved_files.update(agent_improvements)
                    
                    # Track collaboration
                    self.agent_coordination["collaboration_history"].append({
                        "iteration": iteration,
                        "agent": agent_name,
                        "task": "improvements",
                        "focus_areas": improvement_focus,
                        "files_modified": len(agent_improvements),
                        "success": True
                    })
                    
                except Exception as e:
                    logger.error(f"❌ {agent_name} improvements failed: {e}")
        
        return improved_files

    def _assign_improvements_to_agents(self,
                                     requirements: Dict[str, Any],
                                     multi_agent_plan: Dict[str, Any],
                                     iteration: int) -> Dict[str, List[str]]:
        """Assign improvement tasks to appropriate agents"""
        
        # Base improvement focus by iteration
        iteration_improvements = {
            2: ["error_handling", "code_organization"],
            3: ["performance", "security"],
            4: ["documentation", "testing"],
            5: ["maintainability", "scalability"]
        }
        
        base_improvements = iteration_improvements.get(iteration, ["code_quality"])
        agent_assignments = multi_agent_plan["agent_assignments"]
        
        improvement_assignments = {}
        
        # Assign improvements based on agent specialization
        for agent_name, assignment in agent_assignments.items():
            agent_improvements = []
            
            if agent_name == "system_agent":
                agent_improvements = [imp for imp in base_improvements if imp in ["security", "performance", "scalability"]]
            elif agent_name == "endpoints_agent":
                agent_improvements = [imp for imp in base_improvements if imp in ["documentation", "error_handling"]]
            elif agent_name == "integration_agent":
                agent_improvements = [imp for imp in base_improvements if imp in ["error_handling", "security"]]
            elif agent_name == "test_agent":
                agent_improvements = [imp for imp in base_improvements if imp in ["testing", "code_quality"]]
            elif agent_name == "code_generator":
                agent_improvements = [imp for imp in base_improvements if imp in ["maintainability", "code_organization"]]
            
            improvement_assignments[agent_name] = agent_improvements
        
        return improvement_assignments

    async def _get_agent_improvements(self,
                                    agent_name: str,
                                    requirements: Dict[str, Any],
                                    provider: str,
                                    improvement_focus: List[str],
                                    existing_files: Dict[str, str]) -> Dict[str, str]:
        """Get improvements from a specific agent"""
        
        enhanced_requirements = dict(requirements)
        enhanced_requirements["_improvement_context"] = {
            "focus_areas": improvement_focus,
            "agent_specialization": agent_name,
            "improvement_mode": "collaborative"
        }
        
        # Use agent's specialized improvement method if available
        if hasattr(getattr(self, agent_name, None), 'enhance_code_quality'):
            agent = getattr(self, agent_name)
            return await agent.enhance_code_quality(existing_files, improvement_focus, provider)
        
        # Fallback to agent's standard generation with improvement context
        return await self._execute_agent_task(agent_name, enhanced_requirements, provider, existing_files)

    async def _resolve_multi_agent_conflicts(self,
                                           all_files: Dict[str, str],
                                           requirements: Dict[str, Any]) -> Dict[str, str]:
        """Resolve conflicts between files generated by different agents"""
        
        logger.info("🔄 Resolving multi-agent conflicts")
        
        # Simple conflict resolution: later agents override earlier ones for same files
        # In a more sophisticated system, this would involve intelligent merging
        
        resolved_files = {}
        file_sources = {}  # Track which agent generated which file
        
        for file_path, content in all_files.items():
            # Check for potential conflicts (same file from different agents)
            if file_path in resolved_files:
                logger.warning(f"⚠️ File conflict detected: {file_path}")
                # For now, keep the latest version
                file_sources[file_path] = "conflict_resolved"
            else:
                file_sources[file_path] = "single_source"
            
            resolved_files[file_path] = content
        
        logger.info(f"✅ Conflict resolution complete: {len(resolved_files)} files resolved")
        return resolved_files

    async def _update_agent_coordination_strategy(self, errors: List[Dict[str, Any]], iteration: int):
        """Update agent coordination strategy based on current errors"""
        
        # Analyze error patterns to improve coordination
        error_categories = {}
        for error in errors:
            category = error.get("category", "unknown")
            error_categories[category] = error_categories.get(category, 0) + 1
        
        # Update active agents based on error patterns
        if error_categories.get("api", 0) > 3 and "endpoints_agent" not in self.agent_coordination["active_agents"]:
            self.agent_coordination["active_agents"].append("endpoints_agent")
            logger.info("📈 Activated endpoints_agent due to API errors")
        
        if error_categories.get("integration", 0) > 2 and "integration_agent" not in self.agent_coordination["active_agents"]:
            self.agent_coordination["active_agents"].append("integration_agent")
            logger.info("📈 Activated integration_agent due to integration errors")
        
        # Update task distribution
        self.agent_coordination["task_distribution"][f"iteration_{iteration}"] = error_categories

    async def _handle_iteration_failure(self, error: Exception, iteration: int):
        """Handle iteration failure and adjust agent coordination"""
        
        logger.warning(f"🔄 Handling multi-agent iteration {iteration} failure: {error}")
        
        # Simplify agent coordination for next iteration
        if len(self.agent_coordination["active_agents"]) > 2:
            # Reduce to core agents
            self.agent_coordination["active_agents"] = ["system_agent", "code_generator"]
            logger.info("🔄 Simplified agent coordination to core agents")
        
        # Record failure for analysis
        self.agent_coordination["collaboration_history"].append({
            "iteration": iteration,
            "event": "iteration_failure",
            "error": str(error),
            "recovery_action": "simplified_coordination"
        })

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
                project_data["generation_mode"] = "multi_agent_collaborative"
                project_data["active_agents"] = self.agent_coordination["active_agents"]
                
                with open(project_json_path, 'w') as f:
                    json.dump(project_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error updating project.json: {str(e)}")
    
    def request_stop(self):
        """Request stop for the multi-agent orchestrator"""
        logger.info("Stop requested for MultiAgentOrchestrator")
        self.stop_requested = True
        
        # Notify all agents to stop if they support it
        for agent_name in ["system_agent", "integration_agent", "endpoints_agent"]:
            agent = getattr(self, agent_name, None)
            if agent and hasattr(agent, 'request_stop'):
                agent.request_stop()

    # 🎯 MULTI-AGENT SPECIFIC METHODS
    
    def get_agent_coordination_status(self) -> Dict[str, Any]:
        """Get current agent coordination status"""
        return {
            "coordination_strategy": self.agent_coordination,
            "collaboration_history": self.agent_coordination["collaboration_history"][-10:],  # Last 10 events
            "active_agents": self.agent_coordination["active_agents"],
            "total_collaborations": len(self.agent_coordination["collaboration_history"])
        }
    
    async def analyze_requirements(self, requirements: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """
        Analyze requirements using system agent
        (Kept for backward compatibility)
        """
        logger.info("Analyzing requirements with system agent")
        return await self.system_agent.analyze_requirements(requirements, provider)