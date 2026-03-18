from typing import Final, final, override

from azure.core.credentials_async import AsyncTokenCredential

from wirio.settings.azure_key_vault.azure_key_vault_settings_provider import (
    AzureKeyVaultSettingsProvider,
)
from wirio.settings.settings_builder import SettingsBuilder
from wirio.settings.settings_provider import SettingsProvider
from wirio.settings.settings_source import SettingsSource


@final
class AzureKeyVaultSettingsSource(SettingsSource):
    _url: Final[str]
    _credential: Final[AsyncTokenCredential | None]

    def __init__(
        self,
        url: str,
        credential: AsyncTokenCredential | None = None,
    ) -> None:
        self._url = url
        self._credential = credential

    @override
    def build(self, builder: SettingsBuilder) -> SettingsProvider:
        return AzureKeyVaultSettingsProvider(url=self._url, credential=self._credential)
