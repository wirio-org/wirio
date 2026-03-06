import pytest
from pytest_mock import MockerFixture

from wirio.configuration.configuration_root import ConfigurationRoot
from wirio.configuration.configuration_section import ConfigurationSection


class TestConfigurationSection:
    @pytest.mark.parametrize(
        argnames=("expected_path"),
        argvalues=[
            "logging:log_level:default",
            "logging:log_level",
            "logging",
        ],
    )
    def test_get_path(self, expected_path: str, mocker: MockerFixture) -> None:
        configuration_root_mock = mocker.create_autospec(
            ConfigurationRoot, instance=True
        )
        section = ConfigurationSection(root=configuration_root_mock, path=expected_path)

        path = section.path

        assert path == expected_path

    @pytest.mark.parametrize(
        argnames=("section_key", "expected_key"),
        argvalues=[
            ("logging:log_level:default", "default"),
            ("logging:log_level", "log_level"),
            ("logging", "logging"),
        ],
    )
    def test_get_key(
        self, section_key: str, expected_key: str, mocker: MockerFixture
    ) -> None:
        configuration_root_mock = mocker.create_autospec(
            ConfigurationRoot, instance=True
        )
        section = ConfigurationSection(root=configuration_root_mock, path=section_key)

        configuration_key = section.key

        assert configuration_key == expected_key

    def test_get_value_not_specifying_type(self, mocker: MockerFixture) -> None:
        expected_path = "logging:log_level:default"
        expected_value = "WARNING"
        configuration_root_mock = mocker.create_autospec(
            ConfigurationRoot, instance=True
        )
        configuration_root_mock.get_value.return_value = expected_value
        section = ConfigurationSection(root=configuration_root_mock, path=expected_path)

        configuration_value = section.get_value()

        assert configuration_value == expected_value
        configuration_root_mock.get_value.assert_called_once_with(expected_path)

    @pytest.mark.parametrize(
        argnames=("expected_path", "expected_value", "value_type"),
        argvalues=[
            ("logging:log_level:default", 1, int),
            ("logging:log_level:default", "WARNING", str),
            ("logging:log_level:default", [1, 2, 3], list[int]),
        ],
    )
    def test_get_value_specifying_type[TField](
        self,
        expected_path: str,
        expected_value: TField,
        value_type: type[TField],
        mocker: MockerFixture,
    ) -> None:
        configuration_root_mock = mocker.create_autospec(
            ConfigurationRoot, instance=True
        )
        configuration_root_mock.get_value.return_value = expected_value
        section = ConfigurationSection(root=configuration_root_mock, path=expected_path)

        configuration_value = section.get_value(value_type)

        assert configuration_value == expected_value
        configuration_root_mock.get_value.assert_called_once_with(
            expected_path, value_type
        )

    def test_get_value_for_section_with_subsections_below(
        self, mocker: MockerFixture
    ) -> None:
        expected_path = "logging:log_level"
        expected_value = None
        configuration_root_mock = mocker.create_autospec(
            ConfigurationRoot, instance=True
        )
        configuration_root_mock.get_value.return_value = expected_value
        section = ConfigurationSection(root=configuration_root_mock, path=expected_path)

        configuration_value = section.get_value()

        assert configuration_value == expected_value
        configuration_root_mock.get_value.assert_called_once_with(expected_path)

    def test_get_value_for_child_key_not_specifying_type(
        self, mocker: MockerFixture
    ) -> None:
        expected_value = "WARNING"
        configuration_root_mock = mocker.create_autospec(
            ConfigurationRoot, instance=True
        )
        configuration_root_mock.get_value.return_value = expected_value
        section = ConfigurationSection(root=configuration_root_mock, path="logging")

        configuration_value = section.get_value("log_level:default")

        assert configuration_value == expected_value
        configuration_root_mock.get_value.assert_called_once_with(
            "logging:log_level:default"
        )

    def test_get_value_for_child_key_specifying_type(
        self, mocker: MockerFixture
    ) -> None:
        expected_value = 1
        configuration_root_mock = mocker.create_autospec(
            ConfigurationRoot, instance=True
        )
        configuration_root_mock.get_value.return_value = expected_value
        section = ConfigurationSection(root=configuration_root_mock, path="logging")

        configuration_value = section.get_value("log_level:default", int)

        assert configuration_value == expected_value
        configuration_root_mock.get_value.assert_called_once_with(
            "logging:log_level:default", int
        )
