import os
from dotenv import load_dotenv

# Load from .env in the current directory, but don't override existing variables
# This is important for Railway where DATABASE_URL is automatically injected
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=False)

class Config:
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://sports_league_owner:sports_league_password@localhost:5432/sports_league')
