import pytest
from pytest_mock import MockerFixture

from wirio._utils._extra_dependencies import ExtraDependencies


class TestExtraDependencies:
    def test_fail_when_importing_fastapi_when_not_installed(
        self, mocker: MockerFixture
    ) -> None:
        mocker.patch.dict("sys.modules", {"fastapi": None})

        with pytest.raises(ImportError) as exception_info:
            assert (
                str(exception_info) == ExtraDependencies.ensure_fastapi_is_installed()
            )

    def test_fail_when_importing_sqlmodel_when_not_installed(
        self, mocker: MockerFixture
    ) -> None:
        mocker.patch.dict("sys.modules", {"sqlmodel": None, "greenlet": None})

        with pytest.raises(ImportError) as exception_info:
            assert (
                str(exception_info) == ExtraDependencies.ensure_sqlmodel_is_installed()
            )
