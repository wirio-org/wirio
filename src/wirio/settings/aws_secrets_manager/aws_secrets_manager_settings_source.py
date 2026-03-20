from typing import Final, final, override

from wirio.settings.aws_secrets_manager.aws_secrets_manager_settings_provider import (
    AwsSecretsManagerSettingsProvider,
)
from wirio.settings.settings_builder import SettingsBuilder
from wirio.settings.settings_provider import SettingsProvider
from wirio.settings.settings_source import SettingsSource


@final
class AwsSecretsManagerSettingsSource(SettingsSource):
    _secret_name: Final[str]
    _region: Final[str | None]
    _url: Final[str | None]

    def __init__(
        self, secret_name: str, region: str | None = None, url: str | None = None
    ) -> None:
        self._secret_name = secret_name
        self._region = region
        self._url = url

    @override
    def build(self, builder: SettingsBuilder) -> SettingsProvider:
        return AwsSecretsManagerSettingsProvider(
            secret_name=self._secret_name, region=self._region, url=self._url
        )
