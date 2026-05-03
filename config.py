import os
from dotenv import load_dotenv

# Load from .env in the current directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

class Config:
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://sports_league_owner:sports_league_password@localhost:5432/sports_league')
    
    # Debug: Print loaded values
    print(f"[DEBUG] DATABASE_URL loaded as: {DATABASE_URL}")
