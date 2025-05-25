import pytest
from app import app as flask_app, db
from app.models import User, College, Post, Comment # Import your models
from config import TestConfig # Import the TestConfig

@pytest.fixture(scope='session')
def app():
    """Session-wide test Flask application."""
    flask_app.config.from_object(TestConfig)

    # Establish an application context before creating the test database tables
    with flask_app.app_context():
        db.create_all() # Create tables for the in-memory SQLite database

    yield flask_app # provide the app first

    # After the session, you might want to tear down the in-memory database,
    # but for :memory: SQLite, it's often not strictly necessary as it's torn down when connection closes.
    # with flask_app.app_context():
    #     db.drop_all()


@pytest.fixture(scope='function') # Use 'function' scope for client to get a fresh one per test
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def init_database(app):
    """Fixture to create and tear down database for each test function."""
    with app.app_context():
        db.create_all()
        yield db # provide the database connection
        db.session.remove() # Ensure session is closed
        db.drop_all() # Clean up database after each test

@pytest.fixture(scope='function')
def new_user(init_database):
    """Fixture to create a new user."""
    # Requires app_context for db operations
    with init_database.app.app_context():
        user = User(username='testuser', email='test@example.com', role=User.ROLE_STUDENT)
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture(scope='function')
def new_college(init_database):
    """Fixture to create a new college."""
    with init_database.app.app_context():
        college = College(name='Test College', location='Test Location')
        db.session.add(college)
        db.session.commit()
        return college

@pytest.fixture(scope='function')
def new_post(init_database, new_user, new_college):
    """Fixture to create a new post."""
    with init_database.app.app_context():
        post = Post(title="A Sample Post Title", 
                    content="This is the content of a sample post.", 
                    user_id=new_user.id, 
                    college_id=new_college.id)
        db.session.add(post)
        db.session.commit()
        return post
