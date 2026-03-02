# Configuration

Wirio provides a built-in configuration system for loading settings.
We can read values from multiple sources (such as JSON files and environment variables) and compose them using a clear precedence order where newer sources override older ones.

## Quickstart

Define a settings model and read it from `services.configuration`:

```python
from pydantic import BaseModel
from wirio import ServiceCollection


class ApplicationSettings(BaseModel):
    app_name: str
    port: int


services = ServiceCollection()
settings = services.configuration[ApplicationSettings]
```

**Important:** Wirio maps model field names to configuration keys using snake case conventions.

For example, the `APP_NAME` environment variable is read as `app_name`.

## Defaults and required values

When building a settings model, if a field has a default value, that default is used when no value is found.

```python
from pydantic import BaseModel


class ApplicationSettings(BaseModel):
    app_name: str
    port: int | None = None
```

In this example, `port` defaults to `None` when not present.

## Order of precedence

`ConfigurationManager` supports multiple sources, and the latest added source wins.

When the same key exists in more than one source, Wirio resolves the value from the last source that contains that key.

Default priority (highest to lowest):

1. Environment variables
2. `appsettings.{environment}.json`
3. `appsettings.json`

This lets us define base values in `appsettings.json`, override per environment in `appsettings.{environment}.json`, and finally override specific keys via environment variables.

## Accessing configuration in factories

A common pattern is reading typed settings inside a service factory:

```python
from pydantic import BaseModel
from wirio import ServiceCollection


class ApplicationSettings(BaseModel):
    database_connection_string: str


class DatabaseClient:
    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string


services = ServiceCollection()


def inject_database_client() -> DatabaseClient:
    settings = services.configuration[ApplicationSettings]
    return DatabaseClient(settings.database_connection_string)


services.add_singleton(inject_database_client)
```

## Azure Key Vault

Wirio can read configuration values from Azure Key Vault.

First, install the optional dependency:

```bash
uv add "wirio[azure-key-vault]"
```

Then add Key Vault as a configuration source:

```python
from wirio import ServiceCollection


services = ServiceCollection()
services.configuration.add_azure_key_vault(
    url="https://<your-vault-name>.vault.azure.net",
)
```

If no credential is provided, Wirio uses `DefaultAzureCredential`.
We can also pass a custom async Azure credential through the `credential` parameter.

Since the last registered source takes precedence, call `add_azure_key_vault(...)` after other sources to ensure Key Vault values override them.
