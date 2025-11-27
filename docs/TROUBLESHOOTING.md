# Troubleshooting: Dual Sync/Async Interface

This guide helps you resolve common issues when using the dual sync/async interface.

## Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| "RuntimeError: already running" | Use `await` in async functions, not sync calls |
| Event loop errors in Jupyter | Use sync mode (no `await`) or install `nest_asyncio` |
| Type checker warnings | Normal for dual interface, can be safely ignored |
| Slow performance | Use async mode with `asyncio.gather()` for concurrency |

## Common Issues

### Issue 1: RuntimeError: This event loop is already running

**Symptom:**
```python
RuntimeError: This event loop is already running
```

**Full Error:**
```
RuntimeError: This event loop is already running
    at prompt_manager.utils.async_helpers.run_sync()
    at prompt_manager.core.manager.render()

ERROR: Cannot create a nested event loop. You're trying to use sync mode
from within an async context. Use 'await' instead:

    # Instead of:
    result = manager.render("greeting", {})

    # Use:
    result = await manager.render("greeting", {})
```

**Cause:**

You're calling a sync method from within an async function. The library detects an already-running event loop and prevents creating a nested loop.

**Solutions:**

```python
# ❌ Wrong - sync call in async function
async def handler():
    manager = PromptManager.create()  # Error!
    result = manager.render("greeting", {})  # Error!
    return result

# ✅ Solution 1: Use await (recommended)
async def handler():
    manager = await PromptManager.create()
    result = await manager.render("greeting", {})
    return result

# ✅ Solution 2: Run sync code in thread (if you must)
import concurrent.futures
import asyncio

async def handler():
    def sync_code():
        manager = PromptManager.create()
        return manager.render("greeting", {})

    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, sync_code)
    return result
```

**Detection:**

The library checks for a running event loop:
```python
try:
    asyncio.get_running_loop()
    # Loop exists → you're in async context → must use await
except RuntimeError:
    # No loop → you're in sync context → can use sync mode
```

---

### Issue 2: Jupyter Notebook Event Loop Issues

**Symptom:**

```python
RuntimeError: asyncio.run() cannot be called from a running event loop
```

Or:
```python
RuntimeError: This event loop is already running
```

**Cause:**

Jupyter notebooks run their own event loop, which conflicts with creating new loops.

**Solution 1: Use Sync Mode (Recommended)**

```python
# ✅ Simplest - just don't use await in Jupyter
from prompt_manager import PromptManager

manager = PromptManager.create()
result = manager.render("greeting", {"name": "Alice"})
print(result)

# No event loop issues!
```

**Solution 2: Install nest_asyncio**

```python
# If you need async features in Jupyter
import nest_asyncio
nest_asyncio.apply()

# Now async works
from prompt_manager import PromptManager

manager = await PromptManager.create()
result = await manager.render("greeting", {"name": "Alice"})
print(result)
```

**Solution 3: Use IPython's autoawait**

```python
# IPython 7.0+ supports top-level await
# Just enable it:
%autoawait asyncio

# Then use await directly
from prompt_manager import PromptManager

manager = await PromptManager.create()
result = await manager.render("greeting", {"name": "Alice"})
```

---

### Issue 3: FastAPI Integration Issues

**Symptom:**

```python
# Routes not working correctly
@app.get("/render")
def render(prompt_id: str):  # Missing 'async'
    result = await manager.render(prompt_id, {})  # SyntaxError!
```

**Solutions:**

```python
from fastapi import FastAPI
from prompt_manager import PromptManager

app = FastAPI()
manager: PromptManager | None = None

@app.on_event("startup")
async def startup():
    """Initialize manager on startup."""
    global manager
    manager = await PromptManager.create()

# ✅ Solution 1: Async route with await (recommended)
@app.get("/render/{prompt_id}")
async def render_async(prompt_id: str):
    """Async route - use await."""
    result = await manager.render(prompt_id, {})
    return {"result": result}

# ✅ Solution 2: Sync route without await (works but less efficient)
@app.get("/render-sync/{prompt_id}")
def render_sync(prompt_id: str):
    """Sync route - no await."""
    # Note: Manager should still be created async in startup
    # This works but bypasses FastAPI's async benefits
    result = manager.render(prompt_id, {})
    return {"result": result}
```

**Best Practice:**

Use async routes in FastAPI for better performance:

```python
# ✅ Correct pattern
@app.get("/batch")
async def batch_render(prompt_ids: list[str]):
    """Concurrent batch processing."""
    import asyncio

    tasks = [
        manager.render(pid, {})
        for pid in prompt_ids
    ]
    results = await asyncio.gather(*tasks)

    return {"results": results}
```

---

### Issue 4: Type Checker Warnings

**Symptom (mypy):**

```python
result = manager.render("greeting", {})
# error: Incompatible types in assignment
#        (expression has type "str | Awaitable[str]", variable has type "str")
```

**Symptom (Pyright):**

```python
result = manager.render("greeting", {})
# Type of "result" is "str | Coroutine[Any, Any, str]"
```

**Explanation:**

The dual interface returns `Union[T, Awaitable[T]]` to support both modes. Type checkers see this union but can't determine which path you're using.

**Solution 1: Use await (Preferred)**

```python
# ✅ Type checker understands this
async def handler():
    result: str = await manager.render("greeting", {})
    # Type is correctly narrowed to 'str'
```

**Solution 2: Type Assertion**

```python
from typing import cast

# For sync usage
result: str = cast(str, manager.render("greeting", {}))

# Type checker now treats it as 'str'
```

**Solution 3: Ignore for Sync Code**

```python
result = manager.render("greeting", {})  # type: ignore[assignment]
```

**Solution 4: Configure Type Checker**

```toml
# pyproject.toml
[tool.mypy]
warn_return_any = false
disable_error_code = ["assignment"]

[tool.pyright]
reportGeneralTypeIssues = false
```

**Note:** These warnings are cosmetic. The code works correctly at runtime.

---

### Issue 5: Performance Issues (Sync Mode)

**Symptom:**

Sync mode is slow when processing many operations sequentially.

```python
# Slow - takes 10 seconds for 100 operations
manager = PromptManager.create()
results = []
for i in range(100):
    result = manager.render("test", {"id": i})
    results.append(result)
```

**Solution: Use Async Mode with Concurrency**

```python
import asyncio

async def process():
    manager = await PromptManager.create()

    # Fast - takes 1 second for 100 operations
    tasks = [
        manager.render("test", {"id": i})
        for i in range(100)
    ]
    results = await asyncio.gather(*tasks)
    return results

# Run it
results = asyncio.run(process())
```

**When to Use Each:**

```python
# Sync mode: Simple, 1-10 operations
manager = PromptManager.create()
result = manager.render("test", {})  # Fine for single operation

# Async mode: High performance, 10+ concurrent operations
async def batch():
    manager = await PromptManager.create()
    tasks = [manager.render("test", {}) for _ in range(100)]
    results = await asyncio.gather(*tasks)  # 10-50x faster
```

---

### Issue 6: Memory Leaks with Event Loops

**Symptom:**

Memory usage grows over time with repeated sync calls.

```python
# Potential memory leak
for i in range(10000):
    manager = PromptManager.create()  # Creates new manager each time
    result = manager.render("test", {})
```

**Solution: Reuse Manager**

```python
# ✅ Correct - reuse manager
manager = PromptManager.create()  # Create once

for i in range(10000):
    result = manager.render("test", {})  # Reuse many times

# Manager cleaned up when out of scope
```

**For Long-Running Services:**

```python
# ✅ Module-level manager for services
from prompt_manager import PromptManager

# Initialize once at startup
_manager: PromptManager | None = None

def get_manager() -> PromptManager:
    """Get or create manager singleton."""
    global _manager
    if _manager is None:
        _manager = PromptManager.create()
    return _manager

# Use throughout application
def handler():
    manager = get_manager()
    return manager.render("test", {})
```

---

### Issue 7: Mixing Sync and Async in Same Function

**Symptom:**

```python
def mixed_function():
    # Sometimes works, sometimes crashes
    manager = PromptManager.create()
    result1 = manager.render("test1", {})  # Works

    async def inner():
        result2 = await manager.render("test2", {})  # Error!
        return result2

    import asyncio
    result2 = asyncio.run(inner())  # RuntimeError!

    return result1, result2
```

**Cause:**

Can't mix sync-created manager with async inner function.

**Solution:**

```python
# ✅ Option 1: Stay fully sync
def sync_function():
    manager = PromptManager.create()
    result1 = manager.render("test1", {})
    result2 = manager.render("test2", {})
    return result1, result2

# ✅ Option 2: Stay fully async
async def async_function():
    manager = await PromptManager.create()
    result1 = await manager.render("test1", {})
    result2 = await manager.render("test2", {})
    return result1, result2

# Then run it
import asyncio
result1, result2 = asyncio.run(async_function())
```

---

### Issue 8: Flask Integration

**Symptom:**

```python
from flask import Flask

app = Flask(__name__)

@app.route("/render")
def render():
    # Can't use await in Flask route
    result = await manager.render("test", {})  # SyntaxError!
```

**Solution:**

```python
from flask import Flask
from prompt_manager import PromptManager

app = Flask(__name__)

# Initialize manager at startup
manager = PromptManager.create()  # Sync initialization

@app.route("/render/<prompt_id>")
def render(prompt_id: str):
    """Sync Flask route."""
    # Use sync mode - no await needed
    result = manager.render(prompt_id, {})
    return {"result": result}

if __name__ == "__main__":
    app.run()
```

**Alternative: Use Quart (Async Flask)**

```python
from quart import Quart
from prompt_manager import PromptManager

app = Quart(__name__)
manager: PromptManager | None = None

@app.before_serving
async def startup():
    """Initialize manager."""
    global manager
    manager = await PromptManager.create()

@app.route("/render/<prompt_id>")
async def render(prompt_id: str):
    """Async Quart route."""
    result = await manager.render(prompt_id, {})
    return {"result": result}

if __name__ == "__main__":
    app.run()
```

---

### Issue 9: Testing Issues

**Symptom:**

Tests fail with event loop errors.

```python
# Test fails
def test_render():
    manager = PromptManager.create()
    result = manager.render("test", {})  # Sometimes works, sometimes fails
```

**Solution 1: Pure Sync Tests**

```python
import pytest
from prompt_manager import PromptManager

def test_sync_render():
    """Pure sync test."""
    manager = PromptManager.create()
    manager.create_prompt({...})

    result = manager.render("test", {})
    assert "expected" in result
```

**Solution 2: Pure Async Tests**

```python
import pytest
from prompt_manager import PromptManager

@pytest.mark.asyncio
async def test_async_render():
    """Pure async test."""
    manager = await PromptManager.create()
    await manager.create_prompt({...})

    result = await manager.render("test", {})
    assert "expected" in result
```

**Solution 3: Test Both Modes**

```python
import pytest
import asyncio
from prompt_manager import PromptManager

def test_sync_mode():
    """Test sync execution."""
    manager = PromptManager.create()
    result = manager.render("test", {})
    assert result is not None

@pytest.mark.asyncio
async def test_async_mode():
    """Test async execution."""
    manager = await PromptManager.create()
    result = await manager.render("test", {})
    assert result is not None

def test_both_modes_equivalent():
    """Test that both modes produce same results."""
    # Sync
    manager_sync = PromptManager.create()
    result_sync = manager_sync.render("test", {})

    # Async
    async def async_test():
        manager = await PromptManager.create()
        return await manager.render("test", {})

    result_async = asyncio.run(async_test())

    # Should be identical
    assert result_sync == result_async
```

---

### Issue 10: ImportError with Optional Dependencies

**Symptom:**

```python
from prompt_manager.integrations import OpenAIIntegration
# ImportError: OpenAI integration requires 'openai' package
```

**Solution:**

```python
# Install the required dependency
pip install agentic-prompt-manager[openai]

# Or install all integrations
pip install agentic-prompt-manager[all]
```

**Graceful Handling:**

```python
try:
    from prompt_manager.integrations import OpenAIIntegration
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

if HAS_OPENAI:
    # Use OpenAI integration
    integration = OpenAIIntegration(...)
else:
    # Fallback or error message
    print("Install OpenAI: pip install agentic-prompt-manager[openai]")
```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Shows event loop creation/cleanup
from prompt_manager import PromptManager

manager = PromptManager.create()
result = manager.render("test", {})
```

### Check Event Loop State

```python
import asyncio

def check_loop():
    """Check if event loop is running."""
    try:
        loop = asyncio.get_running_loop()
        print(f"✅ Event loop running: {loop}")
        return True
    except RuntimeError:
        print("❌ No event loop running")
        return False

# Use in your code
check_loop()  # Should return False in sync context

async def async_context():
    check_loop()  # Should return True in async context
```

### Profile Performance

```python
import time
from prompt_manager import PromptManager

# Sync performance
start = time.time()
manager = PromptManager.create()
for i in range(100):
    manager.render("test", {})
sync_time = time.time() - start

# Async performance
import asyncio

async def async_test():
    manager = await PromptManager.create()
    tasks = [manager.render("test", {}) for _ in range(100)]
    await asyncio.gather(*tasks)

start = time.time()
asyncio.run(async_test())
async_time = time.time() - start

print(f"Sync: {sync_time:.2f}s, Async: {async_time:.2f}s")
print(f"Speedup: {sync_time/async_time:.1f}x")
```

---

## Getting Help

If you're still having issues:

1. **Check the examples**: See [examples/](../examples/) for working code
2. **Read best practices**: See [BEST_PRACTICES.md](BEST_PRACTICES.md)
3. **Review migration guide**: See [MIGRATION.md](../MIGRATION.md)
4. **File an issue**: [GitHub Issues](https://github.com/joshuamschultz/prompt-manager/issues)

When filing an issue, include:
- Python version
- Prompt Manager version
- Minimal reproduction code
- Full error traceback
- Context (Jupyter, FastAPI, script, etc.)

---

## Summary

| Issue | Solution |
|-------|----------|
| RuntimeError in async | Use `await` |
| Jupyter event loop | Use sync mode or `nest_asyncio` |
| FastAPI issues | Use `async def` routes with `await` |
| Flask issues | Use sync mode (no `await`) |
| Type warnings | Normal, can ignore or cast |
| Slow performance | Use async with `gather()` |
| Memory leaks | Reuse manager instance |
| Test failures | Separate sync and async tests |

The key principle: **Sync in sync contexts, async in async contexts**.
