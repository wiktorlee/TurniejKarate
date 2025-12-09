import os
from dotenv import load_dotenv

load_dotenv()

#Baza danych
DB_URL = os.getenv("DATABASE_URL")
SCHEMA = "karate"

#Flask
SECRET_KEY = os.getenv("SECRET_KEY", "dev")

