import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Application Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-secret-key'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///rights_fixation.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Server Configuration
    PORT = 5001  # Default port for Rights Fixation System
