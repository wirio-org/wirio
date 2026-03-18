import re

import pytest

from wirio.settings.json.json_settings_file_parser import (
    JsonSettingsFileParser,
)


class TestJsonSettingsFileParser:
    def test_parse_scalar_values(self) -> None:
        parser = JsonSettingsFileParser()

        result = parser.parse_json(
            {
                "name": "wirio",
                "port": 8080,
                "enabled": True,
                "notes": None,
                "price": 19.99,
            }
        )

        assert result == {
            "name": "wirio",
            "port": "8080",
            "enabled": "True",
            "notes": None,
            "price": "19.99",
        }

    def test_parse_nested_objects_and_arrays(self) -> None:
        parser = JsonSettingsFileParser()

        result = parser.parse_json(
            {
                "Logging": {"LogLevel": {"Default": "Information"}},
                "AllowedHosts": ["localhost", "example.com"],
            }
        )

        assert result == {
            "Logging:LogLevel:Default": "Information",
            "AllowedHosts:0": "localhost",
            "AllowedHosts:1": "example.com",
        }

    def test_set_null_and_empty_for_empty_structures(self) -> None:
        parser = JsonSettingsFileParser()

        result = parser.parse_json(
            {
                "Section": {},
                "Nested": {"Child": {}},
                "Items": [],
                "NestedItems": {"Items": []},
            }
        )

        assert result == {
            "Section": None,
            "Nested:Child": None,
            "Items": "",
            "NestedItems:Items": "",
        }

    def test_fail_when_duplicate_key_is_found_ignoring_case(self) -> None:
        parser = JsonSettingsFileParser()

        with pytest.raises(
            RuntimeError,
            match=re.escape("A duplicate key 'key' was found"),
        ):
            parser.parse_json({"Key": "value", "key": "other"})
