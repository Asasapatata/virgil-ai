# backend/app/services/requirements_analyzer.py
import logging
from typing import Dict, Any, List, Tuple
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class ProjectComplexity(str, Enum):
    SIMPLE = "simple"           # Landing page, static sites
    MODERATE = "moderate"       # Frontend with some interactivity
    COMPLEX = "complex"         # Full-stack applications
    ENTERPRISE = "enterprise"   # Microservices, multiple databases

class AgentMode(str, Enum):
    SINGLE = "original"                    # Simple CodeGenerator
    ENHANCED = "enhanced_generator"        # Enhanced single agent
    ORCHESTRATED = "updated_orchestrator" # Enhanced with planning
    MULTI_AGENT = "multi_agent"           # Full multi-agent system

class SystemVersion(str, Enum):
    ORIGINAL = "original"      # Vecchio sistema
    ENHANCED_V2 = "enhanced_v2"  # Nuovo sistema unificato

class RequirementsAnalyzer:
    """
    Analyzes project requirements to determine the appropriate
    generation strategy and agent mode.
    
    🔥 NUOVO: Include sistema di routing tra vecchio e nuovo sistema
    """
    
    def __init__(self):
        # 🔥 NUOVO: Mapping per determinare quale sistema usare
        self.SYSTEM_MAPPING = {
            "original": SystemVersion.ORIGINAL,           # Vecchio sistema
            "enhanced_generator": SystemVersion.ENHANCED_V2,    # Nuovo sistema
            "updated_orchestrator": SystemVersion.ENHANCED_V2, # Nuovo sistema  
            "multi_agent": SystemVersion.ENHANCED_V2           # Nuovo sistema
        }
        
        # 🔥 NUOVO: Configurazione modalità per nuovo sistema
        self.V2_MODE_MAPPING = {
            "enhanced_generator": "enhanced_single",
            "updated_orchestrator": "planning_based", 
            "multi_agent": "collaborative_agents"
        }
        
        logger.info("RequirementsAnalyzer initialized with enhanced routing")
    
    def analyze_project(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes requirements and returns generation strategy.
        
        🔥 NUOVO: Include routing information per sistema da usare
        
        Returns:
            Dict containing:
            - complexity: ProjectComplexity
            - agent_mode: AgentMode
            - system_version: SystemVersion (NUOVO)
            - v2_mode: str (NUOVO - modalità specifica per sistema v2)
            - reasoning: List of reasons for the decision
            - max_iterations: Recommended max iterations
            - features_detected: List of detected features
        """
        
        # Extract project info
        project_type = self._extract_project_type(requirements)
        features_detected = self._detect_features(requirements)
        complexity = self._assess_complexity(requirements, features_detected)
        agent_mode = self._recommend_agent_mode(complexity, features_detected)
        max_iterations = self._recommend_iterations(complexity, agent_mode)
        reasoning = self._generate_reasoning(complexity, features_detected, agent_mode)
        
        # 🔥 NUOVO: Determina quale sistema usare
        system_version = self.SYSTEM_MAPPING[agent_mode.value]
        v2_mode = self.V2_MODE_MAPPING.get(agent_mode.value) if system_version == SystemVersion.ENHANCED_V2 else None
        
        analysis = {
            "project_type": project_type,
            "complexity": complexity,
            "agent_mode": agent_mode,
            "system_version": system_version,  # 🔥 NUOVO
            "v2_mode": v2_mode,               # 🔥 NUOVO
            "max_iterations": max_iterations,
            "features_detected": features_detected,
            "reasoning": reasoning,
            "estimated_files": self._estimate_file_count(complexity, features_detected),
            "estimated_duration": self._estimate_duration(complexity, agent_mode),
            "routing_info": self._get_routing_info(system_version, agent_mode, v2_mode)  # 🔥 NUOVO
        }
        
        logger.info(f"Project analysis: {complexity} complexity, {agent_mode} mode, {system_version} system")
        return analysis
    
    def _extract_project_type(self, requirements: Dict[str, Any]) -> str:
        """Extract the explicit or implicit project type"""
        project = requirements.get("project", {})
        
        # Explicit project type
        if "type" in project:
            return project["type"].lower()
        
        # Infer from structure
        has_backend = "backend" in requirements
        has_frontend = "frontend" in requirements
        has_database = self._has_database(requirements)
        
        if has_backend and has_frontend:
            return "fullstack"
        elif has_backend:
            return "backend"
        elif has_frontend:
            return "frontend"
        else:
            return "unknown"
    
    def _detect_features(self, requirements: Dict[str, Any]) -> List[str]:
        """Detect specific features in the requirements"""
        features = []
        
        # Check for authentication
        if self._has_authentication(requirements):
            features.append("authentication")
        
        # Check for database
        if self._has_database(requirements):
            features.append("database")
        
        # Check for API endpoints
        if self._has_api_endpoints(requirements):
            features.append("api_endpoints")
        
        # Check for external integrations
        if self._has_external_integrations(requirements):
            features.append("external_integrations")
        
        # Check for real-time features
        if self._has_realtime_features(requirements):
            features.append("realtime")
        
        # Check for file uploads
        if self._has_file_uploads(requirements):
            features.append("file_uploads")
        
        # Check for payments
        if self._has_payments(requirements):
            features.append("payments")
        
        # Check for testing requirements
        if self._has_testing_requirements(requirements):
            features.append("comprehensive_testing")
        
        # Check for deployment complexity
        if self._has_complex_deployment(requirements):
            features.append("complex_deployment")
        
        # Check for multiple pages/routes
        if self._has_multiple_pages(requirements):
            features.append("multiple_pages")
        
        # Check for interactive elements
        if self._has_interactive_elements(requirements):
            features.append("interactive_elements")
        
        # Check for SEO/marketing features
        if self._is_marketing_site(requirements):
            features.append("marketing_site")
        
        return features
    
    def _assess_complexity(self, requirements: Dict[str, Any], features: List[str]) -> ProjectComplexity:
        """Assess overall project complexity"""
        
        # Simple: Static sites, landing pages
        if self._is_simple_project(requirements, features):
            return ProjectComplexity.SIMPLE
        
        # Enterprise: Microservices, multiple databases, complex integrations
        if self._is_enterprise_project(requirements, features):
            return ProjectComplexity.ENTERPRISE
        
        # Complex: Full-stack apps with multiple features
        if self._is_complex_project(requirements, features):
            return ProjectComplexity.COMPLEX
        
        # Moderate: Frontend with some backend or interactivity
        return ProjectComplexity.MODERATE
    
    def _recommend_agent_mode(self, complexity: ProjectComplexity, features: List[str]) -> AgentMode:
        """Recommend the appropriate agent mode based on complexity"""
        
        if complexity == ProjectComplexity.SIMPLE:
            # For simple projects, use single agent
            if len(features) <= 2 and "interactive_elements" in features:
                return AgentMode.ENHANCED
            return AgentMode.SINGLE
        
        elif complexity == ProjectComplexity.MODERATE:
            # For moderate projects, use enhanced generator
            if "api_endpoints" in features or "database" in features:
                return AgentMode.ORCHESTRATED
            return AgentMode.ENHANCED
        
        elif complexity == ProjectComplexity.COMPLEX:
            # For complex projects, use multi-agent
            return AgentMode.MULTI_AGENT
        
        elif complexity == ProjectComplexity.ENTERPRISE:
            # For enterprise projects, always use multi-agent
            return AgentMode.MULTI_AGENT
        
        return AgentMode.ENHANCED
    
    def _recommend_iterations(self, complexity: ProjectComplexity, agent_mode: AgentMode) -> int:
        """Recommend maximum iterations based on complexity"""
        
        iteration_map = {
            ProjectComplexity.SIMPLE: {
                AgentMode.SINGLE: 1,
                AgentMode.ENHANCED: 2,
                AgentMode.ORCHESTRATED: 3,
                AgentMode.MULTI_AGENT: 3
            },
            ProjectComplexity.MODERATE: {
                AgentMode.SINGLE: 3,
                AgentMode.ENHANCED: 5,
                AgentMode.ORCHESTRATED: 7,
                AgentMode.MULTI_AGENT: 7
            },
            ProjectComplexity.COMPLEX: {
                AgentMode.SINGLE: 5,
                AgentMode.ENHANCED: 8,
                AgentMode.ORCHESTRATED: 10,
                AgentMode.MULTI_AGENT: 12
            },
            ProjectComplexity.ENTERPRISE: {
                AgentMode.SINGLE: 8,
                AgentMode.ENHANCED: 12,
                AgentMode.ORCHESTRATED: 15,
                AgentMode.MULTI_AGENT: 20
            }
        }
        
        return iteration_map.get(complexity, {}).get(agent_mode, 5)
    
    def _generate_reasoning(self, complexity: ProjectComplexity, 
                          features: List[str], agent_mode: AgentMode) -> List[str]:
        """Generate human-readable reasoning for the decisions"""
        reasoning = []
        
        # Complexity reasoning
        if complexity == ProjectComplexity.SIMPLE:
            reasoning.append("Project identified as simple (static site or landing page)")
        elif complexity == ProjectComplexity.MODERATE:
            reasoning.append("Project has moderate complexity with some dynamic features")
        elif complexity == ProjectComplexity.COMPLEX:
            reasoning.append("Project is complex with full-stack requirements")
        elif complexity == ProjectComplexity.ENTERPRISE:
            reasoning.append("Project has enterprise-level complexity")
        
        # Feature-based reasoning
        if "authentication" in features:
            reasoning.append("Authentication system detected - increases complexity")
        if "database" in features:
            reasoning.append("Database requirements detected")
        if "api_endpoints" in features:
            reasoning.append("API endpoints required")
        if "external_integrations" in features:
            reasoning.append("External service integrations needed")
        if "payments" in features:
            reasoning.append("Payment processing required")
        if "realtime" in features:
            reasoning.append("Real-time features detected")
        
        # Agent mode reasoning
        if agent_mode == AgentMode.SINGLE:
            reasoning.append("Using single agent for simple, focused generation")
        elif agent_mode == AgentMode.ENHANCED:
            reasoning.append("Using enhanced generator for improved quality")
        elif agent_mode == AgentMode.ORCHESTRATED:
            reasoning.append("Using orchestrated approach for complex coordination")
        elif agent_mode == AgentMode.MULTI_AGENT:
            reasoning.append("Using multi-agent system for comprehensive development")
        
        return reasoning
    
    def _estimate_file_count(self, complexity: ProjectComplexity, features: List[str]) -> Dict[str, int]:
        """Estimate number of files that will be generated"""
        base_counts = {
            ProjectComplexity.SIMPLE: {"total": 5, "frontend": 5, "backend": 0, "config": 2},
            ProjectComplexity.MODERATE: {"total": 15, "frontend": 8, "backend": 5, "config": 4},
            ProjectComplexity.COMPLEX: {"total": 40, "frontend": 15, "backend": 20, "config": 8},
            ProjectComplexity.ENTERPRISE: {"total": 80, "frontend": 25, "backend": 45, "config": 15}
        }
        
        base = base_counts.get(complexity, base_counts[ProjectComplexity.MODERATE])
        
        # Adjust based on features
        multiplier = 1.0
        if "authentication" in features:
            multiplier += 0.2
        if "database" in features:
            multiplier += 0.3
        if "external_integrations" in features:
            multiplier += 0.2
        if "payments" in features:
            multiplier += 0.15
        
        return {key: int(value * multiplier) for key, value in base.items()}
    
    def _estimate_duration(self, complexity: ProjectComplexity, agent_mode: AgentMode) -> str:
        """Estimate generation duration"""
        base_times = {
            ProjectComplexity.SIMPLE: {"single": "1-2 min", "enhanced": "2-3 min", "orchestrated": "3-5 min", "multi_agent": "5-8 min"},
            ProjectComplexity.MODERATE: {"single": "3-5 min", "enhanced": "5-8 min", "orchestrated": "8-12 min", "multi_agent": "12-18 min"},
            ProjectComplexity.COMPLEX: {"single": "8-12 min", "enhanced": "12-18 min", "orchestrated": "18-25 min", "multi_agent": "25-35 min"},
            ProjectComplexity.ENTERPRISE: {"single": "15-25 min", "enhanced": "25-35 min", "orchestrated": "35-50 min", "multi_agent": "50-80 min"}
        }
        
        mode_key = agent_mode.value.replace("_", " ").replace("original", "single")
        if "single" in mode_key:
            mode_key = "single"
        elif "enhanced" in mode_key and "orchestrator" not in mode_key:
            mode_key = "enhanced"
        elif "orchestrator" in mode_key:
            mode_key = "orchestrated"
        else:
            mode_key = "multi_agent"
        
        return base_times.get(complexity, base_times[ProjectComplexity.MODERATE]).get(mode_key, "5-10 min")
    
    def _get_routing_info(self, system_version: SystemVersion, agent_mode: AgentMode, v2_mode: str = None) -> Dict[str, Any]:
        """
        🔥 NUOVO: Fornisce informazioni dettagliate sul routing
        """
        routing_info = {
            "system_version": system_version.value,
            "agent_mode": agent_mode.value,
            "should_use_v2": system_version == SystemVersion.ENHANCED_V2,
            "v2_specific_mode": v2_mode
        }
        
        if system_version == SystemVersion.ORIGINAL:
            routing_info.update({
                "service_class": "CodeGenerator",
                "method": "generate_code",
                "task_function": "process_code_generation"
            })
        else:
            routing_info.update({
                "service_class": "EnhancedV2Generator", 
                "method": self._get_v2_method(v2_mode),
                "task_function": "process_enhanced_v2_generation"
            })
        
        return routing_info
    
    def _get_v2_method(self, v2_mode: str) -> str:
        """🔥 NUOVO: Determina il metodo da usare nel sistema v2"""
        method_mapping = {
            "enhanced_single": "generate_with_enhanced_single",
            "planning_based": "generate_with_planning",
            "collaborative_agents": "generate_with_collaborative_agents"
        }
        return method_mapping.get(v2_mode, "generate_default")
    
    # Helper methods for feature detection
    def _has_authentication(self, requirements: Dict[str, Any]) -> bool:
        """Check if project requires authentication"""
        # Check in features
        features = requirements.get("features", [])
        for feature in features:
            if isinstance(feature, dict) and "authentication" in feature:
                return True
        
        # Check in backend API structure
        backend = requirements.get("backend", {})
        api_structure = backend.get("api_structure", [])
        for group in api_structure:
            if isinstance(group, dict) and "authentication" in group:
                return True
        
        # Check for protected pages
        frontend = requirements.get("frontend", {})
        pages = frontend.get("pages", [])
        for page in pages:
            if isinstance(page, dict) and page.get("protected", False):
                return True
        
        return False
    
    def _has_database(self, requirements: Dict[str, Any]) -> bool:
        """Check if project requires a database"""
        # Check in features
        features = requirements.get("features", [])
        for feature in features:
            if isinstance(feature, dict) and "database" in feature:
                return True
        
        # Check in backend
        backend = requirements.get("backend", {})
        if "database" in backend:
            return True
        
        # Check for models
        if "models" in backend:
            return True
        
        return False
    
    def _has_api_endpoints(self, requirements: Dict[str, Any]) -> bool:
        """Check if project requires API endpoints"""
        backend = requirements.get("backend", {})
        
        # Check for explicit API structure
        if "api_structure" in backend:
            api_structure = backend["api_structure"]
            if isinstance(api_structure, list) and len(api_structure) > 0:
                return True
        
        # Check for services that imply APIs
        if "services" in backend:
            return True
        
        # Check project type
        project_type = requirements.get("project", {}).get("type", "")
        if project_type in ["fullstack", "backend"]:
            return True
        
        return False
    
    def _has_external_integrations(self, requirements: Dict[str, Any]) -> bool:
        """Check if project requires external service integrations"""
        # Check for authentication providers other than email
        features = requirements.get("features", [])
        for feature in features:
            if isinstance(feature, dict) and "authentication" in feature:
                auth = feature["authentication"]
                if isinstance(auth, dict) and "providers" in auth:
                    providers = auth["providers"]
                    if any(p not in ["email", "password"] for p in providers):
                        return True
        
        # Check for external services
        backend = requirements.get("backend", {})
        services = backend.get("services", [])
        external_services = ["EmailService", "PaymentService", "StorageService", "NotificationService"]
        
        for service in services:
            if isinstance(service, dict):
                for service_name in service.keys():
                    if any(ext_service in service_name for ext_service in external_services):
                        return True
            elif isinstance(service, str) and any(ext_service in service for ext_service in external_services):
                return True
        
        return False
    
    def _has_realtime_features(self, requirements: Dict[str, Any]) -> bool:
        """Check if project requires real-time features"""
        # Check in frontend
        frontend = requirements.get("frontend", {})
        if frontend.get("real_time", False) or frontend.get("websockets", False):
            return True
        
        # Check in features
        features = requirements.get("features", [])
        for feature in features:
            if isinstance(feature, dict):
                if "real_time" in feature or "realtime" in feature or "websockets" in feature:
                    return True
        
        return False
    
    def _has_file_uploads(self, requirements: Dict[str, Any]) -> bool:
        """Check if project requires file upload functionality"""
        # Check for storage services
        backend = requirements.get("backend", {})
        services = backend.get("services", [])
        
        for service in services:
            if isinstance(service, dict):
                for service_name in service.keys():
                    if "Storage" in service_name or "File" in service_name:
                        return True
            elif isinstance(service, str) and ("storage" in service.lower() or "file" in service.lower()):
                return True
        
        # Check in features
        features = requirements.get("features", [])
        for feature in features:
            if isinstance(feature, dict):
                for key in feature.keys():
                    if "upload" in key.lower() or "file" in key.lower() or "media" in key.lower():
                        return True
        
        return False
    
    def _has_payments(self, requirements: Dict[str, Any]) -> bool:
        """Check if project requires payment processing"""
        # Check in services
        backend = requirements.get("backend", {})
        services = backend.get("services", [])
        
        for service in services:
            if isinstance(service, dict):
                for service_name in service.keys():
                    if "Payment" in service_name or "payment" in service_name:
                        return True
            elif isinstance(service, str) and "payment" in service.lower():
                return True
        
        # Check in features
        features = requirements.get("features", [])
        for feature in features:
            if isinstance(feature, dict):
                for key in feature.keys():
                    if "payment" in key.lower() or "subscription" in key.lower() or "billing" in key.lower():
                        return True
        
        return False
    
    def _has_testing_requirements(self, requirements: Dict[str, Any]) -> bool:
        """Check if project has comprehensive testing requirements"""
        testing = requirements.get("testing", {})
        
        # Check for explicit testing configuration
        if testing:
            # Count testing types
            test_types = 0
            if testing.get("backend", {}) or testing.get("frontend", {}):
                test_types += 1
            if testing.get("e2e_tests", False) or testing.get("integration_tests", False):
                test_types += 1
            if testing.get("performance_tests", False) or testing.get("load_testing", False):
                test_types += 1
            
            return test_types >= 2
        
        return False
    
    def _has_complex_deployment(self, requirements: Dict[str, Any]) -> bool:
        """Check if project has complex deployment requirements"""
        deployment = requirements.get("deployment", {})
        
        # Check for containerization
        if deployment.get("containerization", False):
            return True
        
        # Check for orchestration
        if "orchestration" in deployment or "kubernetes" in str(deployment).lower():
            return True
        
        # Check for multiple environments
        environments = deployment.get("environment", [])
        if isinstance(environments, list) and len(environments) > 2:
            return True
        
        # Check for microservices
        backend = requirements.get("backend", {})
        if backend.get("architecture") == "microservices":
            return True
        
        return False
    
    def _has_multiple_pages(self, requirements: Dict[str, Any]) -> bool:
        """Check if project has multiple pages/routes"""
        frontend = requirements.get("frontend", {})
        pages = frontend.get("pages", [])
        
        # Count pages
        if isinstance(pages, list):
            return len(pages) > 3
        
        # Check for routing in features
        features = requirements.get("features", [])
        for feature in features:
            if isinstance(feature, dict):
                for key in feature.keys():
                    if "routing" in key.lower() or "navigation" in key.lower():
                        return True
        
        return False
    
    def _has_interactive_elements(self, requirements: Dict[str, Any]) -> bool:
        """Check if project has interactive elements"""
        # Check for animations
        design = requirements.get("design", {})
        if design.get("animations", {}).get("enable", False):
            return True
        
        # Check for interactive features
        interactive = requirements.get("interactive_elements", [])
        if interactive:
            return True
        
        # Check frontend interactive elements
        frontend_interactive = requirements.get("frontend_interactive_elements", [])
        if frontend_interactive:
            return True
        
        return False
    
    def _is_marketing_site(self, requirements: Dict[str, Any]) -> bool:
        """Check if this is primarily a marketing/landing site"""
        # Check for SEO section
        if "seo" in requirements:
            return True
        
        # Check for marketing-specific features
        features = requirements.get("features", [])
        marketing_indicators = ["testimonials", "pricing", "hero_section", "cta_section"]
        
        for feature in features:
            if isinstance(feature, dict):
                for key in feature.keys():
                    if any(indicator in key.lower() for indicator in marketing_indicators):
                        return True
        
        # Check project description
        project = requirements.get("project", {})
        description = project.get("description", "").lower()
        if any(word in description for word in ["landing", "marketing", "promotional", "showcase"]):
            return True
        
        return False
    
    def _is_simple_project(self, requirements: Dict[str, Any], features: List[str]) -> bool:
        """Determine if project is simple"""
        project_type = requirements.get("project", {}).get("type", "").lower()
        
        # Explicit simple types
        if project_type in ["static", "landing-page", "static-landing-page"]:
            return True
        
        # Marketing sites with minimal interactivity
        if self._is_marketing_site(requirements) and len(features) <= 3:
            return True
        
        # Frontend-only with no backend features
        if project_type == "frontend" and not any(f in features for f in ["database", "api_endpoints", "authentication"]):
            return True
        
        return False
    
    def _is_enterprise_project(self, requirements: Dict[str, Any], features: List[str]) -> bool:
        """Determine if project is enterprise-level"""
        # Check for microservices
        backend = requirements.get("backend", {})
        if backend.get("architecture") == "microservices":
            return True
        
        # Check for multiple databases
        if "multiple_databases" in features:
            return True
        
        # Check for complex deployment
        if "complex_deployment" in features:
            return True
        
        # High number of features indicates enterprise complexity
        if len(features) >= 8:
            return True
        
        return False
    
    def _is_complex_project(self, requirements: Dict[str, Any], features: List[str]) -> bool:
        """Determine if project is complex"""
        # Full-stack with multiple features
        project_type = requirements.get("project", {}).get("type", "").lower()
        if project_type == "fullstack" and len(features) >= 4:
            return True
        
        # Has database and authentication and more
        required_features = ["database", "authentication", "api_endpoints"]
        if all(f in features for f in required_features):
            return True
        
        # Has external integrations and multiple features
        if "external_integrations" in features and len(features) >= 5:
            return True
        
        return False