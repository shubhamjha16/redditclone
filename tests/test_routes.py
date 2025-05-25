import pytest
from app.models import User, College, Post, Comment # For creating test data
from app import db

def test_index_page_logged_out(client):
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b"Sign In" in response.data # Should be redirected to login

def test_index_page_logged_in(client, new_user):
    client.post('/login', data={'email_or_username': new_user.username, 'password': 'password'}, follow_redirects=True)
    response = client.get('/')
    assert response.status_code == 200
    # Check for some text that should be on the index page for logged-in users
    # This might change based on actual index.html content for logged-in users
    assert b"Home" in response.data # Assuming "Home" is in the title or a heading
    assert new_user.username.encode() in response.data # Username should be displayed

def test_college_posts_page(client, new_college):
    # Test accessing a college's post page (even if no posts)
    response = client.get(f'/college/{new_college.id}/posts')
    assert response.status_code == 200
    assert new_college.name.encode() in response.data

def test_view_post_page(client, new_user, new_college): # new_post fixture could be useful here
    with client.application.app_context():
        post = Post(title="View Test Post", content="Content to view", author=new_user, college=new_college)
        db.session.add(post)
        db.session.commit()
        post_id = post.id
    
    response = client.get(f'/post/{post_id}')
    assert response.status_code == 200
    assert b"View Test Post" in response.data # Post title
    assert b"Content to view" in response.data # Post content
    assert new_user.username.encode() in response.data # Author's username

def test_non_existent_post_page(client):
    response = client.get('/post/99999') # Assuming post 99999 does not exist
    assert response.status_code == 404

def test_non_existent_college_page(client):
    response = client.get('/college/99999/posts') # Assuming college 99999 does not exist
    assert response.status_code == 404

def test_user_profile_page(client, new_user):
    response = client.get(f'/user/{new_user.username}')
    assert response.status_code == 200
    assert new_user.username.encode() in response.data
    assert new_user.email.encode() in response.data

def test_non_existent_user_profile_page(client):
    response = client.get('/user/nonexistentuser')
    assert response.status_code == 404

def test_search_route_no_query(client):
    response = client.get('/search')
    assert response.status_code == 200
    assert b"Please enter a search term." in response.data # Flash message for empty query

def test_search_route_with_query(client, new_post): # new_post fixture would create a post
     with client.application.app_context():
        # Ensure the post has searchable content
        post = Post.query.get(new_post.id)
        post.title = "Searchable Title Alpha"
        post.content = "Some unique searchable content beta"
        db.session.commit()

     response = client.get('/search?query=Alpha')
     assert response.status_code == 200
     assert b"Search Results for 'Alpha'" in response.data
     assert b"Searchable Title Alpha" in response.data # Check if the post title appears

     response_content = client.get('/search?query=beta')
     assert response_content.status_code == 200
     assert b"Search Results for 'beta'" in response_content.data
     assert b"unique searchable content beta" in response_content.data

# new_post fixture is now in conftest.py
