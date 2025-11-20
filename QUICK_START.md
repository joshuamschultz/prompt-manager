# Quick Start Guide

Get up and running with Prompt Manager in 5 minutes.

## Installation

```bash
# Install with Poetry (recommended)
poetry add prompt-manager

# Or with pip
pip install prompt-manager

# With optional plugins
poetry add prompt-manager -E all
```

## Basic Usage

### 1. Simple Text Prompt

```python
import asyncio
from prompt_manager import PromptManager, Prompt
from prompt_manager.core.models import PromptFormat, PromptTemplate
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.storage import InMemoryStorage

async def main():
    # Setup
    storage = InMemoryStorage()
    registry = PromptRegistry(storage=storage)
    manager = PromptManager(registry=registry)

    # Create prompt
    prompt = Prompt(
        id="greeting",
        version="1.0.0",
        format=PromptFormat.TEXT,
        template=PromptTemplate(
            content="Hello {{name}}! Welcome to {{service}}.",
            variables=["name", "service"],
        ),
    )

    # Register and render
    await manager.create_prompt(prompt)
    result = await manager.render(
        "greeting",
        {"name": "Alice", "service": "Prompt Manager"},
    )
    print(result)  # "Hello Alice! Welcome to Prompt Manager."

asyncio.run(main())
```

### 2. Chat Prompt

```python
from prompt_manager.core.models import ChatPromptTemplate, Message, Role

chat_prompt = Prompt(
    id="support",
    version="1.0.0",
    format=PromptFormat.CHAT,
    chat_template=ChatPromptTemplate(
        messages=[
            Message(
                role=Role.SYSTEM,
                content="You are a helpful assistant for {{company}}.",
            ),
            Message(
                role=Role.USER,
                content="{{query}}",
            ),
        ],
        variables=["company", "query"],
    ),
)

await manager.create_prompt(chat_prompt)
result = await manager.render(
    "support",
    {"company": "Acme", "query": "I need help!"},
)
```

### 3. Load from YAML

```yaml
# prompts.yaml
version: "1.0.0"
prompts:
  - id: welcome
    version: "1.0.0"
    format: text
    template:
      content: "Welcome {{name}}!"
      variables: [name]
```

```python
from prompt_manager.storage import YAMLLoader
from pathlib import Path

loader = YAMLLoader(registry)
await loader.import_to_registry(Path("prompts.yaml"))
```

### 4. Version Management

```python
# Create v1
prompt = Prompt(id="feature", version="1.0.0", ...)
await manager.create_prompt(prompt, changelog="Initial version")

# Update to v2
prompt.template.content = "Updated content"
await manager.update_prompt(
    prompt,
    bump_version=True,
    changelog="Improved message",
)

# Get history
history = await manager.get_history("feature")
for v in history:
    print(f"{v.version}: {v.changelog}")
```

### 5. Add Observability

```python
from prompt_manager.observability import LoggingObserver, MetricsCollector

# Add observers
logging_obs = LoggingObserver()
metrics = MetricsCollector()

manager = PromptManager(
    registry=registry,
    metrics=metrics,
    observers=[logging_obs],
)

# Later, get metrics
metrics_data = await manager.get_metrics()
print(f"Total renders: {metrics_data['operations']['summary']['total_renders']}")
```

## Common Patterns

### File Storage

```python
from prompt_manager.storage import FileSystemStorage
from pathlib import Path

storage = FileSystemStorage(Path("./prompts"))
registry = PromptRegistry(storage=storage)
manager = PromptManager(registry=registry)
```

### Filtering Prompts

```python
# By tags
prompts = await manager.list_prompts(tags=["production"])

# By status
prompts = await manager.list_prompts(status="active")

# By category
prompts = await manager.list_prompts(category="support")
```

### Error Handling

```python
from prompt_manager.exceptions import PromptNotFoundError, TemplateRenderError

try:
    result = await manager.render("prompt_id", variables)
except PromptNotFoundError as e:
    print(f"Prompt not found: {e.context['prompt_id']}")
except TemplateRenderError as e:
    print(f"Render failed: {e.message}")
```

### With Version Store

```python
from prompt_manager.versioning import VersionStore
from pathlib import Path

version_store = VersionStore(Path("./versions"))
manager = PromptManager(
    registry=registry,
    version_store=version_store,
)

# Now you get full version history
versions = await manager.get_history("prompt_id")
```

## Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/prompt-manager
cd prompt-manager

# Install dependencies
make install-all

# Run tests
make test

# Run linters
make lint

# Format code
make format

# Type check
make type-check
```

## Key Concepts

### Models
- `Prompt`: Main prompt with template and metadata
- `PromptTemplate`: Text template configuration
- `ChatPromptTemplate`: Chat message templates
- `PromptVersion`: Version with changelog

### Components
- `PromptManager`: Main API (orchestrator)
- `PromptRegistry`: In-memory prompt storage
- `TemplateEngine`: Handlebars rendering
- `VersionStore`: Version history tracking

### Protocols
- `StorageBackendProtocol`: Storage interface
- `PluginProtocol`: Plugin interface
- `ObserverProtocol`: Lifecycle hooks

## Configuration

### Settings with Pydantic

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    storage_path: Path = Path("./prompts")
    cache_enabled: bool = True
    log_level: str = "INFO"

settings = Settings()
```

## Tips

1. **Use async/await**: All operations are async
2. **Type hints**: Full type safety with mypy
3. **Versioning**: Always use semantic versioning
4. **Observability**: Add observers for production
5. **Caching**: Enable caching for frequently used prompts
6. **Testing**: Use InMemoryStorage for tests

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for design details
- See [examples/](examples/) for more examples
- Check [RECOMMENDATIONS.md](RECOMMENDATIONS.md) for best practices
- Review [API Reference](docs/api.md) for detailed docs

## Common Issues

### ImportError
```bash
# Make sure package is installed
poetry install
# Or
pip install -e .
```

### Type Errors
```bash
# Run mypy to check types
mypy src/prompt_manager
```

### Test Failures
```bash
# Run tests with verbose output
pytest -v
```

## Help

- GitHub Issues: Bug reports
- Discussions: Questions
- Documentation: Full guides
- Examples: Real usage

## License

MIT License - See LICENSE file
