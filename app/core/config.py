from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Billing Software"
    BACKEND_URL: str = "http://127.0.0.1:8000"
    FRONTEND_URL: str = "http://127.0.0.1:5000"
    DATABASE_URL: str = "sqlite:///billing.db"
    
    # MongoDB Settings
    MONGO_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "billing_db"

    # Security Settings
    SECRET_KEY: str = "insecure-secret-key-for-dev"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_V1_STR: str = "/api/v1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
