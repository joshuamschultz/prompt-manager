# Comprehensive Recommendations

This document provides detailed recommendations for the prompt management system architecture across all requested areas.

## 1. Recommended Package Structure

### ✅ Implemented Structure
```
prompt-manager/
├── src/
│   └── prompt_manager/
│       ├── __init__.py                 # Public API exports
│       ├── exceptions.py               # Exception hierarchy
│       │
│       ├── core/                       # Core domain logic
│       │   ├── __init__.py
│       │   ├── models.py               # Pydantic models
│       │   ├── protocols.py            # Protocol definitions
│       │   ├── registry.py             # Prompt registry
│       │   ├── manager.py              # Main orchestrator
│       │   └── template.py             # Template engine
│       │
│       ├── storage/                    # Persistence layer
│       │   ├── __init__.py
│       │   ├── memory.py               # In-memory storage
│       │   ├── file.py                 # File system storage
│       │   └── yaml_loader.py          # YAML import
│       │
│       ├── versioning/                 # Version management
│       │   ├── __init__.py
│       │   └── store.py                # Version store
│       │
│       ├── plugins/                    # Plugin system
│       │   ├── __init__.py
│       │   ├── base.py                 # Base plugin
│       │   └── registry.py             # Plugin registry
│       │
│       └── observability/              # Telemetry
│           ├── __init__.py
│           ├── logging.py              # Structured logging
│           ├── metrics.py              # Metrics collector
│           └── telemetry.py            # OpenTelemetry
│
├── tests/                              # Test suite
│   ├── conftest.py                     # Fixtures
│   ├── test_core_models.py
│   ├── test_template_engine.py
│   └── ...
│
├── examples/                           # Usage examples
│   └── basic_usage.py
│
├── docs/                               # Documentation (future)
│
├── pyproject.toml                      # Project configuration
├── README.md                           # Quick start
├── ARCHITECTURE.md                     # Architecture docs
├── DESIGN_DECISIONS.md                 # Design rationale
├── PACKAGE_SUMMARY.md                  # Complete overview
└── Makefile                            # Development commands
```

### Rationale
- **Flat is better than nested**: Core modules at first level
- **Separation of concerns**: Each module has clear responsibility
- **Public API control**: `__init__.py` exports define public API
- **Testable**: Tests mirror source structure
- **Extensible**: Easy to add new modules

## 2. Core Abstractions and Interfaces

### Protocol-Based Design (Recommended Approach)

**Why Protocols:**
- No coupling to base classes
- Third-party implementations don't need inheritance
- Structural typing (duck typing with type safety)
- Better testability

**Core Protocols:**

```python
# 1. Storage Backend Protocol
@runtime_checkable
class StorageBackendProtocol(Protocol):
    """Define storage operations without coupling."""
    async def save(self, prompt: Prompt) -> None: ...
    async def load(self, prompt_id: str, version: str | None = None) -> Prompt: ...
    async def delete(self, prompt_id: str, version: str | None = None) -> None: ...
    async def list(self, *, tags: list[str] | None = None) -> list[Prompt]: ...
    async def exists(self, prompt_id: str, version: str | None = None) -> bool: ...

# 2. Template Engine Protocol
@runtime_checkable
class TemplateEngineProtocol(Protocol):
    """Define template operations."""
    async def render(self, template: str, variables: Mapping[str, Any]) -> str: ...
    async def validate(self, template: str) -> bool: ...
    def extract_variables(self, template: str) -> list[str]: ...

# 3. Version Store Protocol
@runtime_checkable
class VersionStoreProtocol(Protocol):
    """Define version management operations."""
    async def save_version(self, version: PromptVersion) -> None: ...
    async def get_version(self, prompt_id: str, version: str) -> PromptVersion: ...
    async def list_versions(self, prompt_id: str) -> list[PromptVersion]: ...
    async def get_latest(self, prompt_id: str) -> PromptVersion: ...

# 4. Observer Protocol (Lifecycle Hooks)
@runtime_checkable
class ObserverProtocol(Protocol):
    """Define observability hooks."""
    async def on_render_start(...) -> None: ...
    async def on_render_complete(...) -> None: ...
    async def on_render_error(...) -> None: ...
    async def on_version_created(...) -> None: ...

# 5. Plugin Protocol
@runtime_checkable
class PluginProtocol(Protocol):
    """Define plugin interface."""
    name: str
    version: str
    async def initialize(self, config: Mapping[str, Any]) -> None: ...
    async def render_for_framework(self, prompt: Prompt, variables: Mapping[str, Any]) -> Any: ...
    async def validate_compatibility(self, prompt: Prompt) -> bool: ...
    async def shutdown(self) -> None: ...
```

### Domain Models (Pydantic v2)

```python
# Core Models
Prompt              # Main prompt with template and metadata
PromptTemplate      # Text template configuration
ChatPromptTemplate  # Chat message templates
PromptMetadata      # Associated metadata
PromptVersion       # Version with changelog
PromptExecution     # Execution record for observability

# Enums
PromptFormat        # TEXT, CHAT, COMPLETION, INSTRUCTION
PromptStatus        # DRAFT, ACTIVE, DEPRECATED, ARCHIVED
Role                # SYSTEM, USER, ASSISTANT, FUNCTION, TOOL
```

### Component Architecture

```
┌──────────────────────────────────────┐
│       PromptManager (Facade)         │
│  - High-level API                    │
│  - Coordinates components            │
└────────┬─────────────────────────────┘
         │
    ┌────┼────┬─────────┬──────────┐
    ▼    ▼    ▼         ▼          ▼
┌────┐ ┌───┐ ┌────┐  ┌────┐   ┌────────┐
│Reg │ │Tpl│ │Ver │  │Obs │   │Plugin  │
│    │ │Eng│ │Str │  │    │   │Registry│
└──┬─┘ └───┘ └────┘  └────┘   └────────┘
   │
   ▼
┌────────┐
│Storage │
└────────┘
```

## 3. Type Safety Recommendations

### Mypy Configuration (Strict Mode)
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
plugins = ["pydantic.mypy"]
```

### Type Annotation Guidelines

**1. Complete Function Signatures**
```python
# ✅ Good
async def render(
    self,
    prompt_id: str,
    variables: Mapping[str, Any],
    *,
    version: str | None = None,
) -> str:
    ...

# ❌ Bad (missing return type)
async def render(self, prompt_id: str, variables: dict):
    ...
```

**2. Use Protocol for Interfaces**
```python
# ✅ Good (flexible, no coupling)
def __init__(self, storage: StorageBackendProtocol):
    ...

# ❌ Less flexible (tight coupling)
def __init__(self, storage: FileSystemStorage):
    ...
```

**3. Generic Types Where Appropriate**
```python
T = TypeVar("T")

async def cached_operation(
    cache_key: str,
    operation: Callable[[], Awaitable[T]],
) -> T:
    ...
```

**4. Literal Types for Constants**
```python
def bump_version(self, level: Literal["major", "minor", "patch"]) -> str:
    ...
```

**5. Use Mapping Instead of dict for Parameters**
```python
# ✅ Good (accepts any mapping)
async def render(self, variables: Mapping[str, Any]) -> str:
    ...

# ❌ Less flexible (only dict)
async def render(self, variables: dict[str, Any]) -> str:
    ...
```

### Pydantic Configuration

```python
class Prompt(BaseModel):
    model_config = ConfigDict(
        frozen=False,              # Allow updates
        extra="forbid",            # No extra fields
        validate_assignment=True,  # Validate on field updates
    )
```

## 4. Dependency Management Approach

### Poetry (Recommended)

**Why Poetry:**
- Modern dependency resolver
- Lock file for reproducibility
- Virtual environment management
- Easy publishing to PyPI
- PEP 517/518 compliant

**Project Structure:**
```toml
[tool.poetry.dependencies]
python = "^3.11"
pydantic = "^2.10.0"
# ... core dependencies

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.0"
# ... dev dependencies

[tool.poetry.extras]
openai = ["openai"]
anthropic = ["anthropic"]
all = ["openai", "anthropic", "langchain-core"]
```

### Dependency Categories

**1. Core Dependencies (Required)**
- pydantic: Models and validation
- pyyaml: YAML support
- pybars4: Handlebars templates
- aiofiles: Async file I/O
- structlog: Structured logging
- opentelemetry-api: Telemetry

**2. Optional Dependencies (Extras)**
- openai: OpenAI plugin
- anthropic: Anthropic plugin
- langchain-core: LangChain plugin
- litellm: LiteLLM plugin

**3. Development Dependencies**
- pytest + plugins: Testing
- black: Formatting
- ruff: Linting
- mypy: Type checking
- bandit: Security

### Version Constraints

```toml
# Pin major+minor for core deps
pydantic = "^2.10.0"    # >=2.10.0, <3.0.0

# Allow patch updates
aiofiles = "^24.1.0"    # >=24.1.0, <25.0.0

# Exact version for dev tools
black = "24.10.0"
```

## 5. Plugin/Extension Patterns

### Plugin Architecture Design

**1. Base Plugin Class**
```python
class BasePlugin(ABC):
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version

    @abstractmethod
    async def initialize(self, config: Mapping[str, Any]) -> None:
        """Initialize plugin with config."""

    @abstractmethod
    async def render_for_framework(
        self, prompt: Prompt, variables: Mapping[str, Any]
    ) -> Any:
        """Render in framework-specific format."""
```

**2. Plugin Discovery**
```python
# Via entry points in pyproject.toml
[tool.poetry.plugins."prompt_manager.plugins"]
openai = "prompt_manager_openai:OpenAIPlugin"
anthropic = "prompt_manager_anthropic:AnthropicPlugin"

# Auto-discovery at runtime
registry = PluginRegistry()
registry.discover_entry_points()
```

**3. Plugin Registration**
```python
# Manual registration
plugin = MyPlugin()
await plugin.initialize({"api_key": "..."})
manager.register_plugin(plugin)

# From module
await registry.load_from_module(
    "mypackage.plugins",
    "MyPlugin",
    config={"api_key": "..."}
)
```

### Extension Points

**1. Custom Storage Backend**
```python
class PostgreSQLStorage:
    """PostgreSQL storage implementation."""

    async def save(self, prompt: Prompt) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO prompts ...",
                prompt.model_dump()
            )
```

**2. Custom Cache Implementation**
```python
class RedisCache:
    """Redis cache implementation."""

    async def get(self, key: str) -> str | None:
        return await self.redis.get(key)

    async def set(self, key: str, value: str, *, ttl: int | None = None) -> None:
        await self.redis.setex(key, ttl or 3600, value)
```

**3. Custom Observer**
```python
class DatadogObserver:
    """Send metrics to Datadog."""

    async def on_render_complete(self, prompt_id, version, execution):
        self.statsd.timing(
            "prompt.render.duration",
            execution.duration_ms,
            tags=[f"prompt:{prompt_id}"]
        )
```

## 6. Testing Strategy

### Test Pyramid

```
           /\
          /E2E\          <- Few (integration/e2e)
         /______\
        /        \
       /Integration\     <- Some (component integration)
      /____________\
     /              \
    /   Unit Tests   \   <- Many (fast, isolated)
   /__________________\
```

### Test Organization

```
tests/
├── unit/                      # Fast, isolated tests
│   ├── test_models.py
│   ├── test_template.py
│   └── test_registry.py
│
├── integration/               # Component integration
│   ├── test_manager_flow.py
│   └── test_storage_backends.py
│
├── e2e/                       # End-to-end scenarios
│   └── test_full_workflow.py
│
├── benchmarks/                # Performance tests
│   └── test_render_performance.py
│
└── conftest.py                # Shared fixtures
```

### Testing Patterns

**1. Unit Tests**
```python
@pytest.mark.unit
async def test_template_render():
    """Test template rendering in isolation."""
    engine = TemplateEngine()
    result = await engine.render(
        "Hello {{name}}",
        {"name": "World"}
    )
    assert result == "Hello World"
```

**2. Integration Tests**
```python
@pytest.mark.integration
async def test_manager_with_storage():
    """Test manager with real storage."""
    storage = FileSystemStorage(tmp_path)
    registry = PromptRegistry(storage=storage)
    manager = PromptManager(registry=registry)

    # Test full flow
    await manager.create_prompt(prompt)
    result = await manager.render(prompt.id, variables)
    assert result is not None
```

**3. Property-Based Tests**
```python
@given(
    template=st.text(),
    variables=st.dictionaries(st.text(), st.text())
)
async def test_template_never_crashes(template, variables):
    """Template engine should never crash."""
    engine = TemplateEngine()
    try:
        await engine.render(template, variables)
    except TemplateError:
        pass  # Expected errors are OK
```

**4. Benchmark Tests**
```python
@pytest.mark.benchmark
def test_render_performance(benchmark):
    """Benchmark template rendering."""

    @benchmark
    def render():
        asyncio.run(manager.render(prompt_id, variables))

    # Assert performance within bounds
    assert benchmark.stats.mean < 0.01  # <10ms average
```

### Coverage Requirements

```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=prompt_manager",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-branch",
    "--cov-fail-under=90",
]
```

**Coverage Targets:**
- Line coverage: ≥90%
- Branch coverage: ≥75%
- All public APIs tested
- Error paths tested

## 7. Performance Optimization Considerations

### Async/Await Strategy

**1. All I/O Operations Async**
```python
# ✅ Good
async def save(self, prompt: Prompt) -> None:
    async with aiofiles.open(path, "w") as f:
        await f.write(data)

# ❌ Bad (blocks event loop)
def save(self, prompt: Prompt) -> None:
    with open(path, "w") as f:
        f.write(data)
```

**2. Concurrent Operations**
```python
# ✅ Good (parallel)
prompts = await asyncio.gather(
    storage.load("prompt1"),
    storage.load("prompt2"),
    storage.load("prompt3"),
)

# ❌ Bad (sequential)
prompts = []
for prompt_id in ["prompt1", "prompt2", "prompt3"]:
    prompts.append(await storage.load(prompt_id))
```

### Caching Strategy

**1. Cache Key Design**
```python
def _make_cache_key(
    prompt_id: str,
    version: str,
    variables: Mapping[str, Any],
) -> str:
    """Create deterministic cache key."""
    var_str = "|".join(f"{k}={v}" for k, v in sorted(variables.items()))
    return f"prompt:{prompt_id}:{version}:{hash(var_str)}"
```

**2. Cache Invalidation**
```python
async def update_prompt(self, prompt: Prompt) -> None:
    """Update prompt and invalidate cache."""
    await self._registry.register(prompt)

    # Invalidate all versions of this prompt
    if self._cache:
        await self._cache.invalidate(f"prompt:{prompt.id}:*")
```

**3. TTL Configuration**
```python
# Short TTL for frequently changing prompts
await cache.set(key, value, ttl=300)  # 5 minutes

# Long TTL for stable prompts
await cache.set(key, value, ttl=3600)  # 1 hour
```

### Memory Management

**1. Generator-Based Iteration**
```python
async def iter_prompts(self) -> AsyncIterator[Prompt]:
    """Iterate prompts without loading all into memory."""
    for prompt_dir in self._base_path.iterdir():
        yield await self.load(prompt_dir.name)
```

**2. Lazy Loading**
```python
class PromptRegistry:
    """Load prompts on-demand, not at init."""

    async def get(self, prompt_id: str) -> Prompt:
        # Check memory first
        if prompt_id in self._prompts:
            return self._prompts[prompt_id]

        # Load from storage if needed
        prompt = await self._storage.load(prompt_id)
        self._prompts[prompt_id] = prompt
        return prompt
```

### Database Optimization (Future)

**1. Connection Pooling**
```python
pool = await asyncpg.create_pool(
    dsn=database_url,
    min_size=10,
    max_size=100,
    command_timeout=60,
)
```

**2. Indexing Strategy**
```sql
CREATE INDEX idx_prompts_id ON prompts(id);
CREATE INDEX idx_prompts_version ON prompts(id, version);
CREATE INDEX idx_prompts_tags ON prompts USING gin(tags);
CREATE INDEX idx_prompts_status ON prompts(status);
```

**3. Query Optimization**
```python
# ✅ Good (single query with join)
SELECT p.*, m.* FROM prompts p
LEFT JOIN metadata m ON p.id = m.prompt_id
WHERE p.id = $1

# ❌ Bad (N+1 queries)
SELECT * FROM prompts WHERE id = $1
SELECT * FROM metadata WHERE prompt_id = $1
```

### Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Simple template render | <1ms | Text prompts with few variables |
| Complex template render | <5ms | Chat prompts with many messages |
| Cache hit | <0.1ms | In-memory cache lookup |
| Registry lookup | <0.1ms | Dictionary access |
| File storage read | <10ms | Depends on disk I/O |
| Version history | <50ms | List all versions |

## Summary of Recommendations

### 1. Package Structure
- ✅ Flat module hierarchy (core, storage, versioning, plugins, observability)
- ✅ Clear separation of concerns
- ✅ Public API control via `__init__.py`

### 2. Core Abstractions
- ✅ Protocol-based design for flexibility
- ✅ Pydantic v2 models for validation
- ✅ Dependency injection throughout

### 3. Type Safety
- ✅ Mypy strict mode enabled
- ✅ Complete type annotations
- ✅ Protocol definitions for interfaces

### 4. Dependency Management
- ✅ Poetry for modern dependency resolution
- ✅ Optional dependencies via extras
- ✅ Lock file for reproducibility

### 5. Plugin Architecture
- ✅ Base plugin class with ABC
- ✅ Entry point discovery
- ✅ Protocol-based interface

### 6. Testing Strategy
- ✅ Test pyramid (many unit, some integration, few e2e)
- ✅ Property-based testing with Hypothesis
- ✅ >90% coverage requirement
- ✅ Benchmark tests for performance

### 7. Performance
- ✅ Async/await throughout
- ✅ Optional caching layer
- ✅ Memory-efficient patterns
- ✅ Database optimization ready

## Next Steps

1. **Implement Plugin Examples**
   - OpenAI plugin
   - Anthropic plugin
   - LangChain integration

2. **Add Storage Backends**
   - PostgreSQL storage
   - Redis cache
   - S3 storage

3. **Build Tooling**
   - CLI tool
   - REST API server
   - Web UI

4. **Advanced Features**
   - A/B testing framework
   - Cost tracking
   - Analytics dashboard

5. **Documentation**
   - API reference (Sphinx)
   - Tutorials
   - Best practices guide
