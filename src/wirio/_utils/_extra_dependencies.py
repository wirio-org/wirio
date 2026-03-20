from typing import ClassVar, final


@final
class ExtraDependencies:
    FASTAPI_NOT_INSTALLED_ERROR_MESSAGE: ClassVar[str] = (
        "'fastapi' is not installed. Please, run 'uv add wirio[fastapi]' to install the required dependencies"
    )
    SQLMODEL_NOT_INSTALLED_ERROR_MESSAGE: ClassVar[str] = (
        "'sqlmodel' or 'greenlet' are not installed. Please, run 'uv add wirio[sqlmodel]' to install the required dependencies"
    )
    AZURE_KEY_VAULT_NOT_INSTALLED_ERROR_MESSAGE: ClassVar[str] = (
        "'azure-keyvault-secrets', 'azure-identity' or 'aiohttp>=3.13.3' are not installed. Please, run 'uv add wirio[azure-key-vault]' to install the required dependencies"
    )
    AWS_SECRETS_MANAGER_NOT_INSTALLED_ERROR_MESSAGE: ClassVar[str] = (
        "'boto3' is not installed. Please, run 'uv add wirio[aws-secrets-manager]' to install the required dependencies"
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

    @staticmethod
    def is_azure_key_vault_installed() -> bool:
        try:
            import aiohttp  # pyright: ignore[reportUnusedImport] # noqa: F401, PLC0415
            import azure.core.credentials  # pyright: ignore[reportUnusedImport] # noqa: PLC0415
            import azure.identity.aio  # pyright: ignore[reportUnusedImport] # noqa: F401, PLC0415
        except ImportError:
            return False

        return True

    @classmethod
    def ensure_azure_key_vault_is_installed(cls) -> None:
        try:
            import aiohttp  # pyright: ignore[reportUnusedImport] # noqa: F401, PLC0415
            import azure.core.credentials  # pyright: ignore[reportUnusedImport] # noqa: PLC0415
            import azure.identity.aio  # pyright: ignore[reportUnusedImport] # noqa: F401, PLC0415
        except ImportError as error:
            raise ImportError(
                cls.AZURE_KEY_VAULT_NOT_INSTALLED_ERROR_MESSAGE
            ) from error

    @staticmethod
    def is_aws_secrets_manager_installed() -> bool:
        try:
            import boto3  # pyright: ignore[reportUnusedImport, reportMissingImports, reportMissingTypeStubs] # noqa: F401, PLC0415
        except ImportError:
            return False

        return True

    @classmethod
    def ensure_aws_secrets_manager_is_installed(cls) -> None:
        try:
            import boto3  # pyright: ignore[reportUnusedImport, reportMissingImports, reportMissingTypeStubs] # noqa: F401, PLC0415
        except ImportError as error:
            raise ImportError(
                cls.AWS_SECRETS_MANAGER_NOT_INSTALLED_ERROR_MESSAGE
            ) from error
