from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

import pytest
from pytest_mock import MockerFixture

from wirio._utils._extra_dependencies import ExtraDependencies
from wirio.settings.convention_changer import ConventionChanger

if TYPE_CHECKING:
    from azure.core.pipeline import PipelineRequest
    from azure.identity.aio import DefaultAzureCredential
    from azure.keyvault.secrets import KeyVaultSecret, SecretProperties
    from azure.keyvault.secrets.aio import SecretClient

    from wirio.settings.azure_key_vault.azure_key_vault_settings_provider import (
        AzureKeyVaultSettingsProvider,
        _NoUserAgentPolicy,  # pyright: ignore[reportPrivateUsage]
    )
else:
    PipelineRequest = Any
    DefaultAzureCredential = Any
    KeyVaultSecret = Any
    SecretProperties = Any
    SecretClient = Any
    _NoUserAgentPolicy = Any
    AzureKeyVaultSettingsProvider = Any

try:
    from azure.core.pipeline import PipelineRequest
    from azure.identity.aio import DefaultAzureCredential
    from azure.keyvault.secrets import KeyVaultSecret, SecretProperties
    from azure.keyvault.secrets.aio import SecretClient

    from wirio.settings.azure_key_vault.azure_key_vault_settings_provider import (
        AzureKeyVaultSettingsProvider,
        _NoUserAgentPolicy,  # pyright: ignore[reportPrivateUsage]
    )
except ImportError:
    pass


@pytest.mark.skipif(
    not ExtraDependencies.is_azure_key_vault_installed(),
    reason=ExtraDependencies.AZURE_KEY_VAULT_NOT_INSTALLED_ERROR_MESSAGE,
)
class TestAzureKeyVaultSettingsProvider:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.vault_url = "https://example.vault.azure.net"

    async def test_load_enabled_secrets(self, mocker: MockerFixture) -> None:
        default_azure_credential_mock = mocker.create_autospec(
            DefaultAzureCredential, instance=True
        )
        default_azure_credential_mock.__aenter__.return_value = (
            default_azure_credential_mock
        )
        default_azure_credential_mock.__aexit__.return_value = None

        enabled_secret_name = "EnabledSecretName"  # noqa: S105
        enabled_secret_value = "SecretValue"  # noqa: S105
        disabled_secret_name = "DisabledSecretName"  # noqa: S105

        enabled_secret_properties_mock = mocker.create_autospec(
            SecretProperties,
            instance=True,
        )
        enabled_secret_properties_mock.name = enabled_secret_name
        enabled_secret_properties_mock.enabled = True

        disabled_secret_properties_mock = mocker.create_autospec(
            SecretProperties,
            instance=True,
        )
        disabled_secret_properties_mock.name = disabled_secret_name
        disabled_secret_properties_mock.enabled = False

        async def list_properties_of_secrets() -> AsyncIterator[SecretProperties]:
            yield enabled_secret_properties_mock
            yield disabled_secret_properties_mock

        secret_client_mock = mocker.create_autospec(SecretClient, instance=True)
        secret_client_mock.__aenter__.return_value = secret_client_mock
        secret_client_mock.__aexit__.return_value = None
        secret_client_mock.list_properties_of_secrets.return_value = (
            list_properties_of_secrets()
        )

        key_vault_secret_mock = mocker.create_autospec(
            KeyVaultSecret,
            instance=True,
        )
        key_vault_secret_mock.value = enabled_secret_value

        secret_client_mock.get_secret.return_value = key_vault_secret_mock
        secret_client_patch = mocker.patch(
            f"{AzureKeyVaultSettingsProvider.__module__}.{SecretClient.__qualname__}",
            autospec=True,
            return_value=secret_client_mock,
        )
        provider = AzureKeyVaultSettingsProvider(
            url=self.vault_url,
            credential=default_azure_credential_mock,
        )

        await provider.load()

        assert provider.data == {
            ConventionChanger.to_snake_case(enabled_secret_name): enabled_secret_value
        }
        secret_client_mock.get_secret.assert_called_once_with(enabled_secret_name)
        secret_client_patch.assert_called_once_with(
            vault_url=self.vault_url,
            credential=default_azure_credential_mock,
            user_agent_policy=mocker.ANY,
        )

    async def test_use_default_azure_credential_when_none_is_passed(
        self, mocker: MockerFixture
    ) -> None:
        default_azure_credential_mock = mocker.create_autospec(
            DefaultAzureCredential, instance=True
        )
        default_azure_credential_mock.__aenter__.return_value = (
            default_azure_credential_mock
        )
        default_azure_credential_mock.__aexit__.return_value = None

        async def list_properties_of_secrets() -> AsyncIterator[Any]:
            if False:
                yield

        secret_client_mock = mocker.create_autospec(SecretClient, instance=True)
        secret_client_mock.__aenter__.return_value = secret_client_mock
        secret_client_mock.__aexit__.return_value = None
        secret_client_mock.list_properties_of_secrets.return_value = (
            list_properties_of_secrets()
        )

        default_credential_patch = mocker.patch(
            f"{AzureKeyVaultSettingsProvider.__module__}.{DefaultAzureCredential.__qualname__}",
            autospec=True,
            return_value=default_azure_credential_mock,
        )
        secret_client_patch = mocker.patch(
            f"{AzureKeyVaultSettingsProvider.__module__}.{SecretClient.__qualname__}",
            autospec=True,
            return_value=secret_client_mock,
        )
        provider = AzureKeyVaultSettingsProvider(url=self.vault_url)

        await provider.load()

        default_credential_patch.assert_called_once_with()
        secret_client_patch.assert_called_once_with(
            vault_url=self.vault_url,
            credential=default_azure_credential_mock,
            user_agent_policy=mocker.ANY,
        )

    async def test_skip_secret_without_name(self, mocker: MockerFixture) -> None:
        default_azure_credential_mock = mocker.create_autospec(
            DefaultAzureCredential, instance=True
        )
        default_azure_credential_mock.__aenter__.return_value = (
            default_azure_credential_mock
        )
        default_azure_credential_mock.__aexit__.return_value = None

        secret_properties_mock = mocker.create_autospec(
            SecretProperties,
            instance=True,
        )
        secret_properties_mock.name = None
        secret_properties_mock.enabled = True

        async def list_properties_of_secrets() -> AsyncIterator[SecretProperties]:
            yield secret_properties_mock

        secret_client_mock = mocker.create_autospec(SecretClient, instance=True)
        secret_client_mock.__aenter__.return_value = secret_client_mock
        secret_client_mock.__aexit__.return_value = None
        secret_client_mock.list_properties_of_secrets.return_value = (
            list_properties_of_secrets()
        )

        mocker.patch(
            f"{AzureKeyVaultSettingsProvider.__module__}.{SecretClient.__qualname__}",
            autospec=True,
            return_value=secret_client_mock,
        )
        provider = AzureKeyVaultSettingsProvider(
            url=self.vault_url,
            credential=default_azure_credential_mock,
        )

        await provider.load()

        assert provider.data == {}
        secret_client_mock.get_secret.assert_not_called()

    async def test_skip_secret_without_value(self, mocker: MockerFixture) -> None:
        default_azure_credential_mock = mocker.create_autospec(
            DefaultAzureCredential, instance=True
        )
        default_azure_credential_mock.__aenter__.return_value = (
            default_azure_credential_mock
        )
        default_azure_credential_mock.__aexit__.return_value = None

        secret_properties_mock = mocker.create_autospec(
            SecretProperties,
            instance=True,
        )
        secret_properties_mock.name = "SecretName"
        secret_properties_mock.enabled = True

        async def list_properties_of_secrets() -> AsyncIterator[SecretProperties]:
            yield secret_properties_mock

        secret_client_mock = mocker.create_autospec(SecretClient, instance=True)
        secret_client_mock.__aenter__.return_value = secret_client_mock
        secret_client_mock.__aexit__.return_value = None
        secret_client_mock.list_properties_of_secrets.return_value = (
            list_properties_of_secrets()
        )

        key_vault_secret_mock = mocker.create_autospec(
            KeyVaultSecret,
            instance=True,
        )
        key_vault_secret_mock.value = None
        secret_client_mock.get_secret.return_value = key_vault_secret_mock

        mocker.patch(
            f"{AzureKeyVaultSettingsProvider.__module__}.{SecretClient.__qualname__}",
            autospec=True,
            return_value=secret_client_mock,
        )
        provider = AzureKeyVaultSettingsProvider(
            url=self.vault_url,
            credential=default_azure_credential_mock,
        )

        await provider.load()

        assert provider.data == {}
        secret_client_mock.get_secret.assert_called_once_with(
            secret_properties_mock.name
        )

    def test_not_modify_user_agent_header(self, mocker: MockerFixture) -> None:
        pipeline_request_mock = mocker.create_autospec(PipelineRequest, instance=True)
        agent_policy = _NoUserAgentPolicy()

        agent_policy.on_request(pipeline_request_mock)

        assert pipeline_request_mock.mock_calls == []

    async def test_replace_double_dash_with_colon_in_secret_name(
        self, mocker: MockerFixture
    ) -> None:
        default_azure_credential_mock = mocker.create_autospec(
            DefaultAzureCredential, instance=True
        )
        default_azure_credential_mock.__aenter__.return_value = (
            default_azure_credential_mock
        )
        default_azure_credential_mock.__aexit__.return_value = None

        secret_name = "Logging--LogLevel--Default"  # noqa: S105
        expected_secret_name = "logging:log_level:default"  # noqa: S105
        secret_value = "WARNING"  # noqa: S105

        secret_properties_mock = mocker.create_autospec(
            SecretProperties,
            instance=True,
        )
        secret_properties_mock.name = secret_name
        secret_properties_mock.enabled = True

        async def list_properties_of_secrets() -> AsyncIterator[SecretProperties]:
            yield secret_properties_mock

        secret_client_mock = mocker.create_autospec(SecretClient, instance=True)
        secret_client_mock.__aenter__.return_value = secret_client_mock
        secret_client_mock.__aexit__.return_value = None
        secret_client_mock.list_properties_of_secrets.return_value = (
            list_properties_of_secrets()
        )

        key_vault_secret_mock = mocker.create_autospec(
            KeyVaultSecret,
            instance=True,
        )
        key_vault_secret_mock.value = secret_value
        secret_client_mock.get_secret.return_value = key_vault_secret_mock

        mocker.patch(
            f"{AzureKeyVaultSettingsProvider.__module__}.{SecretClient.__qualname__}",
            autospec=True,
            return_value=secret_client_mock,
        )
        provider = AzureKeyVaultSettingsProvider(
            url=self.vault_url,
            credential=default_azure_credential_mock,
        )

        await provider.load()

        assert provider.data == {expected_secret_name: secret_value}
        secret_client_mock.get_secret.assert_called_once_with(secret_name)
