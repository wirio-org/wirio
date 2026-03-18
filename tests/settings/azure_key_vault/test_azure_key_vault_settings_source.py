from typing import TYPE_CHECKING, Any

import pytest
from pytest_mock import MockerFixture

from wirio._utils._extra_dependencies import ExtraDependencies
from wirio.settings.settings_builder import SettingsBuilder
from wirio.settings.settings_provider import SettingsProvider

if TYPE_CHECKING:
    from azure.identity.aio import DefaultAzureCredential

    from wirio.settings.azure_key_vault.azure_key_vault_settings_provider import (
        AzureKeyVaultSettingsProvider,
    )
    from wirio.settings.azure_key_vault.azure_key_vault_settings_source import (
        AzureKeyVaultSettingsSource,
    )
else:
    DefaultAzureCredential = Any
    AzureKeyVaultSettingsProvider = Any
    AzureKeyVaultSettingsSource = Any

try:
    from azure.identity.aio import DefaultAzureCredential

    from wirio.settings.azure_key_vault.azure_key_vault_settings_provider import (
        AzureKeyVaultSettingsProvider,
    )
    from wirio.settings.azure_key_vault.azure_key_vault_settings_source import (
        AzureKeyVaultSettingsSource,
    )
except ImportError:
    pass


@pytest.mark.skipif(
    not ExtraDependencies.is_azure_key_vault_installed(),
    reason=ExtraDependencies.AZURE_KEY_VAULT_NOT_INSTALLED_ERROR_MESSAGE,
)
class TestAzureKeyVaultSettingsSource:
    def test_build_provider(self, mocker: MockerFixture) -> None:
        vault_url = "https://example.vault.azure.net/"
        credential = mocker.create_autospec(DefaultAzureCredential, instance=True)
        settings_provider_mock = mocker.create_autospec(SettingsProvider, instance=True)
        settings_builder_mock = mocker.create_autospec(SettingsBuilder, instance=True)
        settings_provider_patch = mocker.patch(
            f"{AzureKeyVaultSettingsSource.__module__}.{AzureKeyVaultSettingsProvider.__qualname__}",
            autospec=True,
            return_value=settings_provider_mock,
        )
        source = AzureKeyVaultSettingsSource(
            url=vault_url,
            credential=credential,
        )

        provider = source.build(settings_builder_mock)

        assert provider is settings_provider_mock
        settings_provider_patch.assert_called_once_with(
            url=vault_url,
            credential=credential,
        )
