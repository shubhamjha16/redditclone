from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField # Added IntegerField
from wtforms.fields import DateTimeField, HiddenField, DateField, FieldList, FormField 
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, URL, Optional, NumberRange # Added NumberRange
from app.models import User, College # Make sure College model is imported

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    college = SelectField('College', coerce=int, validators=[DataRequired()]) # We'll populate choices in the route
    college_id_input = StringField('College ID Number (Optional)', validators=[Length(max=50)])
    year_of_college_choices = [
        ('', '-- Select Year --'),
        ('Freshman', 'Freshman'),
        ('Sophomore', 'Sophomore'),
        ('Junior', 'Junior'),
        ('Senior', 'Senior'),
        ('Graduate Year 1', 'Graduate Year 1'),
        ('Graduate Year 2+', 'Graduate Year 2+'),
        ('Alumni', 'Alumni (if role is Alumni)'), # Conditional or adjust role
        ('Other', 'Other'),
    ]
    year_of_college = SelectField('Year of College (Optional)', choices=year_of_college_choices, validators=[])
    role = SelectField('Role', choices=[
        (User.ROLE_STUDENT, 'Student'), 
        (User.ROLE_ALUMNI, 'Alumni'), 
        (User.ROLE_FACULTY, 'Faculty'),
        (User.ROLE_MANAGEMENT, 'Management')
    ], validators=[DataRequired()])
    profile_picture_url = StringField('Profile Picture URL (Optional)', validators=[Length(max=255)])
    bio = StringField('Bio (Optional)', widget=TextArea(), validators=[Length(max=500)])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use. Please choose a different one.')

class LoginForm(FlaskForm):
    email_or_username = StringField('Email or Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    profile_picture_url = StringField('Profile Picture URL (Optional)', validators=[Length(max=255)])
    bio = StringField('Bio (Optional)', widget=TextArea(), validators=[Length(max=500)])
    submit = SubmitField('Update Profile')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose a different one.')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=140)])
    content = StringField('Content', validators=[DataRequired(), Length(min=1, max=10000)], widget=TextArea()) # Use TextArea for larger input
    submit = SubmitField('Submit Post')

# Need to import TextArea first
from wtforms.widgets import TextArea # This import is already here, ensure it stays
# DateTimeField, HiddenField, DateField, FieldList, FormField are now imported from wtforms.fields at the top
from wtforms_sqlalchemy.fields import QuerySelectField # For StudyGroupForm course selection
from app.models import Course, ReportStatus # To populate QuerySelectField and for ReportStatusUpdateForm

class CommentForm(FlaskForm):
    content = StringField('Comment', validators=[DataRequired(), Length(min=1, max=1000)], widget=TextArea())
    submit = SubmitField('Submit Comment')

class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired(), Length(max=100)])
    course_code = StringField('Course Code (e.g., CS101)', validators=[DataRequired(), Length(max=20)])
    description = StringField('Description', widget=TextArea(), validators=[Length(max=5000)])
    instructor = StringField('Instructor Name (Optional)', validators=[Length(max=100)])
    capacity = IntegerField('Capacity (Optional)', validators=[Optional(), NumberRange(min=1, message="Capacity must be at least 1.")])
    submit = SubmitField('Save Course')

def get_college_courses(college_id):
    """ Helper to provide courses for a specific college to QuerySelectField. """
    return Course.query.filter_by(college_id=college_id).order_by(Course.name)

class StudyGroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired(), Length(max=100)])
    description = StringField('Description/Goals', widget=TextArea(), validators=[Length(max=5000)])
    # The course field will be populated in the route, as it depends on the current user's college
    course = QuerySelectField('Associated Course (Optional)',
                              query_factory=lambda: [], # Placeholder, will be set in route
                              get_label='name',
                              allow_blank=True,
                              blank_text='-- None --')
    submit = SubmitField('Create Study Group')

class EventForm(FlaskForm):
    name = StringField('Event Name', validators=[DataRequired(), Length(max=100)])
    description = StringField('Event Description', widget=TextArea(), validators=[Length(max=5000)])
    date_time = DateTimeField('Date and Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired(), Length(max=200)])
    submit = SubmitField('Create Event')

class CollegeForm(FlaskForm):
    name = StringField('College Name', validators=[DataRequired(), Length(max=140)])
    location = StringField('Location (e.g., City, State)', validators=[DataRequired(), Length(max=140)])
    submit = SubmitField('Save College')

class ReportForm(FlaskForm):
    reason = StringField('Reason for Reporting', widget=TextArea(), validators=[DataRequired(), Length(min=10, max=500)])
    submit = SubmitField('Submit Report')

class ReportStatusUpdateForm(FlaskForm):
    status = SelectField('New Status', choices=[
        (ReportStatus.PENDING, 'Pending'),
        (ReportStatus.REVIEWED_ACTION_TAKEN, 'Reviewed - Action Taken'),
        (ReportStatus.REVIEWED_NO_ACTION, 'Reviewed - No Action')
    ], validators=[DataRequired()])
    admin_notes = StringField('Admin Notes', widget=TextArea(), validators=[Length(max=2000)])
    submit = SubmitField('Update Status')

class AdminEditUserForm(FlaskForm):
    username = StringField('Username', render_kw={'readonly': True}) # Display only, not editable by admin
    email = StringField('Email', render_kw={'readonly': True}) # Display only
    role = SelectField('Role', choices=[
        (User.ROLE_STUDENT, 'Student'),
        (User.ROLE_ALUMNI, 'Alumni'),
        (User.ROLE_FACULTY, 'Faculty'),
        (User.ROLE_MANAGEMENT, 'Management'),
        (User.ROLE_ADMIN, 'Admin')
    ], validators=[DataRequired()])
    is_college_verified = BooleanField('College Affiliation Verified')
    # Add college selection if admin should be able to change it. For now, assume it's fixed or handled elsewhere.
    # college = QuerySelectField('College', query_factory=lambda: College.query.all(), get_label='name', allow_blank=True, blank_text='-- No College --')
    submit = SubmitField('Update User')

# Ensure ReportStatus is imported (it's added in the import block above)
# from app.models import ReportStatus # Handled above

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired(), Length(min=1, max=200)])
    submit = SubmitField('Go')

# --- Reel Forms ---

class ReelForm(FlaskForm):
    video_url = StringField('Video URL', validators=[DataRequired(), URL(), Length(max=512)])
    caption = StringField('Caption', widget=TextArea(), validators=[Length(max=1000)])
    submit = SubmitField('Post Reel')

class ReelCommentForm(FlaskForm):
    content = StringField('Add a comment', widget=TextArea(), validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Comment')

# --- Attendance Forms ---

class StudentAttendanceEntryForm(FlaskForm):
    student_id = HiddenField(validators=[DataRequired()])
    username = StringField('Student', render_kw={'readonly': True}) # For display
    status = SelectField('Status', choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused')
    ], validators=[DataRequired()])

class TakeAttendanceForm(FlaskForm):
    course_id = QuerySelectField('Select Course',
                                 query_factory=lambda: [], # Will be populated in the route
                                 get_label='name',
                                 allow_blank=False,
                                 validators=[DataRequired()])
    date = DateField('Attendance Date', format='%Y-%m-%d', validators=[DataRequired()])
    students = FieldList(FormField(StudentAttendanceEntryForm), min_entries=0)
    submit = SubmitField('Submit Attendance')

class ViewAttendanceForm(FlaskForm):
    course_id = QuerySelectField('Filter by Course (Optional)',
                                 query_factory=lambda: Course.query.order_by(Course.name).all(),
                                 get_label='name',
                                 allow_blank=True,
                                 blank_text='-- All Courses --',
                                 validators=[Optional()])
    # For user_id, consider filtering by role (e.g., only students) in the route or a more specific query_factory
    user_id = QuerySelectField('Filter by Student (Optional)',
                               query_factory=lambda: User.query.order_by(User.username).all(), 
                               get_label='username',
                               allow_blank=True,
                               blank_text='-- All Students --',
                               validators=[Optional()])
    start_date = DateField('Start Date (Optional)', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('End Date (Optional)', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('View Attendance')

# --- Course Enrollment Management Forms (Admin/Faculty/Management) ---

class AddStudentEnrollmentForm(FlaskForm):
    student_username = StringField('Student Username or Email', validators=[DataRequired()])
    status = SelectField('Enrollment Status', choices=[
        ('enrolled', 'Enrolled'),
        ('waitlisted', 'Waitlisted'),
        ('dropped', 'Dropped')
    ], validators=[DataRequired()])
    submit_add_student = SubmitField('Add/Update Student Enrollment')

    def validate_student_username(self, student_username):
        # Check if the user exists by username or email
        user = User.query.filter((User.username == student_username.data) | (User.email == student_username.data)).first()
        if not user:
            raise ValidationError('Student with that username or email does not exist.')
        # Optionally, check if the user is a student, or allow any role to be enrolled
        # if user.role != User.ROLE_STUDENT:
        #     raise ValidationError('This user is not registered as a student.')

class ChangeEnrollmentStatusForm(FlaskForm):
    status = SelectField('New Status', choices=[
        ('enrolled', 'Enrolled'),
        ('waitlisted', 'Waitlisted'),
        ('dropped', 'Dropped'),
        ('completed', 'Completed')
    ], validators=[DataRequired()])
    submit_change_status = SubmitField('Change Status')
