"""Metrics collection for prompt operations."""

from collections import defaultdict
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """
    Metrics collector for prompt operations.

    Implements MetricsCollectorProtocol for integration with PromptManager.
    Tracks renders, cache hits/misses, and performance metrics.
    """

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._render_counts: dict[str, int] = defaultdict(int)
        self._render_errors: dict[str, int] = defaultdict(int)
        self._render_durations: dict[str, list[float]] = defaultdict(list)
        self._cache_hits: dict[str, int] = defaultdict(int)
        self._cache_misses: dict[str, int] = defaultdict(int)
        self._first_render: datetime | None = None
        self._last_render: datetime | None = None
        self._logger = logger.bind(component="metrics_collector")

    def record_render(
        self,
        prompt_id: str,
        version: str,
        duration_ms: float,
        success: bool,
    ) -> None:
        """
        Record a render operation.

        Args:
            prompt_id: Prompt identifier
            version: Version rendered
            duration_ms: Duration in milliseconds
            success: Whether rendering succeeded
        """
        key = f"{prompt_id}:{version}"

        if success:
            self._render_counts[key] += 1
            self._render_durations[key].append(duration_ms)
        else:
            self._render_errors[key] += 1

        # Update timestamps
        now = datetime.utcnow()
        if not self._first_render:
            self._first_render = now
        self._last_render = now

        self._logger.debug(
            "render_recorded",
            prompt_id=prompt_id,
            version=version,
            duration_ms=duration_ms,
            success=success,
        )

    def record_cache_hit(self, prompt_id: str) -> None:
        """
        Record a cache hit.

        Args:
            prompt_id: Prompt identifier
        """
        self._cache_hits[prompt_id] += 1

    def record_cache_miss(self, prompt_id: str) -> None:
        """
        Record a cache miss.

        Args:
            prompt_id: Prompt identifier
        """
        self._cache_misses[prompt_id] += 1

    def get_metrics(
        self,
        *,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get collected metrics.

        Args:
            since: Only metrics after this time (not yet implemented)

        Returns:
            Metrics dictionary
        """
        # Calculate aggregate metrics
        total_renders = sum(self._render_counts.values())
        total_errors = sum(self._render_errors.values())
        total_cache_hits = sum(self._cache_hits.values())
        total_cache_misses = sum(self._cache_misses.values())

        # Calculate average durations
        all_durations = []
        for durations in self._render_durations.values():
            all_durations.extend(durations)

        avg_duration = sum(all_durations) / len(all_durations) if all_durations else 0
        min_duration = min(all_durations) if all_durations else 0
        max_duration = max(all_durations) if all_durations else 0

        # Calculate percentiles
        p50_duration = 0.0
        p95_duration = 0.0
        p99_duration = 0.0

        if all_durations:
            sorted_durations = sorted(all_durations)
            n = len(sorted_durations)
            p50_duration = sorted_durations[int(n * 0.5)]
            p95_duration = sorted_durations[int(n * 0.95)]
            p99_duration = sorted_durations[int(n * 0.99)]

        # Cache hit rate
        total_cache_requests = total_cache_hits + total_cache_misses
        cache_hit_rate = (
            total_cache_hits / total_cache_requests if total_cache_requests > 0 else 0
        )

        # Per-prompt metrics
        per_prompt_metrics = []
        all_prompts = set(
            list(self._render_counts.keys())
            + list(self._render_errors.keys())
            + list(self._cache_hits.keys())
            + list(self._cache_misses.keys())
        )

        for prompt_key in all_prompts:
            renders = self._render_counts.get(prompt_key, 0)
            errors = self._render_errors.get(prompt_key, 0)
            durations = self._render_durations.get(prompt_key, [])

            # Extract prompt_id from key
            prompt_id = prompt_key.split(":")[0]
            cache_hits = self._cache_hits.get(prompt_id, 0)
            cache_misses = self._cache_misses.get(prompt_id, 0)

            avg_dur = sum(durations) / len(durations) if durations else 0

            per_prompt_metrics.append(
                {
                    "prompt": prompt_key,
                    "renders": renders,
                    "errors": errors,
                    "cache_hits": cache_hits,
                    "cache_misses": cache_misses,
                    "avg_duration_ms": round(avg_dur, 2),
                }
            )

        return {
            "summary": {
                "total_renders": total_renders,
                "total_errors": total_errors,
                "total_cache_hits": total_cache_hits,
                "total_cache_misses": total_cache_misses,
                "cache_hit_rate": round(cache_hit_rate, 3),
                "first_render": self._first_render.isoformat() if self._first_render else None,
                "last_render": self._last_render.isoformat() if self._last_render else None,
            },
            "performance": {
                "avg_duration_ms": round(avg_duration, 2),
                "min_duration_ms": round(min_duration, 2),
                "max_duration_ms": round(max_duration, 2),
                "p50_duration_ms": round(p50_duration, 2),
                "p95_duration_ms": round(p95_duration, 2),
                "p99_duration_ms": round(p99_duration, 2),
            },
            "per_prompt": per_prompt_metrics,
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._render_counts.clear()
        self._render_errors.clear()
        self._render_durations.clear()
        self._cache_hits.clear()
        self._cache_misses.clear()
        self._first_render = None
        self._last_render = None
        self._logger.info("metrics_reset")
