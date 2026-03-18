from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wirio.settings.settings_source import SettingsSource


class SettingsBuilder(ABC):
    @property
    @abstractmethod
    def sources(self) -> list["SettingsSource"]: ...
