import os
from pydantic import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Portfolio Optimization Agent"
    API_PREFIX: str = "/api"
    DEBUG: bool = os.getenv("ENV", "development") == "development"
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY", "")
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/portfolio_db")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/portfolio_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    INFLUXDB_URL: str = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    INFLUXDB_TOKEN: str = os.getenv("INFLUXDB_TOKEN", "")
    INFLUXDB_ORG: str = os.getenv("INFLUXDB_ORG", "portfolio")
    INFLUXDB_BUCKET: str = os.getenv("INFLUXDB_BUCKET", "market_data")
    
    # LLM settings
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Cache settings
    CACHE_EXPIRY: int = int(os.getenv("CACHE_EXPIRY", "300"))  # Default 5 minutes
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "debug")

    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()