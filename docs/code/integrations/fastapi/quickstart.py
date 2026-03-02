from typing import Annotated

from fastapi import FastAPI

from wirio import ServiceCollection
from wirio.annotations import FromServices


class EmailService:
    pass


class UserService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service

    async def create_user(self) -> None:
        pass


app = FastAPI()


@app.post("/users")
async def create_user(
    user_service: Annotated[UserService, FromServices()],  # (1)!
) -> None:
    pass


services = ServiceCollection()
services.configure_fastapi(app)  # (2)!
services.add_transient(EmailService)
services.add_transient(UserService)
