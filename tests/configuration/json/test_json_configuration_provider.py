from pathlib import Path

import pytest

from wirio.configuration.json.json_configuration_provider import (
    JsonConfigurationProvider,
)


class TestJsonConfigurationProvider:
    async def test_load_values_from_json_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "appsettings.json"
        file_path.write_text(
            '{"appName": "wirio", "port": 8080, "enabled": true, "notes": null}',
            encoding="utf-8",
        )
        provider = JsonConfigurationProvider(path=file_path, optional=False)

        await provider.load()

        assert provider.data == {
            "app_name": "wirio",
            "port": "8080",
            "enabled": "True",
            "notes": None,
        }

    async def test_return_empty_data_when_optional_file_is_missing(
        self, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "missing.json"
        provider = JsonConfigurationProvider(
            path=file_path,
            optional=True,
        )

        await provider.load()

        assert provider.data == {}

    async def test_fail_when_required_file_is_missing(self, tmp_path: Path) -> None:
        provider = JsonConfigurationProvider(
            path=tmp_path / "missing.json",
            optional=False,
        )

        with pytest.raises(FileNotFoundError):
            await provider.load()
