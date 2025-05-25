import pytest
from app.models import User, College
from app import db

def test_register_page(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b"Register" in response.data

def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Sign In" in response.data # Assuming 'Sign In' is in login.html title or h2

def test_successful_registration_and_login(client, init_database, new_college):
    # Registration
    response_register = client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'college': new_college.id,
        'role': User.ROLE_STUDENT
    }, follow_redirects=True)
    assert response_register.status_code == 200 # Should redirect to login
    assert b"Congratulations, you are now a registered user!" in response_register.data
    assert b"Sign In" in response_register.data # Check if on login page

    # Login
    response_login = client.post('/login', data={
        'email_or_username': 'newuser@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert response_login.status_code == 200
    assert b"Welcome back, newuser!" in response_login.data
    assert b"Home" in response_login.data # Assuming "Home" is title of index page after login

def test_registration_existing_username(client, new_user): # new_user fixture creates 'testuser'
    response = client.post('/register', data={
        'username': 'testuser', # Existing username
        'email': 'another@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'college': '1', # Assuming a college with id 1 exists or handle this better
        'role': User.ROLE_STUDENT
    }, follow_redirects=True)
    assert response.status_code == 200 # Stays on registration page or re-renders
    assert b"That username is already taken." in response.data

def test_registration_existing_email(client, new_user, new_college):
    response = client.post('/register', data={
        'username': 'anotheruser',
        'email': 'test@example.com', # Existing email from new_user
        'password': 'password123',
        'confirm_password': 'password123',
        'college': new_college.id,
        'role': User.ROLE_STUDENT
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"That email is already in use." in response.data

def test_login_invalid_password(client, new_user):
    response = client.post('/login', data={
        'email_or_username': 'testuser',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200 # Stays on login page
    assert b"Invalid username/email or password" in response.data

def test_login_nonexistent_user(client):
    response = client.post('/login', data={
        'email_or_username': 'nouser',
        'password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid username/email or password" in response.data
    
def test_logout(client, new_user):
    # First, log in the user
    client.post('/login', data={
        'email_or_username': new_user.username,
        'password': 'password' # Assuming 'password' is the one set by new_user fixture
    }, follow_redirects=True)

    # Then, test logout
    response_logout = client.get('/logout', follow_redirects=True)
    assert response_logout.status_code == 200
    assert b"You have been logged out." in response_logout.data
    assert b"Sign In" in response_logout.data # Should be back on a page with login link or login page

def test_access_protected_route_logged_out(client):
    response = client.get('/create_post', follow_redirects=True)
    assert response.status_code == 200 # Redirects to login
    assert b"Sign In" in response.data # Should be on login page
    assert b"Please log in to access this page." in response.data # Flash message

def test_access_protected_route_logged_in(client, new_user, new_college):
    # Associate user with college for create_post route
    with client.application.app_context():
        user = User.query.filter_by(username=new_user.username).first()
        user.college_id = new_college.id
        db.session.commit()

    client.post('/login', data={
        'email_or_username': new_user.username,
        'password': 'password'
    }, follow_redirects=True)
    
    response = client.get('/create_post', follow_redirects=True)
    assert response.status_code == 200
    assert b"Create Post" in response.data # Check for content of the create_post page
    assert b"Sign In" not in response.data # Should not be redirected to login
