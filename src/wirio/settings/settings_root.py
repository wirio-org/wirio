from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from wirio.settings.settings import Settings
from wirio.wirio_undefined import WirioUndefined

if TYPE_CHECKING:
    from wirio.settings.settings_provider import SettingsProvider
    from wirio.settings.settings_section import SettingsSection


class SettingsRoot(Settings, ABC):
    """Represent the root node for settings."""

    @property
    @abstractmethod
    def providers(self) -> list["SettingsProvider"]: ...

    @abstractmethod
    def get_section(self, key: str) -> "SettingsSection": ...

    @abstractmethod
    def get_value[TField = str](
        self,
        key: str,
        value_type: type[TField] | type[str] = str,
    ) -> TField | None: ...

    def _try_get_setting(self, key: str) -> str | None | WirioUndefined:
        for provider in reversed(self.providers):
            value = provider.try_get(key)

            if not isinstance(value, WirioUndefined):
                return value

        return WirioUndefined.INSTANCE
