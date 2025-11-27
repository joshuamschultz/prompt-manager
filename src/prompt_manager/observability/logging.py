"""Structured logging observer for prompt operations."""

from collections.abc import Mapping
from typing import Any

import structlog

from prompt_manager.core.models import PromptExecution, PromptVersion

logger = structlog.get_logger(__name__)


class LoggingObserver:
    """
    Observer that logs prompt operations using structlog.

    Implements ObserverProtocol for integration with PromptManager.
    """

    def __init__(self, log_level: str = "INFO") -> None:
        """
        Initialize logging observer.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self._logger = logger.bind(component="logging_observer")
        self._log_level = log_level.upper()

    def on_render_start(
        self,
        prompt_id: str,
        version: str,
        variables: Mapping[str, Any],
    ) -> None:
        """
        Log when prompt rendering starts.

        Args:
            prompt_id: Prompt identifier
            version: Version being rendered
            variables: Variables for rendering
        """
        self._logger.info(
            "render_start",
            prompt_id=prompt_id,
            version=version,
            variable_count=len(variables),
            variables=list(variables.keys()),
        )

    def on_render_complete(
        self,
        prompt_id: str,
        version: str,
        execution: PromptExecution,
    ) -> None:
        """
        Log when prompt rendering completes.

        Args:
            prompt_id: Prompt identifier
            version: Version that was rendered
            execution: Execution record
        """
        self._logger.info(
            "render_complete",
            prompt_id=prompt_id,
            version=version,
            execution_id=str(execution.execution_id),
            duration_ms=execution.duration_ms,
            success=execution.success,
            content_length=len(execution.rendered_content),
        )

    def on_render_error(
        self,
        prompt_id: str,
        version: str,
        error: Exception,
    ) -> None:
        """
        Log when prompt rendering fails.

        Args:
            prompt_id: Prompt identifier
            version: Version that failed
            error: Exception that occurred
        """
        self._logger.error(
            "render_error",
            prompt_id=prompt_id,
            version=version,
            error_type=type(error).__name__,
            error_message=str(error),
        )

    def on_version_created(self, version: PromptVersion) -> None:
        """
        Log when a new version is created.

        Args:
            version: New version
        """
        self._logger.info(
            "version_created",
            prompt_id=version.prompt.id,
            version=version.version,
            parent_version=version.parent_version,
            created_by=version.created_by,
            has_changelog=bool(version.changelog),
        )
