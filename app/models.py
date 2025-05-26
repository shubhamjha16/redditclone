from datetime import datetime
from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Association table for followers
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256)) # Increased length for potentially stronger hashing algorithms
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'))
    # Define roles
    ROLE_STUDENT = 'student'
    ROLE_ALUMNI = 'alumni'
    ROLE_FACULTY = 'faculty' # New role for faculty members
    ROLE_MANAGEMENT = 'management' # New role for management/staff
    ROLE_ADMIN = 'admin' # For site administration
    role = db.Column(db.String(20), default=ROLE_STUDENT, nullable=False)
    is_college_verified = db.Column(db.Boolean, default=False, nullable=False) # True if college affiliation is verified
    college_id_input = db.Column(db.String(50), nullable=True) # For student ID, etc.
    year_of_college = db.Column(db.String(20), nullable=True) # e.g., Freshman, Sophomore, Graduate Year X
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow) # User registration timestamp
    profile_picture_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    votes = db.relationship('Vote', backref='voter', lazy='dynamic')

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        from app.models import Post # Local import to avoid circular dependency issues
        followed_users_posts = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own_posts = Post.query.filter_by(user_id=self.id)
        return followed_users_posts.union(own_posts).order_by(Post.timestamp.desc())

    def __repr__(self):
        return f'<User {self.username}>'

class College(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False, unique=True)
    location = db.Column(db.String(140))
    users = db.relationship('User', backref='college', lazy='dynamic')
    posts = db.relationship('Post', backref='college', lazy='dynamic')

    def __repr__(self):
        return f'<College {self.name}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade="all, delete-orphan")
    votes = db.relationship('Vote', backref='post', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Post {self.title}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    votes = db.relationship('Vote', backref='comment', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Comment {self.id}>'

# Enum for vote types
class VoteType:
    UPVOTE = 1
    DOWNVOTE = -1

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    vote_type = db.Column(db.Integer, nullable=False) # 1 for upvote, -1 for downvote

    # Add a check constraint to ensure that either post_id or comment_id is set, but not both
    __table_args__ = (
        db.CheckConstraint('(post_id IS NOT NULL AND comment_id IS NULL) OR (post_id IS NULL AND comment_id IS NOT NULL)', name='chk_vote_target'),
        db.UniqueConstraint('user_id', 'post_id', name='uq_user_post_vote'),
        db.UniqueConstraint('user_id', 'comment_id', name='uq_user_comment_vote'),
    )

    def __repr__(self):
        return f'<Vote {self.id} - User {self.user_id} on {"Post " + str(self.post_id) if self.post_id else "Comment " + str(self.comment_id)} ({self.vote_type})>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    course_code = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    instructor = db.Column(db.String(100)) # Simple text field for instructor name
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    capacity = db.Column(db.Integer, nullable=True) # Max number of students
    
    college = db.relationship('College', backref=db.backref('courses', lazy='dynamic'))
    study_groups = db.relationship('StudyGroup', backref='course', lazy='dynamic')

    __table_args__ = (db.UniqueConstraint('course_code', 'college_id', name='uq_course_code_college'),)

    def __repr__(self):
        return f'<Course {self.course_code} - {self.name}>'

class StudyGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Creator
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True) # Optional link to a course

    creator = db.relationship('User', backref=db.backref('created_study_groups', lazy='dynamic'))
    college = db.relationship('College', backref=db.backref('study_groups', lazy='dynamic'))
    # If implementing members:
    # members = db.Table('study_group_members',
    #     db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    #     db.Column('study_group_id', db.Integer, db.ForeignKey('study_group.id'), primary_key=True)
    # )
    # member_users = db.relationship('User', secondary=members, lazy='dynamic', backref=db.backref('joined_study_groups', lazy='dynamic'))


    def __repr__(self):
        return f'<StudyGroup {self.name} (College {self.college_id})>'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date_time = db.Column(db.DateTime, nullable=False, index=True)
    location = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Creator
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)

    creator = db.relationship('User', backref=db.backref('created_events', lazy='dynamic'))
    college = db.relationship('College', backref=db.backref('events', lazy='dynamic'))
    # If implementing attendees:
    # attendees = db.Table('event_attendees',
    #     db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    #     db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True)
    # )
    # attending_users = db.relationship('User', secondary=attendees, lazy='dynamic', backref=db.backref('attended_events', lazy='dynamic'))

    def __repr__(self):
        return f'<Event {self.name} on {self.date_time.strftime("%Y-%m-%d %H:%M")} (College {self.college_id})>'

class ReportStatus:
    PENDING = 'pending'
    REVIEWED_ACTION_TAKEN = 'reviewed_action_taken'
    REVIEWED_NO_ACTION = 'reviewed_no_action'

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    status = db.Column(db.String(50), default=ReportStatus.PENDING, nullable=False)
    admin_notes = db.Column(db.Text) # Notes by admin after review

    reporter = db.relationship('User', backref=db.backref('reports_made', lazy='dynamic'))
    reported_post = db.relationship('Post', backref=db.backref('reports', lazy='dynamic', cascade="all, delete-orphan"))
    reported_comment = db.relationship('Comment', backref=db.backref('reports', lazy='dynamic', cascade="all, delete-orphan"))

    __table_args__ = (
        db.CheckConstraint('(post_id IS NOT NULL AND comment_id IS NULL) OR (post_id IS NULL AND comment_id IS NOT NULL)', name='chk_report_target'),
    )

    def __repr__(self):
        target = f"Post {self.post_id}" if self.post_id else f"Comment {self.comment_id}"
        return f'<Report {self.id} on {target} by User {self.reporter_id} - Status: {self.status}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Recipient
    name = db.Column(db.String(128), nullable=False) # e.g., 'new_comment', 'new_reply'
    payload_json = db.Column(db.Text) # JSON string for notification-specific data
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

    def get_payload(self):
        """Returns the payload_json as a Python dictionary."""
        if self.payload_json:
            try:
                return json.loads(self.payload_json)
            except json.JSONDecodeError:
                return {} # Or log an error
        return {}

    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id} - Type: {self.name} (Read: {self.is_read})>'

# Need to import json for get_payload
import json

# --- Reel, ReelComment, and ReelLike Models ---

class Reel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=True) # Allow reels not tied to a specific college
    video_url = db.Column(db.String(512), nullable=False) # For video link or path
    caption = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    views_count = db.Column(db.Integer, default=0)

    author = db.relationship('User', backref=db.backref('reels', lazy='dynamic'))
    college = db.relationship('College', backref=db.backref('reels', lazy='dynamic'))
    comments = db.relationship('ReelComment', backref='reel', lazy='dynamic', cascade="all, delete-orphan")
    likes = db.relationship('ReelLike', backref='reel', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Reel {self.id} by User {self.user_id}>'

class ReelComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reel_id = db.Column(db.Integer, db.ForeignKey('reel.id'), nullable=False)

    author = db.relationship('User', backref=db.backref('reel_comments', lazy='dynamic'))
    # reel backref is defined in Reel.comments

    def __repr__(self):
        return f'<ReelComment {self.id} on Reel {self.reel_id} by User {self.user_id}>'

class ReelLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reel_id = db.Column(db.Integer, db.ForeignKey('reel.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    liker = db.relationship('User', backref=db.backref('reel_likes', lazy='dynamic'))
    # reel backref is defined in Reel.likes

    __table_args__ = (db.UniqueConstraint('user_id', 'reel_id', name='_user_reel_uc'),)

    def __repr__(self):
        return f'<ReelLike {self.id} on Reel {self.reel_id} by User {self.user_id}>'

# --- Attendance Record Model ---

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True) # Student
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True) # Date of the class/session
    status = db.Column(db.String(20), nullable=False) # e.g., 'present', 'absent', 'late', 'excused'
    marked_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # User who marked attendance
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) # Record creation/modification time

    student = db.relationship('User', foreign_keys=[user_id], backref=db.backref('attendance_records', lazy='dynamic'))
    course = db.relationship('Course', backref=db.backref('attendance_records', lazy='dynamic'))
    marker = db.relationship('User', foreign_keys=[marked_by_id], backref=db.backref('marked_attendance_records', lazy='dynamic'))

    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', 'date', name='_student_course_date_uc'),)

    def __repr__(self):
        return f'<AttendanceRecord {self.id} for User {self.user_id} in Course {self.course_id} on {self.date} - {self.status}>'

# --- Course Enrollment Model ---

class CourseEnrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True) # The student enrolling
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False, index=True) # The course being enrolled in
    enrollment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='enrolled', index=True) # e.g., 'enrolled', 'waitlisted', 'dropped', 'completed'
    grade_points = db.Column(db.Float, nullable=True) # Optional: e.g., 4.0, 3.7

    student = db.relationship('User', backref=db.backref('course_enrollments', lazy='dynamic'))
    course = db.relationship('Course', backref=db.backref('student_enrollments', lazy='dynamic'))
    # grade_points field removed as per requirement

    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='_student_course_enrollment_uc'),)

    def __repr__(self):
        return f'<CourseEnrollment User {self.user_id} in Course {self.course_id} - Status: {self.status}>'


# --- Gradebook Model ---

class Gradebook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('course_enrollment.id'), nullable=False, index=True)
    grade_item_name = db.Column(db.String(150), nullable=False) # e.g., "Midterm Exam", "Homework 1"
    score = db.Column(db.Float, nullable=True)
    max_score = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    enrollment = db.relationship('CourseEnrollment', backref=db.backref('gradebook_entries', lazy='dynamic'))

    def __repr__(self):
        return f'<Gradebook {self.id} for Enrollment {self.enrollment_id} - {self.grade_item_name}>'


# --- Assignment Model ---

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    max_points = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course', backref=db.backref('assignments', lazy='dynamic'))

    def __repr__(self):
        return f'<Assignment {self.id} - {self.title} for Course {self.course_id}>'


# --- Submission Model ---

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True) # Student submitting
    submission_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    content = db.Column(db.Text, nullable=True) # For text submissions or links
    file_path = db.Column(db.String(255), nullable=True) # For file uploads
    grade = db.Column(db.Float, nullable=True)
    graded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True) # User who graded it
    grading_comments = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) # Record creation/modification time

    assignment = db.relationship('Assignment', backref=db.backref('submissions', lazy='dynamic'))
    student = db.relationship('User', foreign_keys=[user_id], backref=db.backref('submissions', lazy='dynamic'))
    grader = db.relationship('User', foreign_keys=[graded_by_id], backref=db.backref('graded_submissions', lazy='dynamic'))

    __table_args__ = (db.UniqueConstraint('assignment_id', 'user_id', name='_assignment_user_submission_uc'),)

    def __repr__(self):
        return f'<Submission {self.id} by User {self.user_id} for Assignment {self.assignment_id}>'


# --- FeeStructure Model ---

class FeeStructure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True, index=True)
    fee_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date_pattern = db.Column(db.String(100), nullable=True) # e.g., "start_of_semester", "monthly", "specific_date_YYYY-MM-DD"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    college = db.relationship('College', backref=db.backref('fee_structures', lazy='dynamic'))
    course = db.relationship('Course', backref=db.backref('fee_structures', lazy='dynamic'))

    def __repr__(self):
        return f'<FeeStructure {self.id} - {self.fee_name} for College {self.college_id}>'


# --- StudentFee Model ---

class StudentFee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True) # Student
    fee_structure_id = db.Column(db.Integer, db.ForeignKey('fee_structure.id'), nullable=False, index=True)
    due_date = db.Column(db.Date, nullable=False, index=True)
    amount_due = db.Column(db.Numeric(10, 2), nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    payment_status = db.Column(db.String(50), nullable=False, default='pending', index=True) # e.g., "pending", "paid", "partially_paid", "overdue", "waived"
    transaction_id = db.Column(db.String(255), nullable=True, index=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student = db.relationship('User', backref=db.backref('student_fees', lazy='dynamic'))
    fee_structure = db.relationship('FeeStructure', backref=db.backref('student_fee_entries', lazy='dynamic'))

    __table_args__ = (db.UniqueConstraint('user_id', 'fee_structure_id', 'due_date', name='_user_fee_structure_due_date_uc'),)

    def __repr__(self):
        return f'<StudentFee {self.id} for User {self.user_id} - Status: {self.payment_status}>'


# --- TimeSlot Model ---

class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False, index=True)
    day_of_week = db.Column(db.String(10), nullable=False, index=True) # e.g., "Monday", "Tuesday"
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(100), nullable=True) # e.g., "Room A101", "Online"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    course = db.relationship('Course', backref=db.backref('time_slots', lazy='dynamic'))

    __table_args__ = (db.UniqueConstraint('course_id', 'day_of_week', 'start_time', name='_course_day_start_time_uc'),)

    def __repr__(self):
        return f'<TimeSlot {self.id} for Course {self.course_id} - {self.day_of_week} {self.start_time}-{self.end_time}>'


# --- ResourceType Model ---

class ResourceType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<ResourceType {self.id} - {self.name}>'


# --- Resource Model ---

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_type_id = db.Column(db.Integer, db.ForeignKey('resource_type.id'), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False, index=True)
    location_description = db.Column(db.String(255), nullable=True)
    capacity = db.Column(db.Integer, nullable=True)
    is_available = db.Column(db.Boolean, nullable=False, default=True, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    resource_type = db.relationship('ResourceType', backref=db.backref('resources', lazy='dynamic'))
    college = db.relationship('College', backref=db.backref('resources', lazy='dynamic'))

    def __repr__(self):
        return f'<Resource {self.id} - {self.name} (Type: {self.resource_type_id})>'


# --- ResourceBooking Model ---

class ResourceBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True) # Booker
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True, index=True) # Optional
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True, index=True) # Optional
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False, index=True)
    purpose = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='confirmed', index=True) # e.g., "confirmed", "pending_approval", "cancelled"
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    resource = db.relationship('Resource', backref=db.backref('bookings', lazy='dynamic'))
    booker = db.relationship('User', backref=db.backref('resource_bookings', lazy='dynamic'))
    course = db.relationship('Course', backref=db.backref('resource_bookings', lazy='dynamic'))
    event = db.relationship('Event', backref=db.backref('resource_bookings', lazy='dynamic'))

    __table_args__ = (
        db.CheckConstraint('end_time > start_time', name='chk_booking_end_time_after_start_time'),
    )

    def __repr__(self):
        return f'<ResourceBooking {self.id} for Resource {self.resource_id} by User {self.user_id} from {self.start_time} to {self.end_time}>'


# --- Hackathon Model ---

class Hackathon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False, index=True)
    end_datetime = db.Column(db.DateTime, nullable=False, index=True)
    registration_deadline = db.Column(db.DateTime, nullable=False, index=True)
    venue = db.Column(db.String(200), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    theme = db.Column(db.String(100), nullable=True)
    rules = db.Column(db.Text, nullable=True)
    prizes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='upcoming', index=True) # e.g., upcoming, ongoing, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    college = db.relationship('College', backref=db.backref('hackathons', lazy='dynamic'))
    organizer = db.relationship('User', backref=db.backref('organized_hackathons', lazy='dynamic'))

    __table_args__ = (
        db.CheckConstraint('end_datetime > start_datetime', name='chk_hackathon_end_after_start'),
        db.CheckConstraint('registration_deadline < start_datetime', name='chk_hackathon_reg_deadline_before_start'),
    )

    def __repr__(self):
        return f'<Hackathon {self.id} - {self.title} at College {self.college_id}>'


# --- HackathonTeam Model ---

class HackathonTeam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hackathon_id = db.Column(db.Integer, db.ForeignKey('hackathon.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    leader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True) # User who is the team leader
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hackathon = db.relationship('Hackathon', backref=db.backref('teams', lazy='dynamic'))
    leader = db.relationship('User', backref=db.backref('led_teams', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('hackathon_id', 'name', name='_hackathon_team_name_uc'),
        db.UniqueConstraint('hackathon_id', 'leader_id', name='_hackathon_leader_uc'),
    )

    def __repr__(self):
        return f'<HackathonTeam {self.id} - {self.name} for Hackathon {self.hackathon_id}>'
