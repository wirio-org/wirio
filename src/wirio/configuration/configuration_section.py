from typing import Final, overload

from wirio.configuration.configuration_path import ConfigurationPath
from wirio.configuration.configuration_root import ConfigurationRoot


class ConfigurationSection:
    """Represent a section of application configuration values."""

    _root: Final[ConfigurationRoot]
    _path: Final[str]
    _key: str | None

    def __init__(self, root: "ConfigurationRoot", path: str) -> None:
        self._root = root
        self._path = path
        self._key = None

    @property
    def path(self) -> str:
        """Get the full path of this section from the `ConfigurationRoot`."""
        return self._path

    @property
    def key(self) -> str:
        """Get the key this section occupies in its parent."""
        if self._key is None:
            self._key = ConfigurationPath.get_section_key(self._path)

        assert self._key is not None
        return self._key

    @overload
    def get_value(self, /) -> str | None: ...

    @overload
    def get_value[TField](self, value_type: type[TField], /) -> TField | None: ...

    @overload
    def get_value(self, key: str, /) -> str | None: ...

    @overload
    def get_value[TField](
        self, key: str, value_type: type[TField], /
    ) -> TField | None: ...

    def get_value[TField](
        self,
        key_or_value_type_or_none: str | type[TField] | None = None,
        value_type_or_none: type[TField] | None = None,
    ) -> str | None | TField:
        """Get a configuration value. Optionally, validate the configuration value against the specified type."""
        if key_or_value_type_or_none is None:
            return self._root.get_value(self._path)

        if not isinstance(key_or_value_type_or_none, str):
            value_type: type[TField] = key_or_value_type_or_none
            return self._root.get_value(self._path, value_type)

        key = key_or_value_type_or_none
        path = f"{self._path}{ConfigurationPath.KEY_DELIMITER}{key}"

        if value_type_or_none is None:
            return self._root.get_value(path)

        value_type: type[TField] = value_type_or_none
        return self._root.get_value(path, value_type)
