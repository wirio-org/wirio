import os

import pytest

from wirio.configuration.environment_variables.environment_variables_configuration_provider import (
    EnvironmentVariablesConfigurationProvider,
)


class TestEnvironmentVariablesConfigurationProvider:
    async def test_replace_double_underscore_with_colon_in_environment_variable_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        expected_value = "WARNING"
        monkeypatch.setattr(
            os,
            "environ",
            {"LOGGING__LOG_LEVEL__DEFAULT": expected_value},
        )
        provider = EnvironmentVariablesConfigurationProvider()

        await provider.load()

        assert provider.data == {"logging:log_level:default": expected_value}
