# Prompt Manager

[![PyPI version](https://badge.fury.io/py/prompt-manager.svg)](https://badge.fury.io/py/prompt-manager)
[![Python Version](https://img.shields.io/pypi/pyversions/prompt-manager.svg)](https://pypi.org/project/prompt-manager/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/github/actions/workflow/status/yourusername/prompt-manager/test.yml?branch=main)](https://github.com/yourusername/prompt-manager/actions)
[![Coverage](https://img.shields.io/codecov/c/github/yourusername/prompt-manager)](https://codecov.io/gh/yourusername/prompt-manager)

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
pip install prompt-manager

# With specific framework integration
pip install prompt-manager[openai]      # OpenAI SDK support
pip install prompt-manager[anthropic]   # Anthropic SDK (Claude) support
pip install prompt-manager[langchain]   # LangChain support
pip install prompt-manager[litellm]     # LiteLLM multi-provider support

# With all framework integrations
pip install prompt-manager[all]

# Development installation with Poetry
poetry install --with dev -E all
```

## Quick Start

### Basic Usage

```python
from prompt_manager import PromptManager, Prompt, PromptMetadata
from prompt_manager.core.models import PromptFormat, PromptTemplate, PromptStatus
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.storage import InMemoryStorage

# Create components
storage = InMemoryStorage()
registry = PromptRegistry(storage=storage)
manager = PromptManager(registry=registry)

# Create a prompt
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

# Register prompt
await manager.create_prompt(prompt)

# Render prompt
result = await manager.render(
    "greeting",
    {"name": "Alice", "service": "Prompt Manager"},
)
print(result)  # "Hello Alice! Welcome to Prompt Manager."
```

### Chat Prompts

```python
from prompt_manager.core.models import ChatPromptTemplate, Message, Role

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
)

await manager.create_prompt(chat_prompt)
```

### Loading from YAML

**Individual Files (Recommended):**

Each prompt and schema in its own file for better organization:

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

```python
from prompt_manager import PromptManager
from prompt_manager.storage import YAMLLoader
from pathlib import Path

# Load prompts from directory
loader = YAMLLoader(registry)
await loader.import_directory_to_registry(Path("prompts/"))

# Load schemas for validation
manager = PromptManager(registry=registry)
await manager.load_schemas(Path("schemas/"))
```

**Single File Format:**

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
      tags:
        - greeting
    input_schema: "user_input"  # Optional validation
```

### Versioning

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

### Schema Validation

Validate input and output data with YAML-defined schemas. Schemas are automatically injected into prompts during rendering.

**Individual Schema Files (Recommended):**

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

**Auto-Injection with Prompts:**

```python
from prompt_manager import PromptManager

# Load schemas (loads all YAML files in directory)
manager = PromptManager(registry=registry)
await manager.load_schemas(Path("schemas/"))

# Create prompt with schema reference
prompt = Prompt(
    id="user_onboarding",
    format=PromptFormat.TEXT,
    template=PromptTemplate(content="Welcome {{username}}!"),
    input_schema="user_input",  # Auto-injected during render
    output_schema="user_profile"  # Auto-injected during render
)

# Render - schema descriptions automatically added
result = await manager.render("user_onboarding", {"username": "john_doe"})

# Result includes:
# 1. Input schema description (intro)
# 2. Main prompt content
# 3. Output schema description (ending)
```

**Validating LLM Output:**

```python
# After getting LLM response, validate it
llm_response = {
    "summary": "Brief summary of the content",
    "key_points": ["Point 1", "Point 2"],
    "word_count": 25
}

try:
    # Validate against output schema
    validated = await manager.validate_output(
        "text_summarization_output",
        llm_response
    )
    # Use validated data safely
    print(f"Summary: {validated['summary']}")

except SchemaValidationError as e:
    print(f"LLM returned invalid format: {e}")
    # Handle validation error (retry, log, etc.)
```

**Complete Automatic Workflow (Recommended):**

```python
# ═══════════════════════════════════════════════════════════
# ONE-TIME SETUP
# ═══════════════════════════════════════════════════════════

# Load schemas once at startup
manager = PromptManager(registry=registry)
await manager.load_schemas(Path("schemas/"))

# Define prompt in YAML with schemas
# prompts/summarizer.yaml:
#   input_schema: "text_summarization_input"   # Auto-validates input
#   output_schema: "text_summarization_output" # Auto-validates output

# ═══════════════════════════════════════════════════════════
# PER-REQUEST FLOW (Automatic Validation!)
# ═══════════════════════════════════════════════════════════

# 1. Render prompt (INPUT AUTO-VALIDATED)
prompt_text = await manager.render("summarizer", {
    "content_type": "article",
    "text": "Your content here..."
})
# ✅ Input validated automatically
# ✅ Output schema injected as JSON format instructions

# 2. Send to LLM
llm_response = await openai_client.generate(prompt_text)

# 3. Parse and validate output (OUTPUT AUTO-VALIDATED)
try:
    validated = await manager.render_and_parse(
        "summarizer",
        input_vars,
        llm_response  # Can be dict or JSON string
    )
    # ✅ Output validated automatically
    # Use validated data with confidence!

except SchemaValidationError as e:
    # Handle validation errors gracefully
    logger.error(f"Validation failed: {e}")
```

**What Happens Automatically:**

1. **Input Validation**: `render()` validates input against `input_schema` before rendering
2. **Schema Injection**: Output schema is injected with JSON format instructions
3. **Output Validation**: `render_and_parse()` validates LLM response against `output_schema`
4. **Type Safety**: All data is validated against your schemas

**Supported Field Types:**
- `string`, `integer`, `float`, `boolean`
- `list` (with `item_type` or `item_schema`)
- `dict` (with `nested_schema`)
- `enum` (with `allowed_values`)
- `any` (no type checking)

**Supported Validators:**
- `min_length`, `max_length` - String/list length
- `range` - Numeric min/max
- `regex` - Pattern matching
- `enum` - Choice validation
- `email`, `url`, `uuid` - Format validation
- `date`, `datetime` - Date/time parsing
- `custom` - Custom validator functions

**Schema Features:**
- Required/optional fields with `required: true/false`
- Default values with `default: value`
- Nullable fields with `nullable: true`
- Nested schemas for complex objects
- List validation with item types
- Custom error messages per validator

See [validation README](src/prompt_manager/validation/README.md) for complete documentation.

### Observability

```python
from prompt_manager.observability import (
    LoggingObserver,
    MetricsCollector,
    OpenTelemetryObserver,
)

# Add observers
logging_observer = LoggingObserver()
metrics_collector = MetricsCollector()
otel_observer = OpenTelemetryObserver()

manager.add_observer(logging_observer)
manager.add_observer(otel_observer)

# Create manager with metrics
manager = PromptManager(
    registry=registry,
    metrics=metrics_collector,
)

# Get metrics
metrics = await manager.get_metrics()
print(metrics)
```

## Framework Integration Examples

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
    print(e)  # "OpenAI integration not available. Install with: pip install prompt-manager[openai]"

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
