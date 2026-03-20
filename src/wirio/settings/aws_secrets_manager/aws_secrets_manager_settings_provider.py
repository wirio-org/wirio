import json
from typing import Any, Final, cast, final, override

import boto3  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]

from wirio.settings.json.json_settings_file_parser import JsonSettingsFileParser
from wirio.settings.settings_provider import SettingsProvider


@final
class AwsSecretsManagerSettingsProvider(SettingsProvider):
    _secret_name: Final[str]
    _region: Final[str | None]
    _url: Final[str | None]

    def __init__(
        self, secret_name: str, region: str | None = None, url: str | None = None
    ) -> None:
        super().__init__()
        self._secret_name = secret_name
        self._region = region
        self._url = url

    @override
    async def load(self) -> None:
        secrets_manager_client = cast(
            "Any",
            boto3.client(  # pyright: ignore[reportUnknownMemberType]
                service_name="secretsmanager",
                region_name=self._region,
                endpoint_url=self._url,
            ),
        )
        secret = cast(
            "dict[str, Any]",
            secrets_manager_client.get_secret_value(SecretId=self._secret_name),
        )
        secret_value_str = cast("str", secret["SecretString"])
        secret_value_json = json.loads(secret_value_str)
        self._data = JsonSettingsFileParser().parse_json(
            cast("dict[str, Any]", secret_value_json)
        )
        await super().load()
