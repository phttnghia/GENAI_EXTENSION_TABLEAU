import os


class Settings:
    API_PREFIX_V1 = "/v1"
    BACKEND_CORS_ORIGINS = ["*"]
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    AZURE_SQL_SERVER = os.getenv("AZURE_SQL_SERVER", "")
    AZURE_SQL_DATABASE = os.getenv("AZURE_SQL_DATABASE", "")
    AZURE_SQL_USER = os.getenv("AZURE_SQL_USER", "")
    AZURE_SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD", "")
    AZURE_SQL_PORT = os.getenv("AZURE_SQL_PORT", 1433)
    AZURE_SQL_DRIVER = os.getenv("AZURE_SQL_DRIVER", "ODBC Driver 17 for SQL Server")
    AUZRE_SQL_CONN = "mssql+pyodbc://{AZURE_SQL_USER}:{AZURE_SQL_PASSWORD}@{AZURE_SQL_SERVER}:1433/{AZURE_SQL_DATABASE}?driver={AZURE_SQL_DRIVER}&Encrypt=yes&TrustServerCertificate=no"

settings = Settings()
