# Environments

## Overview

Wirio exposes the current application environment through `services.environment`.

This is useful when we want to register different services, enable diagnostics, or choose configuration behavior based on where the app is running.

## Environment source

Wirio reads the environment from the `WIRIO_ENVIRONMENT` environment variable.

If the variable is not defined, Wirio defaults to `local`.

Supported values by default are:

- `local`
- `development`
- `staging`
- `production`

## Reading the current environment

```python
from wirio import ServiceCollection


services = ServiceCollection()

print(services.environment.environment_name)
```

## Environment checks

Use the built-in helper methods when we only need a boolean check:

```python
from wirio import ServiceCollection


services = ServiceCollection()

if services.environment.is_local():
    print("Running in local")

if services.environment.is_development():
    print("Running in development")

if services.environment.is_staging():
    print("Running in staging")

if services.environment.is_production():
    print("Running in production")
```

For custom values, use `is_environment(...)`:

```python
from wirio import ServiceCollection


services = ServiceCollection()

if services.environment.is_environment("uat"):
    print("UAT behavior")
```
