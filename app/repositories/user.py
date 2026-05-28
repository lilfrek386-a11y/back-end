from app.repositories.base import BaseRepository
from app.models.user import User

class UserRepository(BaseRepository[User]):
    model = User
