from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, overload

from wirio.wirio_undefined import WirioUndefined

if TYPE_CHECKING:
    from wirio.configuration.configuration_provider import ConfigurationProvider


class ConfigurationRoot(ABC):
    """Represent the root node for a configuration."""

    @property
    @abstractmethod
    def providers(self) -> list["ConfigurationProvider"]: ...

    @overload
    @abstractmethod
    def get_value(self, key: str) -> str | None: ...

    @overload
    @abstractmethod
    def get_value[TField](
        self, key: str, value_type: type[TField]
    ) -> TField | None: ...

    @abstractmethod
    def get_value[TField](
        self, key: str, value_type: type[TField] | None = None
    ) -> str | None | TField: ...

    def _try_get_configuration(self, key: str) -> str | None | WirioUndefined:
        for provider in reversed(self.providers):
            value = provider.try_get(key)

            if not isinstance(value, WirioUndefined):
                return value

        return WirioUndefined.INSTANCE
