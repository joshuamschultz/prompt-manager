# Prompt Manager Examples

This directory contains examples demonstrating the Prompt Manager's capabilities.

## Quick Start (Simplified API)

The easiest way to get started:

```python
from prompt_manager import PromptManager

# Create manager with defaults
# - Defaults to ./prompts directory
# - Automatically loads all YAML files
manager = await PromptManager.create()

# Render a prompt
result = await manager.render("my_prompt", {"var": "value"})
```

**Custom configuration:**
```python
# Custom directory
manager = await PromptManager.create(prompt_dir="./my-prompts")

# Disable auto-loading
manager = await PromptManager.create(auto_load_yaml=False)

# With observability
from prompt_manager.observability import MetricsCollector, LoggingObserver

manager = await PromptManager.create(
    metrics=MetricsCollector(),
    observers=[LoggingObserver()],
)
```

## Files

- **`simplified_usage.py`** - NEW! Demonstrates simplified API with auto-loading
- **`basic_usage.py`** - Comprehensive examples showing all features
- **`test_prompt_manager.ipynb`** - Interactive Jupyter notebook for end-to-end testing
- **`prompts/`** - Example YAML prompt definitions
- **`schemas-individual/`** - Example validation schemas

## Running the Jupyter Notebook Test

The `test_prompt_manager.ipynb` notebook provides a comprehensive, interactive test of the prompt manager.

### Prerequisites

1. **Install dependencies:**

   ```bash
   # Install with Anthropic support
   poetry install --extras anthropic

   # Or install all integrations
   poetry install --extras all

   # Install additional dependencies for the notebook
   poetry add python-dotenv jupyter
   ```

2. **Configure API key:**

   The `.env` file in the project root should contain:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

### Running the Notebook

1. **Start Jupyter:**

   ```bash
   poetry run jupyter notebook
   ```

2. **Open the notebook:**

   Navigate to `examples/test_prompt_manager.ipynb`

3. **Run all cells:**

   Use `Cell > Run All` or run each cell individually to see step-by-step results

### What the Notebook Tests

The notebook provides a complete workflow test:

1. **Environment Setup** - Loads API key from `.env`
2. **Prompt Loading** - Imports prompts from YAML files
3. **Template Rendering** - Tests variable substitution
4. **Anthropic Integration** - Converts prompts to Anthropic format
5. **API Calls** - Makes real LLM requests
6. **Response Validation** - Parses and validates JSON responses

Each cell performs a **single action**, making it easy to:
- Debug issues step-by-step
- Understand the complete flow
- Modify variables and re-run specific steps
- Validate that all components work together

### Expected Output

When all tests pass, you should see:

- ✓ checkmarks for each successful step
- Rendered prompts with your variables
- Actual LLM responses from Anthropic
- Parsed and validated JSON output
- Token usage statistics
- A final test summary

### Troubleshooting

**API Key not found:**
- Verify `.env` file exists in project root
- Check that `ANTHROPIC_API_KEY` is set correctly

**Import errors:**
- Ensure you installed with `--extras anthropic`
- Run `poetry install --extras all` to install all integrations

**YAML prompts not loading:**
- Verify `examples/prompts/` directory contains `.yaml` files
- Check file permissions

**Async warnings:**
- The notebook uses `await` syntax - ensure you're using a Jupyter kernel that supports async

## Running the Examples

### Simplified Usage (Recommended for New Users)

```bash
poetry run python examples/simplified_usage.py
```

This demonstrates:
- Default configuration with `./prompts` directory
- Automatic YAML file loading
- Custom directory configuration
- Backward compatibility with old API
- Complete workflow from YAML to rendering

### Comprehensive Examples

For more advanced usage patterns, see `basic_usage.py`:

```bash
poetry run python examples/basic_usage.py
```

This demonstrates:
- Creating and registering prompts
- Loading from YAML
- Rendering templates
- Schema validation
- Framework integrations (OpenAI, Anthropic, LangChain, LiteLLM)

## Migration Guide

### From Old API to New API

**Before (Verbose):**
```python
from prompt_manager import PromptManager
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.storage import FileSystemStorage, YAMLLoader
from pathlib import Path

storage = FileSystemStorage(Path("./data/prompts"))
registry = PromptRegistry(storage=storage)
loader = YAMLLoader(registry)
await loader.import_to_registry(Path("./data/prompts.yaml"))
manager = PromptManager(registry=registry)
```

**After (Simplified):**
```python
from prompt_manager import PromptManager

manager = await PromptManager.create()
```

The old API still works for backward compatibility!
