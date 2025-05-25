import pytest
from app.models import User, College, Post, Comment, Vote, VoteType, Report, ReportStatus, Course, StudyGroup, Event, Notification
from app import db # For database operations
from datetime import datetime

def test_user_model_creation(new_user): # Uses the new_user fixture from conftest.py
    assert new_user.username == 'testuser'
    assert new_user.email == 'test@example.com'
    assert new_user.check_password('password')
    assert not new_user.check_password('wrongpassword')
    assert new_user.role == User.ROLE_STUDENT
    assert new_user.is_college_verified == False # Default

def test_college_model_creation(new_college):
    assert new_college.name == 'Test College'
    assert new_college.location == 'Test Location'

def test_post_model_creation(init_database, new_user, new_college):
    with init_database.app.app_context():
        post = Post(title="Test Post", content="This is test content.", user_id=new_user.id, college_id=new_college.id)
        db.session.add(post)
        db.session.commit()
        assert post.id is not None
        assert post.title == "Test Post"
        assert post.author == new_user
        assert post.college == new_college
        assert post.timestamp is not None

def test_comment_model_creation(init_database, new_user, new_college):
    with init_database.app.app_context():
        post = Post(title="Post for Comment", content="Content", user_id=new_user.id, college_id=new_college.id)
        db.session.add(post)
        db.session.commit()

        comment = Comment(content="Test comment", user_id=new_user.id, post_id=post.id)
        db.session.add(comment)
        db.session.commit()
        assert comment.id is not None
        assert comment.content == "Test comment"
        assert comment.author == new_user
        assert comment.post == post
        assert comment.timestamp is not None

def test_vote_model_creation(init_database, new_user, new_college):
     with init_database.app.app_context():
        post = Post(title="Post for Vote", content="Content", user_id=new_user.id, college_id=new_college.id)
        db.session.add(post)
        db.session.commit()

        vote = Vote(user_id=new_user.id, post_id=post.id, vote_type=VoteType.UPVOTE)
        db.session.add(vote)
        db.session.commit()
        assert vote.id is not None
        assert vote.voter == new_user
        assert vote.post == post
        assert vote.vote_type == VoteType.UPVOTE

def test_report_model_creation(init_database, new_user, new_college):
    with init_database.app.app_context():
        post_author = User(username='postauthor', email='author@example.com')
        post_author.set_password('authorpass')
        db.session.add(post_author)
        db.session.commit()

        post_to_report = Post(title="Reportable Post", content="Content to report", user_id=post_author.id, college_id=new_college.id)
        db.session.add(post_to_report)
        db.session.commit()

        report = Report(reporter_id=new_user.id, post_id=post_to_report.id, reason="Test reason")
        db.session.add(report)
        db.session.commit()

        assert report.id is not None
        assert report.reporter == new_user
        assert report.reported_post == post_to_report
        assert report.reason == "Test reason"
        assert report.status == ReportStatus.PENDING

def test_course_model_creation(init_database, new_college):
    with init_database.app.app_context():
        course = Course(name="Intro to Testing", course_code="TEST101", college_id=new_college.id, instructor="Dr. PyTest")
        db.session.add(course)
        db.session.commit()
        assert course.id is not None
        assert course.name == "Intro to Testing"
        assert course.college == new_college

def test_study_group_model_creation(init_database, new_user, new_college):
    with init_database.app.app_context():
        course = Course(name="Advanced Testing", course_code="TEST201", college_id=new_college.id)
        db.session.add(course)
        db.session.commit()

        study_group = StudyGroup(name="Test Study Group", description="Studying tests", user_id=new_user.id, college_id=new_college.id, course_id=course.id)
        db.session.add(study_group)
        db.session.commit()
        assert study_group.id is not None
        assert study_group.name == "Test Study Group"
        assert study_group.creator == new_user
        assert study_group.college == new_college
        assert study_group.course == course

def test_event_model_creation(init_database, new_user, new_college):
    with init_database.app.app_context():
        event_time = datetime.utcnow()
        event = Event(name="Test Event", description="Event for testing", date_time=event_time, location="Test Location", user_id=new_user.id, college_id=new_college.id)
        db.session.add(event)
        db.session.commit()
        assert event.id is not None
        assert event.name == "Test Event"
        assert event.creator == new_user
        assert event.college == new_college
        assert event.date_time == event_time

def test_notification_model_creation(init_database, new_user):
    with init_database.app.app_context():
        notification = Notification(user_id=new_user.id, name="test_notification", payload_json='{"message": "hello"}')
        db.session.add(notification)
        db.session.commit()
        assert notification.id is not None
        assert notification.user == new_user
        assert notification.name == "test_notification"
        assert notification.is_read is False
        assert notification.get_payload()['message'] == 'hello'

# Test relationships more explicitly
def test_user_post_relationship(init_database, new_user, new_college):
    with init_database.app.app_context():
        post1 = Post(title="Post 1", content="Content 1", author=new_user, college=new_college)
        post2 = Post(title="Post 2", content="Content 2", author=new_user, college=new_college)
        db.session.add_all([post1, post2])
        db.session.commit()
        assert new_user.posts.count() == 2
        assert post1 in new_user.posts.all()

def test_post_comment_relationship(init_database, new_user, new_college):
    with init_database.app.app_context():
        post = Post(title="Test Post", content="Content", author=new_user, college=new_college)
        db.session.add(post)
        db.session.commit()
        comment1 = Comment(content="Comment 1", author=new_user, post=post)
        comment2 = Comment(content="Comment 2", author=new_user, post=post)
        db.session.add_all([comment1, comment2])
        db.session.commit()
        assert post.comments.count() == 2
        assert comment1 in post.comments.all()

def test_college_user_relationship(init_database, new_user, new_college):
     with init_database.app.app_context():
        new_user.college_id = new_college.id
        db.session.add(new_user) # new_user is detached, so add it to session
        db.session.commit()
        assert new_college.users.count() == 1
        assert new_user in new_college.users.all()
        assert new_user.college == new_college


# --- Tests for User Model Enhancements (Profile, Follow/Unfollow, Followed Posts) ---

def test_user_profile_fields(init_database, new_user): # new_user fixture can be used for a single user test
    """Test the new profile fields on the User model."""
    with init_database.app.app_context():
        # new_user is already added to the session by its fixture if it does db operations
        # For this test, let's assume new_user is a fresh instance or we fetch it
        user = User.query.filter_by(username=new_user.username).first()
        if not user: # If new_user fixture doesn't commit, we might need to add and commit it.
                     # Assuming new_user is already in db from fixture.
            user = new_user 
            db.session.add(user) # Ensure it's in the session if not already
            db.session.commit() # Commit to get ID and ensure it's queryable

        user.profile_picture_url = "http://example.com/pic.jpg"
        user.bio = "This is a test bio."
        # last_seen is set on creation, and also by before_request handler in a live app
        # For model testing, we check its default initialization or manual setting.
        user.last_seen = datetime.utcnow() # Explicitly set for test clarity if needed
        
        db.session.commit()

        retrieved_user = User.query.filter_by(username=user.username).first()
        assert retrieved_user.profile_picture_url == "http://example.com/pic.jpg"
        assert retrieved_user.bio == "This is a test bio."
        assert isinstance(retrieved_user.last_seen, datetime)
        # Check if last_seen is recent (e.g., within a few seconds of now)
        assert (datetime.utcnow() - retrieved_user.last_seen).total_seconds() < 5

def test_follow_unfollow(init_database):
    """Test the follow and unfollow functionality."""
    with init_database.app.app_context():
        u1 = User(username='user1', email='user1@example.com')
        u1.set_password('password')
        u2 = User(username='user2', email='user2@example.com')
        u2.set_password('password')
        db.session.add_all([u1, u2])
        db.session.commit()

        # Test initial state
        assert not u1.is_following(u2)
        assert not u2.is_following(u1)
        assert u1.followed.count() == 0
        assert u1.followers.count() == 0
        assert u2.followed.count() == 0
        assert u2.followers.count() == 0

        # Test follow action: u1 follows u2
        u1.follow(u2)
        db.session.commit()
        assert u1.is_following(u2)
        assert not u2.is_following(u1) # u2 does not automatically follow u1
        assert u1.followed.count() == 1
        assert u1.followed.first().username == 'user2'
        assert u2.followers.count() == 1
        assert u2.followers.first().username == 'user1'

        # Test that following an already followed user doesn't duplicate
        u1.follow(u2)
        db.session.commit()
        assert u1.followed.count() == 1

        # Test unfollow action: u1 unfollows u2
        u1.unfollow(u2)
        db.session.commit()
        assert not u1.is_following(u2)
        assert u1.followed.count() == 0
        assert u2.followers.count() == 0

def test_followed_posts_basic(init_database, new_college): # Added new_college fixture
    """Test the followed_posts method for basic functionality."""
    with init_database.app.app_context():
        u1 = User(username='user1_fp', email='user1_fp@example.com')
        u1.set_password('password')
        u2 = User(username='user2_fp', email='user2_fp@example.com')
        u2.set_password('password')
        db.session.add_all([u1, u2])
        db.session.commit() # Commit users first to assign IDs

        # Create posts
        post_u1 = Post(title="U1 Post", content="Content by U1", user_id=u1.id, college_id=new_college.id)
        post_u2 = Post(title="U2 Post", content="Content by U2", user_id=u2.id, college_id=new_college.id)
        db.session.add_all([post_u1, post_u2])
        db.session.commit()

        # u1 follows u2
        u1.follow(u2)
        db.session.commit()

        followed_posts_query = u1.followed_posts()
        assert followed_posts_query is not None
        
        followed_posts_list = followed_posts_query.all()
        
        # Check that u2's post is in u1's followed posts
        assert post_u2 in followed_posts_list
        # Check that u1's own post is also in their followed posts
        assert post_u1 in followed_posts_list
        
        # Check order (most recent first) - assuming post_u1 and post_u2 are added close in time
        # For more robust order testing, manipulate timestamps explicitly.
        # Here, we primarily care about inclusion.
        assert len(followed_posts_list) == 2

        # Unfollow and check again
        u1.unfollow(u2)
        db.session.commit()
        
        followed_posts_after_unfollow = u1.followed_posts().all()
        assert post_u2 not in followed_posts_after_unfollow
        assert post_u1 in followed_posts_after_unfollow # Own posts should still be there
        assert len(followed_posts_after_unfollow) == 1
