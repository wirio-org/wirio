# Configuration

## Overview

Wirio includes a built-in configuration system.
We can load values from multiple sources, then read them as single values, sections or Pydantic models.

## Source priority

Wirio supports multiple sources. When the same key exists in multiple sources, the last added sources have more priority.

The following sources are loaded, by default, in this order:

1. `appsettings.json`
2. `appsettings.{environment}.json`
3. Environment variables

So, in the default configuration, environment variables have higher priority than JSON files because the source is added after them. This means that if a key exists in both `appsettings.json` and environment variables, the value from environment variables will be used.

If we add more sources, those will have higher priority than the defaults. For example, if we add Azure Key Vault as a source, it will override the defaults.

```python
services = ServiceCollection()
services.configuration.add_azure_key_vault(
    "https://example.vault.azure.net"
)
```

## Naming convention

Each source (environment variables, JSON, Azure Key Vault...) has its own naming convention for keys. Wirio uses snake case for configuration keys. When loading from sources, keys are normalized to snake case. For example, the `APP_NAME` environment variable maps to `app_name`.

## Read a Pydantic model

Create a `ServiceCollection`, then read a model from `services.configuration`.

```python
from pydantic import BaseModel
from wirio import ServiceCollection


class ApplicationSettings(BaseModel):
    app_name: str
    port: int


services = ServiceCollection()
application_settings = services.configuration.get_model(ApplicationSettings)
```

## Read one value

- Use `get_required_value` when the key must exist.

```python
openai_api_key = services.configuration.get_required_value("openai_api_key")
timeout_seconds = services.configuration.get_required_value("timeout_seconds", int)
```

By default, the configuration system returns values as strings. To validate and convert to another type, pass the type as a second argument.

```python
timeout_seconds = services.configuration.get_required_value("maximum_retries", int)
```

- Use `get_value` for optional keys.

```python
openai_api_key = services.configuration.get_value("openai_api_key")
timeout_seconds = services.configuration.get_value("maximum_retries", int)
```

## Defaults and required fields

If a model field has a default, that default is used when no value is found.

```python
from pydantic import BaseModel


class ApplicationSettings(BaseModel):
    app_name: str
    port: int | None = None
```

Here, `port` defaults to `None` when missing.
If a required field is missing, `get_model` raises `KeyError`.

## Sections

Use `get_section` to read a section. For example, you can read the next JSON:

```json
{
  "logging": {
    "log_level": "WARNING"
  }
}
```

```python
log_level = services.configuration.get_section("logging").get_required_value(
    "log_level"
)
```

`ConfigurationSection` supports:

- The section value itself with `section.get_required_value()` or `section.get_required_value(type)`.
- A child value with `section.get_required_value("child:key")` or `section.get_required_value("child:key", type)`.

If a section has only children and no value at its own path, `section.get_value()` returns `None`.

## Key format

Nested keys use `:`:

- `database:host`
- `database:port`
- `logging:log_level:default`

## Use configuration in factories

A common pattern is to read settings inside a factory.

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
    settings = services.configuration.get_model(ApplicationSettings)
    return DatabaseClient(settings.database_connection_string)


services.add_singleton(inject_database_client)
```

## Azure Key Vault

Wirio can read configuration values from Azure Key Vault.

1. Install the optional dependency:

```bash
uv add "wirio[azure-key-vault]"
```

2. Add Key Vault as a source:

```python
services.configuration.add_azure_key_vault(
    "https://example.vault.azure.net",
)
```

If no credential is provided, Wirio uses `DefaultAzureCredential`.
We can also pass a custom async Azure credential with the `credential` parameter.
