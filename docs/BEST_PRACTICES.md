# Best Practices: Dual Sync/Async Interface

This guide provides best practices for using the dual sync/async interface effectively in your applications.

## Quick Decision Guide

### Use Sync Mode When:

- ✅ Writing CLI tools or scripts
- ✅ Working in Jupyter notebooks
- ✅ Building simple automation
- ✅ Prototyping ideas
- ✅ Single-threaded operations
- ✅ No other async code
- ✅ Simplicity is priority

### Use Async Mode When:

- ✅ Building web servers (FastAPI, aiohttp)
- ✅ Handling concurrent requests
- ✅ High throughput requirements
- ✅ Existing async codebase
- ✅ Using asyncio features
- ✅ Multiple I/O operations
- ✅ Performance is priority

## Performance Characteristics

### Sync Mode Performance

```python
from prompt_manager import PromptManager

manager = PromptManager.create()

# Single operation: ~1ms overhead
result = manager.render("greeting", {"name": "Alice"})

# 100 sequential operations: ~5% overhead
for i in range(100):
    result = manager.render("greeting", {"name": f"User{i}"})
```

**Characteristics:**
- Minimal overhead (<5% vs async)
- Simple execution model
- Predictable performance
- No concurrency benefits

### Async Mode Performance

```python
import asyncio
from prompt_manager import PromptManager

manager = await PromptManager.create()

# Single operation: identical to sync
result = await manager.render("greeting", {"name": "Alice"})

# 100 concurrent operations: 10-50x faster
tasks = [
    manager.render("greeting", {"name": f"User{i}"})
    for i in range(100)
]
results = await asyncio.gather(*tasks)
```

**Characteristics:**
- ~0% overhead vs v1.x async
- Excellent concurrency
- Scales with I/O operations
- Requires async context

## Use Case Patterns

### Pattern 1: CLI Tool (Sync)

**Scenario:** Command-line tool for managing prompts.

```python
#!/usr/bin/env python3
"""CLI tool for prompt management."""
import click
from prompt_manager import PromptManager
from pathlib import Path

@click.group()
def cli():
    """Prompt Manager CLI."""
    pass

@cli.command()
@click.argument("prompt_id")
@click.option("--name", default="World")
def render(prompt_id: str, name: str):
    """Render a prompt."""
    manager = PromptManager.create()
    result = manager.render(prompt_id, {"name": name})
    click.echo(result)

@cli.command()
def list_prompts():
    """List all prompts."""
    manager = PromptManager.create()
    prompts = manager.list_prompts()

    for prompt in prompts:
        click.echo(f"{prompt.id} (v{prompt.version})")

if __name__ == "__main__":
    cli()
```

**Why Sync:**
- Simple, readable code
- No concurrency needed
- Natural CLI flow
- Easy error handling

### Pattern 2: Web Server (Async)

**Scenario:** FastAPI server handling concurrent requests.

```python
"""FastAPI server with prompt rendering."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prompt_manager import PromptManager
from typing import Dict, Any

app = FastAPI()

# Shared manager instance
manager: PromptManager | None = None

@app.on_event("startup")
async def startup():
    """Initialize manager on startup."""
    global manager
    manager = await PromptManager.create()

class RenderRequest(BaseModel):
    prompt_id: str
    variables: Dict[str, Any]

@app.post("/render")
async def render_prompt(request: RenderRequest):
    """Render a prompt with variables."""
    if not manager:
        raise HTTPException(500, "Manager not initialized")

    try:
        result = await manager.render(
            request.prompt_id,
            request.variables
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.get("/prompts")
async def list_prompts():
    """List all available prompts."""
    if not manager:
        raise HTTPException(500, "Manager not initialized")

    prompts = await manager.list_prompts()
    return {
        "prompts": [
            {"id": p.id, "version": p.version}
            for p in prompts
        ]
    }
```

**Why Async:**
- Handles concurrent requests efficiently
- Non-blocking I/O operations
- FastAPI is async-first
- Better resource utilization

### Pattern 3: Jupyter Notebook (Sync)

**Scenario:** Interactive data exploration and prompt testing.

```python
# Cell 1: Setup
from prompt_manager import PromptManager
from pathlib import Path

# Simple synchronous usage
manager = PromptManager.create()
print(f"Loaded {manager.count()} prompts")

# Cell 2: Test rendering
result = manager.render("greeting", {"name": "Alice"})
print(result)

# Cell 3: Iterate and experiment
prompts = manager.list_prompts()

for prompt in prompts:
    print(f"\n{prompt.id}:")
    result = manager.render(prompt.id, {"name": "Test"})
    print(f"  {result[:50]}...")

# Cell 4: Update and test
prompt = manager.get_prompt("greeting")
prompt.template.content = "Hi {{name}}!"
manager.update_prompt(prompt)

# Test immediately
print(manager.render("greeting", {"name": "World"}))
```

**Why Sync:**
- Natural notebook flow
- No event loop management
- Easy cell-by-cell execution
- Interactive experimentation

### Pattern 4: Batch Processing (Sync)

**Scenario:** Process prompts sequentially with logging.

```python
"""Batch process prompts with detailed logging."""
import logging
from prompt_manager import PromptManager
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_prompts(input_file: Path, output_file: Path):
    """Process prompts from input file."""
    manager = PromptManager.create()

    # Read inputs
    with open(input_file) as f:
        inputs = [line.strip() for line in f]

    # Process each
    results = []
    for i, user_input in enumerate(inputs, 1):
        logger.info(f"Processing {i}/{len(inputs)}: {user_input}")

        try:
            result = manager.render("processor", {
                "input": user_input
            })
            results.append(result)
            logger.info(f"  Success: {len(result)} chars")

        except Exception as e:
            logger.error(f"  Failed: {e}")
            results.append(f"ERROR: {e}")

    # Write outputs
    with open(output_file, "w") as f:
        f.write("\n".join(results))

    logger.info(f"Processed {len(results)} items")

if __name__ == "__main__":
    process_prompts(
        Path("inputs.txt"),
        Path("outputs.txt")
    )
```

**Why Sync:**
- Sequential processing desired
- Detailed logging per item
- Simple error handling
- Predictable execution order

### Pattern 5: Concurrent Processing (Async)

**Scenario:** Process many prompts concurrently for speed.

```python
"""Concurrent prompt processing for high throughput."""
import asyncio
import logging
from prompt_manager import PromptManager
from pathlib import Path
from typing import List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_one(
    manager: PromptManager,
    prompt_id: str,
    variables: dict
) -> Tuple[str, str | Exception]:
    """Process a single prompt."""
    try:
        result = await manager.render(prompt_id, variables)
        return (prompt_id, result)
    except Exception as e:
        return (prompt_id, e)

async def process_many(
    prompts: List[Tuple[str, dict]]
) -> List[Tuple[str, str | Exception]]:
    """Process many prompts concurrently."""
    manager = await PromptManager.create()

    # Create tasks
    tasks = [
        process_one(manager, prompt_id, variables)
        for prompt_id, variables in prompts
    ]

    # Process with progress logging
    logger.info(f"Processing {len(tasks)} prompts concurrently")

    # Use as_completed for progress updates
    results = []
    for i, coro in enumerate(asyncio.as_completed(tasks), 1):
        result = await coro
        results.append(result)

        if i % 10 == 0:
            logger.info(f"  Completed: {i}/{len(tasks)}")

    return results

async def main():
    """Main entry point."""
    # Prepare inputs
    prompts = [
        ("greeting", {"name": f"User{i}"})
        for i in range(100)
    ]

    # Process concurrently
    results = await process_many(prompts)

    # Count successes/failures
    successes = sum(1 for _, r in results if not isinstance(r, Exception))
    logger.info(f"Completed: {successes}/{len(results)} successful")

if __name__ == "__main__":
    asyncio.run(main())
```

**Why Async:**
- Process 100 prompts concurrently
- 10-50x faster than sequential
- Progress updates while running
- Efficient I/O utilization

## Event Loop Management

### Understanding the Event Loop

The dual interface uses event loops differently based on context:

**Sync Mode:**
```python
# Creates a temporary event loop for each operation
manager = PromptManager.create()  # Creates loop
result = manager.render(...)      # Uses loop, then cleans up
```

**Async Mode:**
```python
# Uses the existing running event loop
async def handler():
    manager = await PromptManager.create()  # Uses running loop
    result = await manager.render(...)       # Uses running loop
```

### Best Practice: One Loop per Context

**Good:**
```python
# Sync script - let library manage loops
def main():
    manager = PromptManager.create()
    result = manager.render("greeting", {})
    return result

# Async script - one event loop
async def main():
    manager = await PromptManager.create()
    result = await manager.render("greeting", {})
    return result

asyncio.run(main())
```

**Avoid:**
```python
# Don't mix sync calls in async context
async def main():
    manager = PromptManager.create()  # ❌ Creates nested loop
    result = manager.render("greeting", {})  # ❌ RuntimeError!
```

### Handling Existing Event Loops

**Scenario:** You have an existing event loop and want to add sync code.

```python
# Option 1: Convert to async (preferred)
async def process():
    manager = await PromptManager.create()
    result = await manager.render("greeting", {})
    return result

# Option 2: Run in separate thread (if must stay sync)
import concurrent.futures

def sync_process():
    manager = PromptManager.create()
    return manager.render("greeting", {})

# From async context
async def async_context():
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, sync_process)
    return result
```

## Error Handling

### Sync Error Handling

```python
from prompt_manager import PromptManager
from prompt_manager.exceptions import (
    PromptNotFoundError,
    TemplateError,
    SchemaValidationError
)

def safe_render(prompt_id: str, variables: dict) -> str | None:
    """Render with comprehensive error handling."""
    manager = PromptManager.create()

    try:
        result = manager.render(prompt_id, variables)
        return result

    except PromptNotFoundError:
        print(f"Prompt '{prompt_id}' not found")
        return None

    except TemplateError as e:
        print(f"Template error: {e}")
        return None

    except SchemaValidationError as e:
        print(f"Validation error: {e}")
        return None

    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

### Async Error Handling

```python
import asyncio
from prompt_manager import PromptManager
from prompt_manager.exceptions import PromptNotFoundError

async def safe_render_many(
    prompt_ids: list[str],
    variables: dict
) -> list[str]:
    """Render many prompts with error handling."""
    manager = await PromptManager.create()

    async def render_one(prompt_id: str) -> str:
        try:
            return await manager.render(prompt_id, variables)
        except PromptNotFoundError:
            return f"[Error: {prompt_id} not found]"
        except Exception as e:
            return f"[Error: {e}]"

    # Process concurrently with individual error handling
    tasks = [render_one(pid) for pid in prompt_ids]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    return results
```

## Testing Strategies

### Test Sync Code

```python
"""Test synchronous usage."""
import pytest
from prompt_manager import PromptManager

class TestSyncUsage:
    """Test synchronous prompt operations."""

    def setup_method(self):
        """Setup before each test."""
        self.manager = PromptManager.create()

    def test_create_and_render(self):
        """Test creating and rendering a prompt."""
        # Create
        self.manager.create_prompt({
            "id": "test",
            "version": "1.0.0",
            "template": {"content": "Hello {{name}}!"}
        })

        # Render
        result = self.manager.render("test", {"name": "Alice"})
        assert result == "Hello Alice!"

    def test_list_prompts(self):
        """Test listing prompts."""
        self.manager.create_prompt({...})
        self.manager.create_prompt({...})

        prompts = self.manager.list_prompts()
        assert len(prompts) == 2
```

### Test Async Code

```python
"""Test asynchronous usage."""
import pytest
from prompt_manager import PromptManager

class TestAsyncUsage:
    """Test asynchronous prompt operations."""

    @pytest.mark.asyncio
    async def test_create_and_render(self):
        """Test creating and rendering a prompt."""
        manager = await PromptManager.create()

        # Create
        await manager.create_prompt({
            "id": "test",
            "version": "1.0.0",
            "template": {"content": "Hello {{name}}!"}
        })

        # Render
        result = await manager.render("test", {"name": "Alice"})
        assert result == "Hello Alice!"

    @pytest.mark.asyncio
    async def test_concurrent_rendering(self):
        """Test concurrent rendering."""
        import asyncio

        manager = await PromptManager.create()
        await manager.create_prompt({...})

        # Render 10 times concurrently
        tasks = [
            manager.render("test", {"name": f"User{i}"})
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
```

### Test Both Modes

```python
"""Test that sync and async produce identical results."""
import pytest
import asyncio
from prompt_manager import PromptManager

def test_sync_async_equivalence():
    """Verify sync and async produce same results."""
    # Test data
    prompt_data = {
        "id": "test",
        "version": "1.0.0",
        "template": {"content": "Hello {{name}}!"}
    }
    variables = {"name": "Alice"}

    # Sync execution
    manager_sync = PromptManager.create()
    manager_sync.create_prompt(prompt_data)
    result_sync = manager_sync.render("test", variables)

    # Async execution
    async def async_flow():
        manager = await PromptManager.create()
        await manager.create_prompt(prompt_data)
        return await manager.render("test", variables)

    result_async = asyncio.run(async_flow())

    # Must be identical
    assert result_sync == result_async
```

## Common Anti-Patterns

### Anti-Pattern 1: Sync in Async Context

```python
# ❌ Wrong - will raise RuntimeError
async def handler():
    manager = PromptManager.create()  # Creates nested loop
    result = manager.render("test", {})  # RuntimeError!

# ✅ Correct - use await
async def handler():
    manager = await PromptManager.create()
    result = await manager.render("test", {})
```

### Anti-Pattern 2: Async in Sync for No Reason

```python
# ❌ Wrong - unnecessary complexity
import asyncio

def simple_script():
    async def inner():
        manager = await PromptManager.create()
        return await manager.render("test", {})

    return asyncio.run(inner())

# ✅ Correct - use sync mode
def simple_script():
    manager = PromptManager.create()
    return manager.render("test", {})
```

### Anti-Pattern 3: Creating Manager Per Operation

```python
# ❌ Wrong - inefficient
for i in range(100):
    manager = PromptManager.create()  # Creates new manager each time
    result = manager.render("test", {"id": i})

# ✅ Correct - reuse manager
manager = PromptManager.create()
for i in range(100):
    result = manager.render("test", {"id": i})
```

### Anti-Pattern 4: Not Using Concurrency When Beneficial

```python
# ❌ Wrong - sequential async (no benefit)
async def process():
    manager = await PromptManager.create()
    results = []
    for i in range(100):
        result = await manager.render("test", {"id": i})
        results.append(result)
    return results

# ✅ Correct - concurrent async
async def process():
    manager = await PromptManager.create()
    tasks = [
        manager.render("test", {"id": i})
        for i in range(100)
    ]
    return await asyncio.gather(*tasks)
```

## Memory Management

### Sync Mode

```python
# Manager automatically cleaned up when out of scope
def process():
    manager = PromptManager.create()
    result = manager.render("test", {})
    return result
    # Manager and event loop cleaned up here
```

### Async Mode

```python
# Use context manager for explicit cleanup
async def process():
    async with PromptManager.create_context() as manager:
        result = await manager.render("test", {})
        return result
    # Resources cleaned up here

# Or let Python garbage collection handle it
async def process():
    manager = await PromptManager.create()
    result = await manager.render("test", {})
    return result
    # Manager cleaned up when function exits
```

## Summary

1. **Choose based on context**: Sync for scripts/CLI, async for servers/concurrency
2. **Don't mix**: Sync in sync context, async in async context
3. **Reuse managers**: Create once, use many times
4. **Handle errors**: Both modes raise same exceptions
5. **Test both**: Verify sync and async produce identical results
6. **Leverage concurrency**: Use asyncio.gather() for parallel operations

For more information:
- [Migration Guide](../MIGRATION.md) - Migrating from v1.x
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues
- [Examples](../examples/) - Working code samples
