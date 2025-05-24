with open(project_path / "project.json", 'w') as f:
        json.dump(project_data, f, indent=2)

def generate_initial_code(code_generator: CodeGenerator,
                         requirements: Dict[str, Any],
                         llm_provider: str,
                         output_path: Path) -> Dict[str, str]:
    """Generate initial code based on requirements"""
    
    code_files = {}
    
    # Generate frontend code if specified
    if "frontend" in requirements:
        frontend_files = asyncio.run(
            code_generator.generate_react_app(requirements, llm_provider)
        )
        code_files.update(frontend_files)
    
    # Generate backend code if specified
    if "backend" in requirements:
        backend_files = asyncio.run(
            code_generator.generate_backend_api(requirements, llm_provider)
        )
        code_files.update(backend_files)
    
    return code_files

def regenerate_code_with_fixes(code_generator: CodeGenerator,
                             requirements: Dict[str, Any],
                             llm_provider: str,
                             failures: List[Dict[str, Any]],
                             iteration: int,
                             output_path: Path) -> Dict[str, str]:
    """Regenerate code with fixes for test failures"""
    
    code_files = asyncio.run(
        code_generator.generate_code(
            requirements=requirements,
            provider=llm_provider,
            iteration=iteration,
            previous_errors=failures
        )
    )
    
    return code_files

def save_code_files(output_path: Path, code_files: Dict[str, str]):
    """Save generated code files to disk"""
    
    for file_path, content in code_files.items():
        full_path = output_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
EOL

# Create project model
cat > backend/app/models/project.py << 'EOL'
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class ProjectStatus(str, Enum):
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"

class Project(BaseModel):
    id: str
    name: str
    requirements: Dict[str, Any]
    status: ProjectStatus
    created_at: datetime = datetime.now()
    updated_at: Optional[datetime] = None
    completed_iteration: Optional[int] = None
    task_id: Optional[str] = None
    
    class Config:
        use_enum_values = True

class TestResult(BaseModel):
    success: bool
    type: str  # frontend, backend, e2e
    logs: Optional[str] = None
    exit_code: Optional[int] = None
    failures: List[Dict[str, Any]] = []

class IterationResult(BaseModel):
    iteration: int
    code_files: Dict[str, str]
    test_files: Dict[str, str]
    test_results: Dict[str, TestResult]
    success: bool
    created_at: datetime = datetime.now()
EOL

# Create __init__.py files for packages
touch backend/app/services/__init__.py
touch backend/app/models/__init__.py
touch backend/app/tasks/__init__.py
touch backend/app/core/__init__.py
touch backend/app/api/__init__.py

# Create a basic test file
mkdir -p backend/tests
cat > backend/tests/test_main.py << 'EOL'
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Virgil AI API", "version": "1.0.0"}

def test_llm_providers():
    response = client.get("/llm-providers")
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data
    assert len(data["providers"]) == 3
EOL

# Create pytest configuration
cat > backend/pytest.ini << 'EOL'
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    -s
    --cov=app
    --cov-report=html
    --cov-report=term-missing
env_files = .env.test
EOL

# Create a sample .env.test file
cat > backend/.env.test << 'EOL'
# Test environment variables
OPENAI_API_KEY=test-key
ANTHROPIC_API_KEY=test-key
DEEPSEEK_API_KEY=test-key
DATABASE_URL=sqlite:///:memory:
REDIS_URL=redis://localhost:6379/1
SECRET_KEY=test-secret-key
JWT_SECRET_KEY=test-jwt-secret
EOL

# Create alembic configuration
cat > backend/alembic.ini << 'EOL'
# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = alembic

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
# Uncomment the line below if you want the files to be prepended with date and time
# file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version location specification; This defaults
# to alembic/versions.  When using multiple version
# directories, initial revisions must be specified with --version-path
# version_locations = %(here)s/bar:%(here)s/bat:alembic/versions

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses os.pathsep.
# If this key is omitted entirely, it falls back to the legacy behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os  # Use os.pathsep.
# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = driver://user:pass@localhost/dbname


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOL

echo "✅ Python backend files created successfully!"
echo ""
echo "The following files have been created:"
echo "  - backend/app/main.py"
echo "  - backend/app/core/config.py"
echo "  - backend/app/services/llm_service.py"
echo "  - backend/app/services/code_generator.py"
echo "  - backend/app/services/test_generator.py"
echo "  - backend/app/services/test_runner.py"
echo "  - backend/app/tasks/celery_app.py"
echo "  - backend/app/models/project.py"
echo "  - backend/tests/test_main.py"
echo "  - backend/pytest.ini"
echo "  - backend/.env.test"
echo "  - backend/alembic.ini"
echo ""
echo "Next steps:"
echo "1. Install Python dependencies:"
echo "   cd backend"
echo "   python -m venv venv"
echo "   source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
echo "   pip install -r requirements.txt"
echo "2. Configure environment variables in .env"
echo "3. Start the services with Docker Compose"