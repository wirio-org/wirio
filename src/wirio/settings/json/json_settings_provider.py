import json
from pathlib import Path
from typing import Any, Final, cast, final, override

from wirio.settings.json.json_settings_file_parser import (
    JsonSettingsFileParser,
)
from wirio.settings.settings_provider import SettingsProvider


@final
class JsonSettingsProvider(SettingsProvider):
    _path: Final[Path]
    _optional: Final[bool]

    def __init__(self, path: Path, optional: bool) -> None:
        super().__init__()
        self._path = path
        self._optional = optional

    @override
    async def load(self) -> None:
        if not self._path.exists():
            if self._optional:
                self._data = {}
                await super().load()
                return

            error_message = f"Setting file '{self._path}' was not found"
            raise FileNotFoundError(error_message)

        json_data: Any = {}

        with self._path.open(encoding="utf-8") as file:
            json_data = json.load(file)

        if not isinstance(json_data, dict):
            error_message = "Could not parse the JSON file"
            raise RuntimeError(error_message)  # noqa: TRY004

        self._data = JsonSettingsFileParser().parse_json(
            cast("dict[str, Any]", json_data)
        )
        await super().load()
