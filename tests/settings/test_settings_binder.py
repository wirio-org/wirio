import re
from collections.abc import Sequence
from typing import final, override

import pytest
from pydantic import BaseModel, Field

from wirio.settings.settings_binder import SettingsBinder
from wirio.settings.settings_builder import SettingsBuilder
from wirio.settings.settings_manager import SettingsManager
from wirio.settings.settings_provider import SettingsProvider
from wirio.settings.settings_source import SettingsSource


@final
class _DictionarySettingsProvider(SettingsProvider):
    _values: dict[str, str | None]

    def __init__(self, values: dict[str, str | None]) -> None:
        super().__init__()
        self._values = values

    @override
    async def load(self) -> None:
        self._data = self._values
        await super().load()


@final
class _DictionarySettingsSource(SettingsSource):
    _values: dict[str, str | None]

    def __init__(self, values: dict[str, str | None]) -> None:
        self._values = values

    @override
    def build(self, builder: SettingsBuilder) -> SettingsProvider:
        return _DictionarySettingsProvider(self._values)


class TestSettingsBinder:
    def test_bind_nested_list_item_using_default_when_field_is_missing(
        self,
    ) -> None:
        expected_retries = 3

        class Server(BaseModel):
            name: str
            retries: int = Field(expected_retries)

        class Settings(BaseModel):
            servers: list[Server]

        settings_manager = SettingsManager(content_root_path="", add_default_providers=False)
        settings_manager.add(_DictionarySettingsSource({"servers:0:name": "api"}))

        settings = settings_manager.get_model(Settings)

        assert len(settings.servers) == 1
        assert settings.servers[0].name == "api"
        assert settings.servers[0].retries == expected_retries

    def test_get_empty_string(self) -> None:
        key = "ports"
        settings_manager = SettingsManager(content_root_path="", add_default_providers=False)
        settings_manager.add(_DictionarySettingsSource({key: ""}))

        value = settings_manager.get_value(key, str)
        required_value = settings_manager.get_required_value(key, str)

        assert value == ""
        assert required_value == ""

    def test_fail_when_getting_model_if_some_required_field_is_missing(self) -> None:
        class SubSettings(BaseModel):
            required_subfield_1: str
            required_subfield_2: int

        class RootSettings(BaseModel):
            required_field_1: str
            required_field_2: int
            subsettings: SubSettings | None = None

        settings_manager = SettingsManager(content_root_path="", add_default_providers=False)
        settings_manager.add(_DictionarySettingsSource({"required_field_1": "value"}))

        with pytest.raises(
            KeyError,
            match=re.escape("Missing setting value for key 'required_field_2'"),
        ):
            settings_manager.get_model(RootSettings)

        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "required_field_1": "value",
                    "required_field_2": "1",
                    "subsettings:required_subfield_1": "value",
                }
            )
        )

        with pytest.raises(
            KeyError,
            match=re.escape("Missing setting value for key 'required_subfield_2'"),
        ):
            settings_manager.get_model(RootSettings)

    def test_return_none_when_submodel_is_not_found(self) -> None:
        class ServiceSettings(BaseModel):
            name: str
            port: int

        class Settings(BaseModel):
            service_1: ServiceSettings | None = None
            service_2: ServiceSettings | None

        settings_manager = SettingsManager(content_root_path="", add_default_providers=False)
        settings_manager.add(_DictionarySettingsSource({}))

        settings = settings_manager.get_model(Settings)

        assert settings.service_1 is None
        assert settings.service_2 is None

    @pytest.mark.parametrize(
        argnames=("field_type", "settings_values", "expected_values"),
        argvalues=[
            (int, {"ports:0": "8080", "ports:1": "8081"}, [8080, 8081]),
            (str, {"ports:0": "8080", "ports:1": "8081"}, ["8080", "8081"]),
        ],
    )
    def test_get_sequence[TField](
        self,
        field_type: type[TField],
        settings_values: dict[str, str | None],
        expected_values: list[TField],
    ) -> None:
        class IntSettings(BaseModel):
            ports: list[int]

        class StringSettings(BaseModel):
            ports: list[str]

        model_class = IntSettings if field_type is int else StringSettings
        settings_manager = SettingsManager(content_root_path="", add_default_providers=False)
        settings_manager.add(_DictionarySettingsSource(settings_values))

        settings = settings_manager.get_model(model_class)
        first_value = settings_manager.get_required_value("ports:0", field_type)
        missing_value = settings_manager.get_value("ports:2", field_type)

        assert settings.ports == expected_values
        assert isinstance(first_value, field_type)
        assert first_value == expected_values[0]
        assert missing_value is None

    @pytest.mark.parametrize(
        argnames="field_type",
        argvalues=[
            Sequence[int],
            Sequence[str],
            list[int],
            list[str],
        ],
        ids=["int_sequence", "str_sequence", "int_list", "str_list"],
    )
    def test_get_empty_sequence[TField](self, field_type: type[TField]) -> None:
        key = "ports"
        settings_manager = SettingsManager(content_root_path="", add_default_providers=False)
        settings_manager.add(_DictionarySettingsSource({key: ""}))

        value = settings_manager.get_value(key, field_type)
        required_value = settings_manager.get_required_value(key, field_type)

        assert value == []
        assert required_value == []

    def test_get_model_sequence(self) -> None:
        expected_server_settings = 2
        expected_api_retries = 3
        expected_worker_retries = 5

        class Server(BaseModel):
            name: str
            retries: int

        class Settings(BaseModel):
            servers: list[Server]

        settings_manager = SettingsManager(content_root_path="", add_default_providers=False)
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "servers:0:name": "api",
                    "servers:0:retries": str(expected_api_retries),
                    "servers:1:name": "worker",
                    "servers:1:retries": str(expected_worker_retries),
                }
            )
        )

        settings = settings_manager.get_model(Settings)
        first_server_name = settings_manager.get_required_value("servers:0:name")
        second_server_retries = settings_manager.get_value("servers:1:retries", int)

        assert len(settings.servers) == expected_server_settings
        assert settings.servers[0].name == "api"
        assert settings.servers[0].retries == expected_api_retries
        assert settings.servers[1].name == "worker"
        assert settings.servers[1].retries == expected_worker_retries
        assert first_server_name == "api"
        assert second_server_retries == expected_worker_retries

    @pytest.mark.parametrize(
        argnames=("field_type", "settings_values", "expected_values"),
        argvalues=[
            (
                int,
                {"ports:http": "8080", "ports:https": "8443"},
                {"http": 8080, "https": 8443},
            ),
            (
                str,
                {"ports:http": "8080", "ports:https": "8443"},
                {"http": "8080", "https": "8443"},
            ),
        ],
    )
    def test_get_dictionary[TField](
        self,
        field_type: type[TField],
        settings_values: dict[str, str | None],
        expected_values: dict[str, TField],
    ) -> None:
        class IntSettings(BaseModel):
            ports: dict[str, int]

        class StringSettings(BaseModel):
            ports: dict[str, str]

        model_class = IntSettings if field_type is int else StringSettings
        settings_manager = SettingsManager(content_root_path="", add_default_providers=False)
        settings_manager.add(_DictionarySettingsSource(settings_values))

        settings = settings_manager.get_model(model_class)
        http_value = settings_manager.get_required_value("ports:http", field_type)
        missing_value = settings_manager.get_value("ports:ftp", field_type)

        assert isinstance(settings, BaseModel)
        assert isinstance(settings.ports, dict)
        assert settings.ports == expected_values
        assert http_value == expected_values["http"]
        assert missing_value is None

    def test_get_model_dictionary(self) -> None:
        expected_service_settings = 2
        expected_api_retries = 3
        expected_worker_retries = 5

        class Service(BaseModel):
            url: str
            retries: int

        class Settings(BaseModel):
            services: dict[str, Service]

        settings_manager = SettingsManager(content_root_path="", add_default_providers=False)
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "services:api:url": "https://api.example.com",
                    "services:api:retries": str(expected_api_retries),
                    "services:worker:url": "https://worker.example.com",
                    "services:worker:retries": str(expected_worker_retries),
                }
            )
        )

        settings = settings_manager.get_model(Settings)
        api_url = settings_manager.get_required_value("services:api:url")
        worker_retries = settings_manager.get_value("services:worker:retries", int)

        assert len(settings.services) == expected_service_settings
        assert settings.services["api"].url == "https://api.example.com"
        assert settings.services["api"].retries == expected_api_retries
        assert settings.services["worker"].url == "https://worker.example.com"
        assert settings.services["worker"].retries == expected_worker_retries
        assert api_url == "https://api.example.com"
        assert worker_retries == expected_worker_retries

    def test_skip_section_when_direct_value_is_missing(self) -> None:
        class Settings(BaseModel):
            ports: dict[str, int]

        expected_ports = {"https": 8443}
        settings_manager = SettingsManager(content_root_path="", add_default_providers=False)
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "ports:http:metadata": "ignored",
                    "ports:https": "8443",
                }
            )
        )

        settings = settings_manager.get_model(Settings)

        assert settings.ports == expected_ports

    def test_set_dictionary_to_none_when_key_has_not_direct_values(self) -> None:
        class Settings(BaseModel):
            ports: dict[str, int] | None = None

        settings_manager = SettingsManager(content_root_path="", add_default_providers=False)
        settings_manager.add(
            _DictionarySettingsSource(
                {
                    "ports:http:metadata": "ignored",
                    "ports:https:metadata": "ignored",
                    "ports:ftp:0": "ignored",
                }
            )
        )

        settings = settings_manager.get_model(Settings)

        assert settings.ports is None

    def test_set_dictionary_to_none_section_is_missing(self) -> None:
        class Settings(BaseModel):
            ports: dict[str, int] | None = None

        settings_manager = SettingsManager(content_root_path="", add_default_providers=False)
        settings_manager.add(_DictionarySettingsSource({}))

        settings = settings_manager.get_model(Settings)

        assert settings.ports is None

    def test_return_parent_when_child_key_is_empty_when_joining_keys(self) -> None:
        parent_key = "ports"

        result = SettingsBinder._join_key(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            parent=parent_key, child=""
        )

        assert result == parent_key

    def test_fail_when_getting_model_with_union_of_several_types(self) -> None:
        class Settings(BaseModel):
            port: int | str

        settings_manager = SettingsManager(content_root_path="", add_default_providers=False)
        settings_manager.add(_DictionarySettingsSource({"port": "8080"}))

        with pytest.raises(
            RuntimeError,
            match=re.escape(
                "A field type annotation cannot be resolved because it is a union of multiple types. Only unions of a single type with None are supported to indicate optional fields"
            ),
        ):
            settings_manager.get_model(Settings)

    def test_get_empty_sequence_when_empty_string_found(self) -> None:
        class Settings(BaseModel):
            ports: list[int]

        settings_manager = SettingsManager(content_root_path="", add_default_providers=False)
        settings_manager.add(_DictionarySettingsSource({"ports": ""}))

        settings = settings_manager.get_model(Settings)

        assert settings.ports == []
