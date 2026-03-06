import os
from typing import final, override

from wirio.configuration.configuration_path import ConfigurationPath
from wirio.configuration.configuration_provider import ConfigurationProvider


@final
class EnvironmentVariablesConfigurationProvider(ConfigurationProvider):
    @override
    async def load(self) -> None:
        environment_variables = dict(os.environ)
        normalized_environment_variables: dict[str, str | None] = {}

        for key, value in environment_variables.items():
            normalized_key = self._normalize_key(key)
            normalized_environment_variables[normalized_key] = value

        self._data = normalized_environment_variables
        await super().load()

    def _normalize_key(self, key: str) -> str:
        return key.replace("__", ConfigurationPath.KEY_DELIMITER)
