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
