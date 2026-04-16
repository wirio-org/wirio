import inspect
import typing
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast, overload

from pydantic import BaseModel

from wirio._service_lookup._typed_type import TypedType
from wirio._utils._extra_dependencies import ExtraDependencies
from wirio._utils._python_runtime_path import PythonRuntimePath
from wirio.exceptions import (
    NoKeyedSingletonServiceRegisteredError,
    NoSingletonServiceRegisteredError,
)
from wirio.hosting.host_environment import HostEnvironment
from wirio.service_descriptor import ServiceDescriptor
from wirio.service_lifetime import ServiceLifetime
from wirio.service_provider import ServiceProvider
from wirio.settings.settings_manager import SettingsManager
from wirio.wirio_undefined import WirioUndefined

if TYPE_CHECKING:
    from fastapi import FastAPI

    from wirio.integrations._fastapi_dependency_injection import (
        FastapiDependencyInjection,
    )
    from wirio.integrations._sqlmodel_integration import SqlmodelIntegration
else:
    FastAPI = Any
    FastapiDependencyInjection = Any
    SqlmodelIntegration = Any


class ServiceCollection:
    """Collection of service descriptors provided during configuration."""

    _descriptors: Final[list[ServiceDescriptor]]
    _settings: SettingsManager | None
    _host_environment: Final[HostEnvironment]

    def __init__(self) -> None:
        self._descriptors = []
        self._settings = None
        content_root_path = self._get_content_root_path()
        self._host_environment = HostEnvironment(content_root_path=content_root_path)
        self._validate_on_build = True
        self._populate()

    @property
    def settings(self) -> SettingsManager:
        """Collection of settings providers for the application to compose."""
        if self._settings is None:
            self._settings = self._create_settings()

        return self._settings

    @property
    def environment(self) -> HostEnvironment:
        """Provide information about the hosting environment an application is running."""
        return self._host_environment

    def build_service_provider(
        self, validate_scopes: bool = False, validate_on_build: bool = True
    ) -> ServiceProvider:
        """Create a :class:`ServiceProvider` containing services from the this :class:`ServiceCollection`."""
        return ServiceProvider(
            descriptors=self._descriptors,
            validate_scopes=validate_scopes,
            validate_on_build=validate_on_build,
        )

    @overload
    def add_transient[TService](self, service_type: type[TService], /) -> None: ...

    @overload
    def add_transient[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., AsyncGenerator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_transient[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Generator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_transient[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Awaitable[TService]],
        /,
    ) -> None: ...

    @overload
    def add_transient[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., TService],
        /,
    ) -> None: ...

    @overload
    def add_transient[TService](
        self,
        implementation_factory: Callable[..., AsyncGenerator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_transient[TService](
        self,
        implementation_factory: Callable[..., Generator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_transient[TService](
        self,
        implementation_factory: Callable[..., Awaitable[TService]],
        /,
    ) -> None: ...

    @overload
    def add_transient[TService](
        self,
        implementation_factory: Callable[..., TService],
        /,
    ) -> None: ...

    @overload
    def add_transient[TService](
        self,
        service_type: type[TService],
        implementation_type: type,
        /,
    ) -> None: ...

    def add_transient[TService](
        self,
        service_type_or_implementation_factory: type[TService]
        | Callable[..., AsyncGenerator[TService]]
        | Callable[..., Generator[TService]]
        | Callable[..., Awaitable[TService]]
        | Callable[..., TService],
        implementation_factory_or_implementation_type_or_none: Callable[
            ..., AsyncGenerator[TService]
        ]
        | Callable[..., Generator[TService]]
        | Callable[..., Awaitable[TService]]
        | Callable[..., TService]
        | type
        | None = None,
        /,
    ) -> None:
        """Add a transient service."""
        self._add_from_overloaded_constructor(
            lifetime=ServiceLifetime.TRANSIENT,
            service_type_or_implementation_factory=service_type_or_implementation_factory,
            implementation_factory_or_implementation_type_or_implementation_instance_or_none=implementation_factory_or_implementation_type_or_none,
        )

    @overload
    def add_singleton[TService](self, service_type: type[TService], /) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., AsyncGenerator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Generator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Awaitable[TService]],
        /,
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., TService],
        /,
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        implementation_factory: Callable[..., AsyncGenerator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        implementation_factory: Callable[..., Generator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        implementation_factory: Callable[..., Awaitable[TService]],
        /,
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        implementation_factory: Callable[..., TService],
        /,
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        service_type: type[TService],
        implementation_type: type,
        /,
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        service_type: type[TService],
        implementation_instance: object,
        /,
    ) -> None: ...

    def add_singleton[TService](
        self,
        service_type_or_implementation_factory: type[TService]
        | Callable[..., AsyncGenerator[TService]]
        | Callable[..., Generator[TService]]
        | Callable[..., Awaitable[TService]]
        | Callable[..., TService],
        implementation_factory_or_implementation_type_or_implementation_instance_or_none: Callable[
            ..., Awaitable[TService]
        ]
        | Callable[..., TService]
        | type
        | object
        | None = None,
        /,
    ) -> None:
        """Add a singleton service."""
        self._add_from_overloaded_constructor(
            lifetime=ServiceLifetime.SINGLETON,
            service_type_or_implementation_factory=service_type_or_implementation_factory,
            implementation_factory_or_implementation_type_or_implementation_instance_or_none=implementation_factory_or_implementation_type_or_implementation_instance_or_none,
        )

    @overload
    def add_scoped[TService](self, service_type: type[TService], /) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., AsyncGenerator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Generator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Awaitable[TService]],
        /,
    ) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., TService],
        /,
    ) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        implementation_factory: Callable[..., AsyncGenerator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        implementation_factory: Callable[..., Generator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        implementation_factory: Callable[..., Awaitable[TService]],
        /,
    ) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        implementation_factory: Callable[..., TService],
        /,
    ) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        service_type: type[TService],
        implementation_type: type,
        /,
    ) -> None: ...

    def add_scoped[TService](
        self,
        service_type_or_implementation_factory: type[TService]
        | Callable[..., AsyncGenerator[TService]]
        | Callable[..., Generator[TService]]
        | Callable[..., Awaitable[TService]]
        | Callable[..., TService],
        implementation_factory_or_implementation_type_or_none: Callable[
            ..., AsyncGenerator[TService]
        ]
        | Callable[..., Generator[TService]]
        | Callable[..., Awaitable[TService]]
        | Callable[..., TService]
        | type
        | None = None,
        /,
    ) -> None:
        """Add a scoped service."""
        self._add_from_overloaded_constructor(
            lifetime=ServiceLifetime.SCOPED,
            service_type_or_implementation_factory=service_type_or_implementation_factory,
            implementation_factory_or_implementation_type_or_implementation_instance_or_none=implementation_factory_or_implementation_type_or_none,
        )

    @overload
    def add_keyed_transient[TKey, TService](
        self,
        service_key: TKey | None,  # pyright: ignore[reportInvalidTypeVarUse]
        service_type: type[TService],
        /,
    ) -> None: ...

    @overload
    def add_keyed_transient[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], AsyncGenerator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_transient[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Generator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_transient[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Awaitable[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_transient[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[[TKey | None, *TFactoryParameter], TService],
        /,
    ) -> None: ...

    @overload
    def add_keyed_transient[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], AsyncGenerator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_transient[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Generator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_transient[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Awaitable[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_transient[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[[TKey | None, *TFactoryParameter], TService],
        /,
    ) -> None: ...

    @overload
    def add_keyed_transient[TKey, TService](
        self,
        service_key: TKey | None,  # pyright: ignore[reportInvalidTypeVarUse]
        service_type: type[TService],
        implementation_type: type,
        /,
    ) -> None: ...

    def add_keyed_transient[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type_or_implementation_factory: type[TService]
        | Callable[[TKey | None, *TFactoryParameter], AsyncGenerator[TService]]
        | Callable[[TKey | None, *TFactoryParameter], Generator[TService]]
        | Callable[[TKey | None, *TFactoryParameter], Awaitable[TService]]
        | Callable[[TKey | None, *TFactoryParameter], TService],
        implementation_factory_or_implementation_type_or_none: Callable[
            [TKey | None, *TFactoryParameter], AsyncGenerator[TService]
        ]
        | Callable[[TKey | None, *TFactoryParameter], Generator[TService]]
        | Callable[[TKey | None, *TFactoryParameter], Awaitable[TService]]
        | Callable[[TKey | None, *TFactoryParameter], TService]
        | type
        | None = None,
        /,
    ) -> None:
        """Add a keyed transient service."""
        self._add_from_overloaded_constructor(
            lifetime=ServiceLifetime.TRANSIENT,
            service_type_or_implementation_factory=service_type_or_implementation_factory,
            implementation_factory_or_implementation_type_or_implementation_instance_or_none=implementation_factory_or_implementation_type_or_none,
            service_key=service_key,
        )

    @overload
    def add_keyed_singleton[TKey, TService](
        self,
        service_key: TKey | None,  # pyright: ignore[reportInvalidTypeVarUse]
        service_type: type[TService],
        /,
    ) -> None: ...

    @overload
    def add_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], AsyncGenerator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Generator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Awaitable[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[[TKey | None, *TFactoryParameter], TService],
        /,
    ) -> None: ...

    @overload
    def add_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], AsyncGenerator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Generator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Awaitable[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[[TKey | None, *TFactoryParameter], TService],
        /,
    ) -> None: ...

    @overload
    def add_keyed_singleton[TKey, TService](
        self,
        service_key: TKey | None,  # pyright: ignore[reportInvalidTypeVarUse]
        service_type: type[TService],
        implementation_type: type,
        /,
    ) -> None: ...

    @overload
    def add_keyed_singleton[TKey, TService](
        self,
        service_key: TKey | None,  # pyright: ignore[reportInvalidTypeVarUse]
        service_type: type[TService],
        implementation_instance: object,
        /,
    ) -> None: ...

    def add_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type_or_implementation_factory: type[TService]
        | Callable[[TKey | None, *TFactoryParameter], AsyncGenerator[TService]]
        | Callable[[TKey | None, *TFactoryParameter], Generator[TService]]
        | Callable[[TKey | None, *TFactoryParameter], Awaitable[TService]]
        | Callable[[TKey | None, *TFactoryParameter], TService],
        implementation_factory_or_implementation_type_or_implementation_instance_or_none: Callable[
            [TKey | None, *TFactoryParameter], AsyncGenerator[TService]
        ]
        | Callable[[TKey | None, *TFactoryParameter], Generator[TService]]
        | Callable[[TKey | None, *TFactoryParameter], Awaitable[TService]]
        | Callable[[TKey | None, *TFactoryParameter], TService]
        | type
        | object
        | None = None,
        /,
    ) -> None:
        """Add a keyed singleton service."""
        self._add_from_overloaded_constructor(
            lifetime=ServiceLifetime.SINGLETON,
            service_type_or_implementation_factory=service_type_or_implementation_factory,
            implementation_factory_or_implementation_type_or_implementation_instance_or_none=implementation_factory_or_implementation_type_or_implementation_instance_or_none,
            service_key=service_key,
        )

    @overload
    def add_keyed_scoped[TKey, TService](
        self,
        service_key: TKey | None,  # pyright: ignore[reportInvalidTypeVarUse]
        service_type: type[TService],
        /,
    ) -> None: ...

    @overload
    def add_keyed_scoped[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], AsyncGenerator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_scoped[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Generator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_scoped[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Awaitable[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_scoped[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[[TKey | None, *TFactoryParameter], TService],
        /,
    ) -> None: ...

    @overload
    def add_keyed_scoped[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], AsyncGenerator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_scoped[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Generator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_scoped[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Awaitable[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_keyed_scoped[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[[TKey | None, *TFactoryParameter], TService],
        /,
    ) -> None: ...

    @overload
    def add_keyed_scoped[TKey, TService](
        self,
        service_key: TKey | None,  # pyright: ignore[reportInvalidTypeVarUse]
        service_type: type[TService],
        implementation_type: type,
        /,
    ) -> None: ...

    def add_keyed_scoped[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type_or_implementation_factory: type[TService]
        | Callable[[TKey | None, *TFactoryParameter], AsyncGenerator[TService]]
        | Callable[[TKey | None, *TFactoryParameter], Generator[TService]]
        | Callable[[TKey | None, *TFactoryParameter], Awaitable[TService]]
        | Callable[[TKey | None, *TFactoryParameter], TService],
        implementation_factory_or_implementation_type_or_none: Callable[
            [TKey | None, *TFactoryParameter], AsyncGenerator[TService]
        ]
        | Callable[[TKey | None, *TFactoryParameter], Generator[TService]]
        | Callable[[TKey | None, *TFactoryParameter], Awaitable[TService]]
        | Callable[[TKey | None, *TFactoryParameter], TService]
        | type
        | None = None,
        /,
    ) -> None:
        """Add a keyed scoped service."""
        self._add_from_overloaded_constructor(
            lifetime=ServiceLifetime.SCOPED,
            service_type_or_implementation_factory=service_type_or_implementation_factory,
            implementation_factory_or_implementation_type_or_implementation_instance_or_none=implementation_factory_or_implementation_type_or_none,
            service_key=service_key,
        )

    @overload
    def add_auto_activated_singleton[TService](
        self, service_type: type[TService], /
    ) -> None: ...

    @overload
    def add_auto_activated_singleton[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., AsyncGenerator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_singleton[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Generator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_singleton[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Awaitable[TService]],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_singleton[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., TService],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_singleton[TService](
        self,
        implementation_factory: Callable[..., AsyncGenerator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_singleton[TService](
        self,
        implementation_factory: Callable[..., Generator[TService]],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_singleton[TService](
        self,
        implementation_factory: Callable[..., Awaitable[TService]],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_singleton[TService](
        self,
        implementation_factory: Callable[..., TService],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_singleton[TService](
        self,
        service_type: type[TService],
        implementation_type: type,
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_singleton[TService](
        self,
        service_type: type[TService],
        implementation_instance: object,
        /,
    ) -> None: ...

    def add_auto_activated_singleton[TService](
        self,
        service_type_or_implementation_factory: type[TService]
        | Callable[..., AsyncGenerator[TService]]
        | Callable[..., Generator[TService]]
        | Callable[..., Awaitable[TService]]
        | Callable[..., TService],
        implementation_factory_or_implementation_type_or_implementation_instance_or_none: Callable[
            ..., AsyncGenerator[TService]
        ]
        | Callable[..., Generator[TService]]
        | Callable[..., Awaitable[TService]]
        | Callable[..., TService]
        | type
        | object
        | None = None,
        /,
    ) -> None:
        """Add an auto-activated singleton service.

        An auto-activated singleton service is instantiated when the service provider is built (eagerly), rather than when it's first requested (lazily).
        """
        self._add_from_overloaded_constructor(
            lifetime=ServiceLifetime.SINGLETON,
            service_type_or_implementation_factory=service_type_or_implementation_factory,
            implementation_factory_or_implementation_type_or_implementation_instance_or_none=implementation_factory_or_implementation_type_or_implementation_instance_or_none,
            auto_activate=True,
        )

    @overload
    def add_auto_activated_keyed_singleton[TKey, TService](
        self,
        service_key: TKey | None,  # pyright: ignore[reportInvalidTypeVarUse]
        service_type: type[TService],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], AsyncGenerator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Generator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Awaitable[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type: type[TService],
        implementation_factory: Callable[[TKey | None, *TFactoryParameter], TService],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], AsyncGenerator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Generator[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[
            [TKey | None, *TFactoryParameter], Awaitable[TService]
        ],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        implementation_factory: Callable[[TKey | None, *TFactoryParameter], TService],
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_keyed_singleton[TKey, TService](
        self,
        service_key: TKey | None,  # pyright: ignore[reportInvalidTypeVarUse]
        service_type: type[TService],
        implementation_type: type,
        /,
    ) -> None: ...

    @overload
    def add_auto_activated_keyed_singleton[TKey, TService](
        self,
        service_key: TKey | None,  # pyright: ignore[reportInvalidTypeVarUse]
        service_type: type[TService],
        implementation_instance: object,
        /,
    ) -> None: ...

    def add_auto_activated_keyed_singleton[TKey, TService, *TFactoryParameter](
        self,
        service_key: TKey | None,
        service_type_or_implementation_factory: type[TService]
        | Callable[[TKey | None, *TFactoryParameter], AsyncGenerator[TService]]
        | Callable[[TKey | None, *TFactoryParameter], Generator[TService]]
        | Callable[[TKey | None, *TFactoryParameter], Awaitable[TService]]
        | Callable[[TKey | None, *TFactoryParameter], TService],
        implementation_factory_or_implementation_type_or_implementation_instance_or_none: Callable[
            [TKey | None, *TFactoryParameter], AsyncGenerator[TService]
        ]
        | Callable[[TKey | None, *TFactoryParameter], Generator[TService]]
        | Callable[[TKey | None, *TFactoryParameter], Awaitable[TService]]
        | Callable[[TKey | None, *TFactoryParameter], TService]
        | type
        | object
        | None = None,
        /,
    ) -> None:
        """Add an auto-activated keyed singleton service.

        An auto-activated keyed singleton service is instantiated when the service provider is built (eagerly), rather than when it's first requested (lazily).
        """
        self._add_from_overloaded_constructor(
            lifetime=ServiceLifetime.SINGLETON,
            service_type_or_implementation_factory=service_type_or_implementation_factory,
            implementation_factory_or_implementation_type_or_implementation_instance_or_none=implementation_factory_or_implementation_type_or_implementation_instance_or_none,
            service_key=service_key,
            auto_activate=True,
        )

    def enable_singleton_auto_activation(self, service_type: type) -> None:
        """Mark a registered singleton service as auto-activated.

        An auto-activated singleton service is instantiated when the service provider is built (eagerly), rather than when it's first requested (lazily).
        """
        typed_service_type = TypedType.from_type(service_type)
        is_descriptor_found = False

        for descriptor in self._descriptors:
            if (
                descriptor.service_type == typed_service_type
                and descriptor.lifetime == ServiceLifetime.SINGLETON
            ):
                is_descriptor_found = True
                descriptor.auto_activate = True

        if not is_descriptor_found:
            raise NoSingletonServiceRegisteredError(typed_service_type)

    def enable_keyed_singleton_auto_activation(
        self, service_key: object | None, service_type: type
    ) -> None:
        """Mark a registered keyed singleton service as auto-activated.

        An auto-activated keyed singleton service is instantiated when the service provider is built (eagerly), rather than when it's first requested (lazily).
        """
        typed_service_type = TypedType.from_type(service_type)
        is_descriptor_found = False

        for descriptor in self._descriptors:
            if (
                descriptor.is_keyed_service
                and descriptor.lifetime == ServiceLifetime.SINGLETON
                and descriptor.service_type == typed_service_type
                and descriptor.service_key == service_key
            ):
                is_descriptor_found = True
                descriptor.auto_activate = True

        if not is_descriptor_found:
            raise NoKeyedSingletonServiceRegisteredError(
                service_type=typed_service_type, service_key_type=type(service_key)
            )

    def configure_fastapi(self, app: FastAPI) -> None:
        """Configure the FastAPI application to use dependency injection using the services from this service collection."""
        ExtraDependencies.ensure_fastapi_is_installed()
        global FastapiDependencyInjection  # noqa: PLW0603
        from wirio.integrations._fastapi_dependency_injection import (  # noqa: PLC0415
            FastapiDependencyInjection,
        )

        FastapiDependencyInjection.setup(app, self)

    def add_sqlmodel(self, connection_string: str) -> None:
        """Add asynchronous SQLModel services."""
        self._ensure_sqlmodel_is_installed()
        SqlmodelIntegration.add_async_services(self, connection_string)

    def add_sync_sqlmodel(self, connection_string: str) -> None:
        """Add synchronous SQLModel services."""
        self._ensure_sqlmodel_is_installed()
        SqlmodelIntegration.add_sync_services(self, connection_string)

    def add_settings[TModel: BaseModel](
        self, model_type: type[TModel], key: str | None = None
    ) -> None:
        """Add a settings model as a singleton service."""
        settings = self.settings if key is None else self.settings.get_section(key)
        settings_instance = settings.get_model(model_type)
        self.add_singleton(model_type, settings_instance)

    def _add_from_overloaded_constructor[TService](
        self,
        lifetime: ServiceLifetime,
        service_type_or_implementation_factory: type[TService]
        | Callable[..., AsyncGenerator[TService]]
        | Callable[..., Generator[TService]]
        | Callable[..., Awaitable[TService]]
        | Callable[..., TService],
        implementation_factory_or_implementation_type_or_implementation_instance_or_none: Callable[
            ..., AsyncGenerator[TService]
        ]
        | Callable[..., Generator[TService]]
        | Callable[..., Awaitable[TService]]
        | Callable[..., TService]
        | type
        | object
        | None = None,
        service_key: object | None = WirioUndefined.INSTANCE,
        auto_activate: bool = False,
    ) -> None:
        service_type_to_add: type[TService] | None = None
        implementation_factory_to_add: (
            Callable[..., AsyncGenerator[TService]]
            | Callable[..., Generator[TService]]
            | Callable[..., Awaitable[TService]]
            | Callable[..., TService]
            | None
        ) = None
        implementation_type_to_add: type | None = None
        implementation_instance_to_add: object | None = None

        if self._is_service_type(service_type_or_implementation_factory):
            service_type_to_add = cast(
                "type[TService]", service_type_or_implementation_factory
            )

        if isinstance(
            implementation_factory_or_implementation_type_or_implementation_instance_or_none,
            type,
        ):
            implementation_type_to_add = implementation_factory_or_implementation_type_or_implementation_instance_or_none
        elif (
            service_type_to_add is not None
            and implementation_factory_or_implementation_type_or_implementation_instance_or_none
            is not None
        ):
            if callable(
                implementation_factory_or_implementation_type_or_implementation_instance_or_none
            ):
                implementation_factory_to_add = cast(
                    "Callable[..., AsyncGenerator[TService]] | Callable[..., Generator[TService]] | Callable[..., Awaitable[TService]] | Callable[..., TService]",
                    implementation_factory_or_implementation_type_or_implementation_instance_or_none,
                )
            else:
                implementation_instance_to_add = implementation_factory_or_implementation_type_or_implementation_instance_or_none
        elif (
            service_type_to_add is None
            and implementation_factory_or_implementation_type_or_implementation_instance_or_none
            is None
        ):
            implementation_factory_to_add = service_type_or_implementation_factory

        self._add(
            lifetime=lifetime,
            service_type=service_type_to_add,
            implementation_factory=implementation_factory_to_add,
            implementation_type=implementation_type_to_add,
            implementation_instance=implementation_instance_to_add,
            service_key=service_key,
            auto_activate=auto_activate,
        )

    def _add[TService](  # noqa: C901, PLR0912, PLR0913
        self,
        lifetime: ServiceLifetime,
        service_type: type[TService] | None,
        implementation_factory: Callable[..., AsyncGenerator[TService]]
        | Callable[..., Generator[TService]]
        | Callable[..., Awaitable[TService]]
        | Callable[..., TService]
        | None,
        implementation_type: type | None,
        implementation_instance: object | None,
        service_key: object | None,
        auto_activate: bool,
    ) -> None:
        provided_service_type = self._get_provided_service_type(
            service_type, implementation_factory
        )
        is_service_key_provided = service_key is not WirioUndefined.INSTANCE
        service_key_to_add = service_key if is_service_key_provided else None
        service_descriptor: ServiceDescriptor | None = None

        if implementation_instance is not None:
            service_descriptor = ServiceDescriptor.from_implementation_instance(
                service_type=provided_service_type,
                implementation_instance=implementation_instance,
                service_key=service_key_to_add,
                lifetime=lifetime,
                auto_activate=auto_activate,
            )
        elif implementation_factory is None:
            if implementation_type is not None and (
                not issubclass(implementation_type, provided_service_type)
                or provided_service_type == implementation_type
            ):
                error_message = (
                    f"{implementation_type} is not subclass of {provided_service_type}"
                )
                raise TypeError(error_message)

            implementation_type_to_add = (
                implementation_type
                if implementation_type is not None
                else provided_service_type
            )
            service_descriptor = ServiceDescriptor.from_implementation_type(
                service_type=provided_service_type,
                implementation_type=implementation_type_to_add,
                service_key=service_key_to_add,
                lifetime=lifetime,
                auto_activate=auto_activate,
            )
        elif inspect.isasyncgenfunction(implementation_factory):
            if is_service_key_provided:
                service_descriptor = (
                    ServiceDescriptor.from_keyed_async_generator_implementation_factory(
                        service_type=provided_service_type,
                        implementation_factory=implementation_factory,
                        service_key=service_key_to_add,
                        lifetime=lifetime,
                        auto_activate=auto_activate,
                    )
                )
            else:
                service_descriptor = (
                    ServiceDescriptor.from_async_generator_implementation_factory(
                        service_type=provided_service_type,
                        implementation_factory=implementation_factory,
                        lifetime=lifetime,
                        auto_activate=auto_activate,
                    )
                )
        elif inspect.isgeneratorfunction(implementation_factory):
            if is_service_key_provided:
                service_descriptor = (
                    ServiceDescriptor.from_keyed_sync_generator_implementation_factory(
                        service_type=provided_service_type,
                        implementation_factory=implementation_factory,
                        service_key=service_key_to_add,
                        lifetime=lifetime,
                        auto_activate=auto_activate,
                    )
                )
            else:
                service_descriptor = (
                    ServiceDescriptor.from_sync_generator_implementation_factory(
                        service_type=provided_service_type,
                        implementation_factory=implementation_factory,
                        lifetime=lifetime,
                        auto_activate=auto_activate,
                    )
                )
        elif inspect.iscoroutinefunction(implementation_factory):
            if is_service_key_provided:
                service_descriptor = (
                    ServiceDescriptor.from_keyed_async_implementation_factory(
                        service_type=provided_service_type,
                        implementation_factory=implementation_factory,
                        service_key=service_key_to_add,
                        lifetime=lifetime,
                        auto_activate=auto_activate,
                    )
                )
            else:
                service_descriptor = (
                    ServiceDescriptor.from_async_implementation_factory(
                        service_type=provided_service_type,
                        implementation_factory=implementation_factory,
                        lifetime=lifetime,
                        auto_activate=auto_activate,
                    )
                )
        else:  # noqa: PLR5501
            if is_service_key_provided:
                service_descriptor = (
                    ServiceDescriptor.from_keyed_sync_implementation_factory(
                        service_type=provided_service_type,
                        implementation_factory=implementation_factory,
                        service_key=service_key_to_add,
                        lifetime=lifetime,
                        auto_activate=auto_activate,
                    )
                )
            else:
                service_descriptor = ServiceDescriptor.from_sync_implementation_factory(
                    service_type=provided_service_type,
                    implementation_factory=implementation_factory,
                    lifetime=lifetime,
                    auto_activate=auto_activate,
                )

        assert service_descriptor is not None
        self._descriptors.append(service_descriptor)

    def _is_service_type(self, value: object) -> bool:
        if isinstance(value, type):
            return True

        origin = typing.get_origin(value)
        return isinstance(origin, type)

    def _get_provided_service_type[TService](
        self,
        service_type: type[TService] | None = None,
        implementation_factory: Callable[..., Awaitable[TService]]
        | Callable[..., TService]
        | Callable[..., Generator[TService]]
        | Callable[..., AsyncGenerator[TService]]
        | None = None,
    ) -> type:
        if service_type is not None:
            return service_type

        assert implementation_factory is not None

        type_hints: dict[str, type] = typing.get_type_hints(implementation_factory)
        return_type = type_hints.get("return")

        if return_type is None:
            error_message = "Missing return type hints from 'implementation_factory'"
            raise ValueError(error_message)

        return_type_origin = typing.get_origin(return_type)

        if return_type_origin in (Generator, AsyncGenerator):
            return_type_arguments = typing.get_args(return_type)
            return return_type_arguments[0]

        return return_type

    def _ensure_sqlmodel_is_installed(self) -> None:
        ExtraDependencies.ensure_sqlmodel_is_installed()
        global SqlmodelIntegration  # noqa: PLW0603
        from wirio.integrations._sqlmodel_integration import (  # noqa: PLC0415
            SqlmodelIntegration,
        )

    def _create_settings(self) -> SettingsManager:
        return SettingsManager(
            content_root_path=self._host_environment.content_root_path,
            add_default_providers=True,
        )

    def _get_content_root_path(self) -> str:
        current_frame = inspect.currentframe()

        if current_frame is None:
            return str(Path.cwd().expanduser().resolve())

        try:
            current_working_directory = Path.cwd().expanduser().resolve()
            package_root = Path(__file__).resolve().parent
            frame_filename = ""

            found_only_runtime_external_frames = False
            stack_frame = current_frame.f_back

            while stack_frame is not None:
                notebook_path = stack_frame.f_globals.get("__vsc_ipynb_file__")

                if isinstance(notebook_path, str):
                    resolved_notebook_path = Path(notebook_path).expanduser().resolve()

                    if resolved_notebook_path.exists():
                        return str(resolved_notebook_path.parent)

                current_frame_filename = stack_frame.f_code.co_filename
                current_frame_path = Path(current_frame_filename)

                if not current_frame_path.exists():
                    stack_frame = stack_frame.f_back
                    continue

                resolved_current_frame_path = current_frame_path.resolve()

                if package_root not in resolved_current_frame_path.parents:
                    if PythonRuntimePath.is_python_runtime_path(
                        resolved_current_frame_path
                    ):
                        found_only_runtime_external_frames = True
                        stack_frame = stack_frame.f_back
                        continue

                    return str(resolved_current_frame_path.parent)

                frame_filename = current_frame_filename
                stack_frame = stack_frame.f_back

            if frame_filename == "":
                return str(current_working_directory)

            if found_only_runtime_external_frames:
                return str(current_working_directory)

            return str(Path(frame_filename).parent.resolve())
        finally:
            del current_frame

    def _populate(self) -> None:
        self.add_singleton(HostEnvironment, self._host_environment)

    def __iter__(self) -> Iterator[ServiceDescriptor]:
        return iter(self._descriptors)
