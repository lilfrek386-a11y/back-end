from app.core.postgres import session_factory
from app.repositories.company import CompanyRepository
from app.repositories.user import UserRepository


class UnitOfWork:
    def __init__(self, session_factory=session_factory):
        self._session_factory = session_factory

    async def __aenter__(self):
        self.session = self._session_factory()
        self.users = UserRepository(self.session)
        self.companies = CompanyRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, tb):
        try:
            if exc_type is None:
                await self.session.commit()
            else:
                await self.session.rollback()
        finally:
            await self.session.close()
            self.session = None
