"""
Prompt registry for managing prompts in memory with persistence.

Provides CRUD operations, filtering, and integration with storage backends.
"""

from __future__ import annotations

from typing import Any, List as ListType

import structlog

from prompt_manager.core.models import Prompt, PromptFormat, PromptStatus
from prompt_manager.core.protocols import ObserverProtocol, StorageBackendProtocol
from prompt_manager.exceptions import PromptNotFoundError, PromptValidationError

logger = structlog.get_logger(__name__)


class PromptRegistry:
    """
    In-memory registry for prompts with storage backend integration.

    Provides fast access to prompts while delegating persistence to storage backends.
    """

    def __init__(
        self,
        storage: StorageBackendProtocol | None = None,
        observers: list[ObserverProtocol] | None = None,
    ) -> None:
        """
        Initialize the registry.

        Args:
            storage: Optional storage backend for persistence
            observers: Optional list of observers for lifecycle events
        """
        self._prompts: dict[str, dict[str, Prompt]] = {}  # id -> {version -> Prompt}
        self._storage = storage
        self._observers = observers or []
        self._logger = logger.bind(component="registry")

    def register(self, prompt: Prompt, *, persist: bool = True) -> None:
        """
        Register a prompt in the registry.

        Args:
            prompt: Prompt to register
            persist: Whether to persist to storage backend

        Raises:
            PromptValidationError: If prompt validation fails
        """
        self._logger.info("registering_prompt", prompt_id=prompt.id, version=prompt.version)

        # Validate prompt
        try:
            # Pydantic validates on construction, but we can do additional checks
            if not prompt.id:
                msg = "Prompt ID cannot be empty"
                raise PromptValidationError(msg)
        except Exception as e:
            msg = f"Prompt validation failed: {e}"
            raise PromptValidationError(msg) from e

        # Initialize ID dict if needed
        if prompt.id not in self._prompts:
            self._prompts[prompt.id] = {}

        # Store prompt
        self._prompts[prompt.id][prompt.version] = prompt

        # Persist to storage if requested
        if persist and self._storage:
            self._storage.save(prompt)

        # Notify observers
        for observer in self._observers:
            observer.on_prompt_registered(prompt)

        self._logger.info(
            "prompt_registered",
            prompt_id=prompt.id,
            version=prompt.version,
            persisted=persist and self._storage is not None,
        )

    def get(self, prompt_id: str, version: str | None = None) -> Prompt:
        """
        Get a prompt by ID and optional version.

        Args:
            prompt_id: Prompt identifier
            version: Optional specific version (gets latest if None)

        Returns:
            The requested prompt

        Raises:
            PromptNotFoundError: If prompt not found
        """
        self._logger.debug("getting_prompt", prompt_id=prompt_id, version=version)

        if prompt_id not in self._prompts:
            raise PromptNotFoundError(prompt_id, version)

        versions = self._prompts[prompt_id]

        if version:
            if version not in versions:
                raise PromptNotFoundError(prompt_id, version)
            return versions[version]

        # Get latest version
        if not versions:
            raise PromptNotFoundError(prompt_id, version)

        # Sort versions semantically and get the latest
        sorted_versions = sorted(
            versions.keys(),
            key=lambda v: tuple(map(int, v.split("."))),
            reverse=True,
        )
        return versions[sorted_versions[0]]

    def update(self, prompt: Prompt, *, persist: bool = True) -> None:
        """
        Update an existing prompt.

        Args:
            prompt: Updated prompt
            persist: Whether to persist to storage

        Raises:
            PromptNotFoundError: If prompt doesn't exist
        """
        self._logger.info("updating_prompt", prompt_id=prompt.id, version=prompt.version)

        if prompt.id not in self._prompts:
            raise PromptNotFoundError(prompt.id)

        if prompt.version not in self._prompts[prompt.id]:
            raise PromptNotFoundError(prompt.id, prompt.version)

        # Update prompt
        self._prompts[prompt.id][prompt.version] = prompt

        # Persist to storage
        if persist and self._storage:
            self._storage.save(prompt)

        # Notify observers
        for observer in self._observers:
            observer.on_prompt_updated(prompt)

        self._logger.info("prompt_updated", prompt_id=prompt.id, version=prompt.version)

    def delete(
        self, prompt_id: str, version: str | None = None, *, persist: bool = True
    ) -> None:
        """
        Delete a prompt or specific version.

        Args:
            prompt_id: Prompt identifier
            version: Optional specific version (deletes all if None)
            persist: Whether to persist deletion to storage

        Raises:
            PromptNotFoundError: If prompt not found
        """
        self._logger.info("deleting_prompt", prompt_id=prompt_id, version=version)

        if prompt_id not in self._prompts:
            raise PromptNotFoundError(prompt_id, version)

        if version:
            # Delete specific version
            if version not in self._prompts[prompt_id]:
                raise PromptNotFoundError(prompt_id, version)

            prompt = self._prompts[prompt_id][version]
            del self._prompts[prompt_id][version]

            # Remove ID entry if no versions left
            if not self._prompts[prompt_id]:
                del self._prompts[prompt_id]

            # Persist deletion
            if persist and self._storage:
                self._storage.delete(prompt_id, version)

            # Notify observers
            for observer in self._observers:
                observer.on_prompt_deleted(prompt)
        else:
            # Delete all versions
            prompts = list(self._prompts[prompt_id].values())
            del self._prompts[prompt_id]

            # Persist deletion
            if persist and self._storage:
                self._storage.delete(prompt_id)

            # Notify observers
            for observer in self._observers:
                for prompt in prompts:
                    observer.on_prompt_deleted(prompt)

        self._logger.info("prompt_deleted", prompt_id=prompt_id, version=version)

    def list(
        self,
        *,
        status: PromptStatus | None = None,
        tags: list[str] | None = None,
        category: str | None = None,
        format: PromptFormat | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Prompt]:
        """
        List prompts with optional filtering.

        Args:
            status: Filter by status
            tags: Filter by tags (prompts must have ALL tags)
            category: Filter by category
            format: Filter by format
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of matching prompts (latest versions)
        """
        self._logger.debug(
            "listing_prompts",
            status=status,
            tags=tags,
            category=category,
            format=format,
            limit=limit,
            offset=offset,
        )

        # Collect latest version of each prompt
        prompts = []
        for prompt_id, versions in self._prompts.items():
            if not versions:
                continue

            # Get latest version
            sorted_versions = sorted(
                versions.keys(),
                key=lambda v: tuple(map(int, v.split("."))),
                reverse=True,
            )
            latest = versions[sorted_versions[0]]

            # Apply filters
            if status and latest.status != status:
                continue

            if tags and not all(tag in latest.metadata.tags for tag in tags):
                continue

            if category and latest.metadata.category != category:
                continue

            if format and latest.format != format:
                continue

            prompts.append(latest)

        # Sort by ID for consistency
        prompts.sort(key=lambda p: p.id)

        # Apply pagination
        start = offset
        end = offset + limit if limit else None
        return prompts[start:end]

    def get_versions(self, prompt_id: str) -> ListType[str]:
        """
        Get all versions for a prompt.

        Args:
            prompt_id: Prompt identifier

        Returns:
            List of version strings, sorted semantically (newest first)

        Raises:
            PromptNotFoundError: If prompt not found
        """
        if prompt_id not in self._prompts:
            raise PromptNotFoundError(prompt_id)

        versions = list(self._prompts[prompt_id].keys())
        versions.sort(key=lambda v: tuple(map(int, v.split("."))), reverse=True)
        return versions

    def exists(self, prompt_id: str, version: str | None = None) -> bool:
        """
        Check if a prompt exists.

        Args:
            prompt_id: Prompt identifier
            version: Optional specific version

        Returns:
            True if prompt exists, False otherwise
        """
        if prompt_id not in self._prompts:
            return False

        if version:
            return version in self._prompts[prompt_id]

        return len(self._prompts[prompt_id]) > 0

    def count(
        self,
        *,
        status: PromptStatus | None = None,
        tags: ListType[str] | None = None,
        category: str | None = None,
    ) -> int:
        """
        Count prompts matching criteria.

        Args:
            status: Filter by status
            tags: Filter by tags
            category: Filter by category

        Returns:
            Number of matching prompts
        """
        prompts = self.list(status=status, tags=tags, category=category)
        return len(prompts)

    def clear(self, *, persist: bool = True) -> None:
        """
        Clear all prompts from registry.

        Args:
            persist: Whether to clear storage backend as well

        Warning:
            This operation cannot be undone!
        """
        self._logger.warning("clearing_registry")

        prompt_count = len(self._prompts)
        self._prompts.clear()

        if persist and self._storage:
            # Note: This requires storage backend to implement clear()
            if hasattr(self._storage, "clear"):
                self._storage.clear()

        self._logger.warning("registry_cleared", prompt_count=prompt_count)

    def get_stats(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry statistics
        """
        total_prompts = len(self._prompts)
        total_versions = sum(len(versions) for versions in self._prompts.values())

        status_counts: dict[str, int] = {}
        for versions in self._prompts.values():
            if not versions:
                continue
            # Get latest version
            sorted_versions = sorted(
                versions.keys(),
                key=lambda v: tuple(map(int, v.split("."))),
                reverse=True,
            )
            latest = versions[sorted_versions[0]]
            status = latest.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_prompts": total_prompts,
            "total_versions": total_versions,
            "status_distribution": status_counts,
            "has_storage": self._storage is not None,
            "observer_count": len(self._observers),
        }

    def add_observer(self, observer: ObserverProtocol) -> None:
        """
        Add an observer for registry events.

        Args:
            observer: Observer to add
        """
        self._observers.append(observer)
        self._logger.info("observer_added", observer=type(observer).__name__)

    def remove_observer(self, observer: ObserverProtocol) -> None:
        """
        Remove an observer.

        Args:
            observer: Observer to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)
            self._logger.info("observer_removed", observer=type(observer).__name__)

    def load_from_storage(self) -> int:
        """
        Load all prompts from storage backend.

        Returns:
            Number of prompts loaded

        Raises:
            ValueError: If no storage backend configured
        """
        if not self._storage:
            msg = "No storage backend configured"
            raise ValueError(msg)

        self._logger.info("loading_from_storage")

        # Use list() method which returns all latest prompts
        prompts = self._storage.list()
        count = 0

        for prompt in prompts:
            self.register(prompt, persist=False)  # Already in storage
            count += 1

        self._logger.info("loaded_from_storage", count=count)
        return count
