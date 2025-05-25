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
