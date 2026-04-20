import asyncio
import os
import re
from asyncio import AbstractEventLoop
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, final, override

import pytest
from pydantic import BaseModel, Field
from pytest_mock import MockerFixture

from wirio._utils._extra_dependencies import ExtraDependencies
from wirio.hosting._environment_variable import EnvironmentVariable
from wirio.settings.environment_variables.environment_variables_settings_provider import (
    EnvironmentVariablesSettingsProvider,
)
from wirio.settings.environment_variables.environment_variables_settings_source import (
    EnvironmentVariablesSettingsSource,
)
from wirio.settings.json.json_settings_provider import JsonSettingsProvider
from wirio.settings.json.json_settings_source import JsonSettingsSource
from wirio.settings.settings_builder import SettingsBuilder
from wirio.settings.settings_manager import SettingsManager
from wirio.settings.settings_provider import SettingsProvider
from wirio.settings.settings_source import SettingsSource

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

try:
    from azure.core.credentials_async import AsyncTokenCredential

    from wirio.settings.azure_key_vault.azure_key_vault_settings_source import (
        AzureKeyVaultSettingsSource,
    )
except ImportError:
    pass

try:  # noqa: SIM105
    from wirio.settings.aws_secrets_manager.aws_secrets_manager_settings_source import (
        AwsSecretsManagerSettingsSource,
    )
except ImportError:
    pass


@final
class _DictionarySettingsProvider(SettingsProvider):
    _values: dict[str, str | None]

    def __init__(self, values: dict[str, str | None]) -> None:
        super().__init__()
        self._values = values

    @override
    async def load(self) -> None:
        self._data = self._values
        await super().load()


@final
class _DictionarySettingsSource(SettingsSource):
    _values: dict[str, str | None]

    def __init__(self, values: dict[str, str | None]) -> None:
        self._values = values

    @override
    def build(self, builder: SettingsBuilder) -> SettingsProvider:
        return _DictionarySettingsProvider(self._values)


class _Settings(BaseModel):
    app_name: str
    port: str


class TestSettingsManager:
    def test_get_required_value(self) -> None:
        expected_setting_value = "wirio"
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource({"app_name": expected_setting_value})
        )

        setting_value = settings_manager.get_required_value("app_name")

        assert isinstance(setting_value, str)
        assert setting_value == expected_setting_value

    def test_get_required_value_specifying_type(self) -> None:
        expected_setting_value = 1
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource({"number": str(expected_setting_value)})
        )

        setting_value = settings_manager.get_required_value("number", int)

        assert isinstance(setting_value, int)
        assert setting_value == expected_setting_value

    def test_fail_when_getting_missing_required_value(self) -> None:
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource({"app_name": "wirio"}))

        with pytest.raises(KeyError) as exception_info:
            settings_manager.get_required_value("port")

        assert exception_info.value.args[0] == "Missing setting value for key 'port'"

    def test_fail_when_getting_required_value_with_invalid_type(self) -> None:
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource({"number": "not-a-number"}))

        with pytest.raises(
            ValueError  # noqa: PT011
        ) as exception_info:
            settings_manager.get_required_value("number", int)

        assert "validation error" in str(exception_info.value)

    def test_fail_when_required_value_is_none(self) -> None:
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource({"app_name": None}))

        with pytest.raises(
            ValueError  # noqa: PT011
        ) as exception_info:
            settings_manager.get_required_value("app_name")

        assert str(exception_info.value) == "Setting value for key 'app_name' is None"

    def test_get_value(self) -> None:
        expected_setting_value = "wirio"
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource({"app_name": expected_setting_value})
        )

        setting_value = settings_manager.get_value("app_name")

        assert isinstance(setting_value, str)
        assert setting_value == expected_setting_value

    def test_get_none_value_when_getting_value_with_none_value(self) -> None:
        expected_setting_value = None
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource({"app_name": expected_setting_value})
        )

        setting_value = settings_manager.get_value("app_name")

        assert setting_value is None
        assert setting_value == expected_setting_value

    def test_get_none_value_when_getting_value_with_none_value_and_value_type_is_specified(
        self,
    ) -> None:
        expected_setting_value = None
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource({"app_name": expected_setting_value})
        )

        setting_value = settings_manager.get_value("app_name", int)

        assert setting_value is None
        assert setting_value == expected_setting_value

    def test_get_value_specifying_type(self) -> None:
        expected_setting_value = 1
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource({"number": str(expected_setting_value)})
        )

        setting_value = settings_manager.get_value("number", int)

        assert isinstance(setting_value, int)
        assert setting_value == expected_setting_value

    def test_get_none_when_getting_missing_value(self) -> None:
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource({"app_name": "wirio"}))

        setting_value = settings_manager.get_value("port")

        assert setting_value is None

    def test_fail_when_getting_value_with_invalid_type(self) -> None:
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource({"number": "not-a-number"}))

        with pytest.raises(
            ValueError  # noqa: PT011
        ) as exception_info:
            settings_manager.get_value("number", int)

        assert "validation error" in str(exception_info.value)

    def test_get_model_when_event_loop_is_not_running(self) -> None:
        class Settings(BaseModel):
            app_name: str
            port: int

        expected_app_name = "wirio"
        expected_port = 8080
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "app_name": expected_app_name,
                    "port": str(expected_port),
                }
            )
        )

        settings = settings_manager.get_model(Settings)

        assert isinstance(settings, Settings)
        assert settings.app_name == expected_app_name
        assert settings.port == expected_port

    async def test_add_source_when_event_loop_is_running(self) -> None:
        expected_app_name = "wirio"
        expected_port = "8080"
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {"app_name": expected_app_name, "port": expected_port}
            )
        )

        settings = settings_manager.get_model(_Settings)

        assert settings.app_name == expected_app_name
        assert settings.port == expected_port

    def test_add_source_when_event_loop_is_not_running(self) -> None:
        expected_app_name = "wirio"
        expected_port = "8080"
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {"app_name": expected_app_name, "port": expected_port}
            )
        )

        settings = settings_manager.get_model(_Settings)

        assert settings.app_name == expected_app_name
        assert settings.port == expected_port

    def test_override_values_with_last_source(self) -> None:
        expected_app_name = "wirio"
        expected_port = "9090"

        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource({"app_name": "wirio", "port": "8080"})
        )
        settings_manager.add(_DictionarySettingsSource({"port": expected_port}))

        settings = settings_manager.get_model(_Settings)

        assert settings.app_name == expected_app_name
        assert settings.port == expected_port

    def test_return_none_for_missing_optional_value_of_a_model(self) -> None:
        class Settings(BaseModel):
            app_name: str
            port: int | None = None

        expected_app_name = "wirio"
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource({"app_name": expected_app_name}))

        settings = settings_manager.get_model(Settings)

        assert settings.app_name == expected_app_name
        assert settings.port is None

    def test_fail_when_required_value_of_a_model_is_missing(self) -> None:
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource({"app_name": "wirio"}))

        with pytest.raises(KeyError) as exception_info:
            settings_manager.get_model(_Settings)

        assert exception_info.value.args[0] == "Missing setting value for key 'port'"

    def test_convert_source_names_to_snake_case(self) -> None:
        expected_app_name = "wirio"
        expected_port = "8080"
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {"APP_NAME": expected_app_name, "PORT": expected_port}
            )
        )

        settings = settings_manager.get_model(_Settings)

        assert settings.app_name == expected_app_name
        assert settings.port == expected_port

    def test_return_added_sources(self) -> None:
        expected_sources = 2

        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        source1 = _DictionarySettingsSource({"app_name": "wirio"})
        source2 = _DictionarySettingsSource({"port": "8080"})
        settings_manager.add(source1)
        settings_manager.add(source2)

        sources = settings_manager.sources

        assert len(sources) == expected_sources
        assert sources[0] is source1
        assert sources[1] is source2

    @pytest.mark.skipif(
        not ExtraDependencies.is_azure_key_vault_installed(),
        reason=ExtraDependencies.AZURE_KEY_VAULT_NOT_INSTALLED_ERROR_MESSAGE,
    )
    def test_add_azure_key_vault(self, mocker: MockerFixture) -> None:
        expected_vault_url = "https://example.vault.azure.net"
        token_credential_mock = mocker.create_autospec(
            AsyncTokenCredential,
            instance=True,
        )
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        add_patch = mocker.patch.object(
            settings_manager,
            settings_manager.add.__name__,
            autospec=True,
        )

        settings_manager.add_azure_key_vault(
            url=expected_vault_url,
            credential=token_credential_mock,
        )

        add_patch.assert_called_once()
        source = add_patch.call_args.args[0]
        assert isinstance(source, AzureKeyVaultSettingsSource)

    @pytest.mark.skipif(
        not ExtraDependencies.is_aws_secrets_manager_installed(),
        reason=ExtraDependencies.AWS_SECRETS_MANAGER_NOT_INSTALLED_ERROR_MESSAGE,
    )
    def test_add_aws_secrets_manager(self, mocker: MockerFixture) -> None:
        expected_secret_name = "dev/TestApp"  # noqa: S105
        expected_region = "eu-west-1"
        expected_url = "https://secretsmanager.eu-west-1.amazonaws.com"
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        add_patch = mocker.patch.object(
            settings_manager,
            settings_manager.add.__name__,
            autospec=True,
        )

        settings_manager.add_aws_secrets_manager(
            secret_id=expected_secret_name,
            region=expected_region,
            url=expected_url,
        )

        add_patch.assert_called_once()
        source = add_patch.call_args.args[0]
        assert isinstance(source, AwsSecretsManagerSettingsSource)

    def test_use_default_factory_for_missing_optional_value_of_a_model(self) -> None:
        class Settings(BaseModel):
            app_name: str
            api_url: str = Field(default_factory=lambda: "https://localhost")

        expected_app_name = "wirio"
        expected_api_url = "https://localhost"
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource({"app_name": expected_app_name}))

        settings = settings_manager.get_model(Settings)

        assert settings.app_name == expected_app_name
        assert settings.api_url == expected_api_url

    @pytest.mark.parametrize(
        argnames=("section_key", "expected_path"),
        argvalues=[
            ("logging:log_level", "logging:log_level"),
            ("logging", "logging"),
        ],
    )
    def test_get_section(self, section_key: str, expected_path: str) -> None:
        expected_database_host = "localhost"
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {"logging:log_level:default": expected_database_host}
            )
        )

        section = settings_manager.get_section(section_key)

        assert section.path == expected_path

    def test_fail_when_getting_value_as_section(self) -> None:
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource({"logging:log_level:default": "INFO"})
        )

        with pytest.raises(
            KeyError,
            match=re.escape("Setting key 'logging:log_level:default' is not a section"),
        ):
            settings_manager.get_section("logging:log_level:default")

    def test_fail_when_getting_sequence_as_section(self) -> None:
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource({"node:0": "first", "node:1": "second"})
        )

        with pytest.raises(
            KeyError, match=re.escape("Setting key 'node' is not a section")
        ):
            settings_manager.get_section("node")

    def test_get_section_when_at_least_one_key_is_section(self) -> None:
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "node:0": "first",
                    "node:1": "second",
                    "node:description": "a node",
                }
            )
        )

        settings_manager.get_section("node")

    def test_get_model_from_settings(self) -> None:
        class ServiceSettings(BaseModel):
            name: str
            port: int

        class LogLevelSettings(BaseModel):
            default: str

        class LoggingSettings(BaseModel):
            log_level: LogLevelSettings

        class Settings(BaseModel):
            app_name: str
            is_enabled: bool
            port: int
            found_port: int | None = None
            not_found_port: int | None
            found_port_with_none_value: int | None = None
            not_found_port_with_default_factory_value: int | None = Field(
                default_factory=lambda: 9000
            )
            service: ServiceSettings
            not_found_service: ServiceSettings | None = None
            logging: LoggingSettings
            int_list: list[int]
            found_service_list: list[ServiceSettings]
            not_found_service_list: list[ServiceSettings] | None

        expected_app_name = "wirio"
        expected_is_enabled = True
        expected_port = 8080
        expected_found_port = 8080
        expected_not_found_port: int | None = None
        expected_found_port_with_none_value: int | None = None
        expected_not_found_port_with_default_factory_value = 9000
        expected_service_name_1 = "my_service_1"
        expected_service_port_1 = 8081
        expected_service_name_2 = "my_service_2"
        expected_service_port_2 = 8082
        expected_log_level_default = "WARNING"
        expected_int_list = [1, 2, 3]
        expected_not_found_service_list = None
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "app_name": expected_app_name,
                    "is_enabled": str(expected_is_enabled),
                    "port": str(expected_port),
                    "found_port": str(expected_found_port),
                    "found_port_with_none_value": None,
                    "service:name": expected_service_name_1,
                    "service:port": str(expected_service_port_1),
                    "logging:log_level:default": expected_log_level_default,
                    "int_list:0": str(expected_int_list[0]),
                    "int_list:1": str(expected_int_list[1]),
                    "int_list:2": str(expected_int_list[2]),
                    "found_service_list:0:name": expected_service_name_1,
                    "found_service_list:0:port": str(expected_service_port_1),
                    "found_service_list:1:name": expected_service_name_2,
                    "found_service_list:1:port": str(expected_service_port_2),
                }
            )
        )

        settings = settings_manager.get_model(Settings)

        assert isinstance(settings, Settings)
        assert settings.model_dump() == {
            "app_name": expected_app_name,
            "is_enabled": expected_is_enabled,
            "port": expected_port,
            "found_port": expected_found_port,
            "not_found_port": expected_not_found_port,
            "found_port_with_none_value": expected_found_port_with_none_value,
            "not_found_port_with_default_factory_value": expected_not_found_port_with_default_factory_value,
            "service": {
                "name": expected_service_name_1,
                "port": expected_service_port_1,
            },
            "not_found_service": None,
            "logging": {
                "log_level": {
                    "default": expected_log_level_default,
                }
            },
            "int_list": expected_int_list,
            "found_service_list": [
                {
                    "name": expected_service_name_1,
                    "port": expected_service_port_1,
                },
                {
                    "name": expected_service_name_2,
                    "port": expected_service_port_2,
                },
            ],
            "not_found_service_list": expected_not_found_service_list,
        }

    def test_bind_value_from_settings(self) -> None:
        expected_setting_value = 42
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource({"service:port": str(expected_setting_value)})
        )

        setting_value = settings_manager._bind_value(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            "service:port", int
        )

        assert setting_value == expected_setting_value

    def test_bind_required_value_from_settings(self) -> None:
        expected_setting_value = 42
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource({"service:port": str(expected_setting_value)})
        )

        setting_value = settings_manager._bind_required_value(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            "service:port", int
        )

        assert setting_value == expected_setting_value

    def test_fail_when_binding_missing_required_value_from_settings(self) -> None:
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource({"app_name": "wirio"}))

        with pytest.raises(KeyError) as exception_info:
            settings_manager._bind_required_value(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
                "service:port", int
            )

        assert (
            exception_info.value.args[0]
            == "Missing setting value for key 'service:port'"
        )

    def test_get_model_from_section(self) -> None:
        class ServiceSettings(BaseModel):
            port: int
            host: str

        expected_port = 8080
        expected_host = "localhost"
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "service:port": str(expected_port),
                    "service:host": expected_host,
                }
            )
        )

        settings = settings_manager.get_section("service").get_model(ServiceSettings)

        assert settings.port == expected_port
        assert settings.host == expected_host

    def test_bind_int_list_and_section_values_with_same_field_name_from_different_providers(
        self,
    ) -> None:
        class Settings(BaseModel):
            int_list: list[int]

        class IntListMetadata(BaseModel):
            description: str

        expected_int_list = [1, 2, 3]
        expected_description = "list metadata"

        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "int_list:0": str(expected_int_list[0]),
                    "int_list:1": str(expected_int_list[1]),
                    "int_list:2": str(expected_int_list[2]),
                }
            )
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "int_list:description": expected_description,
                }
            )
        )

        settings = settings_manager.get_model(Settings)
        int_list_metadata = settings_manager.get_section("int_list").get_model(
            IntListMetadata
        )

        assert settings.int_list == expected_int_list
        assert int_list_metadata.description == expected_description

    def test_bind_int_list_and_float_with_same_field_name_from_different_providers(
        self,
    ) -> None:
        class Settings(BaseModel):
            values: list[int]

        expected_int_list = [1, 2, 3]
        expected_float = 0.75

        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "values:0": str(expected_int_list[0]),
                    "values:1": str(expected_int_list[1]),
                    "values:2": str(expected_int_list[2]),
                }
            )
        )
        settings_manager.add(_DictionarySettingsSource({"values": str(expected_float)}))

        settings = settings_manager.get_model(Settings)
        float_value = settings_manager.get_required_value("values", float)

        assert settings.values == expected_int_list
        assert float_value == expected_float

    def test_get_children_from_root(
        self,
    ) -> None:
        expected_child_sections = 4
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "section_1:key": "value1",
                    "section_2:key": "value2",
                    "section_2": "value2",
                    "section_3:subsection:key": "value3",
                    "not_section": "value4",
                }
            )
        )

        child_sections = settings_manager.get_children()

        assert len(child_sections) == expected_child_sections
        child_keys = [section.key for section in child_sections]
        assert child_keys == ["section_1", "section_2", "section_3", "not_section"]

    def test_get_children_from_section(
        self,
    ) -> None:
        expected_child_sections = 4
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "parent_section:section_1:key": "value1",
                    "parent_section:section_2:key": "value2",
                    "parent_section:section_2": "value2",
                    "parent_section:section_3:subsection:key": "value3",
                    "parent_section:not_section": "value4",
                }
            )
        )

        child_sections = settings_manager.get_section("parent_section").get_children()

        assert len(child_sections) == expected_child_sections
        child_keys = [section.key for section in child_sections]
        assert child_keys == ["section_1", "section_2", "section_3", "not_section"]

    def test_bind_nested_list_item_using_default_when_field_is_missing(
        self,
    ) -> None:
        expected_retries = 3

        class Server(BaseModel):
            name: str
            retries: int = Field(expected_retries)

        class Settings(BaseModel):
            servers: list[Server]

        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource({"servers:0:name": "api"}))

        settings = settings_manager.get_model(Settings)

        assert len(settings.servers) == 1
        assert settings.servers[0].name == "api"
        assert settings.servers[0].retries == expected_retries

    def test_get_empty_string(self) -> None:
        key = "ports"
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource({key: ""}))

        value = settings_manager.get_value(key, str)
        required_value = settings_manager.get_required_value(key, str)

        assert value == ""
        assert required_value == ""

    def test_fail_when_getting_model_if_some_required_field_is_missing(self) -> None:
        class SubSettings(BaseModel):
            required_subfield_1: str
            required_subfield_2: int

        class RootSettings(BaseModel):
            required_field_1: str
            required_field_2: int
            subsettings: SubSettings | None = None

        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource({"required_field_1": "value"}))

        with pytest.raises(
            KeyError,
            match=re.escape("Missing setting value for key 'required_field_2'"),
        ):
            settings_manager.get_model(RootSettings)

        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "required_field_1": "value",
                    "required_field_2": "1",
                    "subsettings:required_subfield_1": "value",
                }
            )
        )

        with pytest.raises(
            KeyError,
            match=re.escape("Missing setting value for key 'required_subfield_2'"),
        ):
            settings_manager.get_model(RootSettings)

    def test_return_none_when_submodel_is_not_found(self) -> None:
        class ServiceSettings(BaseModel):
            name: str
            port: int

        class Settings(BaseModel):
            service_1: ServiceSettings | None = None
            service_2: ServiceSettings | None

        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource({}))

        settings = settings_manager.get_model(Settings)

        assert settings.service_1 is None
        assert settings.service_2 is None

    @pytest.mark.parametrize(
        argnames=("field_type", "setting_values", "expected_values"),
        argvalues=[
            (int, {"ports:0": "8080", "ports:1": "8081"}, [8080, 8081]),
            (str, {"ports:0": "8080", "ports:1": "8081"}, ["8080", "8081"]),
        ],
    )
    def test_get_sequence[TField](
        self,
        field_type: type[TField],
        setting_values: dict[str, str | None],
        expected_values: list[TField],
    ) -> None:
        class IntSettings(BaseModel):
            ports: list[int]

        class StringSettings(BaseModel):
            ports: list[str]

        model_class = IntSettings if field_type is int else StringSettings
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource(setting_values))

        settings = settings_manager.get_model(model_class)
        first_value = settings_manager.get_required_value("ports:0", field_type)
        missing_value = settings_manager.get_value("ports:2", field_type)

        assert settings.ports == expected_values
        assert isinstance(first_value, field_type)
        assert first_value == expected_values[0]
        assert missing_value is None

    @pytest.mark.parametrize(
        argnames="field_type",
        argvalues=[
            Sequence[int],
            Sequence[str],
            list[int],
            list[str],
        ],
        ids=["int_sequence", "str_sequence", "int_list", "str_list"],
    )
    def test_get_empty_sequence[TField](self, field_type: type[TField]) -> None:
        key = "ports"
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource({key: ""}))

        value = settings_manager.get_value(key, field_type)
        required_value = settings_manager.get_required_value(key, field_type)

        assert value == []
        assert required_value == []

    def test_get_model_sequence(self) -> None:
        expected_server_settings = 2
        expected_api_retries = 3
        expected_worker_retries = 5

        class Server(BaseModel):
            name: str
            retries: int

        class Settings(BaseModel):
            servers: list[Server]

        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "servers:0:name": "api",
                    "servers:0:retries": str(expected_api_retries),
                    "servers:1:name": "worker",
                    "servers:1:retries": str(expected_worker_retries),
                }
            )
        )

        settings = settings_manager.get_model(Settings)
        first_server_name = settings_manager.get_required_value("servers:0:name")
        second_server_retries = settings_manager.get_value("servers:1:retries", int)

        assert len(settings.servers) == expected_server_settings
        assert settings.servers[0].name == "api"
        assert settings.servers[0].retries == expected_api_retries
        assert settings.servers[1].name == "worker"
        assert settings.servers[1].retries == expected_worker_retries
        assert first_server_name == "api"
        assert second_server_retries == expected_worker_retries

    @pytest.mark.parametrize(
        argnames=("field_type", "setting_values", "expected_values"),
        argvalues=[
            (
                int,
                {"ports:http": "8080", "ports:https": "8443"},
                {"http": 8080, "https": 8443},
            ),
            (
                str,
                {"ports:http": "8080", "ports:https": "8443"},
                {"http": "8080", "https": "8443"},
            ),
        ],
    )
    def test_get_dictionary[TField](
        self,
        field_type: type[TField],
        setting_values: dict[str, str | None],
        expected_values: dict[str, TField],
    ) -> None:
        class IntSettings(BaseModel):
            ports: dict[str, int]

        class StringSettings(BaseModel):
            ports: dict[str, str]

        model_class = IntSettings if field_type is int else StringSettings
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(_DictionarySettingsSource(setting_values))

        settings = settings_manager.get_model(model_class)
        http_value = settings_manager.get_required_value("ports:http", field_type)
        missing_value = settings_manager.get_value("ports:ftp", field_type)

        assert isinstance(settings, BaseModel)
        assert isinstance(settings.ports, dict)
        assert settings.ports == expected_values
        assert http_value == expected_values["http"]
        assert missing_value is None

    def test_get_model_dictionary(self) -> None:
        expected_service_settings = 2
        expected_api_retries = 3
        expected_worker_retries = 5

        class Service(BaseModel):
            url: str
            retries: int

        class Settings(BaseModel):
            services: dict[str, Service]

        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "services:api:url": "https://api.example.com",
                    "services:api:retries": str(expected_api_retries),
                    "services:worker:url": "https://worker.example.com",
                    "services:worker:retries": str(expected_worker_retries),
                }
            )
        )

        settings = settings_manager.get_model(Settings)
        api_url = settings_manager.get_required_value("services:api:url")
        worker_retries = settings_manager.get_value("services:worker:retries", int)

        assert len(settings.services) == expected_service_settings
        assert settings.services["api"].url == "https://api.example.com"
        assert settings.services["api"].retries == expected_api_retries
        assert settings.services["worker"].url == "https://worker.example.com"
        assert settings.services["worker"].retries == expected_worker_retries
        assert api_url == "https://api.example.com"
        assert worker_retries == expected_worker_retries

    def test_return_sections_ignoring_values(self) -> None:
        expected_child_sections = 2
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "parent_section:": "value1",
                    "parent_section:section_1": "value2",
                    "parent_section:section_2:key": "value3",
                }
            )
        )

        child_sections = settings_manager.get_children("parent_section")

        assert len(child_sections) == expected_child_sections
        child_keys = [section.key for section in child_sections]
        assert child_keys == ["section_1", "section_2"]

    def test_ignore_malformed_child_key_when_getting_children(self) -> None:
        expected_child_sections = 2
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "parent_section::orphan": "ignored",
                    "parent_section:section_1": "value1",
                    "parent_section:section_2:key": "value2",
                }
            )
        )

        child_sections = settings_manager.get_children("parent_section")

        assert len(child_sections) == expected_child_sections
        child_keys = [section.key for section in child_sections]
        assert child_keys == ["section_1", "section_2"]

    def test_fail_when_getting_object_list_as_section(self) -> None:
        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "node:0:name": "first",
                    "node:1": "second",
                }
            )
        )

        with pytest.raises(
            KeyError, match=re.escape("Setting key 'node' is not a section")
        ):
            settings_manager.get_section("node")

    def test_get_current_working_directory_as_default_content_root_path(self) -> None:
        expected_content_root_path = str(Path.cwd())

        settings_manager = SettingsManager(add_default_providers=False)

        assert settings_manager._content_root_path == expected_content_root_path  # noqa: SLF001 # pyright: ignore[reportPrivateUsage]

    def test_add_default_providers_by_default(self, mocker: MockerFixture) -> None:
        add_defaults_patch = mocker.patch.object(
            SettingsManager,
            SettingsManager.add_defaults.__name__,
            autospec=True,
        )

        SettingsManager(content_root_path="")

        add_defaults_patch.assert_called_once()

    def test_not_add_default_providers_when_disabled(
        self, mocker: MockerFixture
    ) -> None:
        add_defaults_patch = mocker.patch.object(
            SettingsManager,
            SettingsManager.add_defaults.__name__,
            autospec=True,
        )

        SettingsManager(content_root_path="", add_default_providers=False)

        add_defaults_patch.assert_not_called()

    def test_add_defaults_in_expected_order_and_using_current_environment_name(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        expected_environment_name = "development"
        expected_json_file_name = f"settings.{expected_environment_name}.json"
        expected_sources_count = 3
        expected_providers_count = 3

        mocker.patch.dict(
            os.environ,
            {EnvironmentVariable.WIRIO_ENVIRONMENT.value: expected_environment_name},
        )

        settings_manager = SettingsManager(content_root_path=str(tmp_path))

        assert len(settings_manager.sources) == expected_sources_count
        assert len(settings_manager.providers) == expected_providers_count
        assert isinstance(settings_manager.sources[0], JsonSettingsSource)
        assert isinstance(settings_manager.providers[0], JsonSettingsProvider)
        assert isinstance(settings_manager.sources[1], JsonSettingsSource)
        assert isinstance(settings_manager.providers[1], JsonSettingsProvider)
        assert isinstance(
            settings_manager.sources[2], EnvironmentVariablesSettingsSource
        )
        assert isinstance(
            settings_manager.providers[2],
            EnvironmentVariablesSettingsProvider,
        )

        json_source = settings_manager.sources[1]
        assert isinstance(json_source, JsonSettingsSource)
        assert json_source._path.name == expected_json_file_name  # noqa: SLF001 # pyright: ignore[reportPrivateUsage]

    def test_use_run_until_complete_when_loop_is_available_and_not_running(
        self, mocker: MockerFixture
    ) -> None:
        event_loop_mock = mocker.create_autospec(AbstractEventLoop, instance=True)
        event_loop_mock.is_running.return_value = False
        event_loop_mock.run_until_complete.side_effect = asyncio.run

        mocker.patch(
            f"{asyncio.__name__}.{asyncio.get_running_loop.__name__}",
            autospec=True,
            return_value=event_loop_mock,
        )

        settings_manager = SettingsManager(
            content_root_path="", add_default_providers=False
        )

        async def load_provider() -> None:
            return

        settings_manager._call_async(load_provider())  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

        event_loop_mock.run_until_complete.assert_called_once()
