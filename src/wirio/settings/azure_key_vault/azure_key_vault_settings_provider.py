from typing import Final, final, override

from azure.core.credentials_async import AsyncTokenCredential
from azure.core.pipeline import PipelineRequest
from azure.core.pipeline.policies import UserAgentPolicy
from azure.core.pipeline.policies._universal import HTTPRequestType
from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient

from wirio.settings.settings_path import SettingsPath
from wirio.settings.settings_provider import SettingsProvider


class _NoUserAgentPolicy(UserAgentPolicy):
    """Agent to disable telemetry for Azure SDK clients."""

    def on_request(self, request: PipelineRequest[HTTPRequestType]) -> None:
        pass


@final
class AzureKeyVaultSettingsProvider(SettingsProvider):
    _url: Final[str]
    _credential: Final[AsyncTokenCredential]

    def __init__(
        self,
        url: str,
        credential: AsyncTokenCredential | None = None,
    ) -> None:
        super().__init__()
        self._url = url
        self._credential = (
            credential if credential is not None else DefaultAzureCredential()
        )

    @override
    async def load(self) -> None:
        async with (
            self._credential,
            SecretClient(
                vault_url=self._url,
                credential=self._credential,
                user_agent_policy=_NoUserAgentPolicy(),
            ) as secret_client,
        ):
            secret_names = await self.get_secret_names(secret_client)

            for secret_name in secret_names:
                secret = await secret_client.get_secret(secret_name)

                if secret.value is not None:
                    normalized_secret_name = self._normalize_key(secret_name)
                    self._data[normalized_secret_name] = secret.value

        await super().load()

    async def get_secret_names(self, secret_client: SecretClient) -> list[str]:
        return [
            secret.name
            async for secret in secret_client.list_properties_of_secrets()
            if secret.name is not None and secret.enabled
        ]

    def _normalize_key(self, key: str) -> str:
        return key.replace("--", SettingsPath.KEY_DELIMITER)
