import asyncio

from wirio import ServiceCollection


class EmailService:
    pass


class UserService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service

    async def create_user(self) -> None:
        pass


services = ServiceCollection()
services.add_transient(EmailService)
services.add_transient(UserService)


async def main() -> None:
    async with services.build_service_provider() as service_provider:
        user_service = await service_provider.get_required_service(UserService)
        await user_service.create_user()


if __name__ == "__main__":
    asyncio.run(main())
