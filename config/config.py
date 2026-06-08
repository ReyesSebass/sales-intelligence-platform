# config/config.py
import os
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv(dotenv_path="config/.env")

# Configuración de la base de datos
DB_SERVER = os.getenv("DB_SERVER", "localhost\\SQLEXPRESS")
DB_NAME   = os.getenv("DB_NAME", "SalesIntelligenceDB")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

# String de conexión para SQLAlchemy
CONNECTION_STRING = (
    f"mssql+pyodbc://@{DB_SERVER}/{DB_NAME}"
    f"?driver={DB_DRIVER.replace(' ', '+')}"
    f"&Trusted_Connection=yes"
)

# Rutas del proyecto
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW       = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED = os.path.join(BASE_DIR, "data", "processed")
DATA_EXPORTS   = os.path.join(BASE_DIR, "data", "exports")
LOGS_DIR       = os.path.join(BASE_DIR, "logs")

# Configuración general
ENV       = os.getenv("ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")