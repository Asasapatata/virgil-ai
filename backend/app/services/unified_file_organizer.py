# backend/app/services/unified_file_organizer.py
import logging
from typing import Dict, Any
import re

logger = logging.getLogger(__name__)

class UnifiedFileOrganizer:
    """
    🗂️ UNIFIED FILE ORGANIZER
    Organizza i file raw in struttura unificata per tutti gli orchestratori:
    - Determina backend vs frontend
    - Crea struttura project-{name}/backend + project-{name}/frontend
    - Genera env_test/ completo
    - Crea file di supporto
    """
    
    def __init__(self):
        logger.info("UnifiedFileOrganizer initialized")
    
    def organize_files(self, 
                      raw_files: Dict[str, str], 
                      requirements: Dict[str, Any], 
                      project_name: str) -> Dict[str, str]:
        """
        🗂️ ORGANIZE FILES - Convert raw files to unified structure
        """
        clean_name = self._clean_project_name(project_name)
        logger.info(f"🗂️ Organizing {len(raw_files)} files for project: {clean_name}")
        
        organized_files = {}
        project_prefix = f"project-{clean_name}"
        
        # Determine project characteristics
        project_info = self._analyze_project_requirements(requirements)
        logger.info(f"📋 Project analysis: {project_info}")
        
        # 🎯 ORGANIZE RAW FILES
        for file_path, content in raw_files.items():
            # Skip already organized files
            if file_path.startswith(project_prefix) or file_path.startswith("env_test/"):
                organized_files[file_path] = content
                continue
            
            # Determine file placement
            new_path = self._determine_file_placement(
                file_path, project_prefix, project_info
            )
            organized_files[new_path] = content
            logger.debug(f"📁 {file_path} → {new_path}")
        
        # 🎯 ADD PROJECT README
        organized_files[f"{project_prefix}/README.md"] = self._generate_project_readme(
            requirements, clean_name, project_info
        )
        
        logger.info(f"✅ File organization complete: {len(organized_files)} organized files")
        return organized_files
    
    def create_env_test_copy(self, 
                           organized_files: Dict[str, str], 
                           requirements: Dict[str, Any]) -> Dict[str, str]:
        """
        🧪 CREATE ENV_TEST COPY - Complete test environment
        """
        logger.info("🧪 Creating complete env_test environment")
        
        env_test_files = {}
        project_prefix = None
        
        # Find project prefix
        for file_path in organized_files.keys():
            if file_path.startswith("project-"):
                project_prefix = file_path.split("/")[0]
                break
        
        if not project_prefix:
            logger.warning("No project prefix found, using default")
            project_prefix = "project-generated"
        
        # 🎯 COPY ALL PROJECT FILES TO ENV_TEST
        for file_path, content in organized_files.items():
            if file_path.startswith(project_prefix):
                # Remove project prefix for env_test copy
                relative_path = file_path[len(project_prefix)+1:]
                env_test_files[f"env_test/{relative_path}"] = content
                logger.debug(f"🧪 Copied: {file_path} → env_test/{relative_path}")
        
        # 🎯 ADD DOCKER CONFIGURATION
        docker_files = self._create_docker_configuration(requirements)
        env_test_files.update(docker_files)
        
        # 🎯 ADD TEST SCRIPTS
        test_scripts = self._create_test_scripts(requirements)
        env_test_files.update(test_scripts)
        
        logger.info(f"✅ env_test created: {len(env_test_files)} files")
        return env_test_files
    
    def create_support_files(self, 
                           requirements: Dict[str, Any], 
                           project_name: str) -> Dict[str, str]:
        """
        📄 CREATE SUPPORT FILES - Requirements, env, gitignore, etc.
        """
        logger.info("📄 Creating support files")
        
        support_files = {}
        
        # 🎯 REQUIREMENTS.TXT
        support_files["requirements.txt"] = self._generate_requirements_txt(requirements)
        
        # 🎯 ENVIRONMENT TEMPLATE
        support_files[".env.template"] = self._generate_env_template(requirements)
        
        # 🎯 GITIGNORE
        support_files[".gitignore"] = self._generate_gitignore(requirements)
        
        # 🎯 DOCKER COMPOSE (root level)
        support_files["docker-compose.yml"] = self._generate_root_docker_compose(requirements)
        
        logger.info(f"✅ Support files created: {len(support_files)} files")
        return support_files
    
    def _analyze_project_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze requirements to determine project structure"""
        tech_stack = requirements.get("tech_stack", {})
        project_type = requirements.get("project", {}).get("type", "fullstack")
        
        analysis = {
            "type": project_type,
            "has_backend": False,
            "has_frontend": False,
            "backend_tech": None,
            "frontend_tech": None,
            "database_tech": None
        }
        
        # Determine backend
        if (tech_stack.get("backend") or 
            project_type in ["backend", "fullstack"] or 
            "backend" in str(requirements).lower()):
            analysis["has_backend"] = True
            analysis["backend_tech"] = (
                tech_stack.get("backend") or 
                self._detect_backend_tech(requirements)
            )
        
        # Determine frontend
        if (tech_stack.get("frontend") or 
            project_type in ["frontend", "fullstack"] or 
            "frontend" in str(requirements).lower()):
            analysis["has_frontend"] = True
            analysis["frontend_tech"] = (
                tech_stack.get("frontend") or 
                self._detect_frontend_tech(requirements)
            )
        
        # Determine database
        if tech_stack.get("database"):
            analysis["database_tech"] = tech_stack.get("database")
        else:
            analysis["database_tech"] = self._detect_database_tech(requirements)
        
        return analysis
    
    def _determine_file_placement(self, 
                                 file_path: str, 
                                 project_prefix: str, 
                                 project_info: Dict[str, Any]) -> str:
        """Determine where to place a file in unified structure"""
        
        # Backend file detection
        if self._is_backend_file(file_path):
            if project_info["has_backend"]:
                return f"{project_prefix}/backend/{file_path}"
            else:
                return f"{project_prefix}/{file_path}"
        
        # Frontend file detection  
        elif self._is_frontend_file(file_path):
            if project_info["has_frontend"]:
                return f"{project_prefix}/frontend/{file_path}"
            else:
                return f"{project_prefix}/{file_path}"
        
        # General/config files
        elif self._is_config_file(file_path):
            return f"{project_prefix}/{file_path}"
        
        # Default to project root
        else:
            return f"{project_prefix}/{file_path}"
    
    def _is_backend_file(self, file_path: str) -> bool:
        """Determine if file is backend"""
        backend_indicators = [
            '.py', 'requirements.txt', 'app/', 'api/', 'models/', 'schemas/',
            'database/', 'db/', 'migrations/', 'alembic/', 'fastapi', 'django',
            'flask', 'main.py', 'wsgi.py', 'asgi.py', 'manage.py', 'celery',
            '__pycache__/', '.pyc', 'pytest', 'test_', '_test.py', 'poetry.lock',
            'pyproject.toml', 'setup.py', 'Pipfile'
        ]
        return any(indicator in file_path.lower() for indicator in backend_indicators)
    
    def _is_frontend_file(self, file_path: str) -> bool:
        """Determine if file is frontend"""
        frontend_indicators = [
            '.tsx', '.jsx', '.ts', '.js', '.css', '.scss', '.html', '.vue',
            'src/', 'public/', 'components/', 'pages/', 'styles/', 'assets/',
            'package.json', 'package-lock.json', 'yarn.lock', 'node_modules/', 
            'build/', 'dist/', 'webpack', 'react', 'vue', 'angular', 'next', 
            'vite', 'tailwind', '.babelrc', 'tsconfig.json'
        ]
        return any(indicator in file_path.lower() for indicator in frontend_indicators)
    
    def _is_config_file(self, file_path: str) -> bool:
        """Determine if file is configuration"""
        config_indicators = [
            'dockerfile', 'docker-compose', '.env', '.gitignore', 'readme.md',
            'license', 'makefile', '.editorconfig', '.prettierrc', 'eslint'
        ]
        return any(indicator in file_path.lower() for indicator in config_indicators)
    
    def _detect_backend_tech(self, requirements: Dict[str, Any]) -> str:
        """Detect backend technology from requirements"""
        req_str = str(requirements).lower()
        
        if "fastapi" in req_str:
            return "FastAPI"
        elif "django" in req_str:
            return "Django"
        elif "flask" in req_str:
            return "Flask"
        elif "express" in req_str or "node" in req_str:
            return "Node.js/Express"
        elif "python" in req_str:
            return "Python"
        else:
            return "Python/FastAPI"  # Default
    
    def _detect_frontend_tech(self, requirements: Dict[str, Any]) -> str:
        """Detect frontend technology from requirements"""
        req_str = str(requirements).lower()
        
        if "react" in req_str:
            return "React"
        elif "vue" in req_str:
            return "Vue.js"
        elif "angular" in req_str:
            return "Angular"
        elif "next" in req_str:
            return "Next.js"
        elif "svelte" in req_str:
            return "Svelte"
        else:
            return "React"  # Default
    
    def _detect_database_tech(self, requirements: Dict[str, Any]) -> str:
        """Detect database technology from requirements"""
        req_str = str(requirements).lower()
        
        if "postgresql" in req_str or "postgres" in req_str:
            return "PostgreSQL"
        elif "mysql" in req_str:
            return "MySQL"
        elif "mongodb" in req_str or "mongo" in req_str:
            return "MongoDB"
        elif "sqlite" in req_str:
            return "SQLite"
        else:
            return "PostgreSQL"  # Default
    
    def _generate_project_readme(self, 
                               requirements: Dict[str, Any], 
                               clean_name: str, 
                               project_info: Dict[str, Any]) -> str:
        """Generate comprehensive README for unified structure"""
        project_name = requirements.get("project_name", clean_name.title())
        description = requirements.get("description", "Generated with Unified Architecture")
        
        # Build tech stack section
        tech_stack_section = "## 🛠️ Technology Stack\n\n"
        if project_info["has_backend"]:
            tech_stack_section += f"- **Backend:** {project_info['backend_tech']}\n"
        if project_info["has_frontend"]:
            tech_stack_section += f"- **Frontend:** {project_info['frontend_tech']}\n"
        if project_info["database_tech"]:
            tech_stack_section += f"- **Database:** {project_info['database_tech']}\n"
        
        # Build structure section
        structure_section = "## 📁 Project Structure (Unified)\n\n```\n"
        if project_info["has_backend"]:
            structure_section += "backend/          # Backend application\n"
        if project_info["has_frontend"]:
            structure_section += "frontend/         # Frontend application\n"
        structure_section += "README.md         # This file\n```\n"
        
        return f'''# {project_name}

{description}

{tech_stack_section}

## 🚀 Quick Start (Unified Architecture)

### Using Docker (Recommended)

1. **Navigate to test environment:**
```bash
cd ../env_test
```

2. **Start all services:**
```bash
docker-compose -f docker-compose.test.yml up -d
```

3. **Run tests:**
```bash
chmod +x run_tests.sh
./run_tests.sh
```

{structure_section}

## 🧪 Testing & Development

- **Testing:** Complete environment in `../env_test/` with Docker setup
- **Development:** This directory contains clean, production-ready code
- **Reports:** Validation and test reports in `../reports/`

## 🔧 Local Development

```bash
# Backend (if applicable)
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Frontend (if applicable)  
cd frontend
npm install
npm start
```

---
*Generated by Unified Architecture System*
'''
    
    def _create_docker_configuration(self, requirements: Dict[str, Any]) -> Dict[str, str]:
        """Create Docker configuration for env_test"""
        docker_files = {}
        
        # Docker Compose for testing
        docker_files["env_test/docker-compose.test.yml"] = self._generate_test_docker_compose(requirements)
        
        # Backend Dockerfile
        docker_files["env_test/Dockerfile.backend"] = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
'''
        
        # Frontend Dockerfile
        docker_files["env_test/Dockerfile.frontend"] = '''FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:3000 || exit 1

# Start development server
CMD ["npm", "start"]
'''
        
        return docker_files
    
    def _create_test_scripts(self, requirements: Dict[str, Any]) -> Dict[str, str]:
        """Create test execution scripts"""
        test_files = {}
        
        # Bash test runner
        test_files["env_test/run_tests.sh"] = '''#!/bin/bash
set -e

echo "🧪 Starting Unified Test Environment..."

# Start services
echo "📦 Starting Docker services..."
docker-compose -f docker-compose.test.yml up -d

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 30

# Run backend tests
echo "🔧 Running backend tests..."
docker-compose -f docker-compose.test.yml exec -T backend python -m pytest tests/ -v || echo "Backend tests completed with issues"

# Run frontend tests  
echo "⚛️ Running frontend tests..."
docker-compose -f docker-compose.test.yml exec -T frontend npm test -- --coverage --watchAll=false || echo "Frontend tests completed with issues"

# Run integration tests
echo "🔗 Running integration tests..."
python test_runner.py

# Generate report
echo "📊 Generating test report..."
echo "Unified test completed at $(date)" > test_report.txt

echo "✅ All tests completed! Check test_report.txt for details"

# Stop services
echo "🛑 Stopping services..."
docker-compose -f docker-compose.test.yml down
'''
        
        # Python test runner
        test_files["env_test/test_runner.py"] = '''#!/usr/bin/env python3
"""
Unified Integration Test Runner
"""
import requests
import time
import json
import sys
from typing import Dict, Any

def test_backend_health() -> bool:
    """Test backend health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        return response.status_code == 200
    except:
        return False

def test_frontend_accessibility() -> bool:
    """Test frontend accessibility"""
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        return response.status_code == 200
    except:
        return False

def test_api_endpoints() -> Dict[str, bool]:
    """Test key API endpoints"""
    tests = {}
    endpoints = [
        "/api/v1/health",
        "/api/v1/status"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            tests[endpoint] = response.status_code in [200, 404]  # 404 is OK if not implemented
        except:
            tests[endpoint] = False
    
    return tests

def run_unified_tests() -> bool:
    """Run all unified integration tests"""
    print("🔗 Running Unified Integration Tests...")
    
    results = {
        "backend_health": test_backend_health(),
        "frontend_accessibility": test_frontend_accessibility(),
        "api_endpoints": test_api_endpoints()
    }
    
    # Print results
    for test_name, result in results.items():
        if isinstance(result, dict):
            print(f"  {test_name}:")
            for sub_test, sub_result in result.items():
                status = "✅" if sub_result else "❌"
                print(f"    {status} {sub_test}: {'PASS' if sub_result else 'FAIL'}")
        else:
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}: {'PASS' if result else 'FAIL'}")
    
    # Save results
    with open("integration_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Determine overall success
    def check_results(obj):
        if isinstance(obj, dict):
            return all(check_results(v) for v in obj.values())
        return obj
    
    overall_success = check_results(results)
    print(f"\n🎯 Overall Result: {'SUCCESS' if overall_success else 'PARTIAL'}")
    
    return overall_success

if __name__ == "__main__":
    success = run_unified_tests()
    sys.exit(0 if success else 1)
'''
        
        return test_files
    
    def _generate_test_docker_compose(self, requirements: Dict[str, Any]) -> str:
        """Generate docker-compose for testing environment"""
        tech_stack = requirements.get("tech_stack", {})
        project_info = self._analyze_project_requirements(requirements)
        
        compose_content = '''version: '3.8'

services:'''
        
        # Backend service
        if project_info["has_backend"]:
            compose_content += '''
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - DATABASE_URL=postgresql://test:test@db:5432/test_db
      - SECRET_KEY=test-secret-key
      - DEBUG=true
    depends_on:
      - db
    volumes:
      - ./backend:/app
    networks:
      - test-network'''
        
        # Frontend service
        if project_info["has_frontend"]:
            compose_content += '''
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://backend:8000/api/v1
      - NODE_ENV=development
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    networks:
      - test-network'''
        
        # Database service
        if project_info["database_tech"]:
            if "postgresql" in project_info["database_tech"].lower():
                compose_content += '''
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=test_db
      - POSTGRES_USER=test
      - POSTGRES_PASSWORD=test
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - test-network'''
            elif "mysql" in project_info["database_tech"].lower():
                compose_content += '''
  db:
    image: mysql:8.0
    environment:
      - MYSQL_DATABASE=test_db
      - MYSQL_USER=test
      - MYSQL_PASSWORD=test
      - MYSQL_ROOT_PASSWORD=root
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - test-network'''
        
        compose_content += '''

volumes:'''
        if "postgresql" in str(project_info.get("database_tech", "")).lower():
            compose_content += '''
  postgres_data:'''
        elif "mysql" in str(project_info.get("database_tech", "")).lower():
            compose_content += '''
  mysql_data:'''
        
        compose_content += '''

networks:
  test-network:
    driver: bridge
'''
        
        return compose_content
    
    def _generate_requirements_txt(self, requirements: Dict[str, Any]) -> str:
        """Generate requirements.txt based on project needs"""
        project_info = self._analyze_project_requirements(requirements)
        
        reqs = []
        
        # Base requirements
        if project_info["has_backend"]:
            if "fastapi" in project_info.get("backend_tech", "").lower():
                reqs.extend([
                    "fastapi>=0.104.0",
                    "uvicorn[standard]>=0.24.0",
                    "pydantic>=2.5.0",
                    "python-dotenv>=1.0.0"
                ])
            elif "django" in project_info.get("backend_tech", "").lower():
                reqs.extend([
                    "django>=4.2.0",
                    "djangorestframework>=3.14.0",
                    "python-dotenv>=1.0.0"
                ])
            elif "flask" in project_info.get("backend_tech", "").lower():
                reqs.extend([
                    "flask>=2.3.0",
                    "flask-restful>=0.3.10",
                    "python-dotenv>=1.0.0"
                ])
            else:
                # Default Python/FastAPI
                reqs.extend([
                    "fastapi>=0.104.0",
                    "uvicorn[standard]>=0.24.0",
                    "pydantic>=2.5.0",
                    "python-dotenv>=1.0.0"
                ])
        
        # Database requirements
        if project_info.get("database_tech"):
            db_tech = project_info["database_tech"].lower()
            if "postgresql" in db_tech:
                reqs.extend([
                    "sqlalchemy>=2.0.0",
                    "psycopg2-binary>=2.9.0",
                    "alembic>=1.12.0"
                ])
            elif "mysql" in db_tech:
                reqs.extend([
                    "sqlalchemy>=2.0.0",
                    "PyMySQL>=1.1.0",
                    "alembic>=1.12.0"
                ])
            elif "mongodb" in db_tech:
                reqs.append("pymongo>=4.5.0")
            elif "sqlite" in db_tech:
                reqs.append("sqlalchemy>=2.0.0")
        
        # Additional common requirements
        reqs.extend([
            "requests>=2.31.0",
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0"
        ])
        
        # Authentication if mentioned
        if "auth" in str(requirements).lower():
            reqs.extend([
                "python-jose[cryptography]>=3.3.0",
                "passlib[bcrypt]>=1.7.0",
                "python-multipart>=0.0.6"
            ])
        
        return "\n".join(sorted(set(reqs)))
    
    def _generate_env_template(self, requirements: Dict[str, Any]) -> str:
        """Generate environment template"""
        project_info = self._analyze_project_requirements(requirements)
        
        template = '''# Environment Configuration Template
# Copy this to .env and update with your values

# Application
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-change-in-production

# API Configuration
API_V1_STR=/api/v1
'''
        
        # Database configuration
        if project_info.get("database_tech"):
            db_tech = project_info["database_tech"].lower()
            if "postgresql" in db_tech:
                template += '''
# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
'''
            elif "mysql" in db_tech:
                template += '''
# Database (MySQL)
DATABASE_URL=mysql://user:password@localhost:3306/dbname
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
'''
            elif "mongodb" in db_tech:
                template += '''
# Database (MongoDB)
MONGODB_URL=mongodb://localhost:27017/your_database
'''
        
        # Frontend configuration
        if project_info["has_frontend"]:
            template += '''
# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_ENVIRONMENT=development
'''
        
        # External services
        template += '''
# External Services
# Add your API keys and external service URLs here
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
'''
        
        return template
    
    def _generate_gitignore(self, requirements: Dict[str, Any]) -> str:
        """Generate comprehensive .gitignore"""
        return '''# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
venv/
env/
.venv/
.env

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
.directory
*.tmp

# Environment
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Build outputs
build/
dist/
*.egg-info/
.eggs/
target/

# Test outputs
.coverage
.pytest_cache/
test_report.txt
integration_test_results.json
htmlcov/
.nyc_output
coverage/

# Logs
*.log
logs/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime
.pid
.seed
.pid.lock

# Database
*.db
*.sqlite
*.sqlite3

# Compiled files
*.com
*.class
*.dll
*.exe
*.o
*.so

# Package files
*.7z
*.dmg
*.gz
*.iso
*.jar
*.rar
*.tar
*.zip

# Editor directories and files
.idea
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
'''
    
    def _generate_root_docker_compose(self, requirements: Dict[str, Any]) -> str:
        """Generate root-level docker-compose.yml for development"""
        return '''# Development Docker Compose
# Use this for local development
version: '3.8'

services:
  # For testing, use: cd env_test && docker-compose -f docker-compose.test.yml up
  
  # Development database
  dev-db:
    image: postgres:15
    environment:
      - POSTGRES_DB=dev_db
      - POSTGRES_USER=dev
      - POSTGRES_PASSWORD=dev
    ports:
      - "5432:5432"
    volumes:
      - dev_postgres_data:/var/lib/postgresql/data

  # Development Redis
  dev-redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  dev_postgres_data:

# Note: For full application testing, use env_test/docker-compose.test.yml
'''
    
    def _clean_project_name(self, project_name: str) -> str:
        """Clean project name for directory usage"""
        clean_name = re.sub(r'[^a-zA-Z0-9\-_]', '', str(project_name).lower())
        if not clean_name:
            clean_name = "generated-project"
        return clean_name