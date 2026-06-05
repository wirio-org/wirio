from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

import pytest
from pytest_mock import MockerFixture

from tests.utils.services import ServiceWithNoDependencies, create_test_services
from wirio._utils._extra_dependencies import ExtraDependencies
from wirio.annotations import FromKeyedServices, FromServices
from wirio.exceptions import CannotResolveServiceFromEndpointError
from wirio.hosting.host_environment import HostEnvironment
from wirio.service_collection import ServiceCollection
from wirio.service_container import ServiceContainer
from wirio.service_provider import ServiceProvider

if TYPE_CHECKING:
    from fastapi import APIRouter, Depends, FastAPI
    from fastapi.testclient import TestClient

    from wirio.integrations.fastapi import get_service_container, get_service_provider
else:
    APIRouter = Any
    Depends = Any
    FastAPI = Any
    TestClient = Any
    get_service_container = Any
    get_service_provider = Any

try:
    from fastapi import APIRouter, Depends, FastAPI
    from fastapi.testclient import TestClient

    from wirio.integrations.fastapi import get_service_container, get_service_provider
except ImportError:
    pass


@pytest.mark.skipif(
    not ExtraDependencies.is_fastapi_installed(),
    reason=ExtraDependencies.FASTAPI_NOT_INSTALLED_ERROR_MESSAGE,
)
class TestFastapiDependencyInjection:
    @pytest.fixture
    def app(self) -> FastAPI:
        app = FastAPI()
        router = APIRouter()

        @router.get("/service-with-no-dependencies")
        async def service_with_no_dependencies_endpoint(  # pyright: ignore[reportUnusedFunction]
            service_with_no_dependencies: Annotated[
                ServiceWithNoDependencies, FromServices()
            ],
        ) -> None:
            assert isinstance(service_with_no_dependencies, ServiceWithNoDependencies)

        app.include_router(router)
        services = ServiceCollection()
        services.configure_fastapi(app)
        services.add_transient(ServiceWithNoDependencies)
        return app

    @pytest.fixture
    def test_client(self, app: FastAPI) -> Generator[TestClient]:
        with TestClient(app) as test_client:
            yield test_client

    def test_inject_service(self, test_client: TestClient) -> None:
        response = test_client.get("/service-with-no-dependencies")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

        assert response.status_code == HTTPStatus.OK  # pyright: ignore[reportUnknownMemberType]

    def test_not_interfere_with_sync_endpoints(self) -> None:
        expected_name = "test-name"
        app = FastAPI()

        def get_name() -> str:
            return expected_name

        @app.get("/sync-endpoint")
        def sync_endpoint(  # pyright: ignore[reportUnusedFunction]
            name: Annotated[str, Depends(get_name)],
        ) -> str:
            return name

        services = ServiceCollection()
        services.configure_fastapi(app)

        with TestClient(app) as test_client:
            response = test_client.get("/sync-endpoint")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

            assert response.status_code == HTTPStatus.OK  # pyright: ignore[reportUnknownMemberType]
            assert response.json() == expected_name  # pyright: ignore[reportUnknownMemberType]

    def test_not_do_anything_when_route_is_not_matched(self) -> None:
        app = FastAPI()
        services = ServiceCollection()
        services.configure_fastapi(app)

        with TestClient(app) as test_client:
            response = test_client.get("/not-matched-endpoint")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

            assert response.status_code == HTTPStatus.NOT_FOUND  # pyright: ignore[reportUnknownMemberType]

    def test_not_interfere_with_non_annotated_parameters(self) -> None:
        expected_test_value = "test-value"
        app = FastAPI()
        router = APIRouter()

        @router.get("/non-annotated-parameter")
        async def non_annotated_parameter_endpoint(  # pyright: ignore[reportUnusedFunction]
            some_parameter: str,
        ) -> None:
            assert some_parameter == expected_test_value

        app.include_router(router)
        services = ServiceCollection()
        services.configure_fastapi(app)

        with TestClient(app) as test_client:
            response = test_client.get(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                "/non-annotated-parameter",
                params={"some_parameter": expected_test_value},
            )

            assert response.status_code == HTTPStatus.OK  # pyright: ignore[reportUnknownMemberType]

    def test_not_interfere_with_fastapi_depends(self) -> None:
        expected_test_value = "test-value"
        app = FastAPI()
        router = APIRouter()

        def test_dependency() -> str:
            return expected_test_value

        @router.get("/fastapi-depends")
        async def fastapi_depends_endpoint(  # pyright: ignore[reportUnusedFunction]
            test_dependency: Annotated[str, Depends(test_dependency)],
        ) -> None:
            assert test_dependency == expected_test_value

        app.include_router(router)
        services = ServiceCollection()
        services.configure_fastapi(app)

        with TestClient(app) as test_client:
            response = test_client.get("/fastapi-depends")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

            assert response.status_code == HTTPStatus.OK  # pyright: ignore[reportUnknownMemberType]

    def test_return_service_when_optional_dependency_is_registered(self) -> None:
        app = FastAPI()

        @app.get("/optional-dependency")
        async def optional_dependency_endpoint(  # pyright: ignore[reportUnusedFunction]
            service_with_no_dependencies: Annotated[
                ServiceWithNoDependencies | None, FromServices()
            ],
        ) -> None:
            assert isinstance(service_with_no_dependencies, ServiceWithNoDependencies)

        services = ServiceCollection()
        services.configure_fastapi(app)
        services.add_transient(ServiceWithNoDependencies)

        with TestClient(app) as test_client:
            response = test_client.get("/optional-dependency")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

            assert response.status_code == HTTPStatus.OK  # pyright: ignore[reportUnknownMemberType]

    def test_return_service_when_optional_dependency_is_not_registered(self) -> None:
        app = FastAPI()

        @app.get("/optional-dependency")
        async def optional_dependency_endpoint(  # pyright: ignore[reportUnusedFunction]
            service_with_no_dependencies: Annotated[
                ServiceWithNoDependencies | None, FromServices()
            ],
        ) -> None:
            assert service_with_no_dependencies is None

        services = ServiceCollection()
        services.configure_fastapi(app)

        with TestClient(app) as test_client:
            response = test_client.get("/optional-dependency")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

            assert response.status_code == HTTPStatus.OK  # pyright: ignore[reportUnknownMemberType]

    def test_fail_when_non_optional_dependency_is_missing(self) -> None:
        app = FastAPI()

        @app.get("/non-optional-dependency")
        async def non_optional_dependency_endpoint(  # pyright: ignore[reportUnusedFunction]
            service_with_no_dependencies: Annotated[
                ServiceWithNoDependencies, FromServices()
            ],
        ) -> None:
            pass

        services = ServiceCollection()
        services.configure_fastapi(app)

        with TestClient(app) as test_client:  # noqa: SIM117
            with pytest.raises(CannotResolveServiceFromEndpointError):
                test_client.get("/non-optional-dependency")  # pyright: ignore[reportUnknownMemberType]

    def test_combine_request_types_fastapi_depends_and_wirio_injection(
        self,
    ) -> None:
        expected_request_parameter = "test-value1"
        expected_fastapi_depends = "test-value2"
        expected_wirio_injection = "test-value3"
        app = FastAPI()
        router = APIRouter()

        def test_dependency() -> str:
            return expected_fastapi_depends

        @router.get("/endpoint")
        async def fastapi_depends_endpoint(  # pyright: ignore[reportUnusedFunction]
            request_parameter: str,
            fastapi_depends: Annotated[str, Depends(test_dependency)],
            wirio_inject: Annotated[str, FromServices()],
        ) -> None:
            assert request_parameter == expected_request_parameter
            assert fastapi_depends == expected_fastapi_depends
            assert wirio_inject == expected_wirio_injection

        app.include_router(router)
        services = ServiceCollection()
        services.configure_fastapi(app)
        services.add_singleton(str, expected_wirio_injection)

        with TestClient(app) as test_client:
            response = test_client.get(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                "/endpoint", params={"request_parameter": expected_request_parameter}
            )

            assert response.status_code == HTTPStatus.OK  # pyright: ignore[reportUnknownMemberType]

    def test_resolve_keyed_service(self) -> None:
        service_key = "key"
        app = FastAPI()
        router = APIRouter()

        @router.get("/endpoint")
        async def endpoint(  # pyright: ignore[reportUnusedFunction]
            service: Annotated[
                ServiceWithNoDependencies, FromKeyedServices(service_key)
            ],
        ) -> None:
            assert isinstance(service, ServiceWithNoDependencies)

        app.include_router(router)
        services = ServiceCollection()
        services.configure_fastapi(app)
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)

        with TestClient(app) as test_client:
            response = test_client.get("/endpoint")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

            assert response.status_code == HTTPStatus.OK  # pyright: ignore[reportUnknownMemberType]

    def test_get_service_container(self) -> None:
        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
            services = get_service_container(app)
            assert isinstance(services, ServiceContainer)
            yield

        app = FastAPI(lifespan=lifespan)
        services = ServiceContainer()
        services.configure_fastapi(app)

        with TestClient(app):
            pass

    def test_get_service_provider(self) -> None:
        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
            service_provider = get_service_provider(app)
            assert isinstance(service_provider, ServiceProvider)
            assert service_provider.is_fully_initialized
            yield

        app = FastAPI(lifespan=lifespan)
        services = ServiceCollection()
        services.configure_fastapi(app)

        with TestClient(app):
            pass

    async def test_override_service_of_fastapi_service_provider(
        self, mocker: MockerFixture
    ) -> None:
        app = FastAPI()
        services = ServiceCollection()
        services.configure_fastapi(app)
        services.add_transient(ServiceWithNoDependencies)
        service_with_no_dependencies_mock = mocker.create_autospec(
            ServiceWithNoDependencies, instance=True
        )

        with TestClient(app):
            service_provider = get_service_provider(app)

            with service_provider.override_service(
                ServiceWithNoDependencies, service_with_no_dependencies_mock
            ):
                resolved_service = await service_provider.get_required_service(
                    ServiceWithNoDependencies
                )
                assert resolved_service is service_with_no_dependencies_mock

            resolved_service = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )
            assert resolved_service is not service_with_no_dependencies_mock
            assert isinstance(resolved_service, ServiceWithNoDependencies)

    def test_resolve_service_when_service_is_registered_after_fastapi_integration_setup(
        self,
    ) -> None:
        app = FastAPI()
        router = APIRouter()

        @router.get("/endpoint")
        async def endpoint(  # pyright: ignore[reportUnusedFunction]
            service: Annotated[ServiceWithNoDependencies, FromServices()],
        ) -> None:
            assert isinstance(service, ServiceWithNoDependencies)

        app.include_router(router)
        services = ServiceCollection()
        services.configure_fastapi(app)
        services.add_transient(ServiceWithNoDependencies)

        with TestClient(app) as test_client:
            response = test_client.get("/endpoint")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

            assert response.status_code == HTTPStatus.OK  # pyright: ignore[reportUnknownMemberType]

    def test_return_content_root_path_from_host_environment_with_services_defined_in_current_file(
        self,
    ) -> None:
        expected_content_root_path = str(Path(__file__).parent.resolve())
        app = FastAPI()

        @app.get("/endpoint")
        async def endpoint(  # pyright: ignore[reportUnusedFunction]
            host_environment: Annotated[HostEnvironment, FromServices()],
        ) -> str:
            return host_environment.content_root_path

        services = ServiceCollection()
        services.configure_fastapi(app)

        with TestClient(app) as test_client:
            response = test_client.get("/endpoint")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

            assert response.status_code == HTTPStatus.OK  # pyright: ignore[reportUnknownMemberType]
            content_root_path = response.json()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            assert content_root_path == expected_content_root_path

    def test_return_content_root_path_from_host_environment_with_services_defined_in_another_file(
        self,
    ) -> None:
        expected_content_root_path = str((Path.cwd() / "tests/utils").resolve())
        app = FastAPI()

        @app.get("/endpoint")
        async def endpoint(  # pyright: ignore[reportUnusedFunction]
            host_environment: Annotated[HostEnvironment, FromServices()],
        ) -> str:
            return host_environment.content_root_path

        services = create_test_services()
        services.configure_fastapi(app)

        with TestClient(app) as test_client:
            response = test_client.get("/endpoint")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

            assert response.status_code == HTTPStatus.OK  # pyright: ignore[reportUnknownMemberType]
            content_root_path = response.json()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            assert content_root_path == expected_content_root_path
