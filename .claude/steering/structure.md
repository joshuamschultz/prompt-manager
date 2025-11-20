# Prompt Manager - Project Structure

## Directory Layout

```
prompt-manager/
├── .claude/                      # Claude AI configuration
│   ├── specs/                   # Feature specifications
│   │   └── security-requirements/
│   └── steering/                # Project documentation (this file)
├── src/
│   └── prompt_manager/          # Main package
│       ├── __init__.py          # Public API exports
│       ├── exceptions.py        # Exception hierarchy
│       ├── core/                # Core functionality
│       │   ├── __init__.py
│       │   ├── models.py        # Pydantic data models
│       │   ├── protocols.py     # Protocol definitions
│       │   ├── registry.py      # In-memory prompt registry
│       │   ├── manager.py       # Main orchestrator
│       │   └── template.py      # Handlebars template engine
│       ├── storage/             # Storage backends
│       │   ├── __init__.py
│       │   ├── memory.py        # In-memory storage
│       │   ├── file.py          # File system storage
│       │   └── yaml_loader.py   # YAML schema import
│       ├── versioning/          # Version management
│       │   ├── __init__.py
│       │   └── store.py         # Version store
│       ├── plugins/             # Plugin system
│       │   ├── __init__.py
│       │   ├── base.py          # Base plugin class
│       │   └── registry.py      # Plugin registry
│       └── observability/       # Monitoring & logging
│           ├── __init__.py
│           ├── logging.py       # Structured logging
│           ├── metrics.py       # Metrics collector
│           └── telemetry.py     # OpenTelemetry
├── tests/                       # Test suite
│   ├── conftest.py             # Shared fixtures
│   ├── test_core_models.py     # Model tests
│   ├── test_template_engine.py # Template tests
│   └── ...
├── examples/                    # Usage examples
│   └── basic_usage.py
├── pyproject.toml              # Project configuration
├── README.md                   # Main documentation
├── ARCHITECTURE.md             # Architecture details
├── DESIGN_DECISIONS.md         # Design rationale
├── PACKAGE_SUMMARY.md          # Package overview
├── QUICK_START.md              # Getting started guide
├── RECOMMENDATIONS.md          # Best practices
├── Makefile                    # Common tasks
└── .gitignore                  # Git ignore patterns
```

## Module Organization

### Core Package (`src/prompt_manager/`)

The main package follows a modular architecture with clear separation of concerns.

#### `__init__.py` - Public API
Exports the public interface for users:
```python
from prompt_manager.core.models import (
    Prompt,
    PromptTemplate,
    ChatPromptTemplate,
    Message,
    PromptMetadata,
    PromptFormat,
    PromptStatus,
    Role,
)
from prompt_manager.core.manager import PromptManager
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.storage import (
    InMemoryStorage,
    FileSystemStorage,
    YAMLLoader,
)

__all__ = [
    "Prompt",
    "PromptManager",
    "PromptRegistry",
    # ... other exports
]
```

#### `exceptions.py` - Exception Hierarchy
All custom exceptions with context:
```python
PromptManagerError (base)
├── PromptError
│   ├── PromptNotFoundError
│   └── PromptValidationError
├── TemplateError
│   ├── TemplateRenderError
│   └── TemplateSyntaxError
├── VersionError
│   ├── VersionNotFoundError
│   └── VersionConflictError
├── StorageError
│   ├── StorageReadError
│   └── StorageWriteError
├── PluginError
│   ├── PluginNotFoundError
│   ├── PluginLoadError
│   └── PluginValidationError
├── SchemaError
│   ├── SchemaValidationError
│   └── SchemaParseError
└── ObservabilityError
    ├── TelemetryError
    └── TracingError
```

### Core Module (`core/`)

Contains the fundamental abstractions and core logic.

#### `models.py` - Domain Models
Pydantic v2 models for all data:
- `PromptFormat` (Enum): text, chat, completion, instruction
- `PromptStatus` (Enum): draft, active, deprecated, archived
- `Role` (Enum): system, user, assistant, function, tool
- `Message`: Single chat message (frozen)
- `PromptMetadata`: Metadata with custom fields
- `PromptTemplate`: Template configuration (frozen)
- `ChatPromptTemplate`: Chat-specific template (frozen)
- `Prompt`: Main prompt model with validation
- `PromptVersion`: Version history record
- `PromptExecution`: Execution record for observability

#### `protocols.py` - Interface Definitions
Protocol-based interfaces for extensibility:
- `TemplateEngineProtocol`: Template rendering
- `StorageBackendProtocol`: Storage operations
- `VersionStoreProtocol`: Version management
- `ObserverProtocol`: Lifecycle hooks
- `PluginProtocol`: Framework integrations
- `CacheProtocol`: Caching layer
- `MetricsCollectorProtocol`: Metrics collection

#### `registry.py` - Prompt Registry
In-memory registry for fast access:
- `PromptRegistry`: Main registry class
  - `register()`: Add/update prompt
  - `get()`: Retrieve by ID and version
  - `delete()`: Remove prompt
  - `list_all()`: Async iteration
  - `find_by_tags()`: Filter by tags
  - `find_by_status()`: Filter by status
  - `get_stats()`: Registry statistics

#### `manager.py` - Orchestrator
High-level API coordinating all components:
- `PromptManager`: Main public interface
  - `create_prompt()`: Create with versioning
  - `update_prompt()`: Update with optional version bump
  - `render()`: Render with caching
  - `get_history()`: Version history
  - `add_observer()`: Register observer
  - `register_plugin()`: Add plugin

#### `template.py` - Template Engine
Handlebars-based rendering:
- `TemplateEngine`: Implements TemplateEngineProtocol
  - `render()`: Render template with variables
  - `validate()`: Check syntax
  - `extract_variables()`: Get variable names
  - `_render_chat()`: Render chat messages

### Storage Module (`storage/`)

Pluggable storage backends for persistence.

#### `memory.py` - In-Memory Storage
Fast storage for testing/development:
- `InMemoryStorage`: Dict-based storage
  - Thread-safe with locks
  - No persistence
  - Fast for tests

#### `file.py` - File System Storage
JSON file-based persistence:
- `FileSystemStorage`: Directory-based storage
  - One JSON file per prompt
  - Async I/O with aiofiles
  - Human-readable format
  - Path validation to prevent traversal

#### `yaml_loader.py` - YAML Import
Load prompts from YAML schemas:
- `YAMLLoader`: Import from YAML
  - Schema validation
  - Batch import
  - Error reporting

### Versioning Module (`versioning/`)

Version history and management.

#### `store.py` - Version Store
Track version history:
- `VersionStore`: Version management
  - `save_version()`: Record new version
  - `get_version()`: Retrieve specific version
  - `get_history()`: All versions for prompt
  - `get_latest()`: Latest version
  - Checksum calculation
  - Parent-child relationships

### Plugins Module (`plugins/`)

Plugin system for framework integrations.

#### `base.py` - Base Plugin
Common plugin functionality:
- `BasePlugin`: Abstract base for plugins
  - `initialize()`: Setup plugin
  - `render_for_framework()`: Framework-specific render
  - `validate_compatibility()`: Check prompt compatibility
  - Lifecycle management

#### `registry.py` - Plugin Registry
Plugin discovery and management:
- `PluginRegistry`: Manage plugins
  - Auto-discovery via entry points
  - Plugin lifecycle
  - Version compatibility

### Observability Module (`observability/`)

Logging, metrics, and tracing.

#### `logging.py` - Structured Logging
Observer for structured logs:
- `LoggingObserver`: Implements ObserverProtocol
  - Uses structlog
  - Logs all lifecycle events
  - Contextual information

#### `metrics.py` - Metrics Collection
In-memory metrics aggregation:
- `MetricsCollector`: Implements MetricsCollectorProtocol
  - Render counts
  - Error rates
  - Latency tracking
  - Cache hit rates

#### `telemetry.py` - OpenTelemetry
Distributed tracing integration:
- `OpenTelemetryObserver`: Implements ObserverProtocol
  - Span creation
  - Error recording
  - Context propagation

## Test Organization

### Test Structure (`tests/`)

Tests mirror the source structure with additional categories:

```
tests/
├── conftest.py                    # Shared fixtures
├── unit/                          # Unit tests
│   ├── test_models.py
│   ├── test_template_engine.py
│   ├── test_registry.py
│   └── ...
├── integration/                   # Integration tests
│   ├── test_manager_workflow.py
│   ├── test_storage_backends.py
│   └── ...
├── benchmark/                     # Performance tests
│   ├── test_render_performance.py
│   └── ...
└── property/                      # Property-based tests
    └── test_template_properties.py
```

### Fixture Organization

Common fixtures in `conftest.py`:
```python
@pytest.fixture
def in_memory_storage() -> InMemoryStorage:
    return InMemoryStorage()

@pytest.fixture
def registry(in_memory_storage: InMemoryStorage) -> PromptRegistry:
    return PromptRegistry(storage=in_memory_storage)

@pytest.fixture
def manager(registry: PromptRegistry) -> PromptManager:
    return PromptManager(registry=registry)

@pytest.fixture
def sample_prompt() -> Prompt:
    return Prompt(
        id="test",
        version="1.0.0",
        format=PromptFormat.TEXT,
        template=PromptTemplate(content="Hello {{name}}!", variables=["name"]),
    )
```

## Import Conventions

### Internal Imports
```python
# Absolute imports from package root
from prompt_manager.core.models import Prompt, PromptFormat
from prompt_manager.core.protocols import StorageBackendProtocol
from prompt_manager.exceptions import PromptNotFoundError

# Relative imports within module (when appropriate)
from .models import Prompt
from .protocols import StorageBackendProtocol
```

### Public API Imports
```python
# Users import from top-level package
from prompt_manager import (
    PromptManager,
    Prompt,
    PromptRegistry,
    InMemoryStorage,
)
```

## File Naming Conventions

### Source Files
- `models.py`: Data models (Pydantic)
- `protocols.py`: Protocol definitions (interfaces)
- `registry.py`: Registry implementations
- `manager.py`: Manager/orchestrator classes
- `base.py`: Base classes for inheritance
- `exceptions.py`: Exception definitions

### Test Files
- `test_<module>.py`: Tests for module
- `conftest.py`: Shared test fixtures
- Use same name as source file with `test_` prefix

### Documentation Files
- `README.md`: Main documentation
- `ARCHITECTURE.md`: Architecture details
- `DESIGN_DECISIONS.md`: Design rationale
- `*.md` in PascalCase for multi-word names

## Configuration Files

### `pyproject.toml`
Central configuration for:
- Project metadata
- Dependencies (core and optional)
- Tool configuration (black, ruff, mypy, pytest, etc.)
- Entry points for plugins

### `.gitignore`
Standard Python ignores plus:
- `htmlcov/`: Coverage reports
- `.mypy_cache/`: Mypy cache
- `.pytest_cache/`: Pytest cache
- `.ruff_cache/`: Ruff cache

### `Makefile`
Common development tasks:
```makefile
.PHONY: install test lint format clean

install:
	poetry install

test:
	poetry run pytest

lint:
	poetry run ruff check src/
	poetry run mypy src/

format:
	poetry run black src/
	poetry run ruff check --fix src/
```

## Adding New Modules

### When to Create a New Module

Create a new top-level module when:
1. Functionality is logically separate (e.g., new storage backend type)
2. Has 3+ related files
3. Could be used independently
4. Clear protocol/interface boundary

### Module Creation Checklist

When adding a new module:

1. **Create directory structure**:
   ```
   src/prompt_manager/new_module/
   ├── __init__.py
   ├── <implementation>.py
   └── README.md (if complex)
   ```

2. **Define protocols** (if needed):
   - Add to `core/protocols.py` or create module-specific protocols

3. **Create models** (if needed):
   - Add Pydantic models
   - Include validators
   - Add to `core/models.py` or module-specific

4. **Implement functionality**:
   - Follow async/await patterns
   - Use dependency injection
   - Add type hints
   - Write docstrings

5. **Add tests**:
   - Create `tests/test_new_module.py`
   - Unit tests for all functions
   - Integration tests for workflows
   - Add fixtures to `conftest.py`

6. **Update public API**:
   - Export in module `__init__.py`
   - Add to top-level `__init__.py` if public

7. **Document**:
   - Add docstrings to all public functions
   - Update README.md with new feature
   - Add usage example

## Plugin Structure

### Plugin Package Layout

External plugins should follow this structure:
```
prompt-manager-plugin-<name>/
├── src/
│   └── prompt_manager_plugin_<name>/
│       ├── __init__.py
│       ├── plugin.py         # Plugin implementation
│       └── models.py         # Plugin-specific models
├── tests/
│   └── test_plugin.py
├── pyproject.toml
└── README.md
```

### Plugin Entry Point

Register plugin in `pyproject.toml`:
```toml
[tool.poetry.plugins."prompt_manager.plugins"]
openai = "prompt_manager_plugin_openai.plugin:OpenAIPlugin"
```

## Code Organization Best Practices

### Single Responsibility
- Each module has one clear purpose
- Functions do one thing well
- Classes represent single concepts

### Dependency Direction
```
┌─────────────┐
│   Manager   │ ─────┐
└─────────────┘      │
       │             │
       ▼             ▼
┌─────────────┐ ┌──────────┐
│  Registry   │ │ Plugins  │
└─────────────┘ └──────────┘
       │             │
       ▼             ▼
┌─────────────┐ ┌──────────┐
│   Storage   │ │ Models   │
└─────────────┘ └──────────┘
```
Dependencies flow downward, no circular dependencies.

### Protocol Boundaries
```
[Manager] ─uses─> [StorageProtocol]
                        ↑
                        │
                  implements
                        │
        ┌───────────────┼───────────────┐
        │               │               │
  [FileStorage]  [MemoryStorage]  [PostgreSQL]
```
Protocols define boundaries, implementations can be swapped.

### File Size Guidelines
- Core files: <500 lines
- Model files: <300 lines (one model per file if larger)
- Test files: <500 lines (split if larger)
- Protocol files: <200 lines

### When to Split Files
Split a file when:
1. Exceeds size guidelines above
2. Contains multiple unrelated classes
3. Difficult to navigate or test
4. Mix of high-level and low-level code

## Future Structure Plans

### Planned Additions

```
src/prompt_manager/
├── cache/                    # Caching backends
│   ├── redis.py
│   └── lru.py
├── storage/
│   ├── postgresql.py        # PostgreSQL backend
│   ├── s3.py               # S3 backend
│   └── migrations/         # Schema migrations
├── server/                  # REST API server
│   ├── app.py
│   ├── routes/
│   └── middleware/
├── cli/                     # Command-line interface
│   ├── main.py
│   └── commands/
└── analytics/               # Analytics & optimization
    ├── cost_tracking.py
    └── ab_testing.py
```
