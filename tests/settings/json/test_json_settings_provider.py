import json
import re
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import BaseModel

from wirio.settings.json.json_settings_provider import (
    JsonSettingsProvider,
)
from wirio.settings.settings_manager import SettingsManager


class TestJsonSettingsProvider:
    async def test_load_values_from_json_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "settings.json"
        file_path.write_text(
            '{"appName": "wirio", "port": 8080, "enabled": true, "notes": null}',
            encoding="utf-8",
        )
        provider = JsonSettingsProvider(path=file_path, optional=False)

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
        provider = JsonSettingsProvider(
            path=file_path,
            optional=True,
        )

        await provider.load()

        assert provider.data == {}

    async def test_fail_when_required_file_is_missing(self, tmp_path: Path) -> None:
        file_path = tmp_path / "missing.json"
        provider = JsonSettingsProvider(path=file_path, optional=False)

        with pytest.raises(
            FileNotFoundError,
            match=re.escape(f"Setting file '{file_path}' was not found"),
        ):
            await provider.load()

    async def test_fail_when_json_file_has_invalid_syntax(self, tmp_path: Path) -> None:
        file_path = tmp_path / "settings.json"
        file_path.write_text('{"appName": "wirio"', encoding="utf-8")
        provider = JsonSettingsProvider(path=file_path, optional=False)

        with pytest.raises(json.JSONDecodeError):
            await provider.load()

    async def test_fail_when_json_root_value_is_not_object(
        self, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "settings.json"
        file_path.write_text('["wirio", "config"]', encoding="utf-8")
        provider = JsonSettingsProvider(path=file_path, optional=False)

        with pytest.raises(
            RuntimeError,
            match=re.escape("Could not parse the JSON file"),
        ):
            await provider.load()

    async def test_get_model(self, tmp_path: Path) -> None:
        class Settings(BaseModel):
            app_name: str
            port: int
            enabled: bool
            notes: str | None
            price_as_float: float
            price_as_decimal: Decimal
            int_list: list[int]
            string_list: list[str]

        expected_app_name = "wirio"
        expected_port = 8080
        expected_enabled = True
        expected_notes = None
        expected_price_as_float = 19.99
        expected_price_as_decimal = Decimal("19.99")
        expected_int_list = [1, 2, 3]
        expected_string_list = ["a", "b", "c"]
        file_path = tmp_path / "settings.json"
        file_path.write_text(
            '{"appName": "wirio", "port": 8080, "enabled": true, "notes": null, "priceAsFloat": 19.99, "priceAsDecimal": 19.99, "intList": [1, 2, 3], "stringList": ["a", "b", "c"]}',
            encoding="utf-8",
        )

        settings_manager = SettingsManager(
            content_root_path=str(tmp_path), add_default_providers=False
        )
        settings_manager.add_json_file(
            path="settings.json",
            optional=False,
        )

        model = settings_manager.get_model(Settings)

        assert model.app_name == expected_app_name
        assert model.port == expected_port
        assert model.enabled == expected_enabled
        assert model.notes == expected_notes
        assert model.price_as_float == expected_price_as_float
        assert model.price_as_decimal == expected_price_as_decimal
        assert model.int_list == expected_int_list
        assert model.string_list == expected_string_list
