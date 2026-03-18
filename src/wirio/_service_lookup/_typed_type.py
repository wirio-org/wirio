import typing
from collections.abc import (
    Hashable,
    Mapping,
    Sequence,
)
from typing import Any, Final, final, override


@final
class TypedType(Hashable):
    """Version of :class:`type` that takes into account generic parameters."""

    _annotation: Final[Any]
    _origin: Final[Any]
    _args: Final[tuple[Any, ...]]

    def __init__(
        self,
        annotation: Any,  # noqa: ANN401
    ) -> None:
        self._annotation = annotation
        origin = typing.get_origin(annotation)
        has_generics = origin is not None

        if not has_generics:
            self._origin = annotation
            self._args = ()
            return

        self._origin = origin
        self._args = typing.get_args(annotation)

    @classmethod
    def from_type(cls, type_: type) -> "TypedType":
        return cls(type_)

    @classmethod
    def from_instance(cls, instance: object) -> "TypedType":
        instance_type = getattr(instance, "__orig_class__", None)

        if instance_type is None:
            error_message = "The instance does not retain type hint information because it has no generics"
            raise ValueError(error_message)

        return cls(instance_type)

    @property
    def annotation(
        self,
    ) -> Any:  # noqa: ANN401
        """Get the original type annotation from which this `TypedType` was created."""
        return self._annotation

    @property
    def args(self) -> tuple[Any, ...]:
        """Get the generic type arguments for this type."""
        return self._args

    @property
    def is_generic_type(self) -> bool:
        """Get a value indicating whether the current type is a generic type."""
        return len(self._args) > 0

    @property
    def is_mapping(self) -> bool:
        """Get a value indicating whether the current type is a mapping type."""
        return issubclass(self._origin, Mapping)

    @property
    def is_sequence(self) -> bool:
        """Get a value indicating whether the current type is a collection type."""
        if self._origin in [str, bytes]:
            return False

        return issubclass(self._origin, Sequence)

    def to_type(self) -> type:
        return self._origin

    def invoke(self, parameter_values: list[object]) -> object:
        has_parameters = len(parameter_values) > 0
        has_generics = len(self._args) > 0

        if not has_parameters:
            if not has_generics:
                return self._origin()

            return self._origin[*self._args]()  # pyright: ignore[reportIndexIssue, reportUnknownVariableType]

        if not has_generics:
            return self._origin(*parameter_values)

        return self._origin[*self._args](*parameter_values)  # pyright: ignore[reportIndexIssue, reportUnknownVariableType]

    def get_generic_type_definition(self) -> "TypedType":
        """Return a `TypedType` object that represents a generic type definition from which the current generic type can be constructed."""
        if not self.is_generic_type:
            error_message = "The current type is not a constructed generic type"
            raise RuntimeError(error_message)

        return TypedType(self._origin)

    def generic_type_arguments(self) -> list["TypedType"]:
        """Get an list of the generic type arguments for this type."""
        return [TypedType(argument) for argument in self._args]

    def _create_representation(
        self,
        origin: Any,  # noqa: ANN401
        args: tuple[Any, ...],
    ) -> str:
        args_representation = ""

        if len(args) > 0:
            for arg in args:
                arg_origin = typing.get_origin(arg)
                arg_args = typing.get_args(arg)
                has_generics = arg_origin is not None

                if has_generics:
                    args_representation += self._create_representation(
                        arg_origin, arg_args
                    )
                else:
                    args_representation += f"{arg.__module__}.{arg.__qualname__}"

                if arg != args[-1]:
                    args_representation += ", "

        if len(args_representation) > 0:
            args_representation = f"[{args_representation}]"

        return f"{origin.__module__}.{origin.__qualname__}{args_representation}"

    @override
    def __repr__(self) -> str:
        return self._create_representation(self._origin, self._args)

    @override
    def __hash__(self) -> int:
        return hash(self._origin) ^ hash(self._args)

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, TypedType):
            return NotImplemented

        return self._origin == value._origin and self._args == value._args
