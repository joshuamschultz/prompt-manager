# Architecture Documentation

## Overview

The Prompt Manager is designed using modern Python patterns including Protocol-based design, dependency injection, and async/await throughout. This document describes the architecture, design decisions, and implementation patterns.

## Design Principles

### 1. Protocol-Based Design (Structural Subtyping)

Instead of inheritance hierarchies, we use Protocols for duck typing with type safety:

```python
@runtime_checkable
class StorageBackendProtocol(Protocol):
    async def save(self, prompt: Prompt) -> None: ...
    async def load(self, prompt_id: str, version: str | None = None) -> Prompt: ...
```

**Benefits:**
- No tight coupling to base classes
- Easy to swap implementations
- Supports third-party implementations
- Better testability with mocks
- Mypy type checking without inheritance

### 2. Dependency Injection

Components receive dependencies through constructors:

```python
class PromptManager:
    def __init__(
        self,
        registry: PromptRegistry,
        version_store: VersionStore | None = None,
        cache: CacheProtocol | None = None,
        metrics: MetricsCollectorProtocol | None = None,
    ):
        ...
```

**Benefits:**
- Explicit dependencies
- Easy testing with test doubles
- Flexible configuration
- No hidden global state

### 3. Async/Await Throughout

All I/O operations are async for performance:

```python
async def render(
    self,
    prompt_id: str,
    variables: Mapping[str, Any],
) -> str:
    prompt = await self._registry.get(prompt_id)
    rendered = await self._template_engine.render(...)
    return rendered
```

**Benefits:**
- Non-blocking I/O
- High concurrency
- Efficient resource usage
- Natural async composition

### 4. Immutability Where Possible

Models use Pydantic with frozen=True where appropriate:

```python
class Message(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    role: Role
    content: str
```

**Benefits:**
- Thread safety
- Predictable behavior
- Cacheable results
- Easier reasoning

### 5. Observer Pattern for Extensibility

Lifecycle hooks via observer protocol:

```python
class ObserverProtocol(Protocol):
    async def on_render_start(...) -> None: ...
    async def on_render_complete(...) -> None: ...
    async def on_render_error(...) -> None: ...
```

**Benefits:**
- Decoupled observability
- Multiple observers
- No modification of core logic
- Easy to add/remove

## Core Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────┐
│              PromptManager (Orchestrator)        │
│  - Coordinates all operations                   │
│  - Manages lifecycle                            │
│  - Integrates observers                         │
└──────┬────────────┬─────────────┬────────────┬──┘
       │            │             │            │
       ▼            ▼             ▼            ▼
┌──────────┐ ┌──────────┐  ┌──────────┐ ┌──────────┐
│ Registry │ │ Template │  │ Version  │ │ Plugins  │
│          │ │ Engine   │  │ Store    │ │          │
└────┬─────┘ └──────────┘  └────┬─────┘ └──────────┘
     │                           │
     ▼                           ▼
┌──────────┐              ┌──────────┐
│ Storage  │              │   File   │
│ Backend  │              │ Storage  │
└──────────┘              └──────────┘
```

### Data Flow

#### 1. Prompt Creation Flow

```
User
  │
  ├─> Create Prompt object (Pydantic validation)
  │
  ├─> PromptManager.create_prompt()
  │     │
  │     ├─> Registry.register()
  │     │     └─> StorageBackend.save()
  │     │
  │     ├─> VersionStore.save_version()
  │     │
  │     └─> Notify observers
  │           └─> on_version_created()
  │
  └─> Return Prompt
```

#### 2. Prompt Rendering Flow

```
User
  │
  ├─> PromptManager.render(id, variables)
  │     │
  │     ├─> Notify observers: on_render_start()
  │     │
  │     ├─> Check cache (if enabled)
  │     │
  │     ├─> Registry.get() -> Prompt
  │     │
  │     ├─> TemplateEngine.render()
  │     │     ├─> Validate template
  │     │     ├─> Compile Handlebars
  │     │     └─> Render with variables
  │     │
  │     ├─> Cache result
  │     │
  │     ├─> Record metrics
  │     │
  │     └─> Notify observers: on_render_complete()
  │
  └─> Return rendered string
```

## Module Organization

### 1. Core Module (`core/`)

**Purpose:** Fundamental abstractions and implementations

**Files:**
- `models.py`: Pydantic models for domain entities
- `protocols.py`: Protocol definitions for interfaces
- `registry.py`: In-memory prompt registry
- `manager.py`: Main orchestrator
- `template.py`: Handlebars template engine

**Design:**
- Models are the single source of truth
- Protocols enable pluggable implementations
- Registry provides fast in-memory access
- Manager coordinates all operations
- Template engine is decoupled via protocol

### 2. Storage Module (`storage/`)

**Purpose:** Persistence implementations

**Files:**
- `memory.py`: In-memory storage (testing)
- `file.py`: File system JSON storage
- `yaml_loader.py`: YAML schema import

**Design:**
- All implement StorageBackendProtocol
- No knowledge of higher-level components
- Async I/O with aiofiles
- Error handling with custom exceptions

### 3. Versioning Module (`versioning/`)

**Purpose:** Version history tracking

**Files:**
- `store.py`: Version storage and history

**Design:**
- Implements VersionStoreProtocol
- Semantic versioning enforcement
- Parent-child relationships
- Checksum calculation
- Changelog tracking

### 4. Plugins Module (`plugins/`)

**Purpose:** Framework integrations

**Files:**
- `base.py`: Base plugin implementation
- `registry.py`: Plugin discovery and management

**Design:**
- BasePlugin provides common functionality
- Plugins implement PluginProtocol
- Registry handles discovery and lifecycle
- Entry point support for auto-discovery

### 5. Observability Module (`observability/`)

**Purpose:** Logging, metrics, tracing

**Files:**
- `logging.py`: Structured logging observer
- `metrics.py`: Metrics collector
- `telemetry.py`: OpenTelemetry integration

**Design:**
- All implement ObserverProtocol
- No coupling to core logic
- Can be enabled/disabled independently
- Metrics aggregated in-memory
- OpenTelemetry for distributed tracing

## Type Safety Strategy

### 1. Complete Type Annotations

Every function has full type hints:

```python
async def render(
    self,
    prompt_id: str,
    variables: Mapping[str, Any],
    *,
    version: str | None = None,
    use_cache: bool = True,
) -> str:
    ...
```

### 2. Generic Types

Using TypeVar and ParamSpec for generics:

```python
T = TypeVar("T")
P = ParamSpec("P")

def cache_result(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    ...
```

### 3. Protocol Definitions

Structural typing for flexibility:

```python
@runtime_checkable
class CacheProtocol(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, *, ttl: int | None = None) -> None: ...
```

### 4. Pydantic Models

Runtime validation with Pydantic v2:

```python
class Prompt(BaseModel):
    model_config = ConfigDict(
        frozen=False,
        extra="forbid",
        validate_assignment=True,
    )
    id: str = Field(..., min_length=1)
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
```

### 5. Mypy Configuration

Strict mode in pyproject.toml:

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
disallow_untyped_defs = true
```

## Error Handling

### Exception Hierarchy

```
PromptManagerError
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

### Error Context

All exceptions carry context:

```python
class PromptManagerError(Exception):
    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(message)
        self.message = message
        self.context = context
```

## Performance Considerations

### 1. Caching Strategy

**When to Cache:**
- Frequently used prompts
- Expensive template rendering
- Static variable combinations

**Cache Key Design:**
```python
f"prompt:{prompt_id}:{version}:{hash(variables)}"
```

**Invalidation:**
- On prompt update
- Pattern-based invalidation
- TTL support

### 2. Async Operations

**Benefits:**
- Non-blocking I/O
- High concurrency
- Efficient resource usage

**Implementation:**
- All storage operations async
- Template rendering async
- Observer notifications async

### 3. Memory Management

**Strategies:**
- Version store uses lists (append-only)
- Registry uses dictionaries for O(1) lookup
- Metrics aggregated in-memory
- Generators for large datasets

### 4. Database Considerations

**Future PostgreSQL Backend:**
- Connection pooling
- Prepared statements
- Indexing on prompt_id, version, tags
- JSONB for metadata
- Full-text search for content

## Testing Strategy

### 1. Unit Tests

Test individual components in isolation:

```python
async def test_template_render():
    engine = TemplateEngine()
    result = await engine.render(
        "Hello {{name}}",
        {"name": "World"},
    )
    assert result == "Hello World"
```

### 2. Integration Tests

Test component interactions:

```python
async def test_manager_full_flow():
    manager = create_test_manager()
    prompt = create_test_prompt()
    await manager.create_prompt(prompt)
    result = await manager.render(prompt.id, {"name": "Test"})
    assert "Test" in result
```

### 3. Property-Based Tests

Use Hypothesis for edge cases:

```python
@given(st.text(), st.dictionaries(st.text(), st.text()))
async def test_template_any_input(template, variables):
    engine = TemplateEngine()
    # Should not crash
    try:
        await engine.render(template, variables)
    except TemplateError:
        pass
```

### 4. Benchmark Tests

Performance regression detection:

```python
def test_render_performance(benchmark):
    @benchmark
    def render():
        asyncio.run(manager.render("test", variables))
```

## Plugin Development

### Creating a Plugin

```python
from prompt_manager.plugins import BasePlugin

class MyFrameworkPlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="myframework", version="1.0.0")

    async def _initialize_impl(self, config: Mapping[str, Any]) -> None:
        # Setup framework-specific clients
        self.client = MyFramework(api_key=config["api_key"])

    async def render_for_framework(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> Any:
        # Convert prompt to framework format
        if prompt.format == PromptFormat.CHAT:
            return self._convert_chat_prompt(prompt, variables)
        return self._convert_text_prompt(prompt, variables)

    async def validate_compatibility(self, prompt: Prompt) -> bool:
        # Check if prompt is compatible
        return prompt.format in [PromptFormat.TEXT, PromptFormat.CHAT]
```

### Registering a Plugin

```python
# Via code
plugin = MyFrameworkPlugin()
await plugin.initialize({"api_key": "..."})
manager.register_plugin(plugin)

# Via entry points (pyproject.toml)
[tool.poetry.plugins."prompt_manager.plugins"]
myframework = "mypackage.plugins:MyFrameworkPlugin"
```

## Extension Points

### 1. Custom Storage Backends

Implement `StorageBackendProtocol`:
- Redis backend
- PostgreSQL backend
- S3 backend
- MongoDB backend

### 2. Custom Cache Implementations

Implement `CacheProtocol`:
- Redis cache
- Memcached
- LRU cache with size limits
- Distributed cache

### 3. Custom Observers

Implement `ObserverProtocol`:
- Custom logging
- APM integration
- Webhook notifications
- Analytics tracking

### 4. Custom Template Engines

Implement `TemplateEngineProtocol`:
- Alternative Handlebars implementations
- Mustache engine
- Custom DSL

Note: The current implementation uses Handlebars (pybars4). Custom template engines must maintain compatibility with the Handlebars syntax used in existing prompts, or provide clear migration paths.

## Security Considerations

### 1. Input Validation

- Pydantic validates all inputs
- Template syntax validation
- Variable name validation
- Version format validation

### 2. Template Safety

- No arbitrary code execution
- Sandboxed template rendering
- Variable escaping (context-dependent)
- Partial template restrictions

### 3. Storage Security

- Path traversal prevention
- File permission checks
- Input sanitization
- SQL injection prevention (future)

### 4. Secret Management

- No secrets in prompts
- Environment variable config
- Secret detection in validation
- Audit logging

## Deployment Considerations

### 1. Container Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev
COPY src ./src
CMD ["python", "-m", "prompt_manager.server"]
```

### 2. Environment Configuration

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    storage_path: Path
    cache_enabled: bool = True
    cache_ttl: int = 3600
    metrics_enabled: bool = True
```

### 3. Health Checks

```python
async def health_check() -> dict[str, Any]:
    return {
        "status": "healthy",
        "registry": await manager._registry.get_stats(),
        "metrics": await manager.get_metrics(),
    }
```

## Future Enhancements

### 1. Advanced Features
- A/B testing framework
- Prompt optimization
- Cost tracking
- Usage quotas

### 2. Integrations
- More LLM providers
- Prompt engineering tools
- CI/CD integration
- Monitoring platforms

### 3. Performance
- Query optimization
- Batch operations
- Streaming responses
- CDN integration

### 4. Developer Experience
- CLI tool
- Web UI
- VSCode extension
- Testing utilities
