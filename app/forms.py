from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
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
    role = SelectField('Role', choices=[(User.ROLE_STUDENT, 'Student'), (User.ROLE_ALUMNI, 'Alumni')], validators=[DataRequired()])
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
from wtforms.fields import DateTimeField # For EventForm
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
