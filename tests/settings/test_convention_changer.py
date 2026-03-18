import pytest

from wirio.settings.convention_changer import ConventionChanger


class TestConventionChanger:
    @pytest.mark.parametrize(
        argnames=("string_to_convert", "expected_string"),
        argvalues=[
            ("snake_to_snake", "snake_to_snake"),
            ("camelToSnake", "camel_to_snake"),
            ("camel2Snake", "camel_2_snake"),
            ("Camel2Snake", "camel_2_snake"),
            ("camel2snake", "camel_2snake"),
            ("_camelToSnake", "_camel_to_snake"),
            ("camelToSnake_", "camel_to_snake_"),
            ("__camelToSnake__", "__camel_to_snake__"),
            ("CamelToSnake", "camel_to_snake"),
            ("_CamelToSnake", "_camel_to_snake"),
            ("CamelToSnake_", "camel_to_snake_"),
            ("CAMELToSnake", "camel_to_snake"),
            ("__CamelToSnake__", "__camel_to_snake__"),
            ("Camel2", "camel_2"),
            ("Camel2_", "camel_2_"),
            ("_Camel2", "_camel_2"),
            ("camel2", "camel_2"),
            ("camel2_", "camel_2_"),
            ("_camel2", "_camel_2"),
            ("kebab-to-snake", "kebab_to_snake"),
            ("kebab-Snake", "kebab_snake"),
            ("Kebab-Snake", "kebab_snake"),
            ("PascalToSnake", "pascal_to_snake"),
            ("snakeV2", "snake_v2"),
            ("snakeVV2", "snake_vv2"),
            ("snakev2", "snakev_2"),
        ],
    )
    def test_convert_to_snake_case(
        self, string_to_convert: str, expected_string: str
    ) -> None:
        converted_value = ConventionChanger.to_snake_case(string_to_convert)

        assert converted_value == expected_string
