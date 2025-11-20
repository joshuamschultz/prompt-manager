# Framework Integration Examples

This directory contains complete, runnable examples for integrating Prompt Manager with popular LLM frameworks.

## Available Examples

- **openai_example.py** - OpenAI SDK integration (GPT-4, GPT-3.5, etc.)
- **anthropic_example.py** - Anthropic SDK integration (Claude 3.5, Claude 3, etc.)
- **langchain_example.py** - LangChain integration with LCEL chains
- **litellm_example.py** - LiteLLM multi-provider integration
- **custom_integration_example.py** - Building custom framework integrations

## Setup

### Install Dependencies

```bash
# Install all framework integrations
pip install prompt-manager[all]

# Or install specific frameworks
pip install prompt-manager[openai]
pip install prompt-manager[anthropic]
pip install prompt-manager[langchain]
pip install prompt-manager[litellm]
```

### Set Up API Keys

Create a `.env` file in this directory (or set environment variables):

```bash
# .env (DO NOT commit this file!)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

Or export environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Running Examples

Each example can be run directly:

```bash
# OpenAI example
python openai_example.py

# Anthropic example
python anthropic_example.py

# LangChain example
python langchain_example.py

# LiteLLM example
python litellm_example.py

# Custom integration example
python custom_integration_example.py
```

## Examples Without API Keys

All examples include mock/demo modes that work without real API keys. Look for comments in each file explaining how to run in demo mode.

## What Each Example Demonstrates

### openai_example.py
- Converting TEXT and CHAT prompts to OpenAI message format
- Using with OpenAI SDK (`openai.AsyncOpenAI`)
- Handling function calling and tool use
- Error handling and validation

### anthropic_example.py
- Converting CHAT prompts to Anthropic message format
- System message handling (Anthropic's single system message requirement)
- Message alternation validation
- Using with Anthropic SDK

### langchain_example.py
- Converting prompts to LangChain templates
- Creating `PromptTemplate` and `ChatPromptTemplate`
- Using in LCEL (LangChain Expression Language) chains
- Template composition and partial variables

### litellm_example.py
- Multi-provider support (OpenAI, Anthropic, Google, etc.)
- Unified interface across LLM providers
- Provider-specific configuration
- Fallback and routing strategies

### custom_integration_example.py
- Creating custom integration classes
- Extending `BaseIntegration`
- Implementing required protocol methods
- Plugin registration (optional)

## Common Patterns

### Basic Integration Workflow

```python
from prompt_manager import PromptManager
from prompt_manager.integrations import OpenAIIntegration
from prompt_manager.storage import InMemoryStorage
from prompt_manager.core.registry import PromptRegistry

# 1. Setup prompt manager
storage = InMemoryStorage()
registry = PromptRegistry(storage=storage)
manager = PromptManager(registry=registry)

# 2. Create integration
integration = OpenAIIntegration(manager.template_engine)

# 3. Create or load prompt
prompt = await manager.get_prompt("my_prompt")

# 4. Convert to framework format
messages = await integration.convert(prompt, {"variable": "value"})

# 5. Use with framework SDK
# ... framework-specific code ...
```

### Error Handling Pattern

```python
from prompt_manager.exceptions import (
    IntegrationError,
    IntegrationNotAvailableError,
    ConversionError,
)

try:
    messages = await integration.convert(prompt, variables)
except IntegrationNotAvailableError:
    print("Framework not installed. Install with: pip install prompt-manager[framework]")
except ConversionError as e:
    print(f"Conversion failed: {e}")
    # Handle missing variables, template errors, etc.
```

## Tips

1. **Start Simple**: Begin with basic TEXT prompts, then move to CHAT
2. **Use Type Hints**: Enable autocomplete and type checking in your IDE
3. **Handle Errors**: Always wrap integration calls in try/except
4. **Test Locally**: Use demo mode or mocks before calling real APIs
5. **Read Docstrings**: Integration classes have detailed docstrings

## Troubleshooting

### "IntegrationNotAvailableError"

**Problem**: Framework SDK not installed

**Solution**:
```bash
pip install prompt-manager[openai]  # or anthropic, langchain, litellm
```

### "Missing required variable"

**Problem**: Prompt template uses variables not provided

**Solution**: Check prompt's `template.variables` and provide all required variables

### "Incompatible format"

**Problem**: Framework doesn't support prompt's format

**Solution**: Use compatible format (e.g., Anthropic requires CHAT format)

## Additional Resources

- [Integration Guide](../../docs/INTEGRATION_GUIDE.md) - Creating custom integrations
- [API Documentation](../../docs/api/) - Complete API reference
- [Main README](../../README.md) - Package overview and features

## Contributing Examples

To contribute a new example:

1. Create new file: `framework_name_example.py`
2. Include complete working code
3. Add docstring explaining what it demonstrates
4. Include both real API and mock/demo modes
5. Add entry to this README
6. Test that example runs successfully

---

**Last Updated**: 2025-01-19
