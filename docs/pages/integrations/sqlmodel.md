# SQLModel integration

## Benefits

We had to dive into the docs every time to set up SQLModel: multiple ways to initialize it, context managers everywhere, different settings for sync and async.

Setting up SQLModel should take seconds, and be configured with the best practices by just adding a single line of code.

Some of the SQLModel integration benefits:

- Automatic registration of SQLModel services.
- Recommended settings by default.
- No context managers.
- Consistent and recommended lifetime management out-of-the-box.

## Installation

To use the SQLModel integration, add the `sqlmodel` extra to automatically install the required compatible dependencies.

```bash
uv add wirio[sqlmodel]
```

## Asynchronous setup (recommended)

`add_sqlmodel` configures SQLModel for asynchronous workloads and registers the following services:

- `AsyncEngine` as singleton
- `async_sessionmaker[AsyncSession]` as singleton
- `AsyncSession` as scoped

We only have to provide the connection string, and Wirio will take care of the rest.

```python hl_lines="2-4"
services = ServiceCollection()
services.add_sqlmodel(
    "postgresql+asyncpg://<user>:<password>@<host>:<port>/<database>"
)
```

We're using the `asyncpg` driver (`uv add asyncpg`) in the connection string, but we can use any driver supported by SQLModel.

### Imports to resolve registered async services

It's important to import the correct types to resolve the registered services.

```python
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
```

Then, we can use it in the easiest way possible:

```python
class UserService:
    def __init__(self, sql_session: AsyncSession) -> None:
        self.sql_session = sql_session
```

## Synchronous setup

`add_sync_sqlmodel` configures SQLModel for synchronous workloads and registers the following services:

- `Engine` as singleton
- `sessionmaker[Session]` as singleton
- `Session` as scoped

We only have to provide the connection string, and Wirio will take care of the rest.

```python hl_lines="2-4"
services = ServiceCollection()
services.add_sync_sqlmodel(
    "postgresql+psycopg2://<user>:<password>@<host>:<port>/<database>"
)
```

We're using the `psycopg2` driver (`uv add psycopg2-binary`) in the connection string, but we can use any driver supported by SQLModel.

### Imports to resolve registered synchronous services

It's important to import the correct types to resolve the registered services.

```python
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session
```

Then, we can use it in the easiest way possible:

```python
class UserService:
    def __init__(self, sql_session: Session):
        self.sql_session = sql_session
```
