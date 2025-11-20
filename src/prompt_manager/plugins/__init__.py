"""Plugin system for LLM framework integrations."""

from prompt_manager.plugins.base import BasePlugin
from prompt_manager.plugins.registry import PluginRegistry

__all__ = ["BasePlugin", "PluginRegistry"]
