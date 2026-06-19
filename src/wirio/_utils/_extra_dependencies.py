from typing import ClassVar, final


@final
class ExtraDependencies:
    FASTAPI_NOT_INSTALLED_ERROR_MESSAGE: ClassVar[str] = (
        "'fastapi' is not installed. Please, run 'uv add wirio[fastapi]' to install the required dependencies"
    )
    SQLMODEL_NOT_INSTALLED_ERROR_MESSAGE: ClassVar[str] = (
        "'sqlmodel' or 'greenlet' are not installed. Please, run 'uv add wirio[sqlmodel]' to install the required dependencies"
    )

    @staticmethod
    def is_fastapi_installed() -> bool:
        try:
            import fastapi  # pyright: ignore[reportUnusedImport] # noqa: F401, PLC0415
        except ImportError:
            return False

        return True

    @classmethod
    def ensure_fastapi_is_installed(cls) -> None:
        try:
            from fastapi import (  # noqa: PLC0415
                FastAPI,  # pyright: ignore[reportUnusedImport]  # noqa: F401
            )
        except ImportError as error:
            raise ImportError(cls.FASTAPI_NOT_INSTALLED_ERROR_MESSAGE) from error

    @staticmethod
    def is_sqlmodel_installed() -> bool:
        try:
            import greenlet  # pyright: ignore[reportUnusedImport] # noqa: F401, PLC0415
            import sqlmodel  # pyright: ignore[reportUnusedImport] # noqa: F401, PLC0415
        except ImportError:
            return False

        return True

    @classmethod
    def ensure_sqlmodel_is_installed(cls) -> None:
        try:
            from greenlet import (  # noqa: PLC0415
                greenlet,  # pyright: ignore[reportUnusedImport]  # noqa: F401
            )
            from sqlmodel import (  # noqa: PLC0415
                Session,  # pyright: ignore[reportUnusedImport]  # noqa: F401
            )
        except ImportError as error:
            raise ImportError(cls.SQLMODEL_NOT_INSTALLED_ERROR_MESSAGE) from error
