<div align="center">
<img alt="Logo" src="https://raw.githubusercontent.com/wirio-org/wirio/refs/heads/main/docs/logo.png" width="450" height="450">

[![CI](https://img.shields.io/github/actions/workflow/status/wirio-org/wirio/main.yaml?branch=main&logo=github&label=CI)](https://github.com/wirio-org/wirio/actions/workflows/main.yaml)
[![Coverage status](https://coveralls.io/repos/github/wirio-org/wirio/badge.svg?branch=main)](https://coveralls.io/github/wirio-org/wirio?branch=main)
[![PyPI - version](https://img.shields.io/pypi/v/wirio?color=blue&label=pypi)](https://pypi.org/project/wirio/)
[![Python - versions](https://img.shields.io/pypi/pyversions/wirio.svg)](https://github.com/wirio-org/wirio)
[![License](https://img.shields.io/github/license/wirio-org/wirio.svg)](https://github.com/wirio-org/wirio/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/📚_documentation-3D9970)](https://wirio-org.github.io/wirio)

</div>

## Overview

Wirio is a practical and easy-to-use dependency injection library for Python designed to work in any environment and application type:

- **Use it everywhere:** Use dependency injection in web servers, background tasks, console applications, Jupyter notebooks, tests, etc.
- **Lifetimes**: `Singleton` (same instance per application), `Scoped` (same instance per HTTP request scope) and `Transient` (different instance per resolution).
- **FastAPI integration** out of the box, and pluggable to any web framework.
- **Automatic resolution and disposal**: Automatically resolve constructor parameters and manage async and non-async context managers. It's no longer our concern to know how to create or dispose services.
- **Environment detection**: Detect the current environment and adjust settings and behavior accordingly.
- **Settings providers**: Built-in settings support, including integrations such as environment variables, settings files and Azure Key Vault.
- **Centralized setup**: Register all services in one place using a clean syntax, and without decorators.
- **Integrations**: Optional and ready-to-use integrations for common libraries, such as SQLModel.
- **ty** and **Pyright** strict compliant.

## 📦 Installation

```bash
uv add wirio
```

## ✨ Quickstart with FastAPI

Inject services into async endpoints using `Annotated[..., FromServices()]`.

```python
class EmailService:
    pass


class UserService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service


app = FastAPI()

@app.post("/users")
async def create_user(
    user_service: Annotated[UserService, FromServices()],
) -> None:
    ...

services = ServiceCollection()
services.configure_fastapi(app)
services.add_transient(EmailService)
services.add_transient(UserService)
```

## ✨ Quickstart without FastAPI

Register services and create a service provider.

```python
class EmailService:
    pass


class UserService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service


services = ServiceCollection()
services.add_transient(EmailService)
services.add_transient(UserService)

async with services.build_service_provider() as service_provider:
    user_service = await service_provider.get_required_service(UserService)
```

If we want a scope per operation (e.g., per HTTP request or message from a queue), we can create a scope from the service provider:

```python
async with service_provider.create_scope() as service_scope:
    user_service = await service_scope.get_required_service(UserService)
```

## 🔄 Lifetimes

- `Transient`: A new instance is created every time the service is requested. Examples: Services without state, workflows, repositories, service clients...
- `Singleton`: The same instance is used every time the service is requested. Examples: Settings (`pydantic-settings`), machine learning models, database connection pools, caches.
- `Scoped`: A new instance is created for each new scope, but the same instance is returned within the same scope. Examples: Database clients, unit of work.

## 🏭 Factories

Sometimes, a service cannot be created automatically. For example, consider `DatabaseClient`, which requires a connection string:

```python
class DatabaseClient:
    def __init__(self, connection_string: str) -> None:
        pass
```

`str` is too generic to register as a service. We could have other strings registered (e.g., API URL, logging level, service bus queue), and it wouldn't be clear which string is the connection string.

The connection string could come from anywhere: an environment variable, a config file, a secrets manager, etc.

Let's say we want to get the connection string from an environment variable. We can create a factory function that reads the environment variable and returns `DatabaseClient`, the service we want to register, and then we can register that factory as a service:

```python
def inject_database_client() -> DatabaseClient:
    return DatabaseClient(
        connection_string=os.environ["DATABASE_CONNECTION_STRING"]
    )

services.add_transient(inject_database_client)
```

Wirio will automatically use the returned type (`DatabaseClient`) as the service type to register.

What if our factory needs dependencies itself? No problem! Just add them as parameters to the factory, and Wirio will resolve them for us.

For example, the typical approach to manage settings is to centralize them in an `ApplicationSettings` class, which we register as a singleton service:

```python
from pydantic_settings import BaseSettings


class ApplicationSettings(BaseSettings):
    database_connection_string: str

services.add_singleton(ApplicationSettings, ApplicationSettings())
```

Then, we can inject `ApplicationSettings` into our factory to create the `DatabaseClient`:

```python
def inject_database_client(application_settings: ApplicationSettings) -> DatabaseClient:
    return DatabaseClient(
        connection_string=application_settings.database_connection_string
    )

services.add_transient(inject_database_client)
```

## 🧪 Simplified testing

We can substitute dependencies on the fly meanwhile the context manager is active.

```python
with service_provider.override_service(EmailService, email_service_mock):
    user_service = await service_provider.get_required_service(UserService)
```

## 📝 Interfaces & abstract classes

We can register a service by specifying both the service type (interface / abstract class) and the implementation type (concrete class). This is useful when we want to inject services using abstractions.

```python
class NotificationService(ABC):
    @abstractmethod
    async def send_notification(self, user_id: str, message: str) -> None:
        ...


class EmailService(NotificationService):
    @override
    async def send_notification(self, user_id: str, message: str) -> None:
        pass


class UserService:
    def __init__(self, notification_service: NotificationService) -> None:
        self.notification_service = notification_service

    async def create_user(self, email: str) -> None:
        user = self.create_user(email)
        await self.notification_service.send_notification(user.id, "Welcome to our service!")


services.add_transient(NotificationService, EmailService)
```

## 📝 Keyed services

We can register a service by specifying both the service type and a key. This is useful when we want to resolve services using abstractions and an explicit key.

```python
class NotificationService(ABC):
    @abstractmethod
    async def send_notification(self, user_id: str, message: str) -> None:
        ...


class EmailService(NotificationService):
    @override
    async def send_notification(self, user_id: str, message: str) -> None:
        pass


class PushNotificationService(NotificationService):
    @override
    async def send_notification(self, user_id: str, message: str) -> None:
        pass


class UserService:
    def __init__(
        self,
        notification_service: Annotated[NotificationService, FromKeyedServices("email"),
    ) -> None:
        self.notification_service = notification_service

    async def create_user(self, email: str) -> None:
        user = self.create_user(email)
        await self.notification_service.send_notification(user.id, "Welcome to our service!")


services.add_keyed_transient("email", NotificationService, EmailService)
services.add_keyed_transient("push", NotificationService, PushNotificationService)
```

## 📝 Auto-activated services

We can register a service as auto-activated. This is useful when we want to ensure our FastAPI application doesn't start to serve requests until certain services are fully initialized (e.g., machine learning models, database connection pools and caches).

```python
services.add_auto_activated_singleton(MachineLearningModel)
```

## 💾 SQLModel integration

Ready-to-use SQLModel with the recommended defaults.

```python
services = ServiceCollection()
services.add_sqlmodel("connection_string")


class UserService:
    def __init__(self, sql_session: AsyncSession) -> None:
        self.sql_session = sql_session
```

More information [here](https://wirio-org.github.io/wirio/integrations/sqlmodel).

## 📚 Documentation

For more information, [check out the documentation](https://wirio-org.github.io/wirio).
