"""Benchmark context detection overhead."""

import asyncio
import time
from statistics import mean, stdev

from prompt_manager import PromptManager


def measure_operation(operation, iterations=10000):
    """Measure operation performance."""
    times = []
    for _ in range(5):  # 5 runs
        start = time.perf_counter()
        for _ in range(iterations):
            operation()
        end = time.perf_counter()
        times.append((end - start) / iterations * 1000)  # ms per operation

    return {
        'mean': mean(times),
        'stdev': stdev(times),
        'min': min(times),
        'max': max(times),
    }


async def measure_async_operation(operation, iterations=10000):
    """Measure async operation performance."""
    times = []
    for _ in range(5):
        start = time.perf_counter()
        for _ in range(iterations):
            await operation()
        end = time.perf_counter()
        times.append((end - start) / iterations * 1000)

    return {
        'mean': mean(times),
        'stdev': stdev(times),
        'min': min(times),
        'max': max(times),
    }


def benchmark_context_detection():
    """Benchmark the context detection overhead."""
    manager = PromptManager()

    # Create a test prompt
    prompt_data = {
        "id": "test_prompt",
        "template": {"content": "Hello {{name}}!"},
    }

    print("=" * 60)
    print("Context Detection Overhead Benchmark")
    print("=" * 60)

    # Benchmark: Sync get_stats() (minimal overhead)
    def sync_get_stats():
        manager._registry.get_stats()

    sync_result = measure_operation(sync_get_stats, iterations=10000)
    print(f"\nSync get_stats() (10,000 iterations):")
    print(f"  Mean: {sync_result['mean']:.6f} ms")
    print(f"  Stdev: {sync_result['stdev']:.6f} ms")
    print(f"  Min: {sync_result['min']:.6f} ms")
    print(f"  Max: {sync_result['max']:.6f} ms")

    # Benchmark: Async get_stats()
    async def async_get_stats():
        await manager._registry._get_async("test")

    # Run in async context
    async def run_async_benchmark():
        return await measure_async_operation(async_get_stats, iterations=10000)

    async_result = asyncio.run(run_async_benchmark())
    print(f"\nAsync get_stats() (10,000 iterations):")
    print(f"  Mean: {async_result['mean']:.6f} ms")
    print(f"  Stdev: {async_result['stdev']:.6f} ms")
    print(f"  Min: {async_result['min']:.6f} ms")
    print(f"  Max: {async_result['max']:.6f} ms")

    # Calculate overhead
    overhead = ((async_result['mean'] - sync_result['mean']) / sync_result['mean']) * 100
    print(f"\nContext Detection Overhead: {overhead:.2f}%")
    print(f"Absolute Difference: {async_result['mean'] - sync_result['mean']:.6f} ms")

    # Performance verdict
    if overhead < 5:
        print("\n✅ PASS: Overhead is below 5% threshold")
    else:
        print(f"\n⚠️  WARNING: Overhead is {overhead:.2f}%, exceeds 5% threshold")

    return {
        'sync': sync_result,
        'async': async_result,
        'overhead_percent': overhead,
    }


if __name__ == "__main__":
    results = benchmark_context_detection()
    print("\n" + "=" * 60)
    print("Benchmark Complete")
    print("=" * 60)
