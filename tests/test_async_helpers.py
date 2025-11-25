"""Unit tests for async_helpers module.

Tests the event loop management utilities that enable dual sync/async interface support.
"""

import asyncio
import pytest

from prompt_manager.utils.async_helpers import is_async_context, get_or_create_event_loop, run_sync


# =============================================================================
# Tests for is_async_context()
# =============================================================================

def test_is_async_context_returns_false_in_sync():
    """Test that is_async_context() returns False in synchronous context."""
    result = is_async_context()
    assert result is False


@pytest.mark.asyncio
async def test_is_async_context_returns_true_in_async():
    """Test that is_async_context() returns True in asynchronous context."""
    result = is_async_context()
    assert result is True


@pytest.mark.asyncio
async def test_is_async_context_in_nested_async_function():
    """Test that is_async_context() returns True in nested async functions."""
    async def nested_async():
        return is_async_context()

    result = await nested_async()
    assert result is True


def test_is_async_context_with_pytest_fixture():
    """Test that is_async_context() works correctly in pytest fixture context."""
    # In a regular pytest test (not marked with asyncio), there's no running loop
    result = is_async_context()
    assert result is False


@pytest.mark.asyncio
async def test_is_async_context_multiple_calls():
    """Test that multiple calls to is_async_context() are consistent."""
    results = [is_async_context() for _ in range(5)]
    assert all(result is True for result in results)


def test_is_async_context_in_sync_function_called_from_test():
    """Test is_async_context() when called through a synchronous function."""
    def sync_wrapper():
        return is_async_context()

    result = sync_wrapper()
    assert result is False


@pytest.mark.asyncio
async def test_is_async_context_in_sync_function_called_from_async():
    """Test is_async_context() in sync function called from async context.

    Note: The sync function itself runs in the async context, so it should
    still detect the running loop.
    """
    def sync_wrapper():
        return is_async_context()

    # Even though sync_wrapper is not async, it runs in the async context
    result = sync_wrapper()
    assert result is True


# =============================================================================
# Tests for get_or_create_event_loop()
# =============================================================================

def test_get_or_create_event_loop_creates_new_loop_when_none_exists():
    """Test that get_or_create_event_loop() creates a new loop when none exists."""
    # Close any existing loop to ensure clean state
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.close()
    except RuntimeError:
        pass

    # Clear the event loop
    asyncio.set_event_loop(None)

    # Now get_or_create should create a new loop
    loop = get_or_create_event_loop()
    assert loop is not None
    assert isinstance(loop, asyncio.AbstractEventLoop)
    assert not loop.is_closed()

    # Clean up
    loop.close()


def test_get_or_create_event_loop_returns_existing_loop():
    """Test that get_or_create_event_loop() returns existing loop when available."""
    # Create a loop and set it
    existing_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(existing_loop)

    # Get the loop - should return the same one
    loop = get_or_create_event_loop()
    assert loop is existing_loop
    assert not loop.is_closed()

    # Clean up
    loop.close()


def test_get_or_create_event_loop_creates_new_when_loop_is_closed():
    """Test that get_or_create_event_loop() creates new loop when existing loop is closed."""
    # Create and close a loop
    old_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(old_loop)
    old_loop.close()

    # Get loop - should create a new one since old one is closed
    loop = get_or_create_event_loop()
    assert loop is not old_loop  # Should be a different loop
    assert not loop.is_closed()

    # Clean up
    loop.close()


@pytest.mark.asyncio
async def test_get_or_create_event_loop_raises_in_async_context():
    """Test that get_or_create_event_loop() raises RuntimeError in async context."""
    with pytest.raises(RuntimeError) as exc_info:
        get_or_create_event_loop()

    # Verify error message is helpful
    error_msg = str(exc_info.value)
    assert "Cannot call synchronous method from async context" in error_msg
    assert "await" in error_msg.lower()


def test_get_or_create_event_loop_sets_as_current():
    """Test that get_or_create_event_loop() sets loop as current event loop."""
    # Clear any existing loop
    asyncio.set_event_loop(None)

    # Get or create loop
    loop = get_or_create_event_loop()

    # Verify it's set as the current loop
    current_loop = asyncio.get_event_loop()
    assert current_loop is loop

    # Clean up
    loop.close()


def test_get_or_create_event_loop_thread_local():
    """Test that get_or_create_event_loop() is thread-local (each thread gets its own loop)."""
    import threading

    loops = {}

    def get_loop_in_thread(thread_id):
        """Helper function to get loop in a thread."""
        # Clear any existing loop in this thread
        asyncio.set_event_loop(None)
        loop = get_or_create_event_loop()
        loops[thread_id] = loop

    # Create loops in different threads
    thread1 = threading.Thread(target=get_loop_in_thread, args=(1,))
    thread2 = threading.Thread(target=get_loop_in_thread, args=(2,))

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    # Verify each thread got a different loop
    assert len(loops) == 2
    assert loops[1] is not loops[2]

    # Clean up loops (need to close them in their own threads or use call_soon_threadsafe)
    # For simplicity, we'll just verify they're different and not worry about cleanup
    # in this test since they'll be garbage collected


# =============================================================================
# Tests for run_sync()
# =============================================================================

def test_run_sync_executes_coroutine_and_returns_result():
    """Test that run_sync() executes a coroutine and returns the result."""
    async def simple_coro():
        return "test_result"

    result = run_sync(simple_coro())
    assert result == "test_result"


def test_run_sync_preserves_string_return_value():
    """Test that run_sync() preserves string return values."""
    async def return_string():
        return "Hello, World!"

    result = run_sync(return_string())
    assert result == "Hello, World!"
    assert isinstance(result, str)


def test_run_sync_preserves_dict_return_value():
    """Test that run_sync() preserves dict return values."""
    async def return_dict():
        return {"key": "value", "number": 42}

    result = run_sync(return_dict())
    assert result == {"key": "value", "number": 42}
    assert isinstance(result, dict)


def test_run_sync_preserves_list_return_value():
    """Test that run_sync() preserves list return values."""
    async def return_list():
        return [1, 2, 3, "four", {"five": 5}]

    result = run_sync(return_list())
    assert result == [1, 2, 3, "four", {"five": 5}]
    assert isinstance(result, list)


def test_run_sync_preserves_custom_object_return_value():
    """Test that run_sync() preserves custom object return values."""
    class CustomObject:
        def __init__(self, value):
            self.value = value

        def __eq__(self, other):
            return isinstance(other, CustomObject) and self.value == other.value

    async def return_custom():
        return CustomObject(42)

    result = run_sync(return_custom())
    assert isinstance(result, CustomObject)
    assert result.value == 42


@pytest.mark.asyncio
async def test_run_sync_raises_in_async_context():
    """Test that run_sync() raises RuntimeError when called from async context."""
    async def dummy_coro():
        return "should not reach here"

    with pytest.raises(RuntimeError) as exc_info:
        run_sync(dummy_coro())

    # Verify error message is helpful
    error_msg = str(exc_info.value)
    assert "Cannot call synchronous method from async context" in error_msg
    assert "await" in error_msg.lower()


def test_run_sync_propagates_exceptions():
    """Test that run_sync() propagates exceptions from the coroutine."""
    async def failing_coro():
        raise ValueError("Test exception")

    with pytest.raises(ValueError) as exc_info:
        run_sync(failing_coro())

    assert str(exc_info.value) == "Test exception"


def test_run_sync_preserves_stack_trace():
    """Test that run_sync() preserves the full stack trace of exceptions."""
    async def nested_failing_coro():
        async def inner():
            raise RuntimeError("Deep error")
        return await inner()

    with pytest.raises(RuntimeError) as exc_info:
        run_sync(nested_failing_coro())

    # Verify exception message
    assert "Deep error" in str(exc_info.value)

    # Verify stack trace contains relevant information
    import traceback
    tb_lines = traceback.format_exception(type(exc_info.value), exc_info.value, exc_info.tb)
    tb_str = "".join(tb_lines)
    assert "nested_failing_coro" in tb_str or "inner" in tb_str


def test_run_sync_with_multiple_awaits():
    """Test that run_sync() works with coroutines containing multiple await calls."""
    async def multi_await_coro():
        result1 = await asyncio.sleep(0.01, result="first")
        result2 = await asyncio.sleep(0.01, result="second")
        return f"{result1}-{result2}"

    result = run_sync(multi_await_coro())
    assert result == "first-second"


def test_run_sync_rapid_successive_calls():
    """Test that run_sync() handles rapid successive calls (100+ iterations)."""
    async def counter_coro(n):
        await asyncio.sleep(0)  # Yield control
        return n * 2

    results = []
    for i in range(100):
        result = run_sync(counter_coro(i))
        results.append(result)

    # Verify all results are correct
    assert results == [i * 2 for i in range(100)]
    assert len(results) == 100


def test_run_sync_with_async_context_manager():
    """Test that run_sync() works with coroutines using async context managers."""
    class AsyncContextManager:
        async def __aenter__(self):
            return "entered"

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

    async def use_context_manager():
        async with AsyncContextManager() as value:
            return f"Got: {value}"

    result = run_sync(use_context_manager())
    assert result == "Got: entered"


def test_run_sync_with_asyncio_gather():
    """Test that run_sync() works with asyncio.gather for concurrent operations."""
    async def task(n):
        await asyncio.sleep(0.001)
        return n * 2

    async def run_concurrent():
        results = await asyncio.gather(task(1), task(2), task(3))
        return sum(results)

    result = run_sync(run_concurrent())
    assert result == (1*2 + 2*2 + 3*2)  # 12


# =============================================================================
# Edge Case Tests
# =============================================================================

def test_edge_case_jupyter_notebook_simulation():
    """Test behavior in Jupyter notebook simulation with nested event loops.

    Jupyter notebooks often have a running event loop. This test simulates
    that scenario by testing from within an existing event loop context.
    """
    # This is already tested by test_get_or_create_event_loop_raises_in_async_context
    # and test_run_sync_raises_in_async_context, which verify that calling
    # sync methods from async context (like Jupyter's running loop) raises
    # clear errors with helpful messages.

    # Additional test: Verify error message mentions the right approach
    async def in_jupyter_like_context():
        with pytest.raises(RuntimeError) as exc_info:
            get_or_create_event_loop()

        error_msg = str(exc_info.value)
        assert "await" in error_msg.lower()
        assert "async" in error_msg.lower()

    # Run this test
    asyncio.run(in_jupyter_like_context())


def test_edge_case_closed_event_loop_recovery():
    """Test that utilities gracefully handle closed event loops."""
    # Create and close a loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.close()

    # run_sync should still work by creating a new loop
    async def simple_task():
        return "recovered"

    result = run_sync(simple_task())
    assert result == "recovered"

    # Clean up
    current_loop = asyncio.get_event_loop()
    if not current_loop.is_closed():
        current_loop.close()


def test_edge_case_multiple_sequential_loop_creations():
    """Test creating and closing loops multiple times in sequence."""
    results = []

    for i in range(5):
        # Clear any existing loop
        asyncio.set_event_loop(None)

        # Create and use a loop
        async def task():
            return f"iteration_{i}"

        result = run_sync(task())
        results.append(result)

        # Close the loop
        loop = asyncio.get_event_loop()
        loop.close()

    assert results == [f"iteration_{i}" for i in range(5)]


def test_edge_case_error_messages_are_clear():
    """Test that error messages are clear and actionable."""
    # Test async context error
    async def test_in_async():
        try:
            run_sync(asyncio.sleep(0))
        except RuntimeError as e:
            msg = str(e)
            # Check for key phrases
            assert "Cannot call synchronous method from async context" in msg
            assert "await" in msg
            assert "Example:" in msg or "example" in msg.lower()
            return True
        return False

    result = asyncio.run(test_in_async())
    assert result is True


def test_edge_case_no_memory_leaks_basic():
    """Basic test to ensure no obvious memory leaks with repeated calls."""
    import gc

    # Run many operations
    for _ in range(50):
        async def small_task():
            return "test"

        result = run_sync(small_task())
        assert result == "test"

    # Force garbage collection
    gc.collect()

    # If we got here without crashing or running out of memory, we're good
    # Note: This is a basic smoke test, not a comprehensive memory leak test
    assert True


def test_edge_case_pytest_asyncio_compatibility():
    """Test that utilities work correctly with pytest-asyncio plugin."""
    # This is implicitly tested by all our @pytest.mark.asyncio tests
    # This test just documents that pytest-asyncio is compatible

    @pytest.mark.asyncio
    async def async_test_function():
        # In pytest-asyncio, this runs in an async context
        assert is_async_context() is True

        # Trying to use run_sync should fail
        with pytest.raises(RuntimeError):
            async def dummy():
                return "test"
            run_sync(dummy())

    # Run the test
    asyncio.run(async_test_function())


def test_edge_case_exception_types_preserved():
    """Test that various exception types are preserved through run_sync()."""
    # Test different exception types
    exception_types = [
        (ValueError, "value error", "value error"),
        (TypeError, "type error", "type error"),
        (KeyError, "key_error", "'key_error'"),  # KeyError adds quotes
        (RuntimeError, "runtime error", "runtime error"),
        (AttributeError, "attribute error", "attribute error"),
    ]

    for exc_type, exc_msg, expected_str in exception_types:
        async def raising_coro():
            raise exc_type(exc_msg)

        with pytest.raises(exc_type) as exc_info:
            run_sync(raising_coro())

        assert str(exc_info.value) == expected_str


def test_edge_case_nested_run_sync_calls():
    """Test that nested run_sync calls are handled properly."""
    # Note: Nested run_sync is generally not recommended, but should work
    # if each call is in a synchronous context

    async def inner_async():
        return "inner"

    def sync_wrapper():
        return run_sync(inner_async())

    async def outer_async():
        # This runs in async context, so calling sync_wrapper (which uses run_sync)
        # should fail
        return sync_wrapper()

    # The outer async function tries to use run_sync indirectly
    # This should raise an error
    with pytest.raises(RuntimeError) as exc_info:
        asyncio.run(outer_async())

    assert "Cannot call synchronous method from async context" in str(exc_info.value)
