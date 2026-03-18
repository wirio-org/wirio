from typing import Any, Final, cast

from wirio.settings.settings_path import SettingsPath


class JsonSettingsFileParser:
    _data: Final[dict[str, str | None]]
    _case_folded_data: Final[dict[str, str]]
    _paths: Final[list[str]]

    def __init__(self) -> None:
        self._data = {}
        self._case_folded_data = {}
        self._paths = []

    def parse_json(
        self,
        json_data: dict[str, Any],
    ) -> dict[str, str | None]:
        self._visit_object_element(json_data)
        return self._data

    def _visit_object_element(self, object_: dict[str, Any]) -> None:
        is_empty = True

        for key, value in object_.items():
            is_empty = False
            self._enter_context(key)
            self._visit_value(value)
            self._exit_context()

        self._set_null_if_element_is_empty(is_empty)

    def _visit_value(
        self,
        value: Any,  # noqa: ANN401
    ) -> None:
        if isinstance(value, dict):
            self._visit_object_element(cast("dict[str, Any]", value))
            return

        if isinstance(value, list):
            self._visit_array_element(cast("list[Any]", value))
            return

        key = self._paths[-1]
        case_folded_key = key.casefold()

        if case_folded_key in self._case_folded_data:
            error_message = f"A duplicate key '{key}' was found"
            raise RuntimeError(error_message)

        self._case_folded_data[case_folded_key] = key

        if value is None:
            self._data[key] = None
        else:
            self._data[key] = str(value)

    def _visit_array_element(self, list_: list[Any]) -> None:
        index = 0

        for item in list_:
            self._enter_context(str(index))
            self._visit_value(item)
            self._exit_context()
            index += 1

        is_empty = index == 0
        self._set_empty_if_element_is_empty(is_empty)

    def _set_null_if_element_is_empty(self, is_empty: bool) -> None:
        if is_empty and len(self._paths) > 0:
            self._data[self._paths[-1]] = None

    def _set_empty_if_element_is_empty(self, is_empty: bool) -> None:
        if is_empty and len(self._paths) > 0:
            self._data[self._paths[-1]] = ""

    def _enter_context(self, context: str) -> None:
        new_path = (
            f"{self._paths[-1]}{SettingsPath.KEY_DELIMITER}{context}"
            if len(self._paths) > 0
            else context
        )
        self._paths.append(new_path)

    def _exit_context(self) -> None:
        self._paths.pop()
