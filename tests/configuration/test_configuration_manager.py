from typing import TYPE_CHECKING, Any, final, override

import pytest
from pydantic import BaseModel, Field
from pytest_mock import MockerFixture

from wirio._utils._extra_dependencies import ExtraDependencies
from wirio.configuration.configuration_builder import ConfigurationBuilder
from wirio.configuration.configuration_manager import ConfigurationManager
from wirio.configuration.configuration_provider import ConfigurationProvider
from wirio.configuration.configuration_source import ConfigurationSource

if TYPE_CHECKING:
    from azure.core.credentials_async import AsyncTokenCredential

    from wirio.configuration.azure_key_vault.azure_key_vault_configuration_source import (
        AzureKeyVaultConfigurationSource,
    )
else:
    AsyncTokenCredential = Any
    AzureKeyVaultConfigurationSource = Any

try:
    from azure.core.credentials_async import AsyncTokenCredential

    from wirio.configuration.azure_key_vault.azure_key_vault_configuration_source import (
        AzureKeyVaultConfigurationSource,
    )
except ImportError:
    pass


@final
class _DictionaryConfigurationProvider(ConfigurationProvider):
    _values: dict[str, str | None]

    def __init__(self, values: dict[str, str | None]) -> None:
        super().__init__()
        self._values = values

    @override
    async def load(self) -> None:
        self._data = self._values
        await super().load()


@final
class _DictionaryConfigurationSource(ConfigurationSource):
    _values: dict[str, str | None]

    def __init__(self, values: dict[str, str | None]) -> None:
        self._values = values

    @override
    def build(self, builder: ConfigurationBuilder) -> ConfigurationProvider:
        return _DictionaryConfigurationProvider(self._values)


class _Settings(BaseModel):
    app_name: str
    port: str


class TestConfigurationManager:
    def test_get_required_value(self) -> None:
        expected_configuration_value = "wirio"
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(
            _DictionaryConfigurationSource({"app_name": expected_configuration_value})
        )

        configuration_value = configuration_manager.get_required_value("app_name")

        assert isinstance(configuration_value, str)
        assert configuration_value == expected_configuration_value

    def test_get_required_value_specifying_type(self) -> None:
        expected_configuration_value = 1
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(
            _DictionaryConfigurationSource(
                {"number": str(expected_configuration_value)}
            )
        )

        configuration_value = configuration_manager.get_required_value("number", int)

        assert isinstance(configuration_value, int)
        assert configuration_value == expected_configuration_value

    def test_fail_when_getting_missing_required_value(self) -> None:
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(_DictionaryConfigurationSource({"app_name": "wirio"}))

        with pytest.raises(KeyError) as exception_info:
            configuration_manager.get_required_value("port")

        assert (
            exception_info.value.args[0] == "Missing configuration value for key 'port'"
        )

    def test_fail_when_getting_required_value_with_invalid_type(self) -> None:
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(
            _DictionaryConfigurationSource({"number": "not-a-number"})
        )

        with pytest.raises(
            ValueError  # noqa: PT011
        ) as exception_info:
            configuration_manager.get_required_value("number", int)

        assert "validation error" in str(exception_info.value)

    def test_fail_when_required_value_is_none(self) -> None:
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(_DictionaryConfigurationSource({"app_name": None}))

        with pytest.raises(
            ValueError  # noqa: PT011
        ) as exception_info:
            configuration_manager.get_required_value("app_name")

        assert (
            str(exception_info.value)
            == "Configuration value for key 'app_name' is None"
        )

    def test_get_value(self) -> None:
        expected_configuration_value = "wirio"
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(
            _DictionaryConfigurationSource({"app_name": expected_configuration_value})
        )

        configuration_value = configuration_manager.get_value("app_name", default="a")

        assert isinstance(configuration_value, str)
        assert configuration_value == expected_configuration_value

    def test_get_none_value_when_getting_value_with_none_value(self) -> None:
        expected_configuration_value = None
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(
            _DictionaryConfigurationSource({"app_name": expected_configuration_value})
        )

        configuration_value = configuration_manager.get_value("app_name")

        assert configuration_value is None
        assert configuration_value == expected_configuration_value

    def test_get_value_specifying_type(self) -> None:
        expected_configuration_value = 1
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(
            _DictionaryConfigurationSource(
                {"number": str(expected_configuration_value)}
            )
        )

        configuration_value = configuration_manager.get_value("number", int)

        assert isinstance(configuration_value, int)
        assert configuration_value == expected_configuration_value

    def test_get_none_when_getting_missing_value(self) -> None:
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(_DictionaryConfigurationSource({"app_name": "wirio"}))

        configuration_value = configuration_manager.get_value("port")

        assert configuration_value is None

    def test_fail_when_getting_value_with_invalid_type(self) -> None:
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(
            _DictionaryConfigurationSource({"number": "not-a-number"})
        )

        with pytest.raises(
            ValueError  # noqa: PT011
        ) as exception_info:
            configuration_manager.get_value("number", int)

        assert "validation error" in str(exception_info.value)

    def test_get_default_value_when_getting_missing_value(self) -> None:
        expected_default_value = 1
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(_DictionaryConfigurationSource({}))

        configuration_value = configuration_manager.get_value(
            "number", int, default=expected_default_value
        )

        assert isinstance(configuration_value, int)
        assert configuration_value == expected_default_value

    def test_get_model(self) -> None:
        expected_app_name = "wirio"
        expected_port = "8080"
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(
            _DictionaryConfigurationSource(
                {"app_name": expected_app_name, "port": expected_port}
            )
        )

        settings = configuration_manager.get_model(_Settings)

        assert isinstance(settings, _Settings)
        assert settings.app_name == expected_app_name
        assert settings.port == expected_port

    async def test_add_source_when_event_loop_is_running(self) -> None:
        expected_app_name = "wirio"
        expected_port = "8080"
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(
            _DictionaryConfigurationSource(
                {"app_name": expected_app_name, "port": expected_port}
            )
        )

        settings = configuration_manager.get_model(_Settings)

        assert settings.app_name == expected_app_name
        assert settings.port == expected_port

    def test_add_source_when_event_loop_is_not_running(self) -> None:
        expected_app_name = "wirio"
        expected_port = "8080"
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(
            _DictionaryConfigurationSource(
                {"app_name": expected_app_name, "port": expected_port}
            )
        )

        settings = configuration_manager.get_model(_Settings)

        assert settings.app_name == expected_app_name
        assert settings.port == expected_port

    def test_override_values_with_last_source(self) -> None:
        expected_app_name = "wirio"
        expected_port = "9090"

        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(
            _DictionaryConfigurationSource({"app_name": "wirio", "port": "8080"})
        )
        configuration_manager.add(
            _DictionaryConfigurationSource({"port": expected_port})
        )

        settings = configuration_manager.get_model(_Settings)

        assert settings.app_name == expected_app_name
        assert settings.port == expected_port

    def test_return_none_for_missing_optional_value_of_a_model(self) -> None:
        class Settings(BaseModel):
            app_name: str
            port: int | None = None

        expected_app_name = "wirio"
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(
            _DictionaryConfigurationSource({"app_name": expected_app_name})
        )

        settings = configuration_manager.get_model(Settings)

        assert settings.app_name == expected_app_name
        assert settings.port is None

    def test_fail_when_required_value_of_a_model_is_missing(self) -> None:
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(_DictionaryConfigurationSource({"app_name": "wirio"}))

        with pytest.raises(KeyError) as exception_info:
            configuration_manager.get_model(_Settings)

        assert (
            exception_info.value.args[0] == "Missing configuration value for key 'port'"
        )

    def test_convert_source_names_to_snake_case(self) -> None:
        expected_app_name = "wirio"
        expected_port = "8080"
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(
            _DictionaryConfigurationSource(
                {"APP_NAME": expected_app_name, "PORT": expected_port}
            )
        )

        settings = configuration_manager.get_model(_Settings)

        assert settings.app_name == expected_app_name
        assert settings.port == expected_port

    def test_return_added_sources(self) -> None:
        expected_sources = 2

        configuration_manager = ConfigurationManager(content_root_path="")
        source1 = _DictionaryConfigurationSource({"app_name": "wirio"})
        source2 = _DictionaryConfigurationSource({"port": "8080"})
        configuration_manager.add(source1)
        configuration_manager.add(source2)

        sources = configuration_manager.sources

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
        configuration_manager = ConfigurationManager(content_root_path="")
        add_patch = mocker.patch.object(
            configuration_manager,
            configuration_manager.add.__name__,
            autospec=True,
        )

        configuration_manager.add_azure_key_vault(
            url=expected_vault_url,
            credential=token_credential_mock,
        )

        add_patch.assert_called_once()
        source = add_patch.call_args.args[0]
        assert isinstance(source, AzureKeyVaultConfigurationSource)

    def test_use_default_factory_for_missing_optional_value_of_a_model(self) -> None:
        class Settings(BaseModel):
            app_name: str
            api_url: str = Field(default_factory=lambda: "https://localhost")

        expected_app_name = "wirio"
        expected_api_url = "https://localhost"
        configuration_manager = ConfigurationManager(content_root_path="")
        configuration_manager.add(
            _DictionaryConfigurationSource({"app_name": expected_app_name})
        )

        settings = configuration_manager.get_model(Settings)

        assert settings.app_name == expected_app_name
        assert settings.api_url == expected_api_url
