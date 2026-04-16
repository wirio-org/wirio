import asyncio
from collections.abc import Coroutine
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, Any, Final, Self, cast, final, override

from pydantic import TypeAdapter

from wirio._service_lookup._typed_type import TypedType
from wirio._utils._extra_dependencies import ExtraDependencies
from wirio.settings.environment_variables.environment_variables_settings_source import (
    EnvironmentVariablesSettingsSource,
)
from wirio.settings.json.json_settings_source import JsonSettingsSource
from wirio.settings.settings_builder import SettingsBuilder
from wirio.settings.settings_path import SettingsPath
from wirio.settings.settings_provider import SettingsProvider
from wirio.settings.settings_root import SettingsRoot
from wirio.settings.settings_section import SettingsSection
from wirio.settings.settings_source import SettingsSource
from wirio.wirio_undefined import WirioUndefined

if TYPE_CHECKING:
    from azure.core.credentials_async import AsyncTokenCredential

    from wirio.settings.aws_secrets_manager.aws_secrets_manager_settings_source import (
        AwsSecretsManagerSettingsSource,
    )
    from wirio.settings.azure_key_vault.azure_key_vault_settings_source import (
        AzureKeyVaultSettingsSource,
    )
else:
    AsyncTokenCredential = Any
    AwsSecretsManagerSettingsSource = Any
    AzureKeyVaultSettingsSource = Any


@final
class SettingsManager(SettingsBuilder, SettingsRoot):
    _content_root_path: Final[str]
    _sources: Final[list[SettingsSource]]
    _providers: Final[list[SettingsProvider]]

    def __init__(self, content_root_path: str | None = None) -> None:
        """Initialize the settings manager.

        Args:
            content_root_path: An optional path to be used as the root for resolving relative paths in settings sources. If not provided, the current working directory will be used as the content root path.

        """
        self._content_root_path = self._get_content_root_path(content_root_path)
        self._sources = []
        self._providers = []

    @property
    def sources(self) -> list[SettingsSource]:
        return self._sources

    @property
    @override
    def providers(self) -> list[SettingsProvider]:
        return self._providers

    def add(self, source: SettingsSource) -> None:
        self._add_source(source)

    def add_environment_variables(self) -> Self:
        """Add a settings provider that reads settings values from environment variables."""
        self.add(EnvironmentVariablesSettingsSource())
        return self

    def add_json_file(self, path: str, optional: bool = False) -> Self:
        """Add a settings provider that reads settings values from a JSON file."""
        final_path = (Path(self._content_root_path) / path).resolve()
        self.add(JsonSettingsSource(path=final_path, optional=optional))
        return self

    def add_azure_key_vault(
        self,
        url: str,
        credential: AsyncTokenCredential | None = None,
    ) -> Self:
        """Add a settings provider that reads settings values from Azure Key Vault."""
        ExtraDependencies.ensure_azure_key_vault_is_installed()
        global AzureKeyVaultSettingsSource  # noqa: PLW0603
        from wirio.settings.azure_key_vault.azure_key_vault_settings_source import (  # noqa: PLC0415
            AzureKeyVaultSettingsSource,
        )

        self.add(AzureKeyVaultSettingsSource(url=url, credential=credential))
        return self

    def add_aws_secrets_manager(
        self, secret_id: str, region: str | None = None, url: str | None = None
    ) -> Self:
        """Add a settings provider that reads settings values from AWS Secrets Manager."""
        ExtraDependencies.ensure_aws_secrets_manager_is_installed()
        global AwsSecretsManagerSettingsSource  # noqa: PLW0603
        from wirio.settings.aws_secrets_manager.aws_secrets_manager_settings_source import (  # noqa: PLC0415
            AwsSecretsManagerSettingsSource,
        )

        self.add(
            AwsSecretsManagerSettingsSource(secret_id=secret_id, region=region, url=url)
        )
        return self

    def _add_source(self, source: SettingsSource) -> None:
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

    @override
    def get_required_value[TField = str](
        self,
        key: str,
        value_type: type[TField] | type[str] = str,
    ) -> TField:
        """Get a setting value by its key or raise an error if the key is not found or the value is `None`. Optionally, validate the setting value against the specified type."""
        value = self._try_get_setting(key)

        if isinstance(value, WirioUndefined):
            error_message = f"Missing setting value for key '{key}'"
            raise KeyError(error_message)

        if value is None:
            error_message = f"Setting value for key '{key}' is None"
            raise ValueError(error_message)

        raw_value: object = value
        typed_value_type = TypedType.from_type(value_type)

        if value == "" and typed_value_type.is_sequence:
            raw_value = []

        return cast("TField", TypeAdapter(value_type).validate_python(raw_value))

    @override
    def get_value[TField = str](
        self,
        key: str,
        value_type: type[TField] | type[str] = str,
    ) -> TField | None:
        value = self._try_get_setting(key)

        if isinstance(value, WirioUndefined):
            return None

        if value is None:
            return None

        raw_value: object = value
        typed_value_type = TypedType.from_type(value_type)

        if value == "" and typed_value_type.is_sequence:
            raw_value = []

        return cast("TField", TypeAdapter(value_type).validate_python(raw_value))

    @override
    def get_section(self, key: str) -> SettingsSection:
        """Get a settings section for the specified key. A settings section represents a subsection of the settings values that share a common key prefix."""
        if not self._is_section_key(key):
            error_message = f"Setting key '{key}' is not a section"
            raise KeyError(error_message)

        return SettingsSection(self, key)

    @override
    def get_children(self, key: str | None = None) -> list[SettingsSection]:
        path = key
        child_keys: list[str] = []

        for provider in reversed(self.providers):
            for item_key in provider.data:
                candidate = ""

                if path is None:
                    candidate = item_key
                else:
                    prefix = f"{path}{SettingsPath.KEY_DELIMITER}"

                    if not item_key.startswith(prefix):
                        continue

                    candidate = item_key[len(prefix) :]

                if len(candidate) == 0:
                    continue

                child_key = candidate.split(SettingsPath.KEY_DELIMITER, 1)[0]

                if len(child_key) == 0:
                    continue

                if child_key not in child_keys:
                    child_keys.append(child_key)

        children: list[SettingsSection] = []

        for child_key in child_keys:
            if path is None:
                child_path = child_key
            else:
                child_path = f"{path}{SettingsPath.KEY_DELIMITER}{child_key}"

            children.append(SettingsSection(self, child_path))

        return children

    def _is_section_key(self, key: str) -> bool:
        children = self.get_children(key)

        if len(children) == 0:
            return False

        return any(not child.key.isdigit() for child in children)

    def _get_content_root_path(self, content_root_path: str | None = None) -> str:
        if content_root_path is not None:
            return content_root_path

        return str(Path.cwd().expanduser().resolve())
