"""Optional plugin registry."""

from __future__ import annotations

from imbizo.plugins.interfaces import PluginDescriptor


class PluginRegistry:
    """Registry of local optional extension providers."""

    def __init__(self) -> None:
        self._plugins: list[PluginDescriptor] = []

    def register(self, descriptor: PluginDescriptor) -> None:
        """Register a plugin descriptor."""

        self._plugins.append(descriptor)

    def list_plugins(self) -> list[PluginDescriptor]:
        """Return known plugins."""

        return list(self._plugins)

    def get_provider(self, provider_type: str, name: str) -> object | None:
        """Return an enabled provider by type and name."""

        for descriptor in self._plugins:
            if descriptor.provider_type == provider_type and descriptor.name == name and descriptor.enabled:
                return descriptor.provider
        return None
