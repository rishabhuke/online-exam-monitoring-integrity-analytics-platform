import os

class Config:
    """Configuration class for Candidate Authentication Backend."""
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'default-dev-secret-key-987654321')
    DATABASE_PATH: str = os.path.abspath(
        os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'platform.db'))
    )
