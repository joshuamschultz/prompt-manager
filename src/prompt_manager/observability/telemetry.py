"""OpenTelemetry integration for distributed tracing."""

from collections.abc import Mapping
from typing import Any

import structlog
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from prompt_manager.core.models import PromptExecution, PromptVersion

logger = structlog.get_logger(__name__)


class OpenTelemetryObserver:
    """
    Observer that sends traces to OpenTelemetry.

    Implements ObserverProtocol for integration with PromptManager.
    Provides distributed tracing for prompt operations.
    """

    def __init__(self, tracer_name: str = "prompt-manager") -> None:
        """
        Initialize OpenTelemetry observer.

        Args:
            tracer_name: Name for the tracer
        """
        self._tracer = trace.get_tracer(tracer_name)
        self._logger = logger.bind(component="otel_observer")
        self._active_spans: dict[str, trace.Span] = {}

    def on_render_start(
        self,
        prompt_id: str,
        version: str,
        variables: Mapping[str, Any],
    ) -> None:
        """
        Start a trace span for rendering.

        Args:
            prompt_id: Prompt identifier
            version: Version being rendered
            variables: Variables for rendering
        """
        span = self._tracer.start_span(
            "prompt.render",
            attributes={
                "prompt.id": prompt_id,
                "prompt.version": version,
                "prompt.variable_count": len(variables),
                "prompt.variables": ",".join(variables.keys()),
            },
        )

        # Store span for completion
        key = f"{prompt_id}:{version}"
        self._active_spans[key] = span

        self._logger.debug(
            "trace_started",
            prompt_id=prompt_id,
            version=version,
            span_id=span.get_span_context().span_id,
        )

    def on_render_complete(
        self,
        prompt_id: str,
        version: str,
        execution: PromptExecution,
    ) -> None:
        """
        Complete the trace span with success.

        Args:
            prompt_id: Prompt identifier
            version: Version that was rendered
            execution: Execution record
        """
        key = f"{prompt_id}:{version}"
        span = self._active_spans.pop(key, None)

        if span:
            span.set_attributes(
                {
                    "prompt.execution_id": str(execution.execution_id),
                    "prompt.duration_ms": execution.duration_ms or 0,
                    "prompt.content_length": len(execution.rendered_content),
                }
            )
            span.set_status(Status(StatusCode.OK))
            span.end()

            self._logger.debug(
                "trace_completed",
                prompt_id=prompt_id,
                version=version,
                execution_id=str(execution.execution_id),
            )

    def on_render_error(
        self,
        prompt_id: str,
        version: str,
        error: Exception,
    ) -> None:
        """
        Complete the trace span with error.

        Args:
            prompt_id: Prompt identifier
            version: Version that failed
            error: Exception that occurred
        """
        key = f"{prompt_id}:{version}"
        span = self._active_spans.pop(key, None)

        if span:
            span.set_attributes(
                {
                    "error.type": type(error).__name__,
                    "error.message": str(error),
                }
            )
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.record_exception(error)
            span.end()

            self._logger.debug(
                "trace_error",
                prompt_id=prompt_id,
                version=version,
                error=str(error),
            )

    def on_version_created(self, version: PromptVersion) -> None:
        """
        Create a trace event for version creation.

        Args:
            version: New version
        """
        with self._tracer.start_as_current_span(
            "prompt.version.create",
            attributes={
                "prompt.id": version.prompt.id,
                "prompt.version": version.version,
                "prompt.parent_version": version.parent_version or "",
                "prompt.created_by": version.created_by or "",
            },
        ):
            self._logger.debug(
                "version_trace",
                prompt_id=version.prompt.id,
                version=version.version,
            )
