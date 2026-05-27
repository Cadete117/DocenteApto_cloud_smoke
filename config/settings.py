import os
from dotenv import load_dotenv

load_dotenv()

UTP_USER = os.getenv("UTP_USER")
UTP_PASS = os.getenv("UTP_PASS")

MS_USER = os.getenv("MS_USER")
MS_PASS = os.getenv("MS_PASS")

EXCEL_URL = os.getenv("EXCEL_URL", "https://example.invalid/fake.xlsx")

OUTPUT_DIR = "output"
REPORTES_DIR = "reportes"
DB_PATH = "data/database.db"
