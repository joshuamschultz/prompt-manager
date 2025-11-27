"""Plugin registry for managing and discovering plugins."""

from __future__ import annotations

import importlib
import sys
from typing import Any, List as ListType, cast

import structlog

from prompt_manager.core.protocols import PluginProtocol
from prompt_manager.exceptions import PluginLoadError, PluginNotFoundError

logger = structlog.get_logger(__name__)


class PluginRegistry:
    """
    Registry for managing plugins with auto-discovery.

    Supports loading plugins from entry points and dynamic registration.
    """

    def __init__(self) -> None:
        """Initialize plugin registry."""
        self._plugins: dict[str, PluginProtocol] = {}
        self._logger = logger.bind(component="plugin_registry")

    def register(self, plugin: PluginProtocol) -> None:
        """
        Register a plugin.

        Args:
            plugin: Plugin to register

        Raises:
            PluginError: If plugin with same name already registered
        """
        if plugin.name in self._plugins:
            self._logger.warning(
                "plugin_already_registered",
                plugin=plugin.name,
                action="replacing",
            )

        self._plugins[plugin.name] = plugin
        self._logger.info("plugin_registered", plugin=plugin.name, version=plugin.version)

    def unregister(self, plugin_name: str) -> None:
        """
        Unregister a plugin.

        Args:
            plugin_name: Name of plugin to unregister

        Raises:
            PluginNotFoundError: If plugin not found
        """
        if plugin_name not in self._plugins:
            raise PluginNotFoundError(plugin_name)

        del self._plugins[plugin_name]
        self._logger.info("plugin_unregistered", plugin=plugin_name)

    def get(self, plugin_name: str) -> PluginProtocol:
        """
        Get a plugin by name.

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin instance

        Raises:
            PluginNotFoundError: If plugin not found
        """
        if plugin_name not in self._plugins:
            raise PluginNotFoundError(plugin_name)

        return self._plugins[plugin_name]

    def list(self) -> list[str]:
        """
        List all registered plugins.

        Returns:
            List of plugin names
        """
        return list(self._plugins.keys())

    def has(self, plugin_name: str) -> bool:
        """
        Check if plugin is registered.

        Args:
            plugin_name: Plugin name

        Returns:
            True if registered
        """
        return plugin_name in self._plugins

    def load_from_module(
        self,
        module_path: str,
        class_name: str,
        config: dict[str, Any] | None = None,
    ) -> PluginProtocol:
        """
        Load and register plugin from module.

        Args:
            module_path: Python module path (e.g., "prompt_manager.plugins.openai")
            class_name: Plugin class name
            config: Optional configuration for initialization

        Returns:
            Loaded and initialized plugin

        Raises:
            PluginLoadError: If loading fails
        """
        self._logger.info(
            "loading_plugin_from_module",
            module=module_path,
            class_name=class_name,
        )

        try:
            # Import module
            module = importlib.import_module(module_path)

            # Get plugin class
            plugin_class = getattr(module, class_name)

            # Instantiate plugin
            plugin = plugin_class()

            # Initialize if config provided
            if config:
                plugin.initialize(config)

            # Register
            self.register(plugin)

            return cast(PluginProtocol, plugin)

        except Exception as e:
            msg = f"Failed to load plugin from {module_path}.{class_name}: {e}"
            raise PluginLoadError(msg) from e

    def discover_entry_points(self, group: str = "prompt_manager.plugins") -> ListType[str]:
        """
        Discover plugins from setuptools entry points.

        Args:
            group: Entry point group name

        Returns:
            List of discovered plugin names
        """
        self._logger.info("discovering_plugins", group=group)

        discovered = []

        # Try to import entry_points (Python 3.10+)
        try:
            if sys.version_info >= (3, 10):
                from importlib.metadata import entry_points

                eps = entry_points(group=group)
            else:
                from pkg_resources import iter_entry_points

                eps = iter_entry_points(group)

            for ep in eps:
                try:
                    plugin_class = ep.load()
                    plugin = plugin_class()
                    self.register(plugin)
                    discovered.append(plugin.name)

                    self._logger.info(
                        "plugin_discovered",
                        plugin=plugin.name,
                        entry_point=ep.name,
                    )

                except Exception as e:
                    self._logger.error(
                        "failed_to_load_entry_point",
                        entry_point=ep.name,
                        error=str(e),
                    )
                    continue

        except Exception as e:
            self._logger.warning(
                "entry_point_discovery_failed",
                error=str(e),
            )

        return discovered

    def shutdown_all(self) -> None:
        """Shutdown all registered plugins."""
        self._logger.info("shutting_down_all_plugins")

        for name, plugin in self._plugins.items():
            try:
                plugin.shutdown()
                self._logger.info("plugin_shutdown", plugin=name)
            except Exception as e:
                self._logger.error(
                    "plugin_shutdown_failed",
                    plugin=name,
                    error=str(e),
                )

    def get_stats(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_plugins": len(self._plugins),
            "plugins": [
                {"name": p.name, "version": p.version} for p in self._plugins.values()
            ],
        }
