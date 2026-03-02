import asyncio
from collections.abc import Coroutine
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, Any, final, overload

from pydantic import BaseModel

from wirio._utils._extra_dependencies import ExtraDependencies
from wirio.configuration.configuration_builder import ConfigurationBuilder
from wirio.configuration.configuration_provider import ConfigurationProvider
from wirio.configuration.configuration_source import ConfigurationSource
from wirio.configuration.environment_variables.environment_variables_configuration_source import (
    EnvironmentVariablesConfigurationSource,
)
from wirio.configuration.json.json_configuration_source import JsonConfigurationSource
from wirio.wirio_undefined import WirioUndefined

if TYPE_CHECKING:
    from azure.core.credentials_async import AsyncTokenCredential

    from wirio.configuration.azure_key_vault.azure_key_vault_configuration_source import (
        AzureKeyVaultConfigurationSource,
    )
else:
    AsyncTokenCredential = Any
    AzureKeyVaultConfigurationSource = Any


@final
class ConfigurationManager(ConfigurationBuilder):
    _sources: list[ConfigurationSource]
    _providers: list[ConfigurationProvider]

    def __init__(self, content_root_path: str) -> None:
        self._content_root_path = content_root_path
        self._sources = []
        self._providers = []

    @property
    def sources(self) -> list[ConfigurationSource]:
        return self._sources

    def add(self, source: ConfigurationSource) -> None:
        self._add_source(source)

    def add_environment_variables(self) -> None:
        """Add a configuration provider that reads configuration values from environment variables."""
        self.add(EnvironmentVariablesConfigurationSource())

    def add_json_file(self, path: str, optional: bool) -> None:
        """Add a configuration provider that reads configuration values from a JSON file."""
        final_path = (Path(self._content_root_path) / path).resolve()
        self.add(JsonConfigurationSource(path=final_path, optional=optional))

    def add_azure_key_vault(
        self,
        url: str,
        credential: AsyncTokenCredential | None = None,
    ) -> None:
        """Add a configuration provider that reads configuration values from Azure Key Vault."""
        ExtraDependencies.ensure_azure_key_vault_is_installed()
        global AzureKeyVaultConfigurationSource  # noqa: PLW0603
        from wirio.configuration.azure_key_vault.azure_key_vault_configuration_source import (  # noqa: PLC0415
            AzureKeyVaultConfigurationSource,
        )

        self.add(AzureKeyVaultConfigurationSource(url=url, credential=credential))

    def _add_source(self, source: ConfigurationSource) -> None:
        self._sources.append(source)
        provider = source.build(self)
        self._call_async(provider.load())
        self._providers.append(provider)

    def _call_async[T](self, coroutine: Coroutine[Any, Any, T]) -> None:
        def run_coroutine() -> None:
            asyncio.run(coroutine)

        try:
            event_loop = asyncio.get_running_loop()
            event_loop.run_until_complete(coroutine)
        except RuntimeError:
            thread = Thread(target=run_coroutine)
            thread.start()
            thread.join()

    def _try_get_configuration(self, key: str) -> str | None | WirioUndefined:
        for provider in reversed(self._providers):
            value = provider.try_get(key)

            if not isinstance(value, WirioUndefined):
                return value

        return WirioUndefined.INSTANCE

    @overload
    def __getitem__[T: BaseModel](self, key: str) -> str | None: ...

    @overload
    def __getitem__[T: BaseModel](self, key: type[T]) -> T: ...

    def __getitem__[T: BaseModel](self, key: str | type[T]) -> str | None | T:
        if isinstance(key, str):
            value = self._try_get_configuration(key)

            if isinstance(value, WirioUndefined):
                error_message = f"Missing configuration value for key '{key}'"
                raise KeyError(error_message)

            return value

        values: dict[str, str | None] = {}

        for field_name, field_info in key.model_fields.items():
            value = self._try_get_configuration(field_name)

            if isinstance(value, WirioUndefined):
                if not field_info.is_required():
                    values[field_name] = field_info.get_default(
                        call_default_factory=True
                    )
                else:
                    error_message = (
                        f"Missing configuration value for key '{field_name}'"
                    )
                    raise KeyError(error_message)
            else:
                values[field_name] = value

        return key.model_validate(values)
