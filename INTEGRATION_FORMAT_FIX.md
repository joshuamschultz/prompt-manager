# Integration Format Compatibility Fix

## Date: 2025-11-27

## Issue Encountered

After fixing the `AttributeError`, a new error appeared:

```
IncompatibleFormatError: Prompt format 'PromptFormat.TEXT' is incompatible with framework 'anthropic'.
Supported formats: CHAT (prompt_format='PromptFormat.TEXT', framework='anthropic', supported_formats=['CHAT'])
```

## Root Cause

**This is CORRECT behavior!** The Anthropic integration is working as designed:

1. **Anthropic (Claude) requires CHAT format** - Claude's API needs structured messages with roles
2. **TEXT format doesn't have roles** - Simple text strings can't be mapped to user/assistant messages
3. **The notebook was using TEXT format prompt** - The `greeting` prompt is TEXT format

## Integration Format Support Matrix

| Integration | TEXT Format | CHAT Format |
|-------------|-------------|-------------|
| **AnthropicIntegration** | ❌ No | ✅ Yes |
| **OpenAIIntegration** | ✅ Yes | ✅ Yes |
| **LiteLLMIntegration** | ✅ Yes | ✅ Yes |
| **LangChainIntegration** | ✅ Yes | ✅ Yes |

## The Fix

Changed the notebook to use **CHAT format prompts** with Anthropic integration:

### Before (WRONG) ❌:
```python
# greeting is TEXT format - incompatible with Anthropic
prompt = pm.get_prompt("greeting")
anthropic_format = integration.convert(prompt, {"name": "Alice", "role": "Developer"})
# ERROR: IncompatibleFormatError
```

### After (CORRECT) ✅:
```python
# code_review is CHAT format - compatible with Anthropic
prompt = pm.get_prompt("code_review")
anthropic_format = integration.convert(prompt, {
    "code": "def greet(name): return f'Hello {name}!'",
    "language": "Python",
    "focus_areas": ["style", "best_practices"]
})
# SUCCESS!
```

## Available Prompts by Format

In `examples/prompts/`:

**TEXT Format**:
- `greeting.yaml` - Simple greeting
- `marketing_email.yaml` - Email template
- `text_summarization.yaml` - Summarization

**CHAT Format**:
- `code_review.yaml` - Code review assistant
- `data_analysis.yaml` - Data analysis assistant
- `customer_support.yaml` - Customer support (if exists)

## Choosing the Right Integration

### Use Anthropic Integration When:
- ✅ You have CHAT format prompts
- ✅ You need Claude-specific features
- ✅ You want strict validation

### Use OpenAI/LiteLLM Integration When:
- ✅ You have TEXT format prompts
- ✅ You have CHAT format prompts
- ✅ You need flexibility with both formats

## Updated Notebook Cells

### Cell 31 - Anthropic Integration
**Changed**: Uses `code_review` (CHAT) instead of `greeting` (TEXT)
**Added**: Clear note that Anthropic only supports CHAT format

### Cell 32 - Explanation
**Added**: Explanation of why Anthropic only supports CHAT format

### Cell 40 - LiteLLM Integration
**Added**: Note that LiteLLM supports both TEXT and CHAT formats

## Testing Results

**Before Fix**:
```
IncompatibleFormatError: Prompt format 'PromptFormat.TEXT' is incompatible with framework 'anthropic'
```

**After Fix**:
```
✅ SUCCESS! Anthropic integration works with CHAT format
System: You are an expert code reviewer. Analyze the provided code for:
Messages: 1 message(s)
```

## Key Takeaways

1. **Anthropic = CHAT only** - This is by design, not a bug
2. **OpenAI/LiteLLM = Both formats** - More flexible options
3. **Check prompt format** - Use `prompt.format` to verify
4. **Integration validates format** - It will raise `IncompatibleFormatError` if format doesn't match

## Best Practices

### When Creating Prompts:

```yaml
# For Anthropic (Claude)
format: chat
chat_template:
  messages:
    - role: system
      content: "You are..."
    - role: user
      content: "{{user_input}}"
```

### When Using Integrations:

```python
# Check format compatibility first
from prompt_manager.core.models import PromptFormat

prompt = pm.get_prompt("my_prompt")

if prompt.format == PromptFormat.CHAT:
    # Use any integration
    anthropic_integration.convert(prompt, variables)
elif prompt.format == PromptFormat.TEXT:
    # Use OpenAI or LiteLLM, NOT Anthropic
    openai_integration.convert(prompt, variables)
```

## Summary

This wasn't a bug - it's the **correct validation behavior**! The fix was to:
1. Use CHAT format prompts with Anthropic integration
2. Document the format requirements clearly
3. Show examples of both TEXT and CHAT formats in the notebook

All integrations are now working correctly with appropriate prompt formats.
