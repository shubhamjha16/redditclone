import pytest
from app.models import User, College, Post, Comment, Vote, VoteType, Report, ReportStatus, Course, StudyGroup, Event, Notification, Reel, ReelComment, ReelLike, AttendanceRecord, CourseEnrollment
from app import db # For database operations
from datetime import datetime, date # Added date
from sqlalchemy.exc import IntegrityError

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

# --- Tests for Reel, ReelComment, and ReelLike Models ---

def test_reel_model_creation(init_database, new_user, new_college):
    """Test the creation of a Reel model instance."""
    with init_database.app.app_context():
        reel = Reel(
            user_id=new_user.id,
            college_id=new_college.id,
            video_url="http://example.com/video.mp4",
            caption="Test Reel Caption"
        )
        db.session.add(reel)
        db.session.commit()

        retrieved_reel = Reel.query.get(reel.id)
        assert retrieved_reel is not None
        assert retrieved_reel.video_url == "http://example.com/video.mp4"
        assert retrieved_reel.caption == "Test Reel Caption"
        assert retrieved_reel.author == new_user
        assert retrieved_reel.college == new_college
        assert retrieved_reel.views_count == 0
        assert isinstance(retrieved_reel.timestamp, datetime)

def test_reel_comment_model(init_database, new_user, new_college):
    """Test the creation and relationships of a ReelComment model instance."""
    with init_database.app.app_context():
        reel = Reel(user_id=new_user.id, college_id=new_college.id, video_url="http://reel.com/v.mp4")
        db.session.add(reel)
        db.session.commit()

        comment = ReelComment(
            content="This is a test comment on a reel.",
            user_id=new_user.id,
            reel_id=reel.id
        )
        db.session.add(comment)
        db.session.commit()

        retrieved_comment = ReelComment.query.get(comment.id)
        assert retrieved_comment is not None
        assert retrieved_comment.content == "This is a test comment on a reel."
        assert retrieved_comment.author == new_user
        assert retrieved_comment.reel == reel
        assert comment in reel.comments.all()
        assert isinstance(retrieved_comment.timestamp, datetime)

def test_reel_like_model(init_database, new_user, new_college):
    """Test the creation, relationships, and unique constraint of a ReelLike model instance."""
    with init_database.app.app_context():
        reel = Reel(user_id=new_user.id, college_id=new_college.id, video_url="http://reel.ly/v.mp4")
        # Need another user for liking to avoid confusion if author likes own reel
        liker_user = User(username='likeruser', email='liker@example.com')
        liker_user.set_password('password')
        db.session.add_all([reel, liker_user])
        db.session.commit()

        like = ReelLike(
            user_id=liker_user.id,
            reel_id=reel.id
        )
        db.session.add(like)
        db.session.commit()

        retrieved_like = ReelLike.query.get(like.id)
        assert retrieved_like is not None
        assert retrieved_like.liker == liker_user
        assert retrieved_like.reel == reel
        assert like in reel.likes.all()
        assert isinstance(retrieved_like.timestamp, datetime)

        # Test unique constraint (_user_reel_uc)
        duplicate_like = ReelLike(user_id=liker_user.id, reel_id=reel.id)
        db.session.add(duplicate_like)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback() # Rollback the failed transaction

def test_reel_cascade_delete(init_database, new_user, new_college):
    """Test that ReelComments and ReelLikes are cascade deleted when a Reel is deleted."""
    with init_database.app.app_context():
        # Create users
        reel_author = new_user
        commenter = User(username='commenter_user', email='commenter@example.com')
        commenter.set_password('password')
        liker = User(username='liker_user_cascade', email='likercascade@example.com')
        liker.set_password('password')
        db.session.add_all([commenter, liker]) # new_user (reel_author) is already handled by fixture
        db.session.commit()


        reel = Reel(user_id=reel_author.id, college_id=new_college.id, video_url="http://cascade.com/v.mp4")
        db.session.add(reel)
        db.session.commit()
        reel_id = reel.id

        comment = ReelComment(content="A comment to be deleted.", user_id=commenter.id, reel_id=reel_id)
        db.session.add(comment)
        db.session.commit()
        comment_id = comment.id

        like = ReelLike(user_id=liker.id, reel_id=reel_id)
        db.session.add(like)
        db.session.commit()
        like_id = like.id

        # Ensure everything is created
        assert Reel.query.get(reel_id) is not None
        assert ReelComment.query.get(comment_id) is not None
        assert ReelLike.query.get(like_id) is not None

        # Delete the reel
        db.session.delete(reel)
        db.session.commit()

        # Assert reel, comment, and like are deleted
        assert Reel.query.get(reel_id) is None
        assert ReelComment.query.get(comment_id) is None
        assert ReelLike.query.get(like_id) is None

# --- Tests for AttendanceRecord Model ---

def test_attendance_record_creation(init_database, new_college):
    """Test the creation of an AttendanceRecord model instance."""
    with init_database.app.app_context():
        student1 = User(username='student1_att', email='s1_att@example.com', role=User.ROLE_STUDENT)
        student1.set_password('password')
        faculty_marker = User(username='faculty_att', email='f1_att@example.com', role=User.ROLE_FACULTY)
        faculty_marker.set_password('password')
        
        course1 = Course(name="Attendance Course", course_code="ATT101", college_id=new_college.id, instructor="Prof. Test")
        
        db.session.add_all([student1, faculty_marker, course1])
        db.session.commit()

        attendance_date = date(2023, 10, 26)
        record = AttendanceRecord(
            user_id=student1.id,
            course_id=course1.id,
            date=attendance_date,
            status='present',
            marked_by_id=faculty_marker.id
        )
        db.session.add(record)
        db.session.commit()

        retrieved_record = AttendanceRecord.query.get(record.id)
        assert retrieved_record is not None
        assert retrieved_record.user_id == student1.id
        assert retrieved_record.course_id == course1.id
        assert retrieved_record.date == attendance_date
        assert retrieved_record.status == 'present'
        assert retrieved_record.marked_by_id == faculty_marker.id
        assert isinstance(retrieved_record.timestamp, datetime)
        
        # Test relationships
        assert retrieved_record.student == student1
        assert retrieved_record.course == course1
        assert retrieved_record.marker == faculty_marker

def test_attendance_record_unique_constraint(init_database, new_college):
    """Test the unique constraint (user_id, course_id, date) for AttendanceRecord."""
    with init_database.app.app_context():
        student1 = User(username='student_uc', email='s_uc@example.com', role=User.ROLE_STUDENT)
        student1.set_password('password')
        faculty_marker = User(username='faculty_uc', email='f_uc@example.com', role=User.ROLE_FACULTY)
        faculty_marker.set_password('password')
        course1 = Course(name="Unique Course", course_code="UC101", college_id=new_college.id)
        course2 = Course(name="Another Course", course_code="AC101", college_id=new_college.id) # For testing variation
        student2 = User(username='student2_uc', email='s2_uc@example.com', role=User.ROLE_STUDENT)
        student2.set_password('password')

        db.session.add_all([student1, student2, faculty_marker, course1, course2])
        db.session.commit()

        attendance_date = date(2023, 10, 27)
        
        # Initial record
        record1 = AttendanceRecord(
            user_id=student1.id, course_id=course1.id, date=attendance_date, 
            status='present', marked_by_id=faculty_marker.id
        )
        db.session.add(record1)
        db.session.commit()
        assert record1.id is not None

        # Attempt to create duplicate record (same user, course, date)
        duplicate_record = AttendanceRecord(
            user_id=student1.id, course_id=course1.id, date=attendance_date, 
            status='absent', marked_by_id=faculty_marker.id # Different status, but still duplicate by constraint
        )
        db.session.add(duplicate_record)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Verify different date works
        record_diff_date = AttendanceRecord(
            user_id=student1.id, course_id=course1.id, date=date(2023, 10, 28),
            status='present', marked_by_id=faculty_marker.id
        )
        db.session.add(record_diff_date)
        db.session.commit()
        assert record_diff_date.id is not None

        # Verify different student works
        record_diff_student = AttendanceRecord(
            user_id=student2.id, course_id=course1.id, date=attendance_date,
            status='present', marked_by_id=faculty_marker.id
        )
        db.session.add(record_diff_student)
        db.session.commit()
        assert record_diff_student.id is not None

        # Verify different course works
        record_diff_course = AttendanceRecord(
            user_id=student1.id, course_id=course2.id, date=attendance_date,
            status='present', marked_by_id=faculty_marker.id
        )
        db.session.add(record_diff_course)
        db.session.commit()
        assert record_diff_course.id is not None

def test_attendance_record_backrefs(init_database, new_college):
    """Test the backref relationships for AttendanceRecord."""
    with init_database.app.app_context():
        student1 = User(username='student_br', email='s_br@example.com', role=User.ROLE_STUDENT)
        student1.set_password('password')
        faculty_marker = User(username='faculty_br', email='f_br@example.com', role=User.ROLE_FACULTY)
        faculty_marker.set_password('password')
        course1 = Course(name="Backref Course", course_code="BR101", college_id=new_college.id)
        
        db.session.add_all([student1, faculty_marker, course1])
        db.session.commit()

        attendance_date = date(2023, 10, 29)
        record = AttendanceRecord(
            user_id=student1.id,
            course_id=course1.id,
            date=attendance_date,
            status='late',
            marked_by_id=faculty_marker.id
        )
        db.session.add(record)
        db.session.commit()

        # Refresh objects to ensure backrefs are loaded
        db.session.refresh(student1)
        db.session.refresh(course1)
        db.session.refresh(faculty_marker)

        assert record in student1.attendance_records.all()
        assert record in course1.attendance_records.all()
        assert record in faculty_marker.marked_attendance_records.all()
        
        assert len(student1.attendance_records.all()) == 1
        assert len(course1.attendance_records.all()) == 1
        assert len(faculty_marker.marked_attendance_records.all()) == 1

# --- Tests for CourseEnrollment Model ---

def test_course_enrollment_creation(init_database, new_user, new_college):
    """Test the creation of a CourseEnrollment model instance."""
    with init_database.app.app_context():
        # new_user can be the student for this test
        student = new_user 
        course = Course(name="Enrollment Test Course", course_code="ETC101", college_id=new_college.id)
        db.session.add(course)
        db.session.commit()

        enrollment = CourseEnrollment(
            user_id=student.id,
            course_id=course.id,
            status='enrolled', # Explicitly set, though 'enrolled' is default
            grade_points=3.7
        )
        db.session.add(enrollment)
        db.session.commit()

        retrieved_enrollment = CourseEnrollment.query.get(enrollment.id)
        assert retrieved_enrollment is not None
        assert retrieved_enrollment.user_id == student.id
        assert retrieved_enrollment.course_id == course.id
        assert isinstance(retrieved_enrollment.enrollment_date, datetime) # Default value check
        assert retrieved_enrollment.status == 'enrolled' # Default or explicitly set
        assert retrieved_enrollment.grade_points == 3.7
        
        # Test relationships
        assert retrieved_enrollment.student == student
        assert retrieved_enrollment.course == course
        
        # Test default status if not provided
        enrollment_default_status = CourseEnrollment(user_id=student.id, course_id=course.id) # Create another to avoid PK error with same student/course
        # This will fail due to unique constraint if we try to commit same user/course.
        # Let's use a different student for default status test or different course.
        student2 = User(username='student_default', email='s_default@example.com', role=User.ROLE_STUDENT)
        student2.set_password('password')
        db.session.add(student2)
        db.session.commit()
        enrollment_default_status = CourseEnrollment(user_id=student2.id, course_id=course.id)
        db.session.add(enrollment_default_status)
        db.session.commit()
        assert enrollment_default_status.status == 'enrolled'


def test_course_enrollment_unique_constraint(init_database, new_user, new_college):
    """Test the unique constraint (user_id, course_id) for CourseEnrollment."""
    with init_database.app.app_context():
        student = new_user
        course1 = Course(name="Constraint Course 1", course_code="CC101", college_id=new_college.id)
        course2 = Course(name="Constraint Course 2", course_code="CC102", college_id=new_college.id)
        student2 = User(username='student_uc_enroll', email='s_uc_enroll@example.com', role=User.ROLE_STUDENT)
        student2.set_password('password')

        db.session.add_all([course1, course2, student2])
        db.session.commit() # Student (new_user) is already in session from fixture

        # Initial enrollment
        enrollment1 = CourseEnrollment(user_id=student.id, course_id=course1.id)
        db.session.add(enrollment1)
        db.session.commit()
        assert enrollment1.id is not None

        # Attempt to create duplicate enrollment (same user, same course)
        duplicate_enrollment = CourseEnrollment(user_id=student.id, course_id=course1.id, status='waitlisted')
        db.session.add(duplicate_enrollment)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Verify different student works
        enrollment_diff_student = CourseEnrollment(user_id=student2.id, course_id=course1.id)
        db.session.add(enrollment_diff_student)
        db.session.commit()
        assert enrollment_diff_student.id is not None

        # Verify different course works
        enrollment_diff_course = CourseEnrollment(user_id=student.id, course_id=course2.id)
        db.session.add(enrollment_diff_course)
        db.session.commit()
        assert enrollment_diff_course.id is not None

def test_course_enrollment_backrefs(init_database, new_user, new_college):
    """Test the backref relationships for CourseEnrollment."""
    with init_database.app.app_context():
        student = new_user
        course = Course(name="Enrollment Backref Course", course_code="EBC101", college_id=new_college.id)
        db.session.add(course)
        db.session.commit()

        enrollment = CourseEnrollment(user_id=student.id, course_id=course.id)
        db.session.add(enrollment)
        db.session.commit()

        # Refresh objects
        db.session.refresh(student)
        db.session.refresh(course)

        assert enrollment in student.course_enrollments.all()
        assert enrollment in course.student_enrollments.all()
        assert len(student.course_enrollments.all()) == 1
        assert len(course.student_enrollments.all()) == 1

# --- Test for Course.capacity ---
def test_course_capacity_field(init_database, new_college):
    """Test the capacity field on the Course model."""
    with init_database.app.app_context():
        course = Course(
            name="Capacity Test Course", 
            course_code="CTC101", 
            college_id=new_college.id,
            instructor="Prof. Capacity"
        )
        # Test setting capacity to an integer
        course.capacity = 50
        db.session.add(course)
        db.session.commit()

        retrieved_course = Course.query.get(course.id)
        assert retrieved_course is not None
        assert retrieved_course.capacity == 50

        # Test updating capacity to None (nullable is True)
        retrieved_course.capacity = None
        db.session.commit()
        
        updated_course = Course.query.get(course.id)
        assert updated_course.capacity is None

        # Test creating a course with capacity initially set
        course_with_capacity = Course(
            name="Capacity Init Course", 
            course_code="CIC101", 
            college_id=new_college.id,
            instructor="Dr. Init",
            capacity=30
        )
        db.session.add(course_with_capacity)
        db.session.commit()
        retrieved_course_init = Course.query.get(course_with_capacity.id)
        assert retrieved_course_init.capacity == 30
