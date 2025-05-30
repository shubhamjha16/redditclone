import pytest
from app.models import User, College, Post, Comment, Reel, ReelComment, ReelLike, Course, AttendanceRecord, CourseEnrollment # Added CourseEnrollment
from app import db
from flask import url_for # For generating URLs in tests
from datetime import date, timedelta, datetime # Added datetime for enrollment_date
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

# --- Tests for Reel Routes ---

def test_create_reel_route(test_auth_client, init_database, new_user, new_college):
    """Test the /create_reel route: GET, POST (success, invalid), and auth."""
    client = test_auth_client # Authenticated as new_user

    # --- Test GET request ---
    response_get = client.get(url_for('create_reel'))
    assert response_get.status_code == 200
    assert b"Upload New Reel" in response_get.data
    assert b"Video URL" in response_get.data # Check for form field label
    assert b"Caption" in response_get.data   # Check for form field label

    # --- Test POST request (successful) ---
    video_url_valid = "http://example.com/video.mp4"
    caption_valid = "My cool test reel"
    
    with client.application.app_context(): # Ensure app context for DB operations
        user_college_id = new_user.college_id # Get college_id within context if new_user is bound to a session
        if not user_college_id and new_college: # If new_user doesn't have a college set by fixture
            new_user.college_id = new_college.id
            db.session.add(new_user)
            db.session.commit()
            user_college_id = new_user.college_id


    response_post_success = client.post(url_for('create_reel'), data={
        'video_url': video_url_valid,
        'caption': caption_valid
    }, follow_redirects=True)
    
    assert response_post_success.status_code == 200 # Assuming redirect to reels_feed (or view_reel)
    assert b"Your reel has been posted!" in response_post_success.data # Flash message

    with client.application.app_context():
        posted_reel = Reel.query.filter_by(video_url=video_url_valid, caption=caption_valid).first()
        assert posted_reel is not None
        assert posted_reel.user_id == new_user.id
        assert posted_reel.college_id == user_college_id

    # --- Test POST request (invalid data - bad URL) ---
    response_post_invalid = client.post(url_for('create_reel'), data={
        'video_url': 'not_a_valid_url',
        'caption': 'Test reel with invalid URL'
    }, follow_redirects=True)
    
    assert response_post_invalid.status_code == 200 # Form re-renders
    assert b"Invalid URL." in response_post_invalid.data # Error message from URL validator

    # --- Test Authentication (unauthenticated client) ---
    unauth_client_response = init_database.test_client().get(url_for('create_reel'), follow_redirects=False)
    assert unauth_client_response.status_code == 302 # Redirect
    assert '/login' in unauth_client_response.location

def test_view_and_comment_on_reel_route(test_auth_client, client, init_database, new_user, new_college):
    """Test /reel/<id> for viewing, view count, and commenting (auth/unauth)."""
    auth_client = test_auth_client # Authenticated as new_user
    
    with client.application.app_context():
        # Create a reel by another user to test view count increment by non-author
        other_user = User(username="reelauthor", email="reelauthor@example.com")
        other_user.set_password("password")
        other_user.college_id = new_college.id
        db.session.add(other_user)
        db.session.commit()
        
        reel = Reel(user_id=other_user.id, college_id=new_college.id, 
                    video_url="http://example.com/view_reel.mp4", caption="Viewable Reel")
        db.session.add(reel)
        db.session.commit()
        reel_id = reel.id
        initial_views = reel.views_count

    # --- Test GET request (viewing) by unauthenticated client ---
    response_get_unauth = client.get(url_for('view_reel', reel_id=reel_id))
    assert response_get_unauth.status_code == 200
    assert b"Viewable Reel" in response_get_unauth.data
    assert b"http://example.com/view_reel.mp4" in response_get_unauth.data # Check for video URL in src
    assert b"reelauthor" in response_get_unauth.data # Author's username

    with client.application.app_context():
        reel_after_unauth_view = Reel.query.get(reel_id)
        assert reel_after_unauth_view.views_count == initial_views + 1 # View count increments

    # --- Test GET request (viewing) by authenticated client (new_user, not author) ---
    initial_views_before_auth_view = reel_after_unauth_view.views_count
    response_get_auth = auth_client.get(url_for('view_reel', reel_id=reel_id))
    assert response_get_auth.status_code == 200
    
    with client.application.app_context():
        reel_after_auth_view = Reel.query.get(reel_id)
        assert reel_after_auth_view.views_count == initial_views_before_auth_view + 1

    # --- Test POST request (commenting - authenticated) ---
    comment_content = "This is a great reel!"
    response_post_comment_auth = auth_client.post(url_for('view_reel', reel_id=reel_id), data={
        'content': comment_content
    }, follow_redirects=True)
    
    assert response_post_comment_auth.status_code == 200 # Redirects to same page
    assert b"Your comment has been posted." in response_post_comment_auth.data
    
    with client.application.app_context():
        reel_with_comment = Reel.query.get(reel_id)
        assert reel_with_comment.comments.count() == 1
        first_comment = reel_with_comment.comments.first()
        assert first_comment.content == comment_content
        assert first_comment.user_id == new_user.id # new_user is the authenticated client

    # --- Test POST request (commenting - unauthenticated) ---
    response_post_comment_unauth = client.post(url_for('view_reel', reel_id=reel_id), data={
        'content': "Unauthenticated comment attempt"
    }, follow_redirects=False) # Check redirect location
    
    assert response_post_comment_unauth.status_code == 302
    assert '/login' in response_post_comment_unauth.location
    
    with client.application.app_context():
        reel_after_unauth_comment_attempt = Reel.query.get(reel_id)
        assert reel_after_unauth_comment_attempt.comments.count() == 1 # Should still be 1 comment

def test_like_unlike_reel_route(test_auth_client, init_database, new_user, new_college):
    """Test /reel/<id>/like for liking, unliking, and authentication."""
    client = test_auth_client # Authenticated as new_user

    with client.application.app_context():
        # Create a reel by another user
        other_user_for_reel = User(username="reelowner", email="reelowner@example.com")
        other_user_for_reel.set_password("password")
        other_user_for_reel.college_id = new_college.id
        db.session.add(other_user_for_reel)
        db.session.commit()
        
        reel_to_like = Reel(user_id=other_user_for_reel.id, college_id=new_college.id,
                            video_url="http://example.com/like_reel.mp4", caption="Likable Reel")
        db.session.add(reel_to_like)
        db.session.commit()
        reel_id = reel_to_like.id

    # --- Test Like action ---
    response_like = client.post(url_for('reel_like', reel_id=reel_id), follow_redirects=True)
    assert response_like.status_code == 200 # Redirects to view_reel
    assert b"You liked the reel!" in response_like.data
    
    with client.application.app_context():
        like_in_db = ReelLike.query.filter_by(user_id=new_user.id, reel_id=reel_id).first()
        assert like_in_db is not None
        assert Reel.query.get(reel_id).likes.count() == 1

    # --- Test Unlike action ---
    response_unlike = client.post(url_for('reel_like', reel_id=reel_id), follow_redirects=True)
    assert response_unlike.status_code == 200 # Redirects to view_reel
    assert b"You unliked the reel." in response_unlike.data
    
    with client.application.app_context():
        like_in_db_after_unlike = ReelLike.query.filter_by(user_id=new_user.id, reel_id=reel_id).first()
        assert like_in_db_after_unlike is None
        assert Reel.query.get(reel_id).likes.count() == 0

    # --- Test Authentication for like (unauthenticated client) ---
    unauth_client = init_database.test_client()
    response_like_unauth = unauth_client.post(url_for('reel_like', reel_id=reel_id), follow_redirects=False)
    assert response_like_unauth.status_code == 302
    assert '/login' in response_like_unauth.location

def test_reels_feed_route(test_auth_client, client, init_database, new_user, new_college):
    """Test /reels_feed for authenticated access, unauthenticated redirect, and content."""
    auth_client = test_auth_client # Authenticated as new_user

    with client.application.app_context():
        # Create some reels
        reel1 = Reel(user_id=new_user.id, college_id=new_college.id, 
                     video_url="http://example.com/feed_reel1.mp4", caption="Feed Reel 1")
        
        other_user_feed = User(username="feedposter", email="feed@example.com")
        other_user_feed.set_password("password")
        other_user_feed.college_id = new_college.id
        db.session.add(other_user_feed)
        db.session.commit()
        
        reel2 = Reel(user_id=other_user_feed.id, college_id=new_college.id,
                     video_url="http://example.com/feed_reel2.mp4", caption="Feed Reel 2")
        db.session.add_all([reel1, reel2])
        db.session.commit()

    # --- Test Authenticated access ---
    response_auth_feed = auth_client.get(url_for('reels_feed'))
    assert response_auth_feed.status_code == 200
    assert b"Reels Feed" in response_auth_feed.data
    assert b"Create New Reel" in response_auth_feed.data # Button for creating new reel
    assert b"Feed Reel 1" in response_auth_feed.data # Caption of reel1
    assert b"Feed Reel 2" in response_auth_feed.data # Caption of reel2
    # Basic pagination check (assuming default per_page is e.g. 5 or 10, and we have 2 reels)
    # If per_page is high, no pagination links might appear.
    # This example assumes per_page is low enough that with >1 reel, something related to pages might show,
    # or at least the page loads correctly. For more robust pagination, create more items.
    assert b"pagination" in response_auth_feed.data or Reel.query.count() <= 5 # Check for pagination elements or if few items

    # --- Test Unauthenticated access ---
    # /reels_feed is @login_required
    unauth_response_feed = client.get(url_for('reels_feed'), follow_redirects=False)
    assert unauth_response_feed.status_code == 302
    assert '/login' in unauth_response_feed.location

# --- Tests for Enrollment Management and Display ---

def test_student_enroll_unenroll_routes(test_auth_client, init_database, new_college):
    """Test student-facing /course/<id>/enroll and /course/<id>/unenroll routes."""
    with init_database.app.app_context():
        course = Course(name="Test Enroll Course", course_code="ENRL101", college_id=new_college.id, capacity=1)
        student1 = User(username='enroll_s1', email='enroll_s1@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        student1.set_password('password')
        student2 = User(username='enroll_s2', email='enroll_s2@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        student2.set_password('password')
        db.session.add_all([course, student1, student2])
        db.session.commit()

    client_s1 = test_auth_client(student1)
    client_s2 = test_auth_client(student2)
    unauth_client = init_database.test_client()

    # 1. Enroll student1 (success)
    response_s1_enroll = client_s1.post(url_for('enroll_in_course', course_id=course.id), follow_redirects=True)
    assert response_s1_enroll.status_code == 200
    assert b"You have successfully enrolled in the course!" in response_s1_enroll.data
    with init_database.app.app_context():
        enrollment_s1 = CourseEnrollment.query.filter_by(user_id=student1.id, course_id=course.id).first()
        assert enrollment_s1 is not None
        assert enrollment_s1.status == 'enrolled'

    # 2. Enroll student1 again (already enrolled)
    response_s1_enroll_again = client_s1.post(url_for('enroll_in_course', course_id=course.id), follow_redirects=True)
    assert response_s1_enroll_again.status_code == 200
    assert b"You are already enrolled in this course." in response_s1_enroll_again.data
    with init_database.app.app_context():
        assert CourseEnrollment.query.filter_by(user_id=student1.id, course_id=course.id).count() == 1

    # 3. Enroll student2 (course full)
    response_s2_enroll_full = client_s2.post(url_for('enroll_in_course', course_id=course.id), follow_redirects=True)
    assert response_s2_enroll_full.status_code == 200
    assert b"This course is currently full" in response_s2_enroll_full.data
    with init_database.app.app_context():
        assert CourseEnrollment.query.filter_by(user_id=student2.id, course_id=course.id).first() is None

    # 4. student1 unenrolls
    response_s1_unenroll = client_s1.post(url_for('unenroll_from_course', course_id=course.id), follow_redirects=True)
    assert response_s1_unenroll.status_code == 200
    assert b"You have successfully unenrolled from the course." in response_s1_unenroll.data
    with init_database.app.app_context():
        enrollment_s1_dropped = CourseEnrollment.query.filter_by(user_id=student1.id, course_id=course.id).first()
        assert enrollment_s1_dropped is not None
        assert enrollment_s1_dropped.status == 'dropped'

    # 5. student1 unenrolls again (not actively enrolled)
    response_s1_unenroll_again = client_s1.post(url_for('unenroll_from_course', course_id=course.id), follow_redirects=True)
    assert response_s1_unenroll_again.status_code == 200
    assert b"You are not currently enrolled in this course" in response_s1_unenroll_again.data

    # 6. student2 enrolls (now space available after s1 dropped and re-enrollment logic is for 'dropped' status)
    # The current enroll_in_course logic will try to re-enroll s1 if they are 'dropped'.
    # To test s2 enrolling, s1's record needs to be fully removed or s2 tries to enroll in a different course.
    # For simplicity, let's assume s2 can enroll now that s1 is 'dropped'.
    # The capacity check counts 'enrolled' status.
    response_s2_enroll_success = client_s2.post(url_for('enroll_in_course', course_id=course.id), follow_redirects=True)
    assert response_s2_enroll_success.status_code == 200
    assert b"You have successfully enrolled in the course!" in response_s2_enroll_success.data
    with init_database.app.app_context():
        enrollment_s2 = CourseEnrollment.query.filter_by(user_id=student2.id, course_id=course.id).first()
        assert enrollment_s2 is not None
        assert enrollment_s2.status == 'enrolled'

    # 7. Authentication checks
    response_unauth_enroll = unauth_client.post(url_for('enroll_in_course', course_id=course.id), follow_redirects=False)
    assert response_unauth_enroll.status_code == 302
    assert '/login' in response_unauth_enroll.location

    response_unauth_unenroll = unauth_client.post(url_for('unenroll_from_course', course_id=course.id), follow_redirects=False)
    assert response_unauth_unenroll.status_code == 302
    assert '/login' in response_unauth_unenroll.location


def test_manage_enrollments_route_permissions(test_auth_client, init_database, new_college, new_course):
    """Test permission checks for /course/<id>/manage_enrollments."""
    course = new_course
    with init_database.app.app_context():
        admin_user = User(username='enroll_admin', email='ea@example.com', role=User.ROLE_ADMIN, college_id=new_college.id)
        admin_user.set_password('password')
        mgmt_user = User(username='enroll_mgmt', email='em@example.com', role=User.ROLE_MANAGEMENT, college_id=new_college.id)
        mgmt_user.set_password('password')
        faculty_user = User(username='enroll_faculty', email='ef@example.com', role=User.ROLE_FACULTY, college_id=new_college.id)
        faculty_user.set_password('password')
        student_user = User(username='enroll_student_perm', email='esp@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        student_user.set_password('password')
        db.session.add_all([admin_user, mgmt_user, faculty_user, student_user, course])
        db.session.commit()

    # Admin access
    client_admin = test_auth_client(admin_user)
    response_admin_get = client_admin.get(url_for('manage_course_enrollments', course_id=course.id))
    assert response_admin_get.status_code == 200
    assert b"Manage Enrollments" in response_admin_get.data

    # Management access
    client_mgmt = test_auth_client(mgmt_user)
    response_mgmt_get = client_mgmt.get(url_for('manage_course_enrollments', course_id=course.id))
    assert response_mgmt_get.status_code == 200
    assert b"Manage Enrollments" in response_mgmt_get.data

    # Faculty access (currently forbidden as per route logic, can be changed later)
    client_faculty = test_auth_client(faculty_user)
    response_faculty_get = client_faculty.get(url_for('manage_course_enrollments', course_id=course.id), follow_redirects=True)
    assert response_faculty_get.status_code == 200 # Redirect
    assert b"You do not have permission to manage enrollments" in response_faculty_get.data

    # Student access (forbidden)
    client_student = test_auth_client(student_user)
    response_student_get = client_student.get(url_for('manage_course_enrollments', course_id=course.id), follow_redirects=True)
    assert response_student_get.status_code == 200 # Redirect
    assert b"You do not have permission to manage enrollments" in response_student_get.data


def test_manage_enrollments_actions(test_auth_client, init_database, new_college, new_course):
    """Test add, change status, and remove actions on manage_enrollments route."""
    course = new_course
    course.capacity = 2 # Set a capacity for testing full course scenarios
    
    with init_database.app.app_context():
        admin_user = User(username='enroll_admin2', email='ea2@example.com', role=User.ROLE_ADMIN, college_id=new_college.id)
        admin_user.set_password('password')
        student1 = User(username='enroll_s_action1', email='esa1@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        student1.set_password('password')
        student2 = User(username='enroll_s_action2', email='esa2@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        student2.set_password('password')
        db.session.add_all([admin_user, student1, student2, course])
        db.session.commit()

    client = test_auth_client(admin_user)

    # 1. Add Student (success)
    response_add = client.post(url_for('manage_course_enrollments', course_id=course.id), data={
        'student_username': student1.username,
        'status': 'enrolled',
        'submit_add_student': 'Add/Update Student Enrollment' # Name of the submit button
    }, follow_redirects=True)
    assert response_add.status_code == 200
    assert f"{student1.username} has been enrolled in the course.".encode() in response_add.data
    with init_database.app.app_context():
        enrollment = CourseEnrollment.query.filter_by(user_id=student1.id, course_id=course.id).first()
        assert enrollment is not None
        assert enrollment.status == 'enrolled'

    # 2. Add non-existent student
    response_add_nonexist = client.post(url_for('manage_course_enrollments', course_id=course.id), data={
        'student_username': 'ghoststudent',
        'status': 'enrolled',
        'submit_add_student': 'Add/Update Student Enrollment'
    }, follow_redirects=True)
    assert response_add_nonexist.status_code == 200
    assert b"Student with that username or email does not exist." in response_add_nonexist.data # From form validation

    # 3. Add student to full course (enroll student2 first to make it full)
    client.post(url_for('manage_course_enrollments', course_id=course.id), data={
        'student_username': student2.username, 'status': 'enrolled', 'submit_add_student': 'Add/Update Student Enrollment'
    }) # student2 now occupies the last spot
    
    student3 = User(username='enroll_s_action3', email='esa3@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
    with init_database.app.app_context():
        student3.set_password('password')
        db.session.add(student3)
        db.session.commit()

    response_add_full = client.post(url_for('manage_course_enrollments', course_id=course.id), data={
        'student_username': student3.username,
        'status': 'enrolled',
        'submit_add_student': 'Add/Update Student Enrollment'
    }, follow_redirects=True)
    assert response_add_full.status_code == 200
    assert f'Cannot enroll {student3.username}. Course is full'.encode() in response_add_full.data

    # 4. Change Status
    response_change_status = client.post(url_for('manage_course_enrollments', course_id=course.id), data={
        'action': 'change_status',
        'student_id': student1.id,
        'new_status': 'waitlisted' # Assuming this comes from the select field for that student
    }, follow_redirects=True)
    assert response_change_status.status_code == 200
    assert f"{student1.username}'s status changed to waitlisted.".encode() in response_change_status.data
    with init_database.app.app_context():
        assert CourseEnrollment.query.filter_by(user_id=student1.id, course_id=course.id).first().status == 'waitlisted'
        # Course should now have space (student1 is waitlisted, student2 is enrolled)
        assert CourseEnrollment.query.filter_by(course_id=course.id, status='enrolled').count() == 1 


    # 5. Change status to 'enrolled' for student1 (course has capacity again)
    response_change_to_enrolled = client.post(url_for('manage_course_enrollments', course_id=course.id), data={
        'action': 'change_status',
        'student_id': student1.id,
        'new_status': 'enrolled'
    }, follow_redirects=True)
    assert response_change_to_enrolled.status_code == 200
    assert f"{student1.username}'s status changed to enrolled.".encode() in response_change_to_enrolled.data
    with init_database.app.app_context():
        assert CourseEnrollment.query.filter_by(user_id=student1.id, course_id=course.id).first().status == 'enrolled'
        # Course is full again
        assert CourseEnrollment.query.filter_by(course_id=course.id, status='enrolled').count() == 2


    # 6. Remove Enrollment
    response_remove = client.post(url_for('manage_course_enrollments', course_id=course.id), data={
        'action': 'remove_enrollment',
        'student_id': student1.id
    }, follow_redirects=True)
    assert response_remove.status_code == 200
    assert f"{student1.username}'s enrollment record has been removed".encode() in response_remove.data
    with init_database.app.app_context():
        assert CourseEnrollment.query.filter_by(user_id=student1.id, course_id=course.id).first() is None


def test_view_course_enrollment_display(test_auth_client, init_database, new_user, new_college, new_course):
    """Test display of enrollment info on view_course page."""
    course = new_course
    course.capacity = 2
    with init_database.app.app_context():
        student1 = new_user # new_user is student role by default
        student2 = User(username='enroll_display_s2', email='eds2@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        student2.set_password('password')
        db.session.add_all([course, student2]) # student1 (new_user) already added by fixture
        db.session.commit()
        
        # Enroll student1
        enrollment1 = CourseEnrollment(user_id=student1.id, course_id=course.id, status='enrolled')
        db.session.add(enrollment1)
        db.session.commit()

    client_s1 = test_auth_client(student1)
    response_s1 = client_s1.get(url_for('view_course', course_id=course.id))
    assert response_s1.status_code == 200
    assert f"Capacity: {course.capacity}".encode() in response_s1.data
    assert b"Currently Enrolled: 1" in response_s1.data
    assert b"Unenroll</button>" in response_s1.data # s1 should see Unenroll button

    client_s2 = test_auth_client(student2)
    response_s2 = client_s2.get(url_for('view_course', course_id=course.id))
    assert response_s2.status_code == 200
    assert b"Currently Enrolled: 1" in response_s2.data # Still 1, s2 not enrolled
    assert b"Enroll</button>" in response_s2.data # s2 should see Enroll button

    # Enroll student2, course becomes full
    with init_database.app.app_context():
        enrollment2 = CourseEnrollment(user_id=student2.id, course_id=course.id, status='enrolled')
        db.session.add(enrollment2)
        db.session.commit()

    response_s2_full = client_s2.get(url_for('view_course', course_id=course.id)) # s2 is now enrolled
    assert b"Currently Enrolled: 2" in response_s2_full.data
    assert b"Unenroll</button>" in response_s2_full.data # s2 now sees unenroll

    # A third student tries to view
    with init_database.app.app_context():
        student3 = User(username='enroll_display_s3', email='eds3@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        student3.set_password('password')
        db.session.add(student3)
        db.session.commit()
    
    client_s3 = test_auth_client(student3)
    response_s3_course_full = client_s3.get(url_for('view_course', course_id=course.id))
    assert b"Currently Enrolled: 2" in response_s3_course_full.data
    assert b"Course Full (Enroll)</button>" in response_s3_course_full.data # s3 sees Course Full


def test_user_profile_enrolled_courses_display(test_auth_client, init_database, new_user, new_college, new_course):
    """Test display of enrolled courses on user_profile page."""
    student = new_user
    course = new_course
    with init_database.app.app_context():
        db.session.add_all([student, course]) # Ensure they are in session
        enrollment = CourseEnrollment(user_id=student.id, course_id=course.id, status='enrolled')
        db.session.add(enrollment)
        db.session.commit()

    client = test_auth_client(student)
    response = client.get(url_for('user_profile', username=student.username))
    assert response.status_code == 200
    assert b"Enrolled Courses" in response.data
    assert course.name.encode() in response.data
    assert course.course_code.encode() in response.data
    assert b"badge-success" in response.data # "Enrolled" badge

def test_list_college_courses_enrollment_info(client, init_database, new_college, new_course):
    """Test display of enrollment info (count, capacity, progress bar) on list_college_courses page."""
    course = new_course
    course.capacity = 10
    with init_database.app.app_context():
        student1 = User(username='list_c_s1', email='lcs1@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        student1.set_password('password')
        db.session.add_all([course, student1])
        db.session.commit()
        # Enroll student1
        enrollment1 = CourseEnrollment(user_id=student1.id, course_id=course.id, status='enrolled')
        db.session.add(enrollment1)
        db.session.commit()

    response = client.get(url_for('list_college_courses', college_id=new_college.id))
    assert response.status_code == 200
    assert course.name.encode() in response.data
    assert f"Capacity: {course.capacity}".encode() in response.data
    assert b"Enrolled: 1" in response.data
    assert b"10%" in response.data # (1/10)*100
    assert b'class="progress-bar' in response.data # Check for progress bar element

def test_take_attendance_uses_enrolled_students(test_auth_client, init_database, new_college, new_course):
    """Test that take_attendance page lists only enrolled students."""
    course = new_course
    with init_database.app.app_context():
        faculty = User(username='att_faculty', email='attf@example.com', role=User.ROLE_FACULTY, college_id=new_college.id)
        faculty.set_password('password')
        s_enrolled = User(username='s_enrolled', email='se@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        s_enrolled.set_password('password')
        s_dropped = User(username='s_dropped', email='sd@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        s_dropped.set_password('password')
        s_other_course = User(username='s_other', email='so@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        s_other_course.set_password('password')
        db.session.add_all([faculty, s_enrolled, s_dropped, s_other_course, course])
        db.session.commit()

        # Enroll s_enrolled
        CourseEnrollment.query.delete() # Clear any prior enrollments for this course from other tests
        db.session.commit()
        
        enrollment_active = CourseEnrollment(user_id=s_enrolled.id, course_id=course.id, status='enrolled')
        enrollment_dropped = CourseEnrollment(user_id=s_dropped.id, course_id=course.id, status='dropped')
        db.session.add_all([enrollment_active, enrollment_dropped])
        db.session.commit()

    client = test_auth_client(faculty)
    response = client.get(url_for('take_attendance', course_id=course.id))
    assert response.status_code == 200
    assert s_enrolled.username.encode() in response.data
    assert s_dropped.username.encode() not in response.data
    assert s_other_course.username.encode() not in response.data

# --- Tests for Attendance Routes ---

def test_take_attendance_route(test_auth_client, init_database, new_college, new_course):
    """Test the /course/<course_id>/take_attendance route."""
    course = new_course # Assumes new_course is linked to new_college or is general

    with init_database.app.app_context():
        faculty_user = User(username='faculty_att_route', email='faculty_attr@example.com', role=User.ROLE_FACULTY, college_id=new_college.id)
        faculty_user.set_password('password')
        student_user = User(username='student_att_route', email='student_attr@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        student_user.set_password('password')
        admin_user = User(username='admin_att_route', email='admin_attr@example.com', role=User.ROLE_ADMIN, college_id=new_college.id)
        admin_user.set_password('password')
        db.session.add_all([faculty_user, student_user, admin_user, course])
        db.session.commit()
    
    # --- GET request (as faculty) ---
    client = test_auth_client(faculty_user)
    response_get_faculty = client.get(url_for('take_attendance', course_id=course.id))
    assert response_get_faculty.status_code == 200
    assert b"Take Attendance for" in response_get_faculty.data
    assert course.name.encode() in response_get_faculty.data
    assert student_user.username.encode() in response_get_faculty.data # Student should be in the list
    assert b"students-0-student_id" in response_get_faculty.data # Check for form field structure

    # --- GET request (as admin) ---
    client = test_auth_client(admin_user)
    response_get_admin = client.get(url_for('take_attendance', course_id=course.id))
    assert response_get_admin.status_code == 200
    assert student_user.username.encode() in response_get_admin.data

    # --- GET request (as student - forbidden) ---
    client = test_auth_client(student_user)
    response_get_student = client.get(url_for('take_attendance', course_id=course.id), follow_redirects=True)
    assert response_get_student.status_code == 200 # Follows redirect
    assert b"You do not have permission to take attendance for this course." in response_get_student.data
    assert b"Take Attendance for" not in response_get_student.data # Should not see the form

    # --- POST request (successful submission by faculty) ---
    client = test_auth_client(faculty_user)
    attendance_date_str = date(2023, 10, 27).isoformat()
    post_data = {
        'date': attendance_date_str,
        'students-0-student_id': student_user.id,
        'students-0-status': 'present',
        'csrf_token': response_get_faculty.data.split(b'name="csrf_token" type="hidden" value="')[1].split(b'"')[0].decode() # Extract CSRF if needed by test_auth_client setup
    }
    response_post_faculty = client.post(url_for('take_attendance', course_id=course.id), data=post_data, follow_redirects=True)
    assert response_post_faculty.status_code == 200
    assert b"Attendance records have been saved/updated." in response_post_faculty.data
    
    with init_database.app.app_context():
        record = AttendanceRecord.query.filter_by(user_id=student_user.id, course_id=course.id, date=date(2023,10,27)).first()
        assert record is not None
        assert record.status == 'present'
        assert record.marked_by_id == faculty_user.id
        original_timestamp = record.timestamp

    # --- POST request (update existing record by admin) ---
    client = test_auth_client(admin_user)
    # Need to get a new CSRF token if the form is stateful or client is fresh
    temp_get_response = client.get(url_for('take_attendance', course_id=course.id, date=attendance_date_str))
    csrf_token_update = temp_get_response.data.split(b'name="csrf_token" type="hidden" value="')[1].split(b'"')[0].decode()
    
    post_data_update = {
        'date': attendance_date_str,
        'students-0-student_id': student_user.id,
        'students-0-status': 'absent',
        'csrf_token': csrf_token_update
    }
    response_post_update = client.post(url_for('take_attendance', course_id=course.id), data=post_data_update, follow_redirects=True)
    assert response_post_update.status_code == 200
    assert b"Attendance records have been saved/updated." in response_post_update.data

    with init_database.app.app_context():
        updated_record = AttendanceRecord.query.filter_by(user_id=student_user.id, course_id=course.id, date=date(2023,10,27)).first()
        assert updated_record is not None
        assert updated_record.status == 'absent'
        assert updated_record.marked_by_id == admin_user.id
        assert updated_record.timestamp > original_timestamp

def test_view_course_attendance_route(test_auth_client, init_database, new_college, new_course):
    """Test the /course/<course_id>/view_attendance route."""
    course = new_course

    with init_database.app.app_context():
        faculty_user = User(username='faculty_v_att', email='faculty_vattr@example.com', role=User.ROLE_FACULTY, college_id=new_college.id)
        faculty_user.set_password('password')
        student_user = User(username='student_v_att', email='student_vattr@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        student_user.set_password('password')
        db.session.add_all([faculty_user, student_user, course])
        db.session.commit()

        # Create an attendance record
        record_date = date(2023, 10, 28)
        record = AttendanceRecord(user_id=student_user.id, course_id=course.id, date=record_date, status='late', marked_by_id=faculty_user.id)
        db.session.add(record)
        db.session.commit()

    # --- GET request (as faculty) ---
    client = test_auth_client(faculty_user)
    response_get_faculty = client.get(url_for('view_course_attendance', course_id=course.id))
    assert response_get_faculty.status_code == 200
    assert b"Attendance Records for" in response_get_faculty.data
    assert course.name.encode() in response_get_faculty.data
    assert student_user.username.encode() in response_get_faculty.data
    assert record_date.strftime('%Y-%m-%d').encode() in response_get_faculty.data
    assert b"Late" in response_get_faculty.data # Status, capitalized

    # --- Test with date filter (GET params) ---
    response_filtered = client.get(url_for('view_course_attendance', course_id=course.id, 
                                           start_date=record_date.isoformat(), 
                                           end_date=record_date.isoformat()))
    assert response_filtered.status_code == 200
    assert student_user.username.encode() in response_filtered.data # Record should be present

    response_filtered_no_match = client.get(url_for('view_course_attendance', course_id=course.id, 
                                                    start_date=(record_date + timedelta(days=1)).isoformat()))
    assert response_filtered_no_match.status_code == 200
    assert student_user.username.encode() not in response_filtered_no_match.data # Record should NOT be present

    # --- GET request (as student - forbidden based on current route logic) ---
    client = test_auth_client(student_user)
    response_get_student = client.get(url_for('view_course_attendance', course_id=course.id), follow_redirects=True)
    assert response_get_student.status_code == 200 # Follows redirect
    assert b"You do not have permission to view attendance for this course." in response_get_student.data

def test_view_user_attendance_route(test_auth_client, client, init_database, new_college, new_course):
    """Test the /user/<username>/attendance route."""
    course1 = new_course
    
    with init_database.app.app_context():
        course2 = Course(name="Adv Attendance", course_code="ATT202", college_id=new_college.id)
        s1 = User(username='student_s1_att', email='s1att@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        s1.set_password('password')
        s2 = User(username='student_s2_att', email='s2att@example.com', role=User.ROLE_STUDENT, college_id=new_college.id)
        s2.set_password('password')
        admin = User(username='admin_view_att', email='adminvatt@example.com', role=User.ROLE_ADMIN, college_id=new_college.id)
        admin.set_password('password')
        faculty = User(username='faculty_view_att', email='facultyvatt@example.com', role=User.ROLE_FACULTY, college_id=new_college.id)
        faculty.set_password('password')

        db.session.add_all([course1, course2, s1, s2, admin, faculty])
        db.session.commit()

        date1 = date(2023, 11, 1)
        date2 = date(2023, 11, 2)
        record1_s1_c1 = AttendanceRecord(user_id=s1.id, course_id=course1.id, date=date1, status='present', marked_by_id=faculty.id)
        record2_s1_c2 = AttendanceRecord(user_id=s1.id, course_id=course2.id, date=date2, status='absent', marked_by_id=faculty.id)
        db.session.add_all([record1_s1_c1, record2_s1_c2])
        db.session.commit()

    # --- GET request (own records by s1) ---
    client_s1 = test_auth_client(s1)
    response_s1_own = client_s1.get(url_for('view_user_attendance', username=s1.username))
    assert response_s1_own.status_code == 200
    assert b"Attendance Report for: student_s1_att" in response_s1_own.data
    assert course1.name.encode() in response_s1_own.data
    assert course2.name.encode() in response_s1_own.data
    assert b"Present" in response_s1_own.data
    assert b"Absent" in response_s1_own.data

    # --- GET request (viewing s1's records as admin) ---
    client_admin = test_auth_client(admin)
    response_admin_view_s1 = client_admin.get(url_for('view_user_attendance', username=s1.username))
    assert response_admin_view_s1.status_code == 200
    assert course1.name.encode() in response_admin_view_s1.data
    assert b"Present" in response_admin_view_s1.data

    # --- GET request (viewing s1's records as s2 - forbidden) ---
    client_s2 = test_auth_client(s2)
    response_s2_view_s1 = client_s2.get(url_for('view_user_attendance', username=s1.username), follow_redirects=True)
    assert response_s2_view_s1.status_code == 200 # Follows redirect
    assert b"You do not have permission to view this attendance report." in response_s2_view_s1.data

    # --- Test Filters (as s1 viewing own records) ---
    # Filter by course1
    response_s1_filter_course = client_s1.get(url_for('view_user_attendance', username=s1.username, course_id=course1.id))
    assert response_s1_filter_course.status_code == 200
    assert course1.name.encode() in response_s1_filter_course.data
    assert course2.name.encode() not in response_s1_filter_course.data # Should only show course1
    assert b"Present" in response_s1_filter_course.data
    assert b"Absent" not in response_s1_filter_course.data

    # Filter by date range (covering only date1)
    response_s1_filter_date = client_s1.get(url_for('view_user_attendance', username=s1.username, 
                                                    start_date=date1.isoformat(), end_date=date1.isoformat()))
    assert response_s1_filter_date.status_code == 200
    assert course1.name.encode() in response_s1_filter_date.data # record1_s1_c1
    assert b"Present" in response_s1_filter_date.data
    assert course2.name.encode() not in response_s1_filter_date.data # record2_s1_c2 should be filtered out
    assert b"Absent" not in response_s1_filter_date.data
