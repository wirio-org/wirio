import pytest
from pytest_mock import MockerFixture

from wirio.settings.settings_root import SettingsRoot
from wirio.settings.settings_section import SettingsSection


class TestSettingsSection:
    @pytest.mark.parametrize(
        argnames=("expected_path"),
        argvalues=[
            "logging:log_level:default",
            "logging:log_level",
            "logging",
        ],
    )
    def test_get_path(self, expected_path: str, mocker: MockerFixture) -> None:
        settings_root_mock = mocker.create_autospec(SettingsRoot, instance=True)
        section = SettingsSection(root=settings_root_mock, path=expected_path)

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
        settings_root_mock = mocker.create_autospec(SettingsRoot, instance=True)
        section = SettingsSection(root=settings_root_mock, path=section_key)

        setting_key = section.key

        assert setting_key == expected_key

    def test_get_value_not_specifying_type(self, mocker: MockerFixture) -> None:
        expected_path = "logging:log_level:default"
        expected_value = "WARNING"
        settings_root_mock = mocker.create_autospec(SettingsRoot, instance=True)
        settings_root_mock.get_value.return_value = expected_value
        section = SettingsSection(root=settings_root_mock, path="logging:log_level")

        setting_value = section.get_value("default")

        assert setting_value == expected_value
        settings_root_mock.get_value.assert_called_once_with(expected_path, str)

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
        settings_root_mock = mocker.create_autospec(SettingsRoot, instance=True)
        settings_root_mock.get_value.return_value = expected_value
        section = SettingsSection(root=settings_root_mock, path="logging:log_level")

        setting_value = section.get_value("default", value_type)

        assert setting_value == expected_value
        settings_root_mock.get_value.assert_called_once_with(expected_path, value_type)

    def test_get_value_for_child_key_not_specifying_type(
        self, mocker: MockerFixture
    ) -> None:
        expected_value = "WARNING"
        settings_root_mock = mocker.create_autospec(SettingsRoot, instance=True)
        settings_root_mock.get_value.return_value = expected_value
        section = SettingsSection(root=settings_root_mock, path="logging")

        setting_value = section.get_value("log_level:default")

        assert setting_value == expected_value
        settings_root_mock.get_value.assert_called_once_with(
            "logging:log_level:default", str
        )

    def test_get_value_for_child_key_specifying_type(
        self, mocker: MockerFixture
    ) -> None:
        expected_value = 1
        settings_root_mock = mocker.create_autospec(SettingsRoot, instance=True)
        settings_root_mock.get_value.return_value = expected_value
        section = SettingsSection(root=settings_root_mock, path="logging")

        setting_value = section.get_value("log_level:default", int)

        assert setting_value == expected_value
        settings_root_mock.get_value.assert_called_once_with(
            "logging:log_level:default", int
        )

    def test_get_children_from_child_key(self, mocker: MockerFixture) -> None:
        expected_children = []
        settings_root_mock = mocker.create_autospec(SettingsRoot, instance=True)
        settings_root_mock.get_children.return_value = expected_children
        section = SettingsSection(root=settings_root_mock, path="logging")

        children = section.get_children("log_level")

        assert children == expected_children
        settings_root_mock.get_children.assert_called_once_with("logging:log_level")

    def test_get_required_value_not_specifying_type(
        self, mocker: MockerFixture
    ) -> None:
        expected_path = "logging:log_level:default"
        expected_value = "WARNING"
        settings_root_mock = mocker.create_autospec(SettingsRoot, instance=True)
        settings_root_mock.get_required_value.return_value = expected_value
        section = SettingsSection(root=settings_root_mock, path="logging:log_level")

        setting_value = section.get_required_value("default")

        assert setting_value == expected_value
        settings_root_mock.get_required_value.assert_called_once_with(
            expected_path, str
        )

    @pytest.mark.parametrize(
        argnames=("expected_path", "value_type", "expected_value"),
        argvalues=[
            ("logging:log_level:default", int, 1),
            ("logging:log_level:default", str, "WARNING"),
            ("logging:log_level:default", list[int], [1, 2, 3]),
        ],
    )
    def test_get_required_value_specifying_type[TField](
        self,
        expected_path: str,
        value_type: type[TField],
        expected_value: TField,
        mocker: MockerFixture,
    ) -> None:
        settings_root_mock = mocker.create_autospec(SettingsRoot, instance=True)
        settings_root_mock.get_required_value.return_value = expected_value
        section = SettingsSection(root=settings_root_mock, path="logging:log_level")

        setting_value = section.get_required_value("default", value_type)

        assert setting_value == expected_value
        settings_root_mock.get_required_value.assert_called_once_with(
            expected_path, value_type
        )
