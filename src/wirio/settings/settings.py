from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel, TypeAdapter

from wirio.settings.settings_binder import SettingsBinder

if TYPE_CHECKING:
    from wirio.settings.settings_section import SettingsSection


class Settings(ABC):
    @abstractmethod
    def get_value[TField = str](
        self,
        key: str,
        value_type: type[TField] | type[str] = str,
    ) -> TField | None: ...

    @abstractmethod
    def get_required_value[TField = str](
        self,
        key: str,
        value_type: type[TField] | type[str] = str,
    ) -> TField: ...

    @abstractmethod
    def get_section(self, key: str) -> "SettingsSection": ...

    @abstractmethod
    def get_children(
        self,
        key: str | None = None,
    ) -> list["SettingsSection"]: ...

    def get_model[TModel: BaseModel](self, model_type: type[TModel]) -> TModel:
        """Get a settings model of the specified type. The settings values will be mapped to the model fields by their names."""
        return SettingsBinder.bind_model(self, model_type)

    def _bind_value[TField](self, key: str, value_type: type[TField]) -> TField | None:
        value = self.get_value(key)
        if value is None:
            return None

        return TypeAdapter(value_type).validate_python(value)

    def _bind_required_value[TField](
        self, key: str, value_type: type[TField]
    ) -> TField:
        value = self._bind_value(key, value_type)

        if value is None:
            error_message = f"Missing setting value for key '{key}'"
            raise KeyError(error_message)

        return value
