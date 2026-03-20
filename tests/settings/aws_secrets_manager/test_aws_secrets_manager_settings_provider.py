import json
import os
from typing import TYPE_CHECKING, Any, ClassVar, cast

import pytest
from pytest_mock import MockerFixture

from wirio._utils._extra_dependencies import ExtraDependencies

if TYPE_CHECKING:
    from testcontainers.localstack import (  # pyright: ignore[reportMissingTypeStubs]
        LocalStackContainer,
    )

    from wirio.settings.aws_secrets_manager.aws_secrets_manager_settings_provider import (
        AwsSecretsManagerSettingsProvider,
    )
else:
    LocalStackContainer = Any
    AwsSecretsManagerSettingsProvider = Any

try:
    from testcontainers.localstack import (  # pyright: ignore[reportMissingTypeStubs]
        LocalStackContainer,
    )

    from wirio.settings.aws_secrets_manager.aws_secrets_manager_settings_provider import (
        AwsSecretsManagerSettingsProvider,
    )
except ImportError:
    pass


class _SecretsManagerClient:
    def get_secret_value(self, SecretId: str) -> dict[str, Any]:  # noqa: N803
        raise NotImplementedError


@pytest.mark.skipif(
    not ExtraDependencies.is_aws_secrets_manager_installed(),
    reason=ExtraDependencies.AWS_SECRETS_MANAGER_NOT_INSTALLED_ERROR_MESSAGE,
)
class TestAwsSecretsManagerSettingsProvider:
    LOCAL_STACK_IMAGE: ClassVar[str] = (
        "localstack/localstack@sha256:3ebc37595918b8accb852f8048fef2aff047d465167edd655528065b07bc364a"  # 4.14.0
    )

    async def test_load_values_from_secret_name(self, mocker: MockerFixture) -> None:
        expected_region = "eu-west-1"
        expected_url = "http://localhost:4566"
        expected_secret_name = "dev/TestApp"  # noqa: S105
        secret_value = json.dumps(
            {
                "Logging": {"LogLevel": {"Default": "WARNING"}},
                "Port": 8080,
                "Enabled": True,
                "Notes": None,
                "Items": [],
            }
        )

        secrets_manager_client_mock = mocker.create_autospec(
            _SecretsManagerClient,
            instance=True,
        )
        secrets_manager_client_mock.get_secret_value.return_value = {
            "SecretString": secret_value
        }
        boto_client_patch = mocker.patch(
            f"{AwsSecretsManagerSettingsProvider.__module__}.boto3.client",
            autospec=True,
            return_value=secrets_manager_client_mock,
        )
        provider = AwsSecretsManagerSettingsProvider(
            secret_name=expected_secret_name,
            region=expected_region,
            url=expected_url,
        )

        await provider.load()

        assert provider.data == {
            "logging:log_level:default": "WARNING",
            "port": "8080",
            "enabled": "True",
            "notes": None,
            "items": "",
        }
        boto_client_patch.assert_called_once_with(
            service_name="secretsmanager",
            region_name=expected_region,
            endpoint_url=expected_url,
        )
        secrets_manager_client_mock.get_secret_value.assert_called_once_with(
            SecretId=expected_secret_name
        )

    @pytest.mark.skipif(
        os.environ.get("CI") is None,
        reason="Slow tests",
    )
    async def test_load_secret_from_localstack_secrets_manager(self) -> None:
        expected_region = "us-east-1"
        expected_secret_name = "dev/TestApp"  # noqa: S105
        expected_api_key = "12345"
        expected_database_user = "user1"
        expected_database_password = "pass1"  # noqa: S105
        local_stack_container = LocalStackContainer(
            image=self.LOCAL_STACK_IMAGE,
            region_name=expected_region,
        ).with_services("secretsmanager")  # pyright: ignore[reportUnknownMemberType]

        with local_stack_container:
            secrets_manager_client = cast(
                "Any",
                local_stack_container.get_client("secretsmanager"),  # type: ignore  # noqa: PGH003
            )  # ty:ignore[redundant-cast]
            secrets_manager_client.create_secret(
                Name=expected_secret_name,
                SecretString='{"ServiceApiKey": "12345", "Database": {"User": "user1", "Password": "pass1"}}',
            )
            provider = AwsSecretsManagerSettingsProvider(
                secret_name=expected_secret_name,
                region=expected_region,
                url=local_stack_container.get_url(),
            )

            await provider.load()

        assert provider.data == {
            "service_api_key": expected_api_key,
            "database:user": expected_database_user,
            "database:password": expected_database_password,
        }
