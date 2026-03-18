from typing import Final, cast, final, override

from wirio.settings.settings import Settings
from wirio.settings.settings_path import SettingsPath
from wirio.settings.settings_root import SettingsRoot


@final
class SettingsSection(Settings):
    """Represent a section of application settings values."""

    _root: Final[SettingsRoot]
    _path: Final[str]
    _key: str | None

    def __init__(self, root: "SettingsRoot", path: str) -> None:
        self._root = root
        self._path = path
        self._key = None

    @property
    def path(self) -> str:
        """Get the full path of this section from the `SettingsRoot`."""
        return self._path

    @property
    def key(self) -> str:
        """Get the key this section occupies in its parent."""
        if self._key is None:
            self._key = SettingsPath.get_section_key(self._path)

        assert self._key is not None
        return self._key

    @override
    def get_section(self, key: str) -> "SettingsSection":
        """Get a child settings section for the specified key."""
        child_path = f"{self._path}{SettingsPath.KEY_DELIMITER}{key}"
        return self._root.get_section(child_path)

    @override
    def get_children(self, key: str | None = None) -> list["SettingsSection"]:
        path = self._path

        if key is not None:
            path = f"{path}{SettingsPath.KEY_DELIMITER}{key}"

        return self._root.get_children(path)

    @override
    def get_value[TField = str](
        self,
        key: str,
        value_type: type[TField] | type[str] = str,
    ) -> TField | None:
        child_path = f"{self._path}{SettingsPath.KEY_DELIMITER}{key}"
        typed_value_type = cast("type[TField]", value_type)
        return self._root.get_value(child_path, typed_value_type)

    @override
    def get_required_value[TField = str](
        self,
        key: str,
        value_type: type[TField] | type[str] = str,
    ) -> TField:
        child_path = f"{self._path}{SettingsPath.KEY_DELIMITER}{key}"
        typed_value_type = cast("type[TField]", value_type)
        return self._root.get_required_value(child_path, typed_value_type)
