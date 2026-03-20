from typing import TYPE_CHECKING, Any

import pytest
from pytest_mock import MockerFixture

from wirio._utils._extra_dependencies import ExtraDependencies
from wirio.settings.settings_builder import SettingsBuilder
from wirio.settings.settings_provider import SettingsProvider

if TYPE_CHECKING:
    from wirio.settings.aws_secrets_manager.aws_secrets_manager_settings_provider import (
        AwsSecretsManagerSettingsProvider,
    )
    from wirio.settings.aws_secrets_manager.aws_secrets_manager_settings_source import (
        AwsSecretsManagerSettingsSource,
    )
else:
    AwsSecretsManagerSettingsProvider = Any
    AwsSecretsManagerSettingsSource = Any

try:
    from wirio.settings.aws_secrets_manager.aws_secrets_manager_settings_provider import (
        AwsSecretsManagerSettingsProvider,
    )
    from wirio.settings.aws_secrets_manager.aws_secrets_manager_settings_source import (
        AwsSecretsManagerSettingsSource,
    )
except ImportError:
    pass


@pytest.mark.skipif(
    not ExtraDependencies.is_aws_secrets_manager_installed(),
    reason=ExtraDependencies.AWS_SECRETS_MANAGER_NOT_INSTALLED_ERROR_MESSAGE,
)
class TestAwsSecretsManagerSettingsSource:
    def test_build_provider(self, mocker: MockerFixture) -> None:
        expected_secret_name = "dev/TestApp"  # noqa: S105
        expected_region = "eu-west-1"
        expected_url = "https://secretsmanager.eu-west-1.amazonaws.com"
        settings_provider_mock = mocker.create_autospec(SettingsProvider, instance=True)
        settings_builder_mock = mocker.create_autospec(SettingsBuilder, instance=True)
        settings_provider_patch = mocker.patch(
            f"{AwsSecretsManagerSettingsSource.__module__}.{AwsSecretsManagerSettingsProvider.__qualname__}",
            autospec=True,
            return_value=settings_provider_mock,
        )
        source = AwsSecretsManagerSettingsSource(
            secret_id=expected_secret_name,
            region=expected_region,
            url=expected_url,
        )

        provider = source.build(settings_builder_mock)

        assert provider is settings_provider_mock
        settings_provider_patch.assert_called_once_with(
            secret_id=expected_secret_name,
            region=expected_region,
            url=expected_url,
        )
