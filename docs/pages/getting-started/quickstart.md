# Quickstart

## Define dependencies

To showcase the basics of Wirio, we will create a service collection able to resolve the following:

- `EmailService`: A simple service with no dependencies.
- `UserService`: A service depending on `EmailService`.

```python
--8<-- "docs/code/getting_started/quickstart/define_dependencies.py"
```

## Register services

The next step is to create the service collection and register the dependencies we just defined.

```python title="main.py" hl_lines="4-5"
from wirio import ServiceCollection

services = ServiceCollection()
services.add_transient(EmailService)  # (1)!
services.add_transient(UserService)
```

1. Both services are registered as transient, meaning a new instance will be created each time they're requested

We'll use `.add_X` depending on the desired [lifetime](../core-concepts/lifetimes.md). For example: `.add_transient` for transient services, `.add_singleton` for singleton services and `.add_scoped` for scoped services.

## Use

Finally, we convert the service collection into a service provider, which will validate and build the dependency graph, and we'll be able to request instances from it.

=== "FastAPI"

    To resolve dependencies from the service provider, we annotate the parameter with the type we want to resolve.

    ```python title="main.py" hl_lines="5 9"
    from wirio.annotations import FromServices

    @app.post("/users")
    async def create_user(
        user_service: Annotated[UserService, FromServices()],
    ) -> None:
        pass

    services.configure_fastapi(app)  # (1)!
    ```

    1. This will configure FastAPI to use Wirio's dependency injection

=== "Console application"

    To resolve dependencies from the service provider, we call `get_required_service` with the type we want to resolve.

    ```python title="main.py"

    async with services.build_service_provider() as service_provider:
        user_service = await service_provider.get_required_service(UserService)
    ```

=== "Jupyter notebook"

    To resolve dependencies from the service provider, we call `get_required_service` with the type we want to resolve.

    ```python title="notebook.ipynb"
    service_provider = services.build_service_provider()
    user_service = await service_provider.get_required_service(UserService)
    ```

## Full code

=== "FastAPI"

    ```python hl_lines="26 31-34"
    --8<-- "docs/code/getting_started/quickstart/fastapi_full_code.py"
    ```

=== "Console application"

    ```python hl_lines="17-19 21-22"
    import asyncio

    from wirio import ServiceCollection

    class EmailService:
        pass

    class UserService:
        def __init__(self, email_service: EmailService) -> None:
            self.email_service = email_service

            async def create_user(self) -> None:
                pass


    async def main() -> None:
        services = ServiceCollection()
        services.add_transient(EmailService)
        services.add_transient(UserService)

        async with services.build_service_provider() as service_provider:
            user_service = await service_provider.get_required_service(UserService)

    if __name__ == "__main__":
        asyncio.run(main())
    ```

=== "Jupyter notebook"

    ```python hl_lines="3-4"
    from main import services

    service_provider = services.build_service_provider()
    user_service = await service_provider.get_required_service(UserService)
    ```

## Test

We can substitute dependencies on the fly meanwhile the context manager is active.

```python hl_lines="1"
with service_provider.override_service(EmailService, email_service_mock):
    user_service = await service_provider.get_required_service(UserService)
```

For more information, check the [testing documentation](../testing.md).
