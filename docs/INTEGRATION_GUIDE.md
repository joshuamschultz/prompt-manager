# Framework Integration Guide

This guide explains how to create custom framework integrations for Prompt Manager, allowing you to convert prompts to any LLM framework's format.

## Overview

Framework integrations enable Prompt Manager to convert prompts into framework-specific formats (OpenAI messages, LangChain templates, etc.). The integration system is based on:

1. **BaseIntegration**: Abstract class defining the integration interface
2. **Plugin System**: Optional auto-discovery via entry points
3. **Type Safety**: Generic types for framework-specific return types

## Creating a Custom Integration

### Step 1: Implement BaseIntegration

Create a new class extending `BaseIntegration[T]` where `T` is your framework's prompt type:

```python
from collections.abc import Mapping
from typing import Any
from prompt_manager.integrations.base import BaseIntegration
from prompt_manager.core.models import Prompt
from prompt_manager.exceptions import IntegrationError

# Define your framework's output type
class MyFrameworkPrompt:
    """Your framework's prompt format."""
    def __init__(self, messages: list[dict], config: dict):
        self.messages = messages
        self.config = config

class MyFrameworkIntegration(BaseIntegration[MyFrameworkPrompt]):
    """Integration for MyFramework."""

    async def convert(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> MyFrameworkPrompt:
        """
        Convert Prompt Manager prompt to MyFramework format.

        Args:
            prompt: Prompt to convert
            variables: Variables for rendering

        Returns:
            MyFrameworkPrompt instance

        Raises:
            IntegrationError: If conversion fails
        """
        # 1. Validate compatibility
        if not self.validate_compatibility(prompt):
            raise IntegrationError(
                f"Prompt format {prompt.format} not supported by MyFramework"
            )

        # 2. Render template with variables
        if prompt.format == PromptFormat.CHAT:
            return await self._convert_chat(prompt, variables)
        else:
            return await self._convert_text(prompt, variables)

    async def _convert_chat(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> MyFrameworkPrompt:
        """Convert CHAT format prompt."""
        if not prompt.chat_template:
            raise IntegrationError("Chat template required for CHAT format")

        messages = []
        for msg in prompt.chat_template.messages:
            # Render each message with template engine
            rendered = await self.template_engine.render(
                msg.content,
                variables,
            )

            # Convert to framework format
            messages.append({
                "role": self._map_role(msg.role),
                "content": rendered,
            })

        # Create framework-specific object
        return MyFrameworkPrompt(
            messages=messages,
            config={"temperature": 0.7}  # Framework-specific config
        )

    async def _convert_text(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> MyFrameworkPrompt:
        """Convert TEXT format prompt."""
        if not prompt.template:
            raise IntegrationError("Template required for TEXT format")

        # Render template
        rendered = await self.template_engine.render(
            prompt.template.content,
            variables,
            partials=prompt.template.partials,
        )

        # Convert to framework format
        return MyFrameworkPrompt(
            messages=[{"role": "user", "content": rendered}],
            config={}
        )

    def _map_role(self, role: Role) -> str:
        """Map Prompt Manager roles to framework roles."""
        mapping = {
            Role.SYSTEM: "system",
            Role.USER: "user",
            Role.ASSISTANT: "assistant",
            # Add framework-specific role mappings
        }
        if role not in mapping:
            raise IntegrationError(f"Unsupported role: {role}")
        return mapping[role]

    def validate_compatibility(self, prompt: Prompt) -> bool:
        """
        Check if prompt is compatible with framework.

        Returns:
            True if compatible, False otherwise
        """
        # Example: Framework only supports CHAT format
        return prompt.format == PromptFormat.CHAT
```

### Step 2: Handle Framework-Specific Requirements

Different frameworks have different requirements. Here are common patterns:

#### Example: Framework Requires Single System Message

```python
async def _convert_chat(self, prompt, variables):
    system_message = None
    user_messages = []

    for msg in prompt.chat_template.messages:
        rendered = await self.template_engine.render(msg.content, variables)

        if msg.role == Role.SYSTEM:
            if system_message is not None:
                raise IntegrationError(
                    "Framework allows only one system message"
                )
            system_message = rendered
        else:
            user_messages.append({
                "role": self._map_role(msg.role),
                "content": rendered,
            })

    result = {"messages": user_messages}
    if system_message:
        result["system"] = system_message  # Separate field

    return result
```

#### Example: Framework Requires Message Alternation

```python
def _validate_alternation(self, messages: list[dict]) -> None:
    """Ensure messages alternate between user and assistant."""
    if not messages:
        return

    # First message must be from user
    if messages[0]["role"] != "user":
        raise IntegrationError(
            "First message must be from user in this framework"
        )

    # Check alternation
    for i in range(1, len(messages)):
        if messages[i]["role"] == messages[i-1]["role"]:
            raise IntegrationError(
                f"Messages must alternate roles (position {i})"
            )
```

#### Example: Framework Uses Different Template Syntax

```python
def _convert_template_syntax(self, template: str) -> str:
    """
    Convert Handlebars {{variable}} to framework syntax.

    Example: Convert {{name}} to {name} for Python f-strings
    """
    import re
    # Simple conversion (extend for complex cases)
    return re.sub(r'\{\{(\w+)\}\}', r'{\1}', template)
```

### Step 3: Add Dependency Checks (Optional)

For optional framework dependencies:

```python
try:
    from myframework import PromptTemplate, ChatTemplate
    MYFRAMEWORK_AVAILABLE = True
except ImportError:
    MYFRAMEWORK_AVAILABLE = False

class MyFrameworkIntegration(BaseIntegration):
    def __init__(self, *args, **kwargs):
        if not MYFRAMEWORK_AVAILABLE:
            raise IntegrationError(
                "MyFramework not installed. "
                "Install with: pip install agentic-prompt-manager[myframework]"
            )
        super().__init__(*args, **kwargs)
```

### Step 4: Add Type Definitions

Create TypedDict for framework message formats:

```python
from typing import TypedDict

class MyFrameworkMessage(TypedDict, total=False):
    """Message format for MyFramework."""
    role: str
    content: str
    metadata: dict[str, Any]  # Optional field
```

## Creating a Plugin (Optional)

Plugins enable auto-discovery and registration. Create a plugin class:

```python
from prompt_manager.plugins.base import BasePlugin
from prompt_manager.core.template import TemplateEngine

class MyFrameworkPlugin(BasePlugin):
    """Plugin for MyFramework integration."""

    def __init__(self):
        super().__init__(
            name="myframework",
            version="1.0.0",
        )
        self._integration: MyFrameworkIntegration | None = None

    async def _initialize_impl(self, config: Mapping[str, Any]) -> None:
        """Initialize the integration."""
        # Create template engine
        template_engine = TemplateEngine()

        # Create integration instance
        self._integration = MyFrameworkIntegration(
            template_engine=template_engine,
            strict_validation=config.get("strict_validation", True),
        )

    async def render_for_framework(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> Any:
        """Render prompt in framework format."""
        self._ensure_initialized()
        assert self._integration is not None
        return await self._integration.convert(prompt, variables)

    async def validate_compatibility(self, prompt: Prompt) -> bool:
        """Validate prompt compatibility."""
        self._ensure_initialized()
        assert self._integration is not None
        return self._integration.validate_compatibility(prompt)
```

## Registering Your Plugin

### In Your Package

Add entry point in your package's `pyproject.toml`:

```toml
[tool.poetry.plugins."prompt_manager.plugins"]
myframework = "my_package.integrations:MyFrameworkPlugin"
```

### In Prompt Manager Package

If contributing to Prompt Manager, add to `pyproject.toml`:

```toml
[tool.poetry.plugins."prompt_manager.plugins"]
myframework = "prompt_manager.plugins.myframework_plugin:MyFrameworkPlugin"
```

And add optional dependency:

```toml
[tool.poetry.dependencies]
myframework-sdk = {version = "^1.0.0", optional = true}

[tool.poetry.extras]
myframework = ["myframework-sdk"]
```

## Testing Your Integration

### Unit Tests

Test conversion logic in isolation:

```python
import pytest
from prompt_manager.core.models import Prompt, PromptFormat
from my_package.integrations import MyFrameworkIntegration

@pytest.fixture
def template_engine():
    from prompt_manager.core.template import TemplateEngine
    return TemplateEngine()

@pytest.fixture
def integration(template_engine):
    return MyFrameworkIntegration(template_engine)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_convert_text_prompt(integration):
    """Test converting TEXT prompt."""
    prompt = Prompt(
        id="test",
        format=PromptFormat.TEXT,
        template=PromptTemplate(content="Hello {{name}}"),
    )

    result = await integration.convert(prompt, {"name": "Alice"})

    assert "Alice" in result.messages[0]["content"]

@pytest.mark.unit
def test_validate_compatibility(integration):
    """Test compatibility validation."""
    chat_prompt = create_chat_prompt()
    text_prompt = create_text_prompt()

    assert integration.validate_compatibility(chat_prompt)
    assert not integration.validate_compatibility(text_prompt)
```

### Integration Tests

Test full workflow with framework SDK:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_myframework_e2e(prompt_manager):
    """Test end-to-end with MyFramework SDK."""
    # Create prompt
    prompt = create_test_prompt()
    await prompt_manager.create_prompt(prompt)

    # Convert to framework format
    integration = MyFrameworkIntegration(prompt_manager.template_engine)
    framework_prompt = await integration.convert(
        prompt,
        {"variable": "value"}
    )

    # Use with actual framework (mock API call)
    with patch("myframework.Client") as mock_client:
        mock_response = create_mock_response()
        mock_client.return_value.generate.return_value = mock_response

        # Call framework
        import myframework
        client = myframework.Client()
        response = client.generate(framework_prompt)

        assert response is not None
```

## Best Practices

### Error Handling

1. **Validate Early**: Check compatibility before conversion
2. **Clear Messages**: Provide actionable error messages
3. **Context**: Include prompt ID and format in errors

```python
try:
    result = await integration.convert(prompt, variables)
except IntegrationError as e:
    logger.error(
        "conversion_failed",
        prompt_id=prompt.id,
        format=prompt.format.value,
        error=str(e)
    )
    raise
```

### Performance

1. **Template Caching**: Use template engine's built-in caching
2. **Lazy Loading**: Only import framework when needed
3. **Reuse Instances**: Create integration once, use many times

```python
# Good: Reuse integration instance
integration = MyFrameworkIntegration(template_engine)
for prompt in prompts:
    result = await integration.convert(prompt, variables)

# Bad: Create new instance each time
for prompt in prompts:
    integration = MyFrameworkIntegration(template_engine)
    result = await integration.convert(prompt, variables)
```

### Type Safety

1. **Generic Return Types**: Use `BaseIntegration[T]` with specific type
2. **TypedDict**: Define message formats as TypedDict
3. **Type Hints**: Annotate all parameters and returns

```python
from typing import TypeVar

T = TypeVar('T')

class MyFrameworkIntegration(BaseIntegration[MyFrameworkPrompt]):
    async def convert(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> MyFrameworkPrompt:  # Specific return type
        ...
```

## Examples

See the following built-in integrations for reference:

- **OpenAI**: `src/prompt_manager/integrations/openai.py`
  - Handles both CHAT and TEXT formats
  - Preserves function calling metadata
  - Maps all Role types

- **Anthropic**: `src/prompt_manager/integrations/anthropic.py`
  - Extracts system message separately
  - Validates message alternation
  - Handles CHAT format only

- **LangChain**: `src/prompt_manager/integrations/langchain.py`
  - Converts Handlebars to f-strings
  - Creates PromptTemplate and ChatPromptTemplate
  - Handles dependency checking

- **LiteLLM**: `src/prompt_manager/integrations/litellm.py`
  - Delegates to OpenAI integration
  - Shows composition pattern

## Contributing

To contribute your integration to Prompt Manager:

1. Create integration class and tests
2. Add plugin implementation
3. Update `pyproject.toml` with optional dependency
4. Add example code in `examples/integrations/`
5. Update README.md with integration description
6. Submit pull request with:
   - Integration code
   - Unit and integration tests
   - Example usage
   - Documentation updates

## Troubleshooting

### "IntegrationNotAvailableError"

**Problem**: Framework SDK not installed

**Solution**: Install with extra:
```bash
pip install agentic-prompt-manager[myframework]
```

### "ConversionError: Template required"

**Problem**: Prompt missing required template

**Solution**: Ensure prompt has template or chat_template set

### "IncompatibleFormatError"

**Problem**: Prompt format not supported by framework

**Solution**: Check `validate_compatibility()` and convert to supported format

### Performance Issues

**Problem**: Slow conversion

**Solution**:
- Check if creating new TemplateEngine each time (reuse it)
- Profile with `cProfile` to find bottleneck
- Consider caching converted prompts

## Support

- **Documentation**: See README.md and source code
- **Issues**: Report bugs on GitHub Issues
- **Examples**: Review `examples/integrations/` directory
- **Community**: GitHub Discussions for questions

---

**Last Updated**: 2025-01-19
