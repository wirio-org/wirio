import asyncio
from collections.abc import Coroutine
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, Any, final, overload, override

from pydantic import BaseModel, TypeAdapter

from wirio._utils._extra_dependencies import ExtraDependencies
from wirio.configuration.configuration_builder import ConfigurationBuilder
from wirio.configuration.configuration_provider import ConfigurationProvider
from wirio.configuration.configuration_root import ConfigurationRoot
from wirio.configuration.configuration_section import ConfigurationSection
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
class ConfigurationManager(ConfigurationBuilder, ConfigurationRoot):
    _sources: list[ConfigurationSource]
    _providers: list[ConfigurationProvider]

    def __init__(self, content_root_path: str) -> None:
        self._content_root_path = content_root_path
        self._sources = []
        self._providers = []

    @property
    def sources(self) -> list[ConfigurationSource]:
        return self._sources

    @property
    @override
    def providers(self) -> list[ConfigurationProvider]:
        return self._providers

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

    @overload
    def get_required_value(self, key: str) -> str: ...

    @overload
    def get_required_value[TField](
        self, key: str, value_type: type[TField]
    ) -> TField: ...

    def get_required_value[TField](
        self,
        key: str,
        value_type: type[TField] | WirioUndefined = WirioUndefined.INSTANCE,
    ) -> str | TField:
        """Get a configuration value by its key or raise an error if the key is not found or the value is `None`. Optionally, validate the configuration value against the specified type."""
        value = self._try_get_configuration(key)

        if isinstance(value, WirioUndefined):
            error_message = f"Missing configuration value for key '{key}'"
            raise KeyError(error_message)

        if value is None:
            error_message = f"Configuration value for key '{key}' is None"
            raise ValueError(error_message)

        if isinstance(value_type, WirioUndefined):
            return value

        return TypeAdapter(value_type).validate_python(value)

    @overload
    def get_value(self, key: str) -> str | None: ...

    @overload
    def get_value[TField](
        self, key: str, value_type: type[TField]
    ) -> TField | None: ...

    @override
    def get_value[TField](
        self, key: str, value_type: type[TField] | None = None
    ) -> str | None | TField:
        """Get a configuration value by its key. Optionally, validate the configuration value against the specified type."""
        value = self._try_get_configuration(key)

        if isinstance(value, WirioUndefined):
            return None

        if value_type is None:
            return value

        if value is None:
            return None

        return TypeAdapter(value_type).validate_python(value)

    def get_model[TModel: BaseModel](self, model_type: type[TModel]) -> TModel:
        """Get a configuration model of the specified type. The configuration values will be mapped to the model fields by their names."""
        values: dict[str, Any] = {}

        for field_name, field_info in model_type.model_fields.items():
            value = self._try_get_configuration(field_name)

            if isinstance(value, WirioUndefined):
                array_values = self._try_get_array_configuration(field_name)

                if len(array_values) > 0:
                    values[field_name] = array_values
                    continue

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

        return model_type.model_validate(values)

    def _try_get_array_configuration(self, key: str) -> list[str | None]:
        index = 0
        values: list[str | None] = []

        while True:
            indexed_key = f"{key}:{index}"
            value = self._try_get_configuration(indexed_key)

            if isinstance(value, WirioUndefined):
                break

            values.append(value)
            index += 1

        return values

    def get_section(self, key: str) -> ConfigurationSection:
        """Get a configuration section for the specified key. A configuration section represents a subsection of the configuration values that share a common key prefix."""
        return ConfigurationSection(self, key)
