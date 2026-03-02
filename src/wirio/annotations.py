import contextlib
import importlib
from dataclasses import dataclass
from typing import final, overload

from wirio.abstractions.service_key_lookup_mode import (
    ServiceKeyLookupMode,
)
from wirio.wirio_undefined import WirioUndefined


class Injectable:
    pass


@final
class FromServicesInjectable(Injectable):
    pass


@final
class ServiceKeyInjectable(Injectable):
    pass


@final
@dataclass(frozen=True)
class FromKeyedServicesInjectable(Injectable):
    key: object | None
    lookup_mode: ServiceKeyLookupMode


def _return_injectable[TInjectable: Injectable](
    injectable: type[TInjectable],
) -> TInjectable:
    def _dependency() -> TInjectable:
        return injectable()

    _dependency.__is_wirio_depends__ = True  # pyright: ignore[reportFunctionMemberAccess] # ty: ignore[unresolved-attribute]

    # In case of using FastAPI, wrap the injectable in a Depends
    with contextlib.suppress(ModuleNotFoundError):
        return importlib.import_module("fastapi").Depends(_dependency, use_cache=False)

    return _dependency()


def FromServices() -> Injectable:  # noqa: N802
    """Specify that a parameter should be bound using the requested service."""
    return _return_injectable(FromServicesInjectable)


def ServiceKey() -> ServiceKeyInjectable:  # noqa: N802
    """Specify the parameter to inject the key that was used for registration or resolution."""
    return _return_injectable(ServiceKeyInjectable)


@overload
def FromKeyedServices() -> FromKeyedServicesInjectable: ...


@overload
def FromKeyedServices(key: object | None) -> FromKeyedServicesInjectable: ...


def FromKeyedServices(  # noqa: N802
    key: object | None = WirioUndefined.INSTANCE,
) -> FromKeyedServicesInjectable:
    """Indicate that the parameter should be bound using the keyed service registered with the specified key."""

    def _dependency() -> FromKeyedServicesInjectable:
        is_key_not_provided = isinstance(key, WirioUndefined)

        if is_key_not_provided:
            return FromKeyedServicesInjectable(
                key=None, lookup_mode=ServiceKeyLookupMode.INHERIT_KEY
            )

        lookup_mode = (
            ServiceKeyLookupMode.NULL_KEY
            if key is None
            else ServiceKeyLookupMode.EXPLICIT_KEY
        )
        return FromKeyedServicesInjectable(key=key, lookup_mode=lookup_mode)

    _dependency.__is_wirio_depends__ = True  # pyright: ignore[reportFunctionMemberAccess] # ty: ignore[unresolved-attribute]

    # In case of using FastAPI, wrap the injectable in a Depends
    with contextlib.suppress(ModuleNotFoundError):
        return importlib.import_module("fastapi").Depends(_dependency, use_cache=False)

    return _dependency()


__all__ = [
    "FromKeyedServices",
    "FromServices",
    "ServiceKey",
]
