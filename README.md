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
- **Dual Sync/Async Interface**: Use the same methods with or without `await` - works in both sync and async contexts
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

See [Framework Integration Examples](#framework-integrations) below for usage patterns.

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

## Dual Sync/Async Interface

**NEW in v2.0**: All methods work **with or without `await`**! The library automatically detects your execution context and runs synchronously or asynchronously as needed.

### Synchronous Usage (Scripts, Notebooks, CLI Tools)

Perfect for simple scripts, Jupyter notebooks, and command-line tools where you don't want async complexity:

```python
from prompt_manager import PromptManager

# No asyncio.run() needed!
manager = PromptManager.create()

# Create a prompt - no await
prompt = manager.create_prompt({
    "id": "greeting",
    "version": "1.0.0",
    "format": "text",
    "template": {
        "content": "Hello {{name}}! Welcome to {{role}}."
    }
})

# Render - no await
result = manager.render("greeting", {
    "name": "Alice",
    "role": "Developer"
})
print(result)  # "Hello Alice! Welcome to Developer."

# List all prompts - no await
prompts = manager.list_prompts()
print(f"Total prompts: {len(prompts)}")
```

### Asynchronous Usage (FastAPI, aiohttp, async apps)

Perfect for web servers, high-concurrency applications, and async workflows:

```python
from prompt_manager import PromptManager

# Same API, just add await!
manager = await PromptManager.create()

# Create a prompt - with await
prompt = await manager.create_prompt({
    "id": "greeting",
    "version": "1.0.0",
    "format": "text",
    "template": {
        "content": "Hello {{name}}! Welcome to {{role}}."
    }
})

# Render - with await
result = await manager.render("greeting", {
    "name": "Alice",
    "role": "Developer"
})

# List all prompts - with await
prompts = await manager.list_prompts()
```

### How It Works

The dual interface automatically detects your execution context:

- **In async functions** (`async def`): Returns a coroutine that you `await`
- **In regular functions**: Executes synchronously and returns the result directly
- **No configuration needed**: The library handles everything automatically

### Complete Method Coverage (46 Methods)

All these methods work with or without `await`:

**PromptManager** (9 methods):
- `render()` - Render prompts with variables
- `render_for_plugin()` - Render for specific framework
- `render_and_parse()` - Render and parse JSON output
- `create_prompt()` - Create new prompts
- `get_prompt()` - Retrieve prompts by ID
- `update_prompt()` - Update existing prompts
- `list_prompts()` - List and filter prompts
- `get_history()` - Get version history
- `validate_output()` - Validate output against schema
- `load_schemas()` - Load validation schemas
- `get_metrics()` - Get performance metrics

**PromptRegistry** (10 methods):
- `register()` - Register a prompt
- `get()` - Get prompt by ID
- `update()` - Update a prompt
- `delete()` - Delete a prompt
- `list()` - List all prompts
- `exists()` - Check if prompt exists
- `count()` - Count total prompts
- `get_versions()` - Get version history
- `load_from_storage()` - Load prompts from storage

**Storage Backends** (10 methods total):
- `save()` - Save prompt to storage
- `load()` - Load prompt from storage
- `delete()` - Delete prompt from storage
- `list()` - List all stored prompts
- `exists()` - Check if prompt exists
- `clear()` - Clear all prompts (MemoryStorage only)

**VersionStore** (9 methods):
- `save_version()` - Save a version
- `get_version()` - Get specific version
- `list_versions()` - List all versions
- `get_latest()` - Get latest version
- `get_history()` - Get version history
- `get_changelog()` - Get formatted changelog
- `compare_versions()` - Compare two versions
- `load_from_storage()` - Load versions from storage

**TemplateEngine** (3 methods):
- `render()` - Render template with variables
- `validate()` - Validate template syntax
- `render_messages()` - Render chat messages (ChatTemplateEngine)

**SchemaLoader** (3 methods):
- `load_file()` - Load schema from file
- `load_directory()` - Load schemas from directory
- `validate_data()` - Validate data against schema

### Why This Matters

- ✅ **Same code works in FastAPI (async) and Flask (sync)**
- ✅ **Use in Jupyter notebooks without async complexity**
- ✅ **Simple CLI tools don't need `asyncio.run()`**
- ✅ **Gradual migration from sync to async code**
- ✅ **Test sync and async code paths with same tests**
- ✅ **No breaking changes - all existing async code still works**

### Migration Guide

**Existing async code? No changes needed!** All your existing code with `await` continues to work:

```python
# This still works perfectly
result = await manager.render("greeting", {"name": "Alice"})
```

**Want to simplify?** Just remove `await` and `asyncio.run()`:

```python
# Before (v1.x)
import asyncio

async def main():
    result = await manager.render("greeting", {"name": "Alice"})
    return result

result = asyncio.run(main())

# After (v2.0)
result = manager.render("greeting", {"name": "Alice"})
```

For complete migration guide, troubleshooting, and best practices, see:
- [Migration Guide](MIGRATION.md) - Detailed migration instructions
- [Best Practices](docs/BEST_PRACTICES.md) - When to use sync vs async
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## Quick Start

### Simplest Flow - YAML to LLM in 4 Steps

The fastest way to get started - load a YAML prompt and use it with any LLM.

**Works both synchronously and asynchronously:**

```python
from prompt_manager import PromptManager
from pathlib import Path

# 1. Create manager with auto-loading from prompts directory
manager = PromptManager.create(prompt_dir=Path("prompts/"))

# 2. Render and use with your LLM
# Works with or without await!

# Async usage (in async functions):
prompt_text = await manager.render("greeting", {
    "name": "Alice",
    "role": "Developer"
})

# Sync usage (in regular functions):
prompt_text = manager.render("greeting", {
    "name": "Bob",
    "role": "Designer"
})

# 3. Validate output (optional)
await manager.load_schemas(Path("schemas/"))

# Both sync and async work:
validated = await manager.validate_output("user_profile", llm_response)  # async
validated = manager.validate_output("user_profile", llm_response)        # sync
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
      content: "Hello {{name}}! Welcome to our platform. Your role is {{role}}."
      variables:
        - name
        - role
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
result = await manager.render("greeting", {"name": "Alice", "role": "Developer"})
print(result)  # "Hello Alice! Welcome to our platform. Your role is Developer."
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
        content="Hello {{name}}! Welcome to {{role}}.",
        variables=["name", "role"],
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
    "role": "Developer"
})
print(result)  # "Hello Alice! Welcome to Developer."
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

## Handlebars Template Syntax

Prompt Manager uses **Handlebars** (via pybars4) for templating, NOT Jinja2.

### Basic Variables

```handlebars
Hello {{name}}! Your role is {{role}}.
```

### Conditionals

```handlebars
{{#if premium}}
  Welcome to premium features!
{{else}}
  Upgrade to access premium features.
{{/if}}
```

### Loops

```handlebars
{{#each datasets}}
  - {{name}}: {{rows}} rows
{{/each}}
```

### Important Differences from Jinja2

**Handlebars does NOT support:**
- Filters like `| title`, `| upper`, `| join`
- Python expressions like `{% for item in items %}`
- Built-in functions in templates

**Use Handlebars syntax:**
- Loops: `{{#each items}}...{{/each}}` (not `{% for %}`)
- Conditionals: `{{#if condition}}...{{/if}}` (not `{% if %}`)
- Variables: `{{variable}}` (same as Jinja2)

For advanced template features, use partials and helpers (see documentation).

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
      content: "Hello {{name}}! Welcome to our platform. Your role is {{role}}."
      variables:
        - name
        - role
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

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Roadmap

### Completed ✅
- [x] Auto loading YAML files from directory
- [x] Optional storage with sensible defaults
- [x] Additional plugin implementations (OpenAI, Anthropic, LangChain, LiteLLM)
- [x] **Dual Sync/Async Interface** - All methods work with or without `await` - automatically detects execution context

### Planned Features
- [ ] Security Features
  - [ ] Prompt access control / permissions
  - [ ] Audit logging for prompt changes
  - [ ] Secret scanning in prompts
- [ ] Storage Backends
  - [ ] Redis cache backend
  - [ ] PostgreSQL storage backend
  - [ ] S3/cloud storage backend
- [ ] Advanced Features
  - [ ] A/B testing framework for prompt variants
  - [ ] Prompt analytics dashboard
  - [ ] CLI tool for prompt management
  - [ ] REST API server
  - [ ] Performance optimizations (lazy loading, caching improvements)
  - [ ] Advanced templating features (conditionals, loops via helpers)
