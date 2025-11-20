# Prompt Manager - Technology Stack & Guidelines

## Technology Stack

### Core Language & Runtime
- **Python 3.11+**: Required for performance and modern type system
- **asyncio**: All I/O operations use async/await
- **typing-extensions**: Enhanced type hints

### Data Validation & Modeling
- **Pydantic v2**: Runtime validation and serialization
- **pydantic-settings**: Configuration management
- **Type safety**: 100% type coverage with mypy strict mode

### Templating
- **pybars4**: Handlebars implementation for Python
- Logic-less templates for security
- Partial template support

### Storage & I/O
- **aiofiles**: Async file operations
- **PyYAML**: YAML parsing (safe_load only)
- **pathlib**: Modern path handling

### Observability
- **structlog**: Structured logging
- **opentelemetry-api**: Distributed tracing API
- **opentelemetry-sdk**: Tracing implementation
- **python-dateutil**: Time handling

### Testing
- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- **pytest-benchmark**: Performance testing
- **hypothesis**: Property-based testing

### Code Quality
- **black**: Code formatting (line length: 100)
- **ruff**: Fast Python linter (replaces flake8, isort, etc.)
- **mypy**: Static type checking
- **bandit**: Security scanning
- **pre-commit**: Git hooks

### Optional Plugin Dependencies
- **openai**: OpenAI API integration
- **anthropic**: Anthropic API integration
- **langchain-core**: LangChain integration
- **litellm**: Multi-provider LLM support

## Development Patterns

### 1. Protocol-Based Design (NOT Inheritance)

**Use Protocols for all interfaces:**
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class StorageBackendProtocol(Protocol):
    """Define interface without inheritance."""

    async def save(self, prompt: Prompt) -> None: ...
    async def load(self, prompt_id: str, version: str | None = None) -> Prompt: ...
    async def delete(self, prompt_id: str, version: str | None = None) -> None: ...
    async def list_all(self) -> AsyncIterator[Prompt]: ...
```

**Why Protocols:**
- No tight coupling to base classes
- Third-party implementations don't need inheritance
- Better testability with structural typing
- Mypy validates without runtime overhead

### 2. Async/Await Throughout

**All I/O operations must be async:**
```python
# Good: Async I/O
async def render(self, prompt_id: str, variables: Mapping[str, Any]) -> str:
    prompt = await self._registry.get(prompt_id)
    result = await self._template_engine.render(prompt.template.content, variables)
    return result

# Bad: Blocking I/O
def render(self, prompt_id: str, variables: dict[str, Any]) -> str:
    prompt = self._registry.get(prompt_id)  # Blocks
    return self._template_engine.render(...)  # Blocks
```

**Async patterns to use:**
```python
# Concurrent operations
results = await asyncio.gather(
    manager.render("prompt1", vars1),
    manager.render("prompt2", vars2),
)

# Async iteration
async for prompt in storage.list_all():
    await process_prompt(prompt)

# Async context managers
async with aiofiles.open(path, "r") as f:
    content = await f.read()
```

### 3. Dependency Injection

**Pass dependencies through constructors:**
```python
class PromptManager:
    """Main orchestrator with injected dependencies."""

    def __init__(
        self,
        registry: PromptRegistry,
        version_store: VersionStore | None = None,
        cache: CacheProtocol | None = None,
        metrics: MetricsCollectorProtocol | None = None,
    ) -> None:
        self._registry = registry
        self._version_store = version_store or VersionStore()
        self._cache = cache
        self._metrics = metrics
        self._observers: list[ObserverProtocol] = []
```

**Why dependency injection:**
- Explicit dependencies (no hidden globals)
- Easy to test with mocks
- Flexible configuration
- Clear component relationships

### 4. Type Safety with Mypy Strict Mode

**Every function must have complete type hints:**
```python
# Good: Complete type hints
async def render(
    self,
    prompt_id: str,
    variables: Mapping[str, Any],
    *,
    version: str | None = None,
    use_cache: bool = True,
) -> str:
    ...

# Bad: Missing types
async def render(self, prompt_id, variables, version=None, use_cache=True):
    ...
```

**Use appropriate type constructs:**
```python
from collections.abc import Mapping, AsyncIterator
from typing import Any, Literal, Protocol, TypeVar

# Generic types
T = TypeVar("T")

# Literal types for constants
PromptFormat = Literal["text", "chat", "completion"]

# Mapping instead of dict for parameters
def process(variables: Mapping[str, Any]) -> None:
    ...

# AsyncIterator for generators
async def list_prompts(self) -> AsyncIterator[Prompt]:
    for prompt in self._prompts.values():
        yield prompt
```

### 5. Pydantic Models for Data

**Use Pydantic v2 for all data models:**
```python
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Prompt(BaseModel):
    """Domain model with validation."""

    model_config = ConfigDict(
        frozen=False,  # Mutable for updates
        extra="forbid",  # No extra fields
        validate_assignment=True,  # Validate on field changes
    )

    id: str = Field(..., min_length=1, pattern=r"^[a-z0-9_-]+$")
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    format: PromptFormat
    status: PromptStatus = PromptStatus.DRAFT
    template: PromptTemplate | None = None
    chat_template: ChatPromptTemplate | None = None
    metadata: PromptMetadata = Field(default_factory=PromptMetadata)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        """Validate semantic version format."""
        parts = v.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError("Version must be in X.Y.Z format")
        return v

    @model_validator(mode="after")
    def validate_template(self) -> "Prompt":
        """Ensure exactly one template type is set."""
        has_template = self.template is not None
        has_chat = self.chat_template is not None

        if not has_template and not has_chat:
            raise ValueError("Either template or chat_template must be set")
        if has_template and has_chat:
            raise ValueError("Cannot set both template and chat_template")

        return self
```

**Frozen models for immutability:**
```python
class Message(BaseModel):
    """Immutable message model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Role
    content: str
    name: str | None = None
```

### 5.1. YAML Schema Validation

**Separate schema validation from domain models:**

```python
from prompt_manager.validation import SchemaLoader, SchemaValidationError

# Define schema in YAML
"""
version: "1.0.0"
schemas:
  - name: "user_input"
    version: "1.0.0"
    strict: true
    fields:
      - name: "username"
        type: "string"
        required: true
        validators:
          - type: "min_length"
            min_value: 3
          - type: "regex"
            pattern: "^[a-zA-Z0-9_]+$"
"""

# Load and validate
loader = SchemaLoader()
registry = await loader.load_file(Path("schemas.yaml"))

# Validate data before using
try:
    validated_data = await loader.validate_data("user_input", raw_data)
    result = await prompt_manager.render(prompt_id, validated_data)
except SchemaValidationError as e:
    # Handle validation errors with context
    logger.error("Validation failed", errors=e.context)
```

**When to use Schema Validation vs Pydantic Models:**

- **Schema Validation (YAML)**:
  - External/user input validation (API requests, config files)
  - Dynamic schemas that can change without code changes
  - Input/output contracts for prompts
  - When non-developers need to define validation rules

- **Pydantic Models (Python)**:
  - Internal domain models
  - Type-safe application logic
  - When you need Python methods and behavior
  - Compile-time type checking

**Best Practice: Validate at Boundaries**
```python
async def handle_user_request(request_data: dict) -> Response:
    # 1. Validate external input with schema
    validated = await schema_loader.validate_data("request", request_data)

    # 2. Convert to domain model if needed
    domain_obj = DomainModel.model_validate(validated)

    # 3. Process with type-safe domain logic
    result = await process(domain_obj)

    # 4. Validate output before returning
    output = await schema_loader.validate_data("response", result)
    return output
```

**Schema Features:**
- 8 field types: string, integer, float, boolean, list, dict, enum, any
- 13 validators: length, range, regex, enum, email, URL, UUID, date/datetime, custom
- Nested schemas for complex objects
- Required/optional with defaults
- Custom error messages
- Async loading with caching

### 6. Exception Handling

**Use custom exception hierarchy:**
```python
# Base exception with context
class PromptManagerError(Exception):
    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(message)
        self.message = message
        self.context = context

# Specific exceptions
class PromptNotFoundError(PromptError):
    def __init__(self, prompt_id: str, version: str | None = None) -> None:
        msg = f"Prompt '{prompt_id}' not found"
        if version:
            msg += f" (version: {version})"
        super().__init__(msg, prompt_id=prompt_id, version=version)
```

**Exception handling pattern:**
```python
try:
    result = await manager.render(prompt_id, variables)
except PromptNotFoundError as e:
    logger.error("Prompt not found", **e.context)
    raise
except TemplateRenderError as e:
    logger.error("Render failed", error=str(e), cause=e.__cause__)
    # Re-raise or handle
    raise
```

### 7. Observer Pattern for Extensibility

**Use observers for lifecycle hooks:**
```python
class ObserverProtocol(Protocol):
    """Observer for lifecycle events."""

    async def on_render_start(
        self,
        prompt_id: str,
        version: str,
        variables: Mapping[str, Any],
    ) -> None: ...

    async def on_render_complete(
        self,
        prompt_id: str,
        version: str,
        execution: PromptExecution,
    ) -> None: ...

    async def on_render_error(
        self,
        prompt_id: str,
        version: str,
        error: Exception,
    ) -> None: ...

# In manager
class PromptManager:
    async def render(self, prompt_id: str, variables: Mapping[str, Any]) -> str:
        # Notify observers
        for observer in self._observers:
            await observer.on_render_start(prompt_id, version, variables)

        try:
            result = await self._do_render(prompt_id, variables)

            for observer in self._observers:
                await observer.on_render_complete(prompt_id, version, execution)

            return result
        except Exception as e:
            for observer in self._observers:
                await observer.on_render_error(prompt_id, version, e)
            raise
```

### 8. Structured Logging

**Use structlog for all logging:**
```python
import structlog

logger = structlog.get_logger(__name__)

# Good: Structured logging
logger.info(
    "prompt_rendered",
    prompt_id=prompt_id,
    version=version,
    duration_ms=duration,
    cache_hit=cache_hit,
    success=True,
)

# Bad: String formatting
logger.info(f"Rendered prompt {prompt_id} v{version} in {duration}ms")
```

**Configure structlog:**
```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)
```

## Code Style Guidelines

### Formatting
- **black**: Line length 100, target Python 3.11+
- **Imports**: Use ruff isort (absolute imports, group by stdlib/third-party/local)
- **Docstrings**: Google style with type hints in signature

### Naming Conventions
```python
# Classes: PascalCase
class PromptManager: ...

# Functions/methods: snake_case
async def render_prompt(self, prompt_id: str) -> str: ...

# Constants: UPPER_SNAKE_CASE
DEFAULT_TIMEOUT = 30

# Private: leading underscore
def _internal_method(self) -> None: ...

# Type variables: Single letter or PascalCase with _T suffix
T = TypeVar("T")
PromptT = TypeVar("PromptT", bound=Prompt)
```

### Docstring Format (Google Style)
```python
async def render(
    self,
    prompt_id: str,
    variables: Mapping[str, Any],
    *,
    version: str | None = None,
    use_cache: bool = True,
) -> str:
    """
    Render a prompt with variables.

    Retrieves the prompt from the registry and renders it with the provided
    variables. Optionally uses caching and version pinning.

    Args:
        prompt_id: Unique identifier for the prompt
        variables: Variables to use in rendering
        version: Specific version to render (None for latest)
        use_cache: Whether to use cached results

    Returns:
        Rendered prompt string

    Raises:
        PromptNotFoundError: If prompt doesn't exist
        TemplateRenderError: If rendering fails
        VersionNotFoundError: If specific version doesn't exist

    Examples:
        >>> result = await manager.render(
        ...     "greeting",
        ...     {"name": "Alice", "service": "Support"}
        ... )
        "Hello Alice! Welcome to Support."
    """
    ...
```

## Testing Patterns

### Test Structure
```python
import pytest
from prompt_manager import PromptManager, Prompt

@pytest.fixture
async def manager() -> PromptManager:
    """Create test manager with in-memory storage."""
    storage = InMemoryStorage()
    registry = PromptRegistry(storage=storage)
    return PromptManager(registry=registry)

@pytest.fixture
def sample_prompt() -> Prompt:
    """Create a sample prompt for testing."""
    return Prompt(
        id="test_prompt",
        version="1.0.0",
        format=PromptFormat.TEXT,
        template=PromptTemplate(
            content="Hello {{name}}!",
            variables=["name"],
        ),
    )

class TestPromptManager:
    """Test suite for PromptManager."""

    async def test_render_simple(self, manager: PromptManager, sample_prompt: Prompt) -> None:
        """Test basic prompt rendering."""
        await manager.create_prompt(sample_prompt)

        result = await manager.render("test_prompt", {"name": "World"})

        assert result == "Hello World!"

    async def test_render_missing_variable(
        self, manager: PromptManager, sample_prompt: Prompt
    ) -> None:
        """Test rendering fails with missing variable."""
        await manager.create_prompt(sample_prompt)

        with pytest.raises(TemplateRenderError):
            await manager.render("test_prompt", {})
```

### Test Markers
```python
@pytest.mark.unit
async def test_template_parsing() -> None:
    """Unit test for template parsing."""
    ...

@pytest.mark.integration
async def test_full_workflow() -> None:
    """Integration test for complete workflow."""
    ...

@pytest.mark.benchmark
def test_render_performance(benchmark) -> None:
    """Benchmark test for rendering."""
    ...
```

### Property-Based Testing
```python
from hypothesis import given, strategies as st

@given(st.text(), st.dictionaries(st.text(), st.text()))
async def test_template_never_crashes(template: str, variables: dict[str, str]) -> None:
    """Template engine should handle any input without crashing."""
    engine = TemplateEngine()

    try:
        await engine.render(template, variables)
    except (TemplateError, TemplateRenderError):
        pass  # Expected errors are fine
    # Any other exception fails the test
```

## Performance Guidelines

### Caching Strategy
```python
# Cache expensive operations
class PromptManager:
    async def render(
        self,
        prompt_id: str,
        variables: Mapping[str, Any],
        *,
        use_cache: bool = True,
    ) -> str:
        if use_cache and self._cache:
            cache_key = self._make_cache_key(prompt_id, variables)
            cached = await self._cache.get(cache_key)
            if cached:
                return cached

        result = await self._do_render(prompt_id, variables)

        if use_cache and self._cache:
            await self._cache.set(cache_key, result)

        return result
```

### Async Iteration for Large Datasets
```python
# Good: Async generator
async def list_all(self) -> AsyncIterator[Prompt]:
    """List all prompts without loading into memory."""
    for prompt in self._prompts.values():
        yield prompt

# Use with async for
async for prompt in storage.list_all():
    await process_prompt(prompt)
```

### Avoid Blocking Operations
```python
# Bad: Blocking I/O in async function
async def load_prompt(self, path: Path) -> Prompt:
    with open(path) as f:  # Blocks event loop
        content = f.read()
    return Prompt.model_validate_json(content)

# Good: Async I/O
async def load_prompt(self, path: Path) -> Prompt:
    async with aiofiles.open(path) as f:
        content = await f.read()
    return Prompt.model_validate_json(content)
```

## Security Best Practices

### Input Validation
- Use Pydantic for all external inputs
- Validate patterns with regex (e.g., semver, IDs)
- Reject unexpected fields with `extra="forbid"`

### Template Safety
- Use logic-less templates (Handlebars)
- No arbitrary code execution
- Escape output based on context
- Validate template syntax before saving

### File System Security
```python
from pathlib import Path

# Prevent path traversal
def _validate_path(self, path: Path) -> Path:
    """Ensure path is within allowed directory."""
    resolved = path.resolve()
    if not resolved.is_relative_to(self._base_path):
        raise StorageError("Path outside allowed directory")
    return resolved
```

### Secret Management
- Never store secrets in prompts
- Use environment variables for config
- Add validation to detect potential secrets
- Audit log access to sensitive prompts

## Mypy Configuration

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
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
plugins = ["pydantic.mypy"]

[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
warn_required_dynamic_aliases = true
```

## Tools & Commands

### Development Workflow
```bash
# Install dependencies
poetry install
poetry install -E all  # With all plugins

# Run tests
pytest                              # All tests
pytest -m unit                      # Unit tests only
pytest --cov=prompt_manager         # With coverage
pytest --cov-report=html            # HTML coverage report

# Type checking
mypy src/prompt_manager

# Linting
ruff check src/
ruff check --fix src/               # Auto-fix

# Formatting
black src/
black --check src/                  # Check only

# Security scan
bandit -r src/

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### Build & Package
```bash
# Build package
poetry build

# Publish to PyPI (test)
poetry publish --repository testpypi

# Publish to PyPI (production)
poetry publish
```
