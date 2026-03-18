from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from wirio.settings.settings_provider import SettingsProvider

if TYPE_CHECKING:
    from wirio.settings.settings_builder import SettingsBuilder


class SettingsSource(ABC):
    """Represent a source of key/values settings for an application."""

    @abstractmethod
    def build(self, builder: "SettingsBuilder") -> SettingsProvider: ...
