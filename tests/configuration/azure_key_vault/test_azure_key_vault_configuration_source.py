from typing import TYPE_CHECKING, Any

import pytest
from pytest_mock import MockerFixture

from wirio._utils._extra_dependencies import ExtraDependencies
from wirio.configuration.configuration_builder import ConfigurationBuilder
from wirio.configuration.configuration_provider import ConfigurationProvider

if TYPE_CHECKING:
    from azure.identity.aio import DefaultAzureCredential

    from wirio.configuration.azure_key_vault.azure_key_vault_configuration_provider import (
        AzureKeyVaultConfigurationProvider,
    )
    from wirio.configuration.azure_key_vault.azure_key_vault_configuration_source import (
        AzureKeyVaultConfigurationSource,
    )
else:
    DefaultAzureCredential = Any
    AzureKeyVaultConfigurationProvider = Any
    AzureKeyVaultConfigurationSource = Any

try:
    from azure.identity.aio import DefaultAzureCredential

    from wirio.configuration.azure_key_vault.azure_key_vault_configuration_provider import (
        AzureKeyVaultConfigurationProvider,
    )
    from wirio.configuration.azure_key_vault.azure_key_vault_configuration_source import (
        AzureKeyVaultConfigurationSource,
    )
except ImportError:
    pass


@pytest.mark.skipif(
    not ExtraDependencies.is_azure_key_vault_installed(),
    reason=ExtraDependencies.AZURE_KEY_VAULT_NOT_INSTALLED_ERROR_MESSAGE,
)
class TestAzureKeyVaultConfigurationSource:
    def test_build_provider(self, mocker: MockerFixture) -> None:
        vault_url = "https://example.vault.azure.net/"
        credential = mocker.create_autospec(DefaultAzureCredential, instance=True)
        configuration_provider_mock = mocker.create_autospec(
            ConfigurationProvider, instance=True
        )
        configuration_builder_mock = mocker.create_autospec(
            ConfigurationBuilder, instance=True
        )
        configuration_provider_patch = mocker.patch(
            f"{AzureKeyVaultConfigurationSource.__module__}.{AzureKeyVaultConfigurationProvider.__qualname__}",
            autospec=True,
            return_value=configuration_provider_mock,
        )
        source = AzureKeyVaultConfigurationSource(
            url=vault_url,
            credential=credential,
        )

        provider = source.build(configuration_builder_mock)

        assert provider is configuration_provider_mock
        configuration_provider_patch.assert_called_once_with(
            url=vault_url,
            credential=credential,
        )
