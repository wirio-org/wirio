from typing import final

from wirio.settings.settings_provider import SettingsProvider


class TestSettingsProvider:
    def test_stringify(self) -> None:
        @final
        class SettingsProviderFake(SettingsProvider):
            pass

        provider = SettingsProviderFake()

        assert str(provider) == SettingsProviderFake.__name__
