# Contributing to Prompt Manager

Thank you for your interest in contributing to Prompt Manager! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Poetry 1.8+
- Git

### Getting Started

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/prompt-manager.git
cd prompt-manager
```

2. **Install dependencies**

```bash
# Generate lock file (first time only)
poetry lock

# Install all dependencies including dev tools and all framework extras
poetry install --with dev -E all

# Or install specific extras only
poetry install --with dev -E openai
```

3. **Install pre-commit hooks**

```bash
# Using make (if available)
make pre-commit-install

# Or manually
poetry run pre-commit install
```

4. **Verify installation**

```bash
# Run tests to verify setup
poetry run pytest

# Check that imports work
poetry run python -c "import prompt_manager; print(prompt_manager.__version__)"
```

## Development Workflow

### Running Tests

```bash
# Run all tests
make test
# Or: poetry run pytest

# Run unit tests only
make test-unit
# Or: poetry run pytest -m unit

# Run integration tests only
make test-integration
# Or: poetry run pytest -m integration

# Run with coverage report
make test-cov
# Or: poetry run pytest --cov=prompt_manager --cov-report=html

# Run specific test file
poetry run pytest tests/core/test_manager.py

# Run specific test function
poetry run pytest tests/core/test_manager.py::test_render_prompt
```

### Code Quality

```bash
# Run all quality checks
make ci
# Or run individually:

# Linting
make lint
# Or: poetry run ruff check src/

# Format code
make format
# Or: poetry run black src/ tests/

# Type checking
make type-check
# Or: poetry run mypy src/

# Security scanning
make security
# Or: poetry run bandit -r src/
# Or: poetry run safety check
```

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **Mypy**: Type checking
- **Trailing whitespace**: Remove trailing whitespace
- **End of file**: Ensure files end with newline

To run manually:

```bash
poetry run pre-commit run --all-files
```

## Code Standards

### Type Hints

All functions must have complete type annotations:

```python
# Good
async def render(
    self,
    prompt_id: str,
    variables: Mapping[str, Any],
    *,
    version: str | None = None,
) -> str:
    ...

# Bad - missing type hints
async def render(self, prompt_id, variables, version=None):
    ...
```

### Docstrings

Use Google-style docstrings for all public classes and methods:

```python
def convert(
    self,
    prompt: Prompt,
    variables: Mapping[str, Any],
) -> list[OpenAIMessage]:
    """
    Convert prompt to OpenAI message format.

    Args:
        prompt: Prompt to convert
        variables: Variables for rendering

    Returns:
        List of OpenAI-compatible message dictionaries

    Raises:
        IntegrationError: If conversion fails
        ConversionError: If template rendering fails

    Example:
        >>> integration = OpenAIIntegration(template_engine)
        >>> messages = await integration.convert(prompt, {"name": "Alice"})
        >>> print(messages[0]["role"])
        "system"
    """
    ...
```

### Testing Requirements

- **Coverage**: Minimum 90% line coverage, 85% branch coverage
- **Test Types**: Unit tests for all functions, integration tests for workflows
- **Fixtures**: Use pytest fixtures for common setup
- **Markers**: Use `@pytest.mark.unit` or `@pytest.mark.integration`
- **Async Tests**: Use `@pytest.mark.asyncio` for async functions
- **Dual Interface**: Test both sync and async modes

Example test structure:

```python
import pytest
from prompt_manager.core.manager import PromptManager

@pytest.fixture
def manager(registry):
    """Create PromptManager instance for testing."""
    return PromptManager(registry=registry)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_render_text_prompt(manager):
    """Test rendering a simple text prompt."""
    # Arrange
    prompt = create_text_prompt()
    await manager.create_prompt(prompt)

    # Act
    result = await manager.render("test", {"name": "Alice"})

    # Assert
    assert "Alice" in result
    assert isinstance(result, str)
```

## Testing Dual Sync/Async Interface

The dual interface allows methods to work with or without `await`. When contributing code that uses the dual interface, follow these testing guidelines.

### Test Pattern: Both Sync and Async

All dual interface methods should be tested in both sync and async modes:

```python
import pytest
import asyncio
from prompt_manager import PromptManager

def test_sync_render():
    """Test synchronous rendering."""
    manager = PromptManager.create()
    manager.create_prompt({...})

    # Sync call - no await
    result = manager.render("test", {"name": "Alice"})

    assert "Alice" in result
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_async_render():
    """Test asynchronous rendering."""
    manager = await PromptManager.create()
    await manager.create_prompt({...})

    # Async call - with await
    result = await manager.render("test", {"name": "Alice"})

    assert "Alice" in result
    assert isinstance(result, str)


def test_sync_async_equivalence():
    """Test that sync and async produce identical results."""
    # Sync execution
    manager_sync = PromptManager.create()
    manager_sync.create_prompt({...})
    result_sync = manager_sync.render("test", {"name": "Alice"})

    # Async execution
    async def async_flow():
        manager = await PromptManager.create()
        await manager.create_prompt({...})
        return await manager.render("test", {"name": "Alice"})

    result_async = asyncio.run(async_flow())

    # Should be identical
    assert result_sync == result_async
```

### Fixture Pattern

Create separate fixtures for sync and async managers:

```python
import pytest
from prompt_manager import PromptManager

@pytest.fixture
def sync_manager():
    """Create synchronous manager."""
    return PromptManager.create()


@pytest.fixture
async def async_manager():
    """Create asynchronous manager."""
    return await PromptManager.create()


# Use in tests
def test_with_sync_manager(sync_manager):
    """Test using sync manager."""
    result = sync_manager.render("test", {})
    assert result is not None


@pytest.mark.asyncio
async def test_with_async_manager(async_manager):
    """Test using async manager."""
    result = await async_manager.render("test", {})
    assert result is not None
```

### Testing Error Handling

Verify that errors are raised identically in both modes:

```python
import pytest
from prompt_manager import PromptManager
from prompt_manager.exceptions import PromptNotFoundError

def test_sync_error_handling():
    """Test sync mode error handling."""
    manager = PromptManager.create()

    with pytest.raises(PromptNotFoundError):
        manager.render("nonexistent", {})


@pytest.mark.asyncio
async def test_async_error_handling():
    """Test async mode error handling."""
    manager = await PromptManager.create()

    with pytest.raises(PromptNotFoundError):
        await manager.render("nonexistent", {})
```

### Testing Concurrent Operations

For async mode, test concurrent execution:

```python
import pytest
import asyncio
from prompt_manager import PromptManager

@pytest.mark.asyncio
async def test_concurrent_rendering():
    """Test concurrent prompt rendering."""
    manager = await PromptManager.create()
    await manager.create_prompt({...})

    # Render 10 prompts concurrently
    tasks = [
        manager.render("test", {"name": f"User{i}"})
        for i in range(10)
    ]
    results = await asyncio.gather(*tasks)

    assert len(results) == 10
    assert all("User" in r for r in results)
```

### Type Checking in Tests

The dual interface returns `Union[T, Awaitable[T]]`. In tests, type checkers may show warnings. This is expected:

```python
# Type checker may warn, but this is correct
result = manager.render("test", {})  # Returns str in sync context

# Type checker understands this
result = await manager.render("test", {})  # Returns str in async context

# Optional: Use type assertions if needed
from typing import cast
result = cast(str, manager.render("test", {}))
```

### What to Test

When adding dual interface support to a new method:

1. **Sync execution**: Test method works without `await`
2. **Async execution**: Test method works with `await`
3. **Equivalence**: Verify both modes produce identical results
4. **Error handling**: Test errors raised identically in both modes
5. **Edge cases**: Test with empty inputs, missing data, etc.
6. **Performance**: Verify no significant performance regression

### Example: Complete Test Suite

```python
import pytest
import asyncio
from prompt_manager import PromptManager
from prompt_manager.exceptions import PromptNotFoundError

class TestDualInterfaceRender:
    """Test dual interface for render method."""

    def test_sync_render_success(self):
        """Test successful sync rendering."""
        manager = PromptManager.create()
        manager.create_prompt({
            "id": "test",
            "version": "1.0.0",
            "template": {"content": "Hello {{name}}!"}
        })

        result = manager.render("test", {"name": "Alice"})
        assert result == "Hello Alice!"

    @pytest.mark.asyncio
    async def test_async_render_success(self):
        """Test successful async rendering."""
        manager = await PromptManager.create()
        await manager.create_prompt({
            "id": "test",
            "version": "1.0.0",
            "template": {"content": "Hello {{name}}!"}
        })

        result = await manager.render("test", {"name": "Alice"})
        assert result == "Hello Alice!"

    def test_sync_render_not_found(self):
        """Test sync rendering with non-existent prompt."""
        manager = PromptManager.create()

        with pytest.raises(PromptNotFoundError):
            manager.render("nonexistent", {})

    @pytest.mark.asyncio
    async def test_async_render_not_found(self):
        """Test async rendering with non-existent prompt."""
        manager = await PromptManager.create()

        with pytest.raises(PromptNotFoundError):
            await manager.render("nonexistent", {})

    def test_sync_async_equivalence(self):
        """Test that sync and async produce identical results."""
        # Sync
        manager_sync = PromptManager.create()
        manager_sync.create_prompt({
            "id": "test",
            "version": "1.0.0",
            "template": {"content": "Hello {{name}}!"}
        })
        result_sync = manager_sync.render("test", {"name": "Alice"})

        # Async
        async def async_flow():
            manager = await PromptManager.create()
            await manager.create_prompt({
                "id": "test",
                "version": "1.0.0",
                "template": {"content": "Hello {{name}}!"}
            })
            return await manager.render("test", {"name": "Alice"})

        result_async = asyncio.run(async_flow())

        # Verify equivalence
        assert result_sync == result_async

    @pytest.mark.asyncio
    async def test_concurrent_rendering(self):
        """Test concurrent async rendering."""
        manager = await PromptManager.create()
        await manager.create_prompt({
            "id": "test",
            "version": "1.0.0",
            "template": {"content": "Hello {{name}}!"}
        })

        # Render 10 times concurrently
        tasks = [
            manager.render("test", {"name": f"User{i}"})
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(f"User{i}" in results[i] for i in range(10))
```

### Reference Documentation

For more details on the dual interface implementation and patterns:

- [TYPE_CHECKING.md](TYPE_CHECKING.md) - Type checking patterns and configuration
- [MIGRATION.md](MIGRATION.md) - Migration guide from async-only to dual interface
- [docs/BEST_PRACTICES.md](docs/BEST_PRACTICES.md) - When to use sync vs async
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common issues and solutions

### Code Style

- **Line length**: 88 characters (Black default)
- **Imports**: Sorted with isort/ruff
- **Strings**: Double quotes for strings, single quotes for small literals
- **Async/Await**: Use async/await throughout, no blocking operations
- **Error Handling**: Raise descriptive exceptions with context

## Creating Framework Integrations

See [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) for detailed guide on creating custom framework integrations.

### Quick Overview

1. **Extend BaseIntegration**

```python
from prompt_manager.integrations.base import BaseIntegration

class MyFrameworkIntegration(BaseIntegration[MyFrameworkType]):
    async def convert(self, prompt: Prompt, variables: Mapping[str, Any]) -> MyFrameworkType:
        # Implement conversion logic
        ...

    def validate_compatibility(self, prompt: Prompt) -> bool:
        # Check if prompt is compatible
        ...
```

2. **Create Plugin (Optional)**

```python
from prompt_manager.plugins.base import BasePlugin

class MyFrameworkPlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="myframework", version="1.0.0")

    async def _initialize_impl(self, config):
        self._integration = MyFrameworkIntegration(...)
```

3. **Register Entry Point**

In your package's `pyproject.toml`:

```toml
[tool.poetry.plugins."prompt_manager.plugins"]
myframework = "my_package.plugins:MyFrameworkPlugin"
```

## Submitting Changes

### Pull Request Process

1. **Create a feature branch**

```bash
git checkout -b feature/my-new-feature
# Or: git checkout -b fix/bug-description
```

2. **Make changes with tests**

- Write code following style guidelines
- Add unit tests for new functionality
- Add integration tests for workflows
- Update documentation if needed
- Add changelog entry (see below)

3. **Ensure all checks pass**

```bash
# Run all quality checks
make ci

# Verify tests pass
poetry run pytest

# Check coverage
poetry run pytest --cov=prompt_manager --cov-report=term-missing
```

4. **Commit changes**

```bash
# Pre-commit hooks will run automatically
git add .
git commit -m "feat: add new framework integration"

# Or for bug fixes:
git commit -m "fix: resolve template rendering issue"
```

5. **Push and create PR**

```bash
git push origin feature/my-new-feature
```

Then create a pull request on GitHub with:
- Clear description of changes
- Link to related issues
- Screenshots (if UI changes)
- Test results
- Breaking changes (if any)

### Commit Message Format

Follow conventional commits:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions or changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

Examples:
```
feat: add Anthropic SDK integration
fix: resolve chat template rendering bug
docs: update integration guide with examples
test: add unit tests for OpenAI integration
refactor: simplify template engine caching
```

### Changelog

For significant changes, add entry to CHANGELOG.md under `[Unreleased]`:

```markdown
## [Unreleased]

### Added
- New framework integration for XYZ

### Fixed
- Template rendering issue with nested variables

### Changed
- Improved error messages for integration failures
```

## Code Review

All submissions require review. We review:

- **Code quality**: Following style guidelines and best practices
- **Tests**: Adequate test coverage and passing tests
- **Documentation**: Clear docstrings and updated guides
- **Breaking changes**: Properly documented and justified
- **Performance**: No performance regressions

## Community Guidelines

- **Be respectful**: Treat all contributors with respect
- **Be constructive**: Provide helpful feedback in reviews
- **Be patient**: Maintainers are volunteers
- **Be clear**: Explain your reasoning and ask questions
- **Be collaborative**: Work together to improve the project

## Getting Help

- **Documentation**: Check README.md and docs/ directory
- **Issues**: Search existing issues for similar problems
- **Discussions**: Use GitHub Discussions for questions
- **Examples**: Review examples/ directory for usage patterns

## Recognition

Contributors will be acknowledged in:
- GitHub contributors list
- Release notes for significant contributions
- CHANGELOG.md for feature additions

Thank you for contributing to Prompt Manager!

---

**Last Updated**: 2025-01-25
