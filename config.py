import os

basedir = os.path.abspath(os.path.dirname(__file__))

# Configuration settings for the Flask application
# Add your configurations here
# For example:
# SECRET_KEY = 'your_secret_key'
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess' # Added a default secret key

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use in-memory SQLite for tests
    WTF_CSRF_ENABLED = False # Disable CSRF for simpler form testing in unit tests
    SECRET_KEY = 'test-secret-key' # Consistent secret key for tests
