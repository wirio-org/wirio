from typing import final, override

from wirio.settings.environment_variables.environment_variables_settings_provider import (
    EnvironmentVariablesSettingsProvider,
)
from wirio.settings.settings_builder import SettingsBuilder
from wirio.settings.settings_provider import SettingsProvider
from wirio.settings.settings_source import SettingsSource


@final
class EnvironmentVariablesSettingsSource(SettingsSource):
    @override
    def build(self, builder: SettingsBuilder) -> SettingsProvider:
        return EnvironmentVariablesSettingsProvider()
