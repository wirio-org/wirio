import sys
from collections.abc import Mapping, Sequence
from types import UnionType
from typing import Any, cast

import pytest

from tests.utils.services import ServiceWithNoDependencies
from wirio._service_lookup._typed_type import TypedType


class CustomClass:
    pass


class CustomClassWithGeneric1[T]:
    pass


class CustomClassWithGeneric2[T]:
    pass


class CustomClassWithGeneric3[T]:
    pass


class CustomClassWithGenerics1[T1, T2]:
    pass


class CustomClassWithGenerics2[T1, T2]:
    pass


class CustomClassWithOptionalGeneric1[T = None]:
    pass


class CustomClassWithOptionalGeneric2[T = None]:
    pass


class CustomClassWithGenericAndOptionalGeneric1[T1, T2 = None]:
    pass


class CustomClassWithGenericAndConstructorParameters[T]:
    def __init__(self, parameter_1: T, parameter_2: T) -> None:
        self.parameter_1 = parameter_1
        self.parameter_2 = parameter_2


class TestTypedType:
    @pytest.mark.parametrize(
        argnames=(
            "type_",
            "expected_representation_python_less_than_3_14",
            "expected_representation_python_greater_than_or_equal_3_14",
        ),
        argvalues=[
            (int, "builtins.int", "builtins.int"),
            (list[int], "builtins.list[builtins.int]", "builtins.list[builtins.int]"),
            (
                CustomClass,
                "tests._service_lookup.test_typed_type.CustomClass",
                "tests._service_lookup.test_typed_type.CustomClass",
            ),
            (
                CustomClassWithGeneric1[int],
                "tests._service_lookup.test_typed_type.CustomClassWithGeneric1[builtins.int]",
                "tests._service_lookup.test_typed_type.CustomClassWithGeneric1[builtins.int]",
            ),
            (
                CustomClassWithGeneric2[CustomClassWithGeneric2[int]],
                "tests._service_lookup.test_typed_type.CustomClassWithGeneric2[tests._service_lookup.test_typed_type.CustomClassWithGeneric2[builtins.int]]",
                "tests._service_lookup.test_typed_type.CustomClassWithGeneric2[tests._service_lookup.test_typed_type.CustomClassWithGeneric2[builtins.int]]",
            ),
            (
                CustomClassWithGenerics1[int, str],
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics1[builtins.int, builtins.str]",
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics1[builtins.int, builtins.str]",
            ),
            (
                int | str,
                "types.UnionType[builtins.int, builtins.str]",
                "typing.Union[builtins.int, builtins.str]",
            ),
            (
                CustomClassWithGenerics2[
                    int | CustomClassWithGeneric1[int | str],
                    CustomClassWithGeneric1[CustomClassWithGeneric1[str]],
                ],
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics2[typing.Union[builtins.int, tests._service_lookup.test_typed_type.CustomClassWithGeneric1[types.UnionType[builtins.int, builtins.str]]], tests._service_lookup.test_typed_type.CustomClassWithGeneric1[tests._service_lookup.test_typed_type.CustomClassWithGeneric1[builtins.str]]]",
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics2[typing.Union[builtins.int, tests._service_lookup.test_typed_type.CustomClassWithGeneric1[typing.Union[builtins.int, builtins.str]]], tests._service_lookup.test_typed_type.CustomClassWithGeneric1[tests._service_lookup.test_typed_type.CustomClassWithGeneric1[builtins.str]]]",
            ),
        ],
    )
    def test_represent_types(
        self,
        type_: type,
        expected_representation_python_less_than_3_14: str,
        expected_representation_python_greater_than_or_equal_3_14: str,
    ) -> None:
        typed_type = TypedType.from_type(type_)

        representation = repr(typed_type)

        if sys.version_info >= (3, 14):
            assert (
                representation
                == expected_representation_python_greater_than_or_equal_3_14
            )
        if sys.version_info < (3, 14):
            assert representation == expected_representation_python_less_than_3_14

    @pytest.mark.parametrize(
        argnames=(
            "type_",
            "expected_representation_python_less_than_3_14",
            "expected_representation_python_greater_than_or_equal_3_14",
        ),
        argvalues=[
            (int, None, None),
            (CustomClass, None, None),
            (
                CustomClassWithGenerics2[
                    int | CustomClassWithGeneric1[int], CustomClass
                ],
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics2[typing.Union[int, tests._service_lookup.test_typed_type.CustomClassWithGeneric1[int]], tests._service_lookup.test_typed_type.CustomClass]",
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics2[int | tests._service_lookup.test_typed_type.CustomClassWithGeneric1[int], tests._service_lookup.test_typed_type.CustomClass]",
            ),
        ],
    )
    def test_retain_type_information_when_creating_instances_of_classes_with_generics(
        self,
        type_: type,
        expected_representation_python_less_than_3_14: str | None,
        expected_representation_python_greater_than_or_equal_3_14: str | None,
    ) -> None:
        typed_type = TypedType.from_type(type_)
        type_instance = typed_type.invoke(parameter_values=[])

        orig_class = (
            str(getattr(type_instance, "__orig_class__"))  # noqa: B009
            if hasattr(type_instance, "__orig_class__")
            else None
        )

        if sys.version_info >= (3, 14):
            assert (
                orig_class == expected_representation_python_greater_than_or_equal_3_14
            )
        if sys.version_info < (3, 14):
            assert orig_class == expected_representation_python_less_than_3_14

    @pytest.mark.parametrize(
        argnames=("type_1", "type_2", "is_equal"),
        argvalues=[
            (int, int, True),
            (int, str, False),
            (CustomClassWithOptionalGeneric1, CustomClassWithOptionalGeneric1, True),
            (
                CustomClassWithOptionalGeneric1[int],
                CustomClassWithOptionalGeneric1[str],
                False,
            ),
            (
                CustomClassWithOptionalGeneric2[int],
                CustomClassWithOptionalGeneric2,
                False,
            ),
            (
                CustomClassWithGenerics1[int, str],
                CustomClassWithGenerics1[str, int],
                False,
            ),
        ],
    )
    def test_equality_and_hash(
        self, type_1: type, type_2: type, is_equal: bool
    ) -> None:
        typed_type_1 = TypedType.from_type(type_1)
        typed_type_2 = TypedType.from_type(type_2)

        if is_equal:
            assert typed_type_1 == typed_type_2
            assert hash(typed_type_1) == hash(typed_type_2)
        else:
            assert typed_type_1 != typed_type_2
            assert hash(typed_type_1) != hash(typed_type_2)

    def test_inequality_with_non_typed_type(
        self,
    ) -> None:
        typed_type = TypedType.from_type(ServiceWithNoDependencies)
        non_typed_type = "another_type"

        assert typed_type != non_typed_type

    def test_extract_type_hints_from_instance(self) -> None:
        expected_typed_type = TypedType.from_type(CustomClassWithGenerics2[int, str])

        typed_type = TypedType.from_instance(CustomClassWithGenerics2[int, str]())

        assert typed_type == expected_typed_type
        assert repr(typed_type) == repr(expected_typed_type)

    @pytest.mark.parametrize(
        argnames=("type_"),
        argvalues=[int, CustomClass],
    )
    def test_fail_when_creating_from_instance_without_type_information(
        self, type_: type
    ) -> None:
        with pytest.raises(
            ValueError,
            match="The instance does not retain type hint information because it has no generics",
        ):
            TypedType.from_instance(type_())

    @pytest.mark.parametrize(
        argnames=("type_", "is_generic"),
        argvalues=[
            (int, False),
            (list[int], True),
            (ServiceWithNoDependencies, False),
            (CustomClassWithGeneric3, False),
            (CustomClassWithGeneric1[int], True),
            (CustomClassWithGenerics2[int, str], True),
            (CustomClassWithOptionalGeneric1[list[int]], True),
            (CustomClassWithOptionalGeneric2, False),
            (CustomClassWithGenericAndOptionalGeneric1[int], True),
        ],
    )
    def test_return_if_type_is_generic(self, type_: type, is_generic: bool) -> None:
        typed_type = TypedType.from_type(type_)

        assert typed_type.is_generic_type == is_generic

    def test_return_generic_type_definition(self) -> None:
        typed_type = TypedType.from_type(CustomClassWithGenerics2[int, str])

        generic_type = typed_type.get_generic_type_definition()

        assert generic_type == TypedType.from_type(CustomClassWithGenerics2)

    def test_fail_when_getting_generic_type_definition_when_type_has_no_generics(
        self,
    ) -> None:
        typed_type = TypedType.from_type(int)

        with pytest.raises(RuntimeError):
            typed_type.get_generic_type_definition()

    def test_get_generic_type_arguments(self) -> None:
        typed_type = TypedType.from_type(CustomClassWithGenerics1[int, str])

        arguments = typed_type.generic_type_arguments()

        assert arguments == [
            TypedType.from_type(int),
            TypedType.from_type(str),
        ]

    def test_not_get_generic_type_arguments_when_type_has_no_generics_specified(
        self,
    ) -> None:
        typed_type = TypedType.from_type(CustomClassWithGenerics1)

        assert typed_type.generic_type_arguments() == []

    def test_create_generic_type_instance_with_parameters(self) -> None:
        expected_parameter_1 = "value_1"
        expected_parameter_2 = "value_2"

        typed_type = TypedType.from_type(
            CustomClassWithGenericAndConstructorParameters[str]
        )

        instance = cast(
            "CustomClassWithGenericAndConstructorParameters[str]",
            typed_type.invoke(
                parameter_values=[expected_parameter_1, expected_parameter_2]
            ),
        )

        assert isinstance(instance, CustomClassWithGenericAndConstructorParameters)
        assert instance.parameter_1 == expected_parameter_1
        assert instance.parameter_2 == expected_parameter_2

    @pytest.mark.parametrize(
        argnames=("type_", "is_mapping"),
        argvalues=[
            (int, False),
            (CustomClass, False),
            (list[int], False),
            (tuple[int, ...], False),
            (Mapping[str, int], True),
            (dict[str, int], True),
            (CustomClassWithGeneric1[int], False),
            (Any, False),
        ],
    )
    def test_return_if_type_is_mapping(self, type_: type, is_mapping: bool) -> None:
        typed_type = TypedType.from_type(type_)

        assert typed_type.is_mapping == is_mapping

    @pytest.mark.parametrize(
        argnames=("type_", "is_sequence"),
        argvalues=[
            (int, False),
            (CustomClass, False),
            (list[int], True),
            (tuple[int, ...], True),
            (Mapping[str, int], False),
            (dict[str, int], False),
            (Sequence[int], True),
            (CustomClassWithGeneric1[int], False),
            (Any, False),
            (str, False),
            (bytes, False),
        ],
    )
    def test_return_if_type_is_sequence(self, type_: type, is_sequence: bool) -> None:
        typed_type = TypedType.from_type(type_)

        assert typed_type.is_sequence == is_sequence

    @pytest.mark.parametrize(
        argnames=("type_", "expected_type"),
        argvalues=[
            (int, int),
            (list[int], list),
            (CustomClassWithGenerics1[int, str], CustomClassWithGenerics1),
            (
                int | str,
                __import__("typing").Union
                if sys.version_info >= (3, 14)
                else UnionType,
            ),
        ],
    )
    def test_return_origin_type(self, type_: type, expected_type: type) -> None:
        typed_type = TypedType.from_type(type_)

        result = typed_type.to_type()

        assert result is expected_type

    @pytest.mark.parametrize(
        argnames=("annotation"),
        argvalues=[
            (int),
            (list[int]),
            (CustomClassWithGenerics1[int, str]),
            (int | str),
        ],
    )
    def test_return_annotation(
        self,
        annotation: Any,  # noqa: ANN401
    ) -> None:
        typed_type = TypedType.from_type(annotation)

        assert typed_type.annotation == annotation
