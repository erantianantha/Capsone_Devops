import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://pantrypal:pantrypal@localhost:5432/pantrypal",
)
APP_VERSION = os.getenv("APP_VERSION", "dev")
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
