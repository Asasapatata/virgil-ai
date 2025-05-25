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
    
    🔥 AGGIORNATO: Logica perfezionata per Enhanced Generator routing
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
        
        🔥 AGGIORNATO: Logica migliorata per Enhanced Generator
        
        Returns:
            Dict containing:
            - complexity: ProjectComplexity
            - agent_mode: AgentMode
            - system_version: SystemVersion
            - v2_mode: str (modalità specifica per sistema v2)
            - reasoning: List of reasons for the decision
            - max_iterations: Recommended max iterations
            - features_detected: List of detected features
        """
        
        # Extract project info
        project_type = self._extract_project_type(requirements)
        features_detected = self._detect_features(requirements)
        complexity = self._assess_complexity(requirements, features_detected)
        agent_mode = self._recommend_agent_mode(complexity, features_detected, requirements)
        max_iterations = self._recommend_iterations(complexity, agent_mode)
        reasoning = self._generate_reasoning(complexity, features_detected, agent_mode, requirements)
        
        # 🔥 NUOVO: Determina quale sistema usare
        system_version = self.SYSTEM_MAPPING[agent_mode.value]
        v2_mode = self.V2_MODE_MAPPING.get(agent_mode.value) if system_version == SystemVersion.ENHANCED_V2 else None
        
        analysis = {
            "project_type": project_type,
            "complexity": complexity,
            "agent_mode": agent_mode,
            "system_version": system_version,
            "v2_mode": v2_mode,
            "max_iterations": max_iterations,
            "features_detected": features_detected,
            "reasoning": reasoning,
            "estimated_files": self._estimate_file_count(complexity, features_detected),
            "estimated_duration": self._estimate_duration(complexity, agent_mode),
            "routing_info": self._get_routing_info(system_version, agent_mode, v2_mode),
            "is_standard_stack": self._is_standard_tech_stack(requirements.get("tech_stack", {}))
        }
        
        logger.info(f"Project analysis: {complexity} complexity, {agent_mode} mode, {system_version} system")
        logger.info(f"Features: {len(features_detected)} detected - {', '.join(features_detected[:5])}")
        
        return analysis
    
    def _recommend_agent_mode(self, 
                            complexity: ProjectComplexity, 
                            features: List[str], 
                            requirements: Dict[str, Any]) -> AgentMode:
        """
        🔥 AGGIORNATO: Logica perfezionata per raccomandazione agent mode
        
        Questa è la logica che determina perché NovaPLM usa enhanced_generator!
        """
        
        feature_count = len(features)
        tech_stack = requirements.get("tech_stack", {})
        is_standard_stack = self._is_standard_tech_stack(tech_stack)
        
        logger.info(f"Agent mode decision: complexity={complexity}, features={feature_count}, standard_stack={is_standard_stack}")
        
        if complexity == ProjectComplexity.SIMPLE:
            # Per progetti semplici
            if feature_count <= 2:
                return AgentMode.SINGLE
            else:
                return AgentMode.ENHANCED
        
        elif complexity == ProjectComplexity.MODERATE:
            # 🎯 QUI: La logica per NovaPLM
            
            # Se ha DB + API ed è uno stack standard, usa enhanced_generator
            has_database = "database" in features
            has_api = "api_endpoints" in features
            
            if has_database and has_api and is_standard_stack and feature_count <= 6:
                logger.info(f"Selecting enhanced_generator: standard stack ({tech_stack}) with {feature_count} features")
                return AgentMode.ENHANCED  # ✅ NovaPLM finisce qui
            
            # Altrimenti usa orchestrator
            elif has_database or has_api or feature_count > 4:
                return AgentMode.ORCHESTRATED
            
            # Default per moderate
            return AgentMode.ENHANCED
        
        elif complexity == ProjectComplexity.COMPLEX:
            # Per progetti complessi
            if feature_count > 8 or not is_standard_stack:
                return AgentMode.MULTI_AGENT
            else:
                return AgentMode.ORCHESTRATED
        
        elif complexity == ProjectComplexity.ENTERPRISE:
            # Per progetti enterprise, sempre multi-agent
            return AgentMode.MULTI_AGENT
        
        # Default safe choice
        return AgentMode.ENHANCED
    
    def _is_standard_tech_stack(self, tech_stack: Dict[str, Any]) -> bool:
        """
        🔥 AGGIORNATO: Verifica se il tech stack è standard e ben supportato
        
        Questa funzione determina se NovaPLM ha uno stack "standard"!
        """
        if not tech_stack:
            return True
        
        # Normalize values for comparison
        frontend = str(tech_stack.get("frontend", "")).lower()
        backend = str(tech_stack.get("backend", "")).lower()
        database = str(tech_stack.get("database", "")).lower()
        
        # Standard frontend frameworks
        standard_frontends = ["react", "vue", "angular", "nextjs", "nuxt"]
        frontend_is_standard = any(f in frontend for f in standard_frontends)
        
        # Standard backend frameworks  
        standard_backends = ["node.js", "node", "express", "fastapi", "django", "flask", "python"]
        backend_is_standard = any(b in backend for b in standard_backends)
        
        # Standard databases
        standard_databases = ["postgresql", "postgres", "mysql", "sqlite", "mongodb", "mongo"]
        database_is_standard = any(d in database for d in standard_databases) if database else True
        
        # 🎯 CONDIZIONE: Stack è standard se frontend E backend sono standard
        is_standard = frontend_is_standard and backend_is_standard and database_is_standard
        
        logger.info(f"Tech stack analysis: frontend={frontend}({frontend_is_standard}), backend={backend}({backend_is_standard}), db={database}({database_is_standard}) → standard={is_standard}")
        
        return is_standard
    
    def _generate_reasoning(self, 
                          complexity: ProjectComplexity, 
                          features: List[str], 
                          agent_mode: AgentMode,
                          requirements: Dict[str, Any]) -> List[str]:
        """
        🔥 AGGIORNATO: Reasoning più dettagliato
        """
        reasoning = []
        
        # Complexity reasoning
        feature_count = len(features)
        if complexity == ProjectComplexity.SIMPLE:
            reasoning.append(f"Project identified as simple ({feature_count} features, basic functionality)")
        elif complexity == ProjectComplexity.MODERATE:
            reasoning.append(f"Project has moderate complexity ({feature_count} features, standard business app)")
        elif complexity == ProjectComplexity.COMPLEX:
            reasoning.append(f"Project is complex ({feature_count} features, advanced integrations)")
        elif complexity == ProjectComplexity.ENTERPRISE:
            reasoning.append(f"Project has enterprise-level complexity ({feature_count}+ features)")
        
        # Tech stack reasoning
        tech_stack = requirements.get("tech_stack", {})
        if self._is_standard_tech_stack(tech_stack):
            stack_desc = f"{tech_stack.get('frontend', 'Unknown')} + {tech_stack.get('backend', 'Unknown')}"
            reasoning.append(f"Standard technology stack detected: {stack_desc}")
        else:
            reasoning.append("Non-standard or complex technology stack")
        
        # Feature-based reasoning
        key_features = ["authentication", "database", "api_endpoints", "external_integrations", "payments"]
        detected_key_features = [f for f in key_features if f in features]
        if detected_key_features:
            reasoning.append(f"Key features detected: {', '.join(detected_key_features)}")
        
        # Agent mode reasoning con più dettagli
        if agent_mode == AgentMode.SINGLE:
            reasoning.append("Using original single agent for simple, focused generation")
        elif agent_mode == AgentMode.ENHANCED:
            reasoning.append(f"Using enhanced generator: optimal for {feature_count} features with standard stack")
        elif agent_mode == AgentMode.ORCHESTRATED:
            reasoning.append("Using orchestrated approach for complex coordination needs")
        elif agent_mode == AgentMode.MULTI_AGENT:
            reasoning.append("Using multi-agent system for comprehensive enterprise development")
        
        # 🔥 NUOVO: Reasoning specifico per Enhanced Generator
        if agent_mode == AgentMode.ENHANCED:
            reasoning.append(f"Enhanced Generator chosen: efficient single-agent with quality validation")
            reasoning.append(f"Expected generation time: 3-8 minutes (vs 15-60 for multi-agent)")
        
        return reasoning
    
    def _extract_project_type(self, requirements: Dict[str, Any]) -> str:
        """Extract the explicit or implicit project type"""
        project = requirements.get("project", {})
        
        # Explicit project type
        if "type" in project:
            return project["type"].lower()
        
        # Infer from structure
        has_backend = "backend" in requirements or "tech_stack" in requirements and "backend" in requirements["tech_stack"]
        has_frontend = "frontend" in requirements or "tech_stack" in requirements and "frontend" in requirements["tech_stack"]
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
        """
        🔥 AGGIORNATO: Valutazione complessità più precisa
        """
        feature_count = len(features)
        tech_stack = requirements.get("tech_stack", {})
        
        # Simple: Static sites, landing pages
        if self._is_simple_project(requirements, features):
            return ProjectComplexity.SIMPLE
        
        # Enterprise: Microservices, multiple databases, complex integrations
        if self._is_enterprise_project(requirements, features):
            return ProjectComplexity.ENTERPRISE
        
        # Complex: Full-stack apps with multiple features
        if self._is_complex_project(requirements, features):
            return ProjectComplexity.COMPLEX
        
        # 🎯 MODERATE: Qui finisce NovaPLM
        # - Ha 5 features (auth, database, api, pages, uploads)  
        # - È fullstack ma non troppo complesso
        # - Stack standard (React + Node + PostgreSQL)
        return ProjectComplexity.MODERATE
    
    def _recommend_iterations(self, complexity: ProjectComplexity, agent_mode: AgentMode) -> int:
        """
        🔥 AGGIORNATO: Iterazioni raccomandate più precise
        """
        
        iteration_map = {
            ProjectComplexity.SIMPLE: {
                AgentMode.SINGLE: 1,
                AgentMode.ENHANCED: 2,
                AgentMode.ORCHESTRATED: 3,
                AgentMode.MULTI_AGENT: 3
            },
            ProjectComplexity.MODERATE: {
                AgentMode.SINGLE: 3,
                AgentMode.ENHANCED: 4,  # 🎯 NovaPLM: 4 iterations per enhanced_generator
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
    
    def _estimate_file_count(self, complexity: ProjectComplexity, features: List[str]) -> Dict[str, int]:
        """Estimate number of files that will be generated"""
        base_counts = {
            ProjectComplexity.SIMPLE: {"total": 5, "frontend": 5, "backend": 0, "config": 2},
            ProjectComplexity.MODERATE: {"total": 20, "frontend": 10, "backend": 8, "config": 5},  # 🎯 NovaPLM
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
        """
        🔥 AGGIORNATO: Stime durata più accurate
        """
        base_times = {
            ProjectComplexity.SIMPLE: {
                "single": "1-2 min", 
                "enhanced": "2-3 min", 
                "orchestrated": "3-5 min", 
                "multi_agent": "5-8 min"
            },
            ProjectComplexity.MODERATE: {
                "single": "3-5 min", 
                "enhanced": "3-8 min",  # 🎯 NovaPLM: tempo ottimale
                "orchestrated": "8-12 min", 
                "multi_agent": "12-18 min"
            },
            ProjectComplexity.COMPLEX: {
                "single": "8-12 min", 
                "enhanced": "12-18 min", 
                "orchestrated": "18-25 min", 
                "multi_agent": "25-35 min"
            },
            ProjectComplexity.ENTERPRISE: {
                "single": "15-25 min", 
                "enhanced": "25-35 min", 
                "orchestrated": "35-50 min", 
                "multi_agent": "50-80 min"
            }
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
        🔥 AGGIORNATO: Informazioni dettagliate sul routing
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
                "service_class": "EnhancedV2System", 
                "method": self._get_v2_method(v2_mode),
                "task_function": "process_enhanced_code_generation"
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
    
    # Helper methods for feature detection (mantengo quelli esistenti)
    def _has_authentication(self, requirements: Dict[str, Any]) -> bool:
        """Check if project requires authentication"""
        # Check in features
        features = requirements.get("features", [])
        for feature in features:
            if isinstance(feature, dict):
                # Check for auth-related keys
                auth_keys = ["authentication", "login", "auth", "user"]
                if any(key in feature for key in auth_keys):
                    return True
                # Check nested content
                for value in feature.values():
                    if isinstance(value, (str, dict)) and any(key in str(value).lower() for key in auth_keys):
                        return True
        
        # Check in security section
        security = requirements.get("security", [])
        for item in security:
            if "authentication" in str(item).lower() or "jwt" in str(item).lower():
                return True
        
        return False
    
    def _has_database(self, requirements: Dict[str, Any]) -> bool:
        """Check if project requires a database"""
        # Check tech stack
        tech_stack = requirements.get("tech_stack", {})
        if "database" in tech_stack:
            return True
        
        # Check database schema
        if "database_schema" in requirements:
            return True
        
        # Check features for data persistence
        features = requirements.get("features", [])
        for feature in features:
            if isinstance(feature, dict):
                # Look for database-related terms
                db_terms = ["database", "storage", "persist", "save", "store"]
                if any(term in str(feature).lower() for term in db_terms):
                    return True
        
        return False
    
    def _has_api_endpoints(self, requirements: Dict[str, Any]) -> bool:
        """Check if project requires API endpoints"""
        # Check tech stack
        tech_stack = requirements.get("tech_stack", {})
        if "api" in tech_stack:
            return True
        
        # Check project type
        project_type = requirements.get("project", {}).get("type", "")
        if project_type in ["fullstack", "backend"]:
            return True
        
        # Check for backend presence
        if "backend" in tech_stack:
            return True
        
        return False
    
    def _has_external_integrations(self, requirements: Dict[str, Any]) -> bool:
        """Check if project requires external service integrations"""
        # Check features for external services
        features = requirements.get("features", [])
        external_terms = ["external", "api", "integration", "service", "third-party", "payment", "email"]
        
        for feature in features:
            if isinstance(feature, dict):
                if any(term in str(feature).lower() for term in external_terms):
                    return True
        
        return False
    
    def _has_realtime_features(self, requirements: Dict[str, Any]) -> bool:
        """Check if project requires real-time features"""
        features = requirements.get("features", [])
        realtime_terms = ["real-time", "realtime", "websocket", "live", "instant"]
        
        for feature in features:
            if isinstance(feature, dict):
                if any(term in str(feature).lower() for term in realtime_terms):
                    return True
        
        return False
    
    def _has_file_uploads(self, requirements: Dict[str, Any]) -> bool:
        """Check if project requires file upload functionality"""
        features = requirements.get("features", [])
        upload_terms = ["upload", "file", "image", "document", "media", "attachment"]
        
        for feature in features:
            if isinstance(feature, dict):
                if any(term in str(feature).lower() for term in upload_terms):
                    return True
                    
        # 🎯 SPECIAL: Check for "Gestione Documentazione" in NovaPLM
        for feature in features:
            if isinstance(feature, dict):
                for key, value in feature.items():
                    if "documentazione" in key.lower() or "upload" in str(value).lower():
                        return True
        
        return False
    
    def _has_payments(self, requirements: Dict[str, Any]) -> bool:
        """Check if project requires payment processing"""
        features = requirements.get("features", [])
        payment_terms = ["payment", "billing", "subscription", "checkout", "purchase"]
        
        for feature in features:
            if isinstance(feature, dict):
                if any(term in str(feature).lower() for term in payment_terms):
                    return True
        
        return False
    
    def _has_testing_requirements(self, requirements: Dict[str, Any]) -> bool:
        """Check if project has comprehensive testing requirements"""
        return "testing" in requirements and bool(requirements["testing"])
    
    def _has_complex_deployment(self, requirements: Dict[str, Any]) -> bool:
        """Check if project has complex deployment requirements"""
        deployment = requirements.get("deployment", {})
        
        # Check for containerization
        if "docker" in str(deployment).lower() or "container" in str(deployment).lower():
            return True
        
        return False
    
    def _has_multiple_pages(self, requirements: Dict[str, Any]) -> bool:
        """Check if project has multiple pages/routes"""
        features = requirements.get("features", [])
        
        # Count features that imply pages
        page_features = 0
        for feature in features:
            if isinstance(feature, dict):
                for key in feature.keys():
                    page_indicators = ["page", "dashboard", "login", "home", "gestione"]
                    if any(indicator in key.lower() for indicator in page_indicators):
                        page_features += 1
        
        return page_features > 2
    
    def _has_interactive_elements(self, requirements: Dict[str, Any]) -> bool:
        """Check if project has interactive elements"""
        features = requirements.get("features", [])
        interactive_terms = ["interactive", "animation", "dynamic", "form", "button", "workflow"]
        
        for feature in features:
            if isinstance(feature, dict):
                if any(term in str(feature).lower() for term in interactive_terms):
                    return True
        
        return False
    
    def _is_marketing_site(self, requirements: Dict[str, Any]) -> bool:
        """Check if this is primarily a marketing/landing site"""
        project = requirements.get("project", {})
        description = project.get("description", "").lower()
        
        marketing_terms = ["landing", "marketing", "promotional", "showcase", "informativa"]
        return any(term in description for term in marketing_terms)
    
    def _is_simple_project(self, requirements: Dict[str, Any], features: List[str]) -> bool:
        """Determine if project is simple"""
        project_type = requirements.get("project", {}).get("type", "").lower()
        
        # Explicit simple types
        if project_type in ["static", "landing-page", "static-landing-page"]:
            return True
        
        # Marketing sites with minimal features
        if self._is_marketing_site(requirements) and len(features) <= 2:
            return True
        
        return False
    
    def _is_enterprise_project(self, requirements: Dict[str, Any], features: List[str]) -> bool:
        """Determine if project is enterprise-level"""
        # High number of features
        if len(features) >= 10:
            return True
        
        # Check for enterprise indicators
        enterprise_features = ["complex_deployment", "external_integrations", "comprehensive_testing"]
        if sum(1 for f in enterprise_features if f in features) >= 2:
            return True
        
        return False
    
    def _is_complex_project(self, requirements: Dict[str, Any], features: List[str]) -> bool:
        """Determine if project is complex"""
        # Check for complex indicators
        if len(features) >= 7:
            return True
        
        # Has multiple advanced features
        advanced_features = ["payments", "realtime", "external_integrations", "complex_deployment"]
        advanced_count = sum(1 for f in advanced_features if f in features)
        
        if advanced_count >= 2:
            return True
        
        return False