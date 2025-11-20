# Prompt Manager - Python Best Practices

## Python Version Requirements

### Minimum Version: Python 3.11

**Why Python 3.11+:**
- 10-60% performance improvements over 3.10
- Enhanced error messages with better tracebacks
- Exception groups for better async error handling
- Built-in TOML support (tomllib)
- Better type hint support (Self, LiteralString, etc.)
- Faster startup and runtime

**Version-Specific Features Used:**
```python
# Self type (3.11+)
from typing import Self

class Prompt(BaseModel):
    def clone(self) -> Self:  # Returns same type
        return self.model_copy()

# Exception groups (3.11+)
try:
    await process_prompts()
except* PromptError as eg:  # Catch group of exceptions
    for e in eg.exceptions:
        logger.error("prompt_error", error=str(e))
```

## Async/Await Patterns

### Always Use Async for I/O

**Rule: All I/O operations must be async**

```python
# Good: Async file I/O
import aiofiles

async def load_prompt(path: Path) -> Prompt:
    async with aiofiles.open(path, "r") as f:
        content = await f.read()
    return Prompt.model_validate_json(content)

# Bad: Blocking I/O in async context
async def load_prompt(path: Path) -> Prompt:
    with open(path, "r") as f:  # Blocks event loop!
        content = f.read()
    return Prompt.model_validate_json(content)
```

### Concurrent Operations

**Use gather for parallel async operations:**
```python
# Good: Parallel execution
results = await asyncio.gather(
    manager.render("prompt1", vars1),
    manager.render("prompt2", vars2),
    manager.render("prompt3", vars3),
    return_exceptions=True,  # Don't fail all on one error
)

# Bad: Sequential execution
results = []
for prompt_id in prompt_ids:
    result = await manager.render(prompt_id, variables)
    results.append(result)
```

### Async Context Managers

**Implement async context managers for resource management:**
```python
from typing import AsyncIterator

class AsyncPromptLoader:
    async def __aenter__(self) -> Self:
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._cleanup()

# Usage
async with AsyncPromptLoader(path) as loader:
    prompts = await loader.load_all()
```

### Async Generators

**Use async generators for streaming/iteration:**
```python
from collections.abc import AsyncIterator

async def list_prompts(self) -> AsyncIterator[Prompt]:
    """Stream prompts without loading all into memory."""
    for prompt_id in self._index:
        prompt = await self._load(prompt_id)
        yield prompt

# Usage
async for prompt in storage.list_prompts():
    await process_prompt(prompt)
```

### Error Handling in Async

**Proper async exception handling:**
```python
async def render_with_retry(
    self,
    prompt_id: str,
    variables: Mapping[str, Any],
    max_retries: int = 3,
) -> str:
    for attempt in range(max_retries):
        try:
            return await self.render(prompt_id, variables)
        except TemplateRenderError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            continue
    raise RuntimeError("Unreachable")
```

## Type Hints & Type Safety

### Complete Type Coverage

**Every function must have complete type hints:**
```python
# Good: Complete types
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

### Use Specific Collection Types

**Prefer Mapping/Sequence over dict/list in signatures:**
```python
from collections.abc import Mapping, Sequence, AsyncIterator

# Good: Accepts any mapping
def process_vars(variables: Mapping[str, Any]) -> None:
    for key, value in variables.items():
        ...

# Bad: Requires exact type
def process_vars(variables: dict[str, Any]) -> None:
    ...
```

### Type Variables for Generics

**Use TypeVar for generic functions:**
```python
from typing import TypeVar

T = TypeVar("T")

async def cache_get_or_compute(
    key: str,
    compute_fn: Callable[[], Awaitable[T]],
) -> T:
    """Generic caching with type preservation."""
    cached = await self._cache.get(key)
    if cached is not None:
        return cached
    result = await compute_fn()
    await self._cache.set(key, result)
    return result
```

### Literal Types for Constants

**Use Literal for limited string values:**
```python
from typing import Literal

PromptFormatType = Literal["text", "chat", "completion", "instruction"]

def validate_format(format: PromptFormatType) -> bool:
    # Type checker knows all possible values
    return True
```

### Protocol for Structural Typing

**Use Protocol instead of ABC for interfaces:**
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Renderable(Protocol):
    """Anything that can be rendered."""

    async def render(self, variables: Mapping[str, Any]) -> str:
        ...

# No inheritance needed
class MyTemplate:
    async def render(self, variables: Mapping[str, Any]) -> str:
        return "result"

# Type checker accepts it
def process(renderable: Renderable) -> None:
    isinstance(renderable, Renderable)  # Works at runtime too
```

### Type Narrowing

**Use type guards for narrowing:**
```python
from typing import TypeGuard

def is_chat_prompt(prompt: Prompt) -> TypeGuard[ChatPrompt]:
    """Type guard for chat prompts."""
    return prompt.format == PromptFormat.CHAT

def process_prompt(prompt: Prompt) -> None:
    if is_chat_prompt(prompt):
        # Type checker knows prompt is ChatPrompt here
        messages = prompt.chat_template.messages
```

## Pydantic Best Practices

### Model Configuration

**Use ConfigDict for model configuration:**
```python
from pydantic import BaseModel, ConfigDict

class Prompt(BaseModel):
    model_config = ConfigDict(
        frozen=False,           # Allow mutations
        extra="forbid",         # No extra fields
        validate_assignment=True,  # Validate on field changes
        str_strip_whitespace=True,  # Strip strings
        use_enum_values=False,  # Keep enum types
    )
```

### Field Validation

**Use field validators for complex validation:**
```python
from pydantic import BaseModel, field_validator, model_validator

class Prompt(BaseModel):
    version: str

    @field_validator("version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        """Validate semantic version."""
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError("Invalid semver format")
        return v

    @model_validator(mode="after")
    def validate_template(self) -> Self:
        """Cross-field validation."""
        if not self.template and not self.chat_template:
            raise ValueError("Must have template or chat_template")
        return self
```

### Immutable Models

**Use frozen models for immutability:**
```python
class Message(BaseModel):
    """Immutable message - cannot be changed after creation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Role
    content: str

# Cannot modify
message = Message(role=Role.USER, content="Hello")
message.content = "World"  # Raises ValidationError
```

### Serialization

**Use Pydantic serialization methods:**
```python
# Serialize to dict
prompt_dict = prompt.model_dump()
prompt_dict_json = prompt.model_dump(mode="json")  # JSON-compatible

# Serialize to JSON
prompt_json = prompt.model_dump_json()

# Deserialize
prompt = Prompt.model_validate(data)
prompt = Prompt.model_validate_json(json_str)
```

### Custom Types

**Create custom Pydantic types:**
```python
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

class SemanticVersion:
    """Custom semantic version type."""

    def __init__(self, version: str) -> None:
        parts = version.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError("Invalid semver")
        self.major, self.minor, self.patch = map(int, parts)
        self.version = version

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.str_schema(),
        )

class Prompt(BaseModel):
    version: SemanticVersion
```

## Error Handling

### Exception Hierarchy

**Create specific exceptions with context:**
```python
class PromptManagerError(Exception):
    """Base exception with context."""

    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(message)
        self.message = message
        self.context = context

    def __str__(self) -> str:
        if self.context:
            ctx = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            return f"{self.message} ({ctx})"
        return self.message

class PromptNotFoundError(PromptManagerError):
    """Specific error with typed context."""

    def __init__(self, prompt_id: str, version: str | None = None) -> None:
        msg = f"Prompt '{prompt_id}' not found"
        if version:
            msg += f" (version: {version})"
        super().__init__(msg, prompt_id=prompt_id, version=version)
```

### Exception Handling Patterns

**Handle exceptions at appropriate level:**
```python
# Good: Handle at boundary, log with context
async def render(self, prompt_id: str, variables: Mapping[str, Any]) -> str:
    try:
        prompt = await self._registry.get(prompt_id)
        result = await self._template_engine.render(
            prompt.template.content,
            variables,
        )
        return result
    except PromptNotFoundError:
        logger.error("prompt_not_found", prompt_id=prompt_id)
        raise  # Re-raise for caller to handle
    except TemplateRenderError as e:
        logger.error("render_failed", error=str(e), **e.context)
        raise

# Bad: Silent exception swallowing
async def render(self, prompt_id: str, variables: Mapping[str, Any]) -> str:
    try:
        return await self._do_render(prompt_id, variables)
    except Exception:
        return ""  # Lost error information!
```

### Context Managers for Cleanup

**Use context managers for resource cleanup:**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def transaction(self) -> AsyncIterator[None]:
    """Transaction context manager."""
    await self._begin()
    try:
        yield
        await self._commit()
    except Exception:
        await self._rollback()
        raise
    finally:
        await self._close()

# Usage
async with storage.transaction():
    await storage.save(prompt)
```

## Code Organization

### Function Length

**Keep functions focused and short:**
```python
# Good: Single responsibility
async def render_prompt(
    self,
    prompt_id: str,
    variables: Mapping[str, Any],
) -> str:
    """Render a prompt with variables."""
    prompt = await self._get_prompt(prompt_id)
    validated_vars = self._validate_variables(prompt, variables)
    return await self._render_template(prompt, validated_vars)

# Bad: Too many responsibilities
async def render_prompt(self, prompt_id: str, variables: dict) -> str:
    # 100+ lines of logic mixing concerns
    ...
```

### Class Design

**Prefer composition over inheritance:**
```python
# Good: Composition with dependency injection
class PromptManager:
    def __init__(
        self,
        registry: PromptRegistry,
        template_engine: TemplateEngineProtocol,
        version_store: VersionStoreProtocol,
    ) -> None:
        self._registry = registry
        self._template_engine = template_engine
        self._version_store = version_store

# Bad: Deep inheritance hierarchy
class PromptManager(BaseManager, Renderable, Versionable):
    ...
```

### Module Organization

**One primary class per file, related helpers inline:**
```python
# prompt_manager/core/registry.py

class PromptRegistry:
    """Main registry class - primary export."""
    ...

class _PromptIndex:
    """Internal helper - not exported."""
    ...

def _validate_prompt_id(prompt_id: str) -> None:
    """Internal helper function."""
    ...
```

## Performance Patterns

### Lazy Evaluation

**Defer expensive operations:**
```python
from functools import cached_property

class Prompt(BaseModel):
    template: PromptTemplate

    @cached_property
    def variable_set(self) -> set[str]:
        """Compute once, cache result."""
        return set(self.template.variables)
```

### Generator Expressions

**Use generators for large datasets:**
```python
# Good: Generator (memory efficient)
total_tokens = sum(
    len(prompt.template.content.split())
    for prompt in prompts
)

# Bad: List comprehension (loads all in memory)
total_tokens = sum([
    len(prompt.template.content.split())
    for prompt in prompts
])
```

### Avoid Premature Optimization

**Profile before optimizing:**
```python
import cProfile
import pstats

# Profile code
profiler = cProfile.Profile()
profiler.enable()

# Run code
await manager.render(prompt_id, variables)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats("cumulative")
stats.print_stats(10)
```

### Caching Strategies

**Cache expensive computations:**
```python
from functools import lru_cache

@lru_cache(maxsize=1024)
def parse_template(template: str) -> ParsedTemplate:
    """Cache template parsing."""
    return compiler.compile(template)

# Or use instance-level cache
class TemplateEngine:
    def __init__(self) -> None:
        self._compiled_cache: dict[str, ParsedTemplate] = {}

    async def render(self, template: str, variables: Mapping[str, Any]) -> str:
        if template not in self._compiled_cache:
            self._compiled_cache[template] = parse_template(template)
        compiled = self._compiled_cache[template]
        return compiled.render(variables)
```

## Testing Patterns

### Fixture Organization

**Create reusable fixtures:**
```python
import pytest
from prompt_manager import PromptManager, PromptRegistry, InMemoryStorage

@pytest.fixture
def storage() -> InMemoryStorage:
    """In-memory storage for tests."""
    return InMemoryStorage()

@pytest.fixture
def registry(storage: InMemoryStorage) -> PromptRegistry:
    """Registry with test storage."""
    return PromptRegistry(storage=storage)

@pytest.fixture
async def manager(registry: PromptRegistry) -> PromptManager:
    """Fully configured test manager."""
    manager = PromptManager(registry=registry)
    # Add test prompts
    await manager.create_prompt(create_test_prompt("greeting"))
    return manager
```

### Parametrized Tests

**Test multiple cases efficiently:**
```python
import pytest

@pytest.mark.parametrize(
    "template,variables,expected",
    [
        ("Hello {{name}}", {"name": "World"}, "Hello World"),
        ("{{a}} + {{b}}", {"a": 1, "b": 2}, "1 + 2"),
        ("No variables", {}, "No variables"),
    ],
)
async def test_template_rendering(
    template: str,
    variables: dict[str, Any],
    expected: str,
) -> None:
    engine = TemplateEngine()
    result = await engine.render(template, variables)
    assert result == expected
```

### Async Test Patterns

**Use pytest-asyncio for async tests:**
```python
import pytest

@pytest.mark.asyncio
async def test_async_operation() -> None:
    """Test async operations."""
    result = await async_function()
    assert result == expected

# Or use auto mode in pytest.ini
# asyncio_mode = auto
async def test_auto_async() -> None:
    """Automatically detected as async."""
    ...
```

### Mock Async Functions

**Mock async dependencies:**
```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_storage() -> AsyncMock:
    """Mock storage backend."""
    storage = AsyncMock(spec=StorageBackendProtocol)
    storage.load.return_value = create_test_prompt()
    return storage

async def test_with_mock(mock_storage: AsyncMock) -> None:
    registry = PromptRegistry(storage=mock_storage)
    prompt = await registry.get("test")
    mock_storage.load.assert_called_once_with("test", None)
```

### Property-Based Testing

**Use Hypothesis for edge cases:**
```python
from hypothesis import given, strategies as st

@given(
    template=st.text(),
    variables=st.dictionaries(st.text(), st.text()),
)
async def test_render_never_crashes(
    template: str,
    variables: dict[str, str],
) -> None:
    """Template engine should handle any input gracefully."""
    engine = TemplateEngine()
    try:
        await engine.render(template, variables)
    except (TemplateError, TemplateRenderError):
        pass  # Expected errors are OK
    # Any other exception fails the test
```

## Logging Best Practices

### Structured Logging

**Always use structured logging:**
```python
import structlog

logger = structlog.get_logger(__name__)

# Good: Structured with context
logger.info(
    "prompt_rendered",
    prompt_id=prompt_id,
    version=version,
    duration_ms=duration,
    cache_hit=cache_hit,
)

# Bad: String interpolation
logger.info(f"Rendered {prompt_id} v{version} in {duration}ms")
```

### Log Levels

**Use appropriate log levels:**
```python
# DEBUG: Detailed diagnostic information
logger.debug("template_compiled", template_hash=hash)

# INFO: General informational messages
logger.info("prompt_created", prompt_id=prompt_id, version=version)

# WARNING: Warning messages for recoverable issues
logger.warning("cache_miss", prompt_id=prompt_id)

# ERROR: Error messages for failures
logger.error("render_failed", prompt_id=prompt_id, error=str(e))

# CRITICAL: Critical errors requiring immediate attention
logger.critical("storage_corrupted", path=path)
```

### Context Management

**Add context to all logs in scope:**
```python
from structlog import contextvars

# Bind context for all logs in this scope
contextvars.bind_contextvars(request_id=request_id, user_id=user_id)

logger.info("operation_started")  # Includes request_id and user_id
logger.info("operation_completed")  # Includes request_id and user_id

# Clear context when done
contextvars.clear_contextvars()
```

## Security Best Practices

### Input Validation

**Validate all external inputs:**
```python
from pydantic import BaseModel, Field, field_validator

class PromptCreateRequest(BaseModel):
    """Validated API request."""

    id: str = Field(..., pattern=r"^[a-z0-9_-]+$", min_length=1, max_length=100)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    template: str = Field(..., min_length=1, max_length=10000)

    @field_validator("template")
    @classmethod
    def no_secrets(cls, v: str) -> str:
        """Detect potential secrets."""
        if "api_key" in v.lower() or "password" in v.lower():
            raise ValueError("Template may contain secrets")
        return v
```

### Path Validation

**Prevent path traversal:**
```python
from pathlib import Path

def validate_path(self, path: Path) -> Path:
    """Ensure path is within allowed directory."""
    resolved = path.resolve()
    if not resolved.is_relative_to(self._base_path):
        raise StorageError("Path traversal attempt")
    return resolved
```

### Template Safety

**Use logic-less templates:**
```python
# Good: Logic-less Handlebars
"Hello {{name}}!"

# Bad: Logic in templates (Jinja2-style)
"Hello {% if premium %}Premium {% endif %}{{name}}!"
```

## Documentation Patterns

### Docstring Format

**Use Google-style docstrings:**
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

    Retrieves the prompt from the registry and renders it using the template
    engine. Optionally uses caching for improved performance.

    Args:
        prompt_id: Unique identifier for the prompt
        variables: Dictionary of variables to substitute in template
        version: Specific version to render. If None, uses latest version.
        use_cache: Whether to use cached rendered results

    Returns:
        Rendered prompt string with variables substituted

    Raises:
        PromptNotFoundError: If the prompt doesn't exist
        VersionNotFoundError: If the specified version doesn't exist
        TemplateRenderError: If template rendering fails

    Examples:
        >>> result = await manager.render(
        ...     "greeting",
        ...     {"name": "Alice", "service": "Support"},
        ... )
        "Hello Alice! Welcome to Support."

        >>> result = await manager.render(
        ...     "greeting",
        ...     {"name": "Bob"},
        ...     version="1.0.0",
        ... )
        "Hello Bob! Welcome to our service."
    """
    ...
```

### Type Hints as Documentation

**Type hints document expected types:**
```python
# Type hints make the signature self-documenting
async def create_prompt(
    self,
    prompt: Prompt,
    *,
    changelog: str | None = None,
) -> Prompt:
    """Create a new prompt with optional changelog."""
    # Types tell the story
```

## Common Antipatterns to Avoid

### Avoid Mutable Default Arguments

```python
# Bad: Mutable default
def add_tag(self, tags: list[str] = []) -> None:
    tags.append("new")  # Modifies shared default!

# Good: Use None and create new list
def add_tag(self, tags: list[str] | None = None) -> None:
    if tags is None:
        tags = []
    tags.append("new")

# Better: Use immutable default
def add_tag(self, tags: tuple[str, ...] = ()) -> None:
    tags = list(tags) + ["new"]
```

### Avoid Bare Except

```python
# Bad: Catches everything including KeyboardInterrupt
try:
    result = await operation()
except:
    pass

# Good: Catch specific exceptions
try:
    result = await operation()
except (PromptError, TemplateError) as e:
    logger.error("operation_failed", error=str(e))
    raise
```

### Avoid String Type Checking

```python
# Bad: String comparison
if type(obj).__name__ == "Prompt":
    ...

# Good: isinstance
if isinstance(obj, Prompt):
    ...

# Better: Protocol-based
if isinstance(obj, RenderableProtocol):
    ...
```

### Avoid Blocking in Async

```python
# Bad: Blocking call in async function
async def process(self) -> None:
    time.sleep(1)  # Blocks event loop!
    result = requests.get(url)  # Blocks event loop!

# Good: Use async libraries
async def process(self) -> None:
    await asyncio.sleep(1)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            result = await resp.json()
```
