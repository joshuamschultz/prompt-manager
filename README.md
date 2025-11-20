# Prompt Manager

[![PyPI version](https://badge.fury.io/py/agentic-prompt-manager.svg)](https://badge.fury.io/py/agentic-prompt-manager)
[![Python Version](https://img.shields.io/pypi/pyversions/agentic-prompt-manager.svg)](https://pypi.org/project/agentic-prompt-manager/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/github/actions/workflow/status/joshuamschultz/prompt-manager/test.yml?branch=master)](https://github.com/joshuamschultz/prompt-manager/actions)
[![Coverage](https://img.shields.io/codecov/c/github/joshuamschultz/prompt-manager)](https://codecov.io/gh/joshuamschultz/prompt-manager)

A modern, production-ready Python 3.11+ prompt management system with Pydantic v2 validation, YAML schema support, Handlebars templating, plugin architecture, and comprehensive observability.

## Features

- **Type-Safe Models**: Pydantic v2 with strict validation and serialization
- **YAML Schema Support**: Define prompts in YAML with automatic validation
- **Handlebars Templating**: Powerful templating with partials and helpers
- **Plugin Architecture**: Extensible framework integrations (OpenAI, Anthropic, LangChain, etc.)
- **Versioning**: Full version history with semantic versioning and changelogs
- **Observability**: Structured logging, metrics collection, and OpenTelemetry integration
- **Async/Await**: Full async support for high-performance operations
- **Storage Backends**: File system and in-memory storage with pluggable interface
- **Caching**: Optional caching layer for rendered prompts
- **Protocol-Based Design**: Structural subtyping for flexible integration

## Framework Integrations

Seamlessly integrate with popular LLM frameworks:

- **OpenAI SDK**: Convert prompts to OpenAI message format for GPT models
- **Anthropic SDK**: Convert prompts to Claude-compatible message format
- **LangChain**: Convert to `PromptTemplate` and `ChatPromptTemplate` for chain composition
- **LiteLLM**: Multi-provider support with unified interface (100+ LLM providers)

All integrations support:
- Automatic template rendering with variables
- Framework-specific format conversion
- Role mapping and message structure validation
- Type-safe outputs with full IDE support

See [Framework Integration Examples](#framework-integration-examples) below for usage patterns.

## Installation

```bash
# Core package only
pip install agentic-prompt-manager

# With specific framework integration
pip install agentic-prompt-manager[openai]      # OpenAI SDK support
pip install agentic-prompt-manager[anthropic]   # Anthropic SDK (Claude) support
pip install agentic-prompt-manager[langchain]   # LangChain support
pip install agentic-prompt-manager[litellm]     # LiteLLM multi-provider support

# With all framework integrations
pip install agentic-prompt-manager[all]

# Development installation with Poetry
poetry install --with dev -E all
```

## Quick Start

### Simplest Flow - YAML to LLM in 4 Steps

The fastest way to get started - load a YAML prompt and use it with any LLM:

```python
from prompt_manager import PromptManager
from prompt_manager.storage import YAMLLoader, InMemoryStorage
from prompt_manager.core.registry import PromptRegistry
from pathlib import Path

# 1. Setup (one-time)
storage = InMemoryStorage()
registry = PromptRegistry(storage=storage)
manager = PromptManager(registry=registry)

# 2. Load prompts from YAML
loader = YAMLLoader(registry)
await loader.import_directory_to_registry(Path("prompts/"))

# 3. Render and use with your LLM
prompt_text = await manager.render("greeting", {
    "name": "Alice",
    "service": "Prompt Manager"
})

# 4. Validate output (optional)
await manager.load_schemas(Path("schemas/"))
validated = await manager.validate_output(
    "user_profile",  # schema name
    llm_response     # LLM's JSON response
)
```

**Example YAML prompt:**
```yaml
# prompts/greeting.yaml
version: "1.0.0"
prompts:
  - id: greeting
    version: "1.0.0"
    format: text
    status: active
    template:
      content: "Hello {{name}}! Welcome to {{service}}."
      variables:
        - name
        - service
```

### Complete Setup with Storage and Registry

For production use, here's the full setup with proper imports and configuration:

```python
from prompt_manager import PromptManager, Prompt, PromptMetadata
from prompt_manager.core.models import PromptFormat, PromptTemplate, PromptStatus
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.storage import InMemoryStorage, YAMLLoader
from pathlib import Path

# Initialize storage backend
storage = InMemoryStorage()  # or FileSystemStorage(Path("./prompts_db"))

# Create registry
registry = PromptRegistry(storage=storage)

# Create manager
manager = PromptManager(registry=registry)

# Load prompts and schemas
loader = YAMLLoader(registry)
await loader.import_directory_to_registry(Path("prompts/"))
await manager.load_schemas(Path("schemas/"))

# Now use the same workflow as above
result = await manager.render("greeting", {"name": "Alice", "service": "API"})
print(result)  # "Hello Alice! Welcome to API."
```

### Creating Prompts Programmatically

Create prompts and schemas directly in Python without YAML files:

**Simple Text Prompt:**
```python
from prompt_manager import Prompt, PromptMetadata
from prompt_manager.core.models import PromptFormat, PromptTemplate, PromptStatus

# Create a text prompt
prompt = Prompt(
    id="greeting",
    version="1.0.0",
    format=PromptFormat.TEXT,
    status=PromptStatus.ACTIVE,
    template=PromptTemplate(
        content="Hello {{name}}! Welcome to {{service}}.",
        variables=["name", "service"],
    ),
    metadata=PromptMetadata(
        author="System",
        description="Simple greeting prompt",
        tags=["greeting", "welcome"],
    ),
)

# Register and use
await manager.create_prompt(prompt)
result = await manager.render("greeting", {
    "name": "Alice",
    "service": "Prompt Manager"
})
print(result)  # "Hello Alice! Welcome to Prompt Manager."
```

**Chat Prompt:**
```python
from prompt_manager.core.models import ChatPromptTemplate, Message, Role

# Create a chat prompt with multiple messages
chat_prompt = Prompt(
    id="customer_support",
    version="1.0.0",
    format=PromptFormat.CHAT,
    status=PromptStatus.ACTIVE,
    chat_template=ChatPromptTemplate(
        messages=[
            Message(
                role=Role.SYSTEM,
                content="You are a helpful assistant for {{company}}.",
            ),
            Message(
                role=Role.USER,
                content="{{user_query}}",
            ),
        ],
        variables=["company", "user_query"],
    ),
    metadata=PromptMetadata(
        description="Customer support chatbot",
        tags=["support", "chat"],
    ),
)

await manager.create_prompt(chat_prompt)
```

**Creating Schemas Programmatically:**
```python
from prompt_manager.validation.models import (
    ValidationSchema,
    SchemaField,
    FieldValidator,
)

# Define validation schema in code
user_schema = ValidationSchema(
    name="user_input",
    version="1.0.0",
    description="User input validation",
    strict=True,
    fields=[
        SchemaField(
            name="username",
            type="string",
            required=True,
            validators=[
                FieldValidator(type="min_length", min_value=3),
                FieldValidator(
                    type="regex",
                    pattern="^[a-zA-Z0-9_]+$",
                    error_message="Username must be alphanumeric"
                ),
            ],
        ),
        SchemaField(
            name="email",
            type="string",
            required=True,
            validators=[FieldValidator(type="email")],
        ),
    ],
)

# Register schema
await manager.register_schema(user_schema)

# Use in prompt
prompt.input_schema = "user_input"
```

## Advanced Features

### YAML File Organization

**Individual Files (Recommended):**

Organize prompts and schemas in separate files for better maintainability:

```
project/
├── prompts/              # One YAML file per prompt
│   ├── greeting.yaml
│   ├── customer_support.yaml
│   └── code_review.yaml
└── schemas/              # One YAML file per schema
    ├── user_profile.yaml
    ├── code_review_input.yaml
    └── text_summarization_output.yaml
```

**YAML Prompt Example:**

```yaml
# prompts/greeting.yaml
version: "1.0.0"
prompts:
  - id: greeting
    version: "1.0.0"
    format: text
    status: active
    template:
      content: "Hello {{name}}! Welcome to {{service}}."
      variables:
        - name
        - service
    metadata:
      author: System
      description: "Simple greeting prompt"
      tags:
        - greeting
    input_schema: "user_input"  # Optional validation
    output_schema: "user_profile"  # Optional validation
```

**YAML Schema Example:**

```yaml
# schemas/user_input.yaml
version: "1.0.0"
metadata:
  description: "User input validation schema"
  author: "Team"
schemas:
  - name: "user_input"
    version: "1.0.0"
    description: "Validation for user input variables"
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
            error_message: "Username must be alphanumeric"
      - name: "email"
        type: "string"
        required: true
        validators:
          - type: "email"
      - name: "age"
        type: "integer"
        required: false
        validators:
          - type: "range"
            min_value: 13
            max_value: 120
```

### Schema Validation

Automatically validate input/output data with YAML or programmatic schemas.

```python
# Setup once
await manager.load_schemas(Path("schemas/"))

# Render with automatic input validation
prompt_text = await manager.render("user_onboarding", {
    "username": "john_doe",  # Validated against input_schema
    "email": "john@example.com"
})

# After LLM responds, validate output
llm_response = {"user_id": 123, "status": "active"}
try:
    validated = await manager.validate_output(
        "user_profile",  # output schema name
        llm_response
    )
    print(f"Validated: {validated}")
except SchemaValidationError as e:
    print(f"Validation failed: {e}")
```

**Supported Field Types:** `string`, `integer`, `float`, `boolean`, `list`, `dict`, `enum`, `any`

**Supported Validators:** `min_length`, `max_length`, `range`, `regex`, `enum`, `email`, `url`, `uuid`, `date`, `datetime`, `custom`

See [validation README](src/prompt_manager/validation/README.md) for complete documentation.

### Versioning

Track prompt changes with automatic version management:

```python
# Create initial version
prompt = Prompt(id="feature", version="1.0.0", ...)
await manager.create_prompt(prompt, changelog="Initial version")

# Update and bump version
prompt.template.content = "Updated content"
await manager.update_prompt(
    prompt,
    bump_version=True,
    changelog="Updated greeting message",
)

# Get version history
history = await manager.get_history("feature")
for version in history:
    print(f"{version.version}: {version.changelog}")
```

### Observability

Add logging, metrics, and tracing:

```python
from prompt_manager.observability import (
    LoggingObserver,
    MetricsCollector,
    OpenTelemetryObserver,
)

# Add observers
manager.add_observer(LoggingObserver())
manager.add_observer(OpenTelemetryObserver())

# Get metrics
metrics = await manager.get_metrics()
```

## Framework Integrations

### OpenAI SDK

Convert prompts to OpenAI message format for use with GPT models:

```python
from prompt_manager import PromptManager
from prompt_manager.integrations import OpenAIIntegration
import openai

# Setup
manager = PromptManager(registry=registry)
integration = OpenAIIntegration(manager.template_engine)

# Get prompt
prompt = await manager.get_prompt("customer_support")

# Convert to OpenAI format
messages = await integration.convert(prompt, {
    "company": "Acme Corp",
    "user_query": "How do I reset my password?"
})

# Use with OpenAI SDK
client = openai.AsyncOpenAI()
response = await client.chat.completions.create(
    model="gpt-4",
    messages=messages
)

print(response.choices[0].message.content)
```

### Anthropic SDK (Claude)

Convert prompts to Anthropic's Claude format:

```python
from prompt_manager.integrations import AnthropicIntegration
import anthropic

# Setup integration
integration = AnthropicIntegration(manager.template_engine)

# Convert prompt (returns dict with 'system' and 'messages' keys)
claude_format = await integration.convert(prompt, {
    "company": "Acme Corp",
    "user_query": "Explain quantum computing"
})

# Use with Anthropic SDK
client = anthropic.AsyncAnthropic()
response = await client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=claude_format.get("system"),  # System message (if present)
    messages=claude_format["messages"]   # User/assistant messages
)

print(response.content[0].text)
```

### LangChain

Convert prompts to LangChain templates for chain composition:

```python
from prompt_manager.integrations import LangChainIntegration
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

# Setup integration
integration = LangChainIntegration(manager.template_engine)

# Convert to LangChain ChatPromptTemplate
chat_template = await integration.convert(prompt, {})

# Use in LCEL chain
chain = chat_template | ChatOpenAI(model="gpt-4") | StrOutputParser()

# Invoke chain
result = await chain.ainvoke({
    "company": "Acme Corp",
    "user_query": "What are your pricing plans?"
})

print(result)
```

### LiteLLM

Use with LiteLLM for multi-provider support:

```python
from prompt_manager.integrations import LiteLLMIntegration
import litellm

# Setup integration
integration = LiteLLMIntegration(manager.template_engine)

# Convert to LiteLLM format (OpenAI-compatible)
messages = await integration.convert(prompt, {
    "company": "Acme Corp",
    "user_query": "Compare your plans"
})

# Use with any LLM provider via LiteLLM
response = await litellm.acompletion(
    model="gpt-4",  # or "claude-3", "gemini-pro", etc.
    messages=messages
)

print(response.choices[0].message.content)
```

### Error Handling

All integrations provide clear error messages:

```python
from prompt_manager.exceptions import (
    IntegrationError,
    IntegrationNotAvailableError,
    ConversionError,
    IncompatibleFormatError,
)

try:
    messages = await integration.convert(prompt, variables)
except IntegrationNotAvailableError as e:
    # Framework not installed
    print(e)  # "OpenAI integration not available. Install with: pip install agentic-prompt-manager[openai]"

except IncompatibleFormatError as e:
    # Prompt format not supported by framework
    print(e)  # "Anthropic requires CHAT format"

except ConversionError as e:
    # Conversion failed (missing variable, template error, etc.)
    print(e)  # "Missing required variable 'company'"
```

For complete examples, see [examples/integrations/](examples/integrations/) directory.

For creating custom integrations, see [Integration Guide](docs/INTEGRATION_GUIDE.md).

## Architecture

### Core Components

1. **Models** (`core/models.py`): Pydantic v2 models with validation
   - `Prompt`: Main prompt model with versioning
   - `PromptTemplate`: Text template configuration
   - `ChatPromptTemplate`: Chat message templates
   - `PromptVersion`: Version tracking
   - `PromptExecution`: Execution records

2. **Protocols** (`core/protocols.py`): Protocol-based interfaces
   - `TemplateEngineProtocol`: Template rendering
   - `StorageBackendProtocol`: Storage operations
   - `VersionStoreProtocol`: Version management
   - `ObserverProtocol`: Lifecycle hooks
   - `PluginProtocol`: Framework integrations
   - `CacheProtocol`: Caching layer
   - `MetricsCollectorProtocol`: Metrics collection

3. **Registry** (`core/registry.py`): In-memory prompt registry
   - Fast access with optional persistence
   - Filtering by tags, status, category
   - Version management

4. **Manager** (`core/manager.py`): Main orchestrator
   - High-level API
   - Rendering with caching
   - Version management
   - Plugin integration
   - Observability hooks

5. **Template Engine** (`core/template.py`): Handlebars rendering
   - Variable extraction
   - Partial templates
   - Chat message rendering

### Storage Backends

- **InMemoryStorage**: Fast in-memory storage for testing
- **FileSystemStorage**: JSON file-based persistence
- **YAMLLoader**: Load prompts from YAML schemas

### Plugin System

Plugins enable framework-specific rendering:

```python
from prompt_manager.plugins import BasePlugin

class OpenAIPlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="openai", version="1.0.0")

    async def render_for_framework(self, prompt, variables):
        # Convert to OpenAI format
        ...
```

### Observability

Three observer implementations:

1. **LoggingObserver**: Structured logging with structlog
2. **MetricsCollector**: In-memory metrics aggregation
3. **OpenTelemetryObserver**: Distributed tracing

## Type Safety

Full mypy strict mode compliance:

```bash
mypy src/prompt_manager
```

All public APIs have complete type annotations using:
- Generic types with `TypeVar`
- Protocol definitions for duck typing
- Pydantic v2 models for runtime validation
- `Literal` types for constants
- `TypedDict` for structured dictionaries

## Testing

```bash
# Run tests with coverage
pytest

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m benchmark

# Check coverage
pytest --cov=prompt_manager --cov-report=html
```

## Performance

- **Async operations**: All I/O operations are async
- **Caching layer**: Optional caching for rendered prompts
- **Memory efficient**: Generator-based iteration
- **Type checking**: Zero runtime overhead with proper annotations

## Development

```bash
# Install dependencies
poetry install

# Run linters
ruff check src/
black --check src/
mypy src/

# Format code
black src/
ruff check --fix src/

# Security scan
bandit -r src/

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

## Project Structure

```
prompt-manager/
├── src/
│   └── prompt_manager/
│       ├── __init__.py
│       ├── exceptions.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py          # Pydantic models
│       │   ├── protocols.py        # Protocol definitions
│       │   ├── registry.py         # Prompt registry
│       │   ├── manager.py          # Main manager
│       │   └── template.py         # Template engine
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── memory.py           # In-memory storage
│       │   ├── file.py             # File system storage
│       │   └── yaml_loader.py      # YAML import
│       ├── versioning/
│       │   ├── __init__.py
│       │   └── store.py            # Version store
│       ├── plugins/
│       │   ├── __init__.py
│       │   ├── base.py             # Base plugin
│       │   └── registry.py         # Plugin registry
│       └── observability/
│           ├── __init__.py
│           ├── logging.py          # Structured logging
│           ├── metrics.py          # Metrics collector
│           └── telemetry.py        # OpenTelemetry
├── tests/                          # Test suite
├── pyproject.toml                  # Project configuration
└── README.md
```

## License

MIT License

## Contributing

Contributions welcome! Please ensure:
- Type hints on all functions
- Docstrings in Google style
- Test coverage > 90%
- Mypy strict mode passes
- Black formatting applied
- Security scans pass

## Roadmap

- [ ] Additional plugin implementations (OpenAI, Anthropic, LangChain)
- [ ] Redis cache backend
- [ ] PostgreSQL storage backend
- [ ] A/B testing framework
- [ ] Prompt analytics dashboard
- [ ] CLI tool for management
- [ ] REST API server
- [ ] Performance optimizations
- [ ] Advanced templating features
