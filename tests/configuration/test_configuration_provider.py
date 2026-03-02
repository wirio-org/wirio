from typing import final

from wirio.configuration.configuration_provider import ConfigurationProvider


class TestConfigurationProvider:
    def test_stringify(self) -> None:
        @final
        class ConfigurationProviderFake(ConfigurationProvider):
            pass

        provider = ConfigurationProviderFake()

        assert str(provider) == ConfigurationProviderFake.__name__
