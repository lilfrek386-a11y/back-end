from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    HOST: str
    PORT: int
    USER: str
    PASS: str
    NAME: str

    @property
    def URL(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASS}@{self.HOST}:{self.PORT}/{self.NAME}"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="DB_", extra="ignore")


class RedisConfig(BaseSettings):
    HOST: str
    PORT: int

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="REDIS_", extra="ignore"
    )


class LogConfig(BaseSettings):
    LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="LOG_", extra="ignore"
    )


class JWTConfig(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="JWT_", extra="ignore"
    )


class Auth0Config(BaseSettings):
    DOMAIN: str
    AUDIENCE: str

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="AUTH0_", extra="ignore"
    )


class AppSettings(BaseSettings):
    db: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    log: LogConfig = LogConfig()
    jwt: JWTConfig = JWTConfig()
    auth0: Auth0Config = Auth0Config()


settings = AppSettings()
