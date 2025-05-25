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


# --- Tests for User Profile and Follow/Unfollow Routes ---

def test_edit_profile_route(test_auth_client, init_database, new_user):
    """Test the /edit_profile route for GET and POST requests."""
    # test_auth_client is authenticated as new_user
    client = test_auth_client
    user = new_user # This is the currently logged-in user via test_auth_client

    with client.application.app_context():
        # Ensure user is in the session for lazy loading attributes if not already loaded
        db.session.add(user) 
        db.session.commit() # Commit to ensure user is fully in DB for subsequent queries

        # --- Test GET request ---
        response_get = client.get('/edit_profile')
        assert response_get.status_code == 200
        assert user.username.encode() in response_get.data
        if user.bio: # Bio can be None initially
            assert user.bio.encode() in response_get.data
        if user.profile_picture_url: # Can be None
            assert user.profile_picture_url.encode() in response_get.data
        assert b"Edit Your Profile" in response_get.data

        # --- Test POST request (successful update) ---
        new_username_val = "updateduser"
        new_bio_val = "This is an updated bio."
        new_pic_url_val = "http://example.com/newpic.jpg"
        
        response_post_success = client.post('/edit_profile', data={
            'username': new_username_val,
            'bio': new_bio_val,
            'profile_picture_url': new_pic_url_val
        }, follow_redirects=True)
        
        assert response_post_success.status_code == 200 # After redirect to profile
        assert b"Your profile has been updated!" in response_post_success.data # Flash message
        
        updated_user = User.query.get(user.id)
        assert updated_user.username == new_username_val
        assert updated_user.bio == new_bio_val
        assert updated_user.profile_picture_url == new_pic_url_val
        # Ensure the route redirects to the new username's profile if username changed
        assert updated_user.username.encode() in response_post_success.data # Check if new username is on redirected page

        # --- Test POST request (username taken) ---
        # Create another user
        other_user = User(username='otheruser', email='other@example.com')
        other_user.set_password('password')
        db.session.add(other_user)
        db.session.commit()

        # Attempt to update current user (originally updateduser) to 'otheruser'
        response_post_taken = client.post('/edit_profile', data={
            'username': other_user.username, # Attempt to take other_user's username
            'bio': 'Trying to take username.',
            'profile_picture_url': ''
        }, follow_redirects=True)

        assert response_post_taken.status_code == 200 # Should re-render form
        assert b"That username is already taken." in response_post_taken.data # Error message
        
        current_user_still_updated = User.query.get(user.id)
        # Username should not have changed to other_user.username; should still be new_username_val
        assert current_user_still_updated.username == new_username_val 
        assert current_user_still_updated.bio != 'Trying to take username.' # Bio should also not change on this error

def test_follow_unfollow_routes(test_auth_client, init_database, new_user):
    """Test /follow/<username> and /unfollow/<username> routes."""
    client = test_auth_client # Authenticated as new_user (u1)
    u1 = new_user

    with client.application.app_context():
        db.session.add(u1) # Ensure u1 is in session

        u2 = User(username='user2follow', email='user2follow@example.com')
        u2.set_password('password')
        db.session.add(u2)
        db.session.commit()
        u2_id = u2.id # Store id before potential detachment

        # --- Test follow ---
        response_follow = client.post(f'/follow/{u2.username}', follow_redirects=True)
        assert response_follow.status_code == 200 # Redirects to u2's profile
        assert f"You are now following {u2.username}.".encode() in response_follow.data
        
        # Re-fetch users from DB to check relationship
        u1_db = User.query.get(u1.id)
        u2_db = User.query.get(u2_id)
        assert u1_db.is_following(u2_db)

        # --- Test unfollow ---
        response_unfollow = client.post(f'/unfollow/{u2.username}', follow_redirects=True)
        assert response_unfollow.status_code == 200 # Redirects to u2's profile
        assert f"You have unfollowed {u2.username}.".encode() in response_unfollow.data
        
        u1_db_after_unfollow = User.query.get(u1.id)
        u2_db_after_unfollow = User.query.get(u2_id) # u2_id is stable
        assert not u1_db_after_unfollow.is_following(u2_db_after_unfollow)

        # --- Test self-follow prevention ---
        response_self_follow = client.post(f'/follow/{u1.username}', follow_redirects=True)
        assert response_self_follow.status_code == 200 # Stays on own profile or redirects there
        assert b"You cannot follow yourself." in response_self_follow.data
        
        u1_db_after_self_follow_attempt = User.query.get(u1.id)
        assert u1_db_after_self_follow_attempt.followed.count() == 0

def test_follow_route_auth_required(client, init_database): # Using unauthenticated client
    """Test that /follow route requires authentication."""
    with client.application.app_context():
        target_user = User(username='targetuserauth', email='target@auth.com')
        target_user.set_password('password')
        db.session.add(target_user)
        db.session.commit()

    response = client.post(f'/follow/{target_user.username}', follow_redirects=False) # Don't follow redirects to check location
    assert response.status_code == 302 # Redirect
    assert '/login' in response.location # Redirects to login

def test_user_profile_displays_new_info(client, test_auth_client, init_database, new_user):
    """Test that user profile page displays bio, profile picture, and follow/unfollow buttons."""
    # u_test is the user whose profile is being viewed
    # current_user is the user viewing the profile (from test_auth_client)
    current_user_for_view = new_user # From test_auth_client fixture

    with client.application.app_context(): # Use client.application.app_context for db ops
        u_test = User(username='testprofileuser', email='testprofile@example.com',
                      bio='This is a test bio for display.', 
                      profile_picture_url='http://example.com/profile.jpg')
        u_test.set_password('password')
        db.session.add(u_test)
        db.session.add(current_user_for_view) # Ensure viewing user is in session
        db.session.commit()

        # --- Test viewing another user's profile (u_test) as an authenticated user (current_user_for_view) ---
        response_view_other = test_auth_client.get(f'/user/{u_test.username}')
        assert response_view_other.status_code == 200
        assert u_test.bio.encode() in response_view_other.data
        assert u_test.profile_picture_url.encode() in response_view_other.data
        assert b'Follow</button>' in response_view_other.data or b'value="Follow"' in response_view_other.data # Check for Follow button

        # current_user_for_view follows u_test
        current_user_for_view.follow(u_test)
        db.session.commit()

        response_view_other_after_follow = test_auth_client.get(f'/user/{u_test.username}')
        assert response_view_other_after_follow.status_code == 200
        assert u_test.bio.encode() in response_view_other_after_follow.data
        assert u_test.profile_picture_url.encode() in response_view_other_after_follow.data
        assert b'Unfollow</button>' in response_view_other_after_follow.data or b'value="Unfollow"' in response_view_other_after_follow.data # Check for Unfollow button

        # --- Test viewing own profile (current_user_for_view) ---
        # Update current_user_for_view's profile to have specific info
        current_user_for_view.bio = "My own bio for my profile."
        current_user_for_view.profile_picture_url = "http://example.com/myownpic.jpg"
        db.session.commit()

        response_view_self = test_auth_client.get(f'/user/{current_user_for_view.username}')
        assert response_view_self.status_code == 200
        assert current_user_for_view.bio.encode() in response_view_self.data
        assert current_user_for_view.profile_picture_url.encode() in response_view_self.data
        assert b'Edit Profile' in response_view_self.data # Check for Edit Profile button
        assert b'Follow</button>' not in response_view_self.data # Should not see follow button for self
        assert b'value="Follow"' not in response_view_self.data 
        assert b'Unfollow</button>' not in response_view_self.data # Should not see unfollow button for self
        assert b'value="Unfollow"' not in response_view_self.data
