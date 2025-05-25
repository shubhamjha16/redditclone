from flask import render_template, flash, redirect, url_for, request, abort
from app import app, db
from app.forms import (
    LoginForm, RegistrationForm, PostForm, CommentForm,
    CourseForm, StudyGroupForm, EventForm, get_college_courses,
    CollegeForm, ReportForm, ReportStatusUpdateForm, AdminEditUserForm,
    SearchForm, EditProfileForm, ReelForm, ReelCommentForm, # Added Reel forms
    TakeAttendanceForm, StudentAttendanceEntryForm, ViewAttendanceForm, # Added Attendance forms
    AddStudentEnrollmentForm, ChangeEnrollmentStatusForm # Added Enrollment Management forms
)
from app.models import (User, College, Post, Comment, Vote, VoteType, 
                        Course, StudyGroup, Event, Report, ReportStatus, Notification, # Added Notification
                        Reel, ReelComment, ReelLike, AttendanceRecord, CourseEnrollment) # Added Reel, Attendance and CourseEnrollment models
from app.utils import get_target_score, send_notification # Added send_notification
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy import or_
from datetime import datetime, date # Added date


@app.route('/')
@app.route('/index')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    # Show posts from user's college first, then others, or just all recent if no college.
    if current_user.is_authenticated and current_user.college_id:
        posts_query = Post.query.filter(Post.college_id == current_user.college_id)\
            .order_by(Post.timestamp.desc())
    else: # Or show all posts for guests or users without a college
        posts_query = Post.query.order_by(Post.timestamp.desc())
    
    posts_pagination = posts_query.paginate(page=page, per_page=10) # Renamed for clarity
    return render_template('index.html', title='Home', posts=posts_pagination.items, pagination=posts_pagination)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter((User.username == form.email_or_username.data) | (User.email == form.email_or_username.data)).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username/email or password', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(next_page) if next_page else redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form) # We'll create this template later

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    # Populate college choices
    form.college.choices = [(c.id, c.name) for c in College.query.order_by('name').all()]
    if not form.college.choices: # Add a default if no colleges exist
        form.college.choices = [(0, 'No colleges available - please add one')]


    if form.validate_on_submit():
        if form.college.data == 0 and College.query.count() > 0: # Check if default was selected when colleges exist
            flash('Please select a valid college.', 'danger')
            return render_template('register.html', title='Register', form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            college_id=form.college.data if form.college.data != 0 else None,
            role=form.role.data,
            is_college_verified=False,
            college_id_input=form.college_id_input.data,
            year_of_college=form.year_of_college.data if form.year_of_college.data else None,
            profile_picture_url=form.profile_picture_url.data,
            bio=form.bio.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if not current_user.college_id:
        flash('You must be affiliated with a college to create a post. Please update your profile.', 'warning')
        # Or, allow posts without a college if desired, by removing this check
        # and adjusting Post model (e.g. college_id nullable) and logic.
        return redirect(url_for('index'))

    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.id,
            college_id=current_user.college_id
        )
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('view_post', post_id=post.id))
    return render_template('create_post.html', title='Create Post', form=form)

# def get_target_score(target_model, target_id): # Moved to app/utils.py
#     """Helper function to get the score for a post or comment."""
#     score = db.session.query(func.sum(Vote.vote_type)).filter(
#         (Vote.post_id == target_id if target_model == Post else Vote.comment_id == target_id) # This logic is now in utils
#     ).scalar()
#     return score or 0

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    comment_form = CommentForm()

    if comment_form.validate_on_submit() and current_user.is_authenticated:
        comment = Comment(
            content=comment_form.content.data,
            user_id=current_user.id,
            post_id=post.id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published.', 'success')
        return redirect(url_for('view_post', post_id=post.id))
    elif comment_form.is_submitted() and not current_user.is_authenticated:
        flash('You need to be logged in to comment.', 'warning')
        return redirect(url_for('login', next=url_for('view_post', post_id=post.id)))


    page = request.args.get('page', 1, type=int)
    comments_pagination = Comment.query.filter_by(post_id=post.id).order_by(Comment.timestamp.asc()).paginate(page=page, per_page=10) # Renamed for clarity
    
    # Scores are now handled by context_processor or passed if needed for specific optimization
    # For view_post, it's good to pass them directly for clarity for this specific view
    post_score = get_target_score('Post', post.id)
    comment_scores = {comment.id: get_target_score('Comment', comment.id) for comment in comments_pagination.items}

    if comment_form.validate_on_submit() and current_user.is_authenticated: # This was part of original logic, moved up for clarity
        comment = Comment(
            content=comment_form.content.data,
            user_id=current_user.id,
            post_id=post.id
        )
        db.session.add(comment)
        
        # --- Notification Logic ---
        if post.author.id != current_user.id: # Don't notify if user comments on their own post
            payload = {
                'post_id': post.id,
                'post_title': post.title, # For quick display in notification
                'commenter_id': current_user.id,
                'commenter_username': current_user.username,
                'comment_id': comment.id # Will be available after commit, but we might need to flush
            }
            # To get comment.id, we need to flush or commit.
            # Let's flush to get the ID before full commit.
            db.session.flush() # Assigns ID to comment object
            payload['comment_id'] = comment.id # Now comment.id is available
            
            send_notification(post.author.id, 'new_comment_on_post', payload)
        # --- End Notification Logic ---
            
        db.session.commit() # Commit comment and notification
        flash('Your comment has been published.', 'success')
        return redirect(url_for('view_post', post_id=post.id, _anchor=f'comment-{comment.id}'))
    # The rest of the route remains largely the same, just the comment creation part is modified/moved

    return render_template('view_post.html', title=post.title, post=post, comments=comments_pagination.items, 
                           comment_form=comment_form, pagination=comments_pagination,
                           post_score=post_score, comment_scores=comment_scores)

@app.route('/vote/<target_type>/<int:target_id>/<vote_action>', methods=['POST'])
@login_required
def vote(target_type, target_id, vote_action):
    if target_type not in ['post', 'comment']:
        abort(404)
    
    target_model = Post if target_type == 'post' else Comment
    target = target_model.query.get_or_404(target_id)

    if vote_action not in ['upvote', 'downvote']:
        abort(400) # Bad request

    vote_value = VoteType.UPVOTE if vote_action == 'upvote' else VoteType.DOWNVOTE

    existing_vote = Vote.query.filter(
        Vote.user_id == current_user.id,
        (Vote.post_id == target_id) if target_type == 'post' else (Vote.comment_id == target_id)
    ).first()

    if existing_vote:
        if existing_vote.vote_type == vote_value: # Clicking upvote again on an upvoted post (remove vote)
            db.session.delete(existing_vote)
            flash('Your vote has been removed.', 'info')
        else: # Changing vote (e.g., from upvote to downvote)
            existing_vote.vote_type = vote_value
            flash('Your vote has been changed.', 'success')
    else: # New vote
        new_vote_args = {'user_id': current_user.id, 'vote_type': vote_value}
        if target_type == 'post':
            new_vote_args['post_id'] = target_id
        else:
            new_vote_args['comment_id'] = target_id
        
        new_vote = Vote(**new_vote_args)
        db.session.add(new_vote)
        flash('Your vote has been recorded.', 'success')
    
    db.session.commit()

    # Redirect back to the post or the page containing the comment
    if target_type == 'post':
        return redirect(url_for('view_post', post_id=target_id))
    else: # comment
        # A comment is always part of a post, so redirect to the comment's post page
        return redirect(url_for('view_post', post_id=target.post_id, _anchor=f'comment-{target_id}'))


@app.route('/college/<int:college_id>/posts')
def college_posts(college_id):
    college = College.query.get_or_404(college_id)
    page = request.args.get('page', 1, type=int)
    posts_pagination = Post.query.filter_by(college_id=college.id).order_by(Post.timestamp.desc()).paginate(page=page, per_page=10)
    return render_template('college_posts.html', title=f"Posts for {college.name}", posts=posts_pagination.items, college=college, pagination=posts_pagination)


# Placeholder for college verification - can be expanded later
@app.route('/verify_college_email/<token>')
@login_required
def verify_college_email(token):
    # This would be part of a more complex email verification system
    # For now, it's a placeholder.
    # We might use itsdangerous to generate and verify tokens sent to user's college email.
    flash('College email verification functionality to be implemented.', 'info')
    return redirect(url_for('index'))

# Example of a protected route that requires a specific role
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != User.ROLE_ADMIN:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))
    # return "Admin Dashboard - Only accessible by users with 'admin' role."
    # For testing, let's make a simple admin page that lists users
    users = User.query.all()
    return render_template('admin_dashboard.html', title="Admin Dashboard", users=users)


# -------------------------- Course Routes --------------------------

@app.route('/college/<int:college_id>/courses', methods=['GET'])
def list_college_courses(college_id):
    college = College.query.get_or_404(college_id)
    page = request.args.get('page', 1, type=int)
    courses_pagination = Course.query.filter_by(college_id=college.id)\
        .order_by(Course.name.asc())\
        .paginate(page=page, per_page=10)
    
    courses_on_page = courses_pagination.items
    enrollment_info = {}
    for course_item in courses_on_page:
        enrolled_count = CourseEnrollment.query.filter_by(course_id=course_item.id, status='enrolled').count()
        enrollment_info[course_item.id] = enrolled_count
        
    return render_template('college_courses.html', title=f"Courses at {college.name}", 
                           college=college, courses_pagination=courses_pagination, 
                           enrollment_info=enrollment_info)

@app.route('/college/<int:college_id>/course/create', methods=['GET', 'POST'])
@login_required
def create_course(college_id):
    college = College.query.get_or_404(college_id)
    if current_user.college_id != college.id:
        # Add role check here: and not current_user.is_admin(): # or a specific role like 'faculty'
        flash('You are not authorized to create courses for this college.', 'danger')
        return redirect(url_for('list_college_courses', college_id=college.id))
    
    form = CourseForm()
    if form.validate_on_submit():
        existing_course = Course.query.filter_by(college_id=college.id, course_code=form.course_code.data).first()
        if existing_course:
            flash('A course with this code already exists for this college.', 'warning')
        else:
            course = Course(
                name=form.name.data,
                course_code=form.course_code.data,
                description=form.description.data,
                instructor=form.instructor.data,
                college_id=college.id,
                capacity=form.capacity.data
            )
            db.session.add(course)
            db.session.commit()
            flash(f'Course "{course.name}" has been created successfully!', 'success')
            return redirect(url_for('list_college_courses', college_id=college.id))
    return render_template('create_course.html', title='Create New Course', form=form, college=college)

@app.route('/course/<int:course_id>', methods=['GET'])
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Calculate enrolled_count
    enrolled_count = CourseEnrollment.query.filter_by(course_id=course.id, status='enrolled').count()
    
    # Determine current_enrollment for the logged-in user
    current_enrollment = None
    if current_user.is_authenticated:
        current_enrollment = CourseEnrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
        
    # study_groups already available via course.study_groups relationship
    return render_template('view_course.html', title=course.name, course=course,
                           enrolled_count=enrolled_count, current_enrollment=current_enrollment)


# -------------------------- Study Group Routes --------------------------

@app.route('/college/<int:college_id>/studygroups', methods=['GET'])
def list_college_study_groups(college_id):
    college = College.query.get_or_404(college_id)
    page = request.args.get('page', 1, type=int)
    # Filter study groups by college and order them, e.g., by name
    studygroups_pagination = StudyGroup.query.filter_by(college_id=college.id)\
        .order_by(StudyGroup.name.asc())\
        .paginate(page=page, per_page=10)
    return render_template('college_studygroups.html', title=f"Study Groups at {college.name}",
                           college=college, study_groups=studygroups_pagination)

@app.route('/college/<int:college_id>/studygroup/create', methods=['GET', 'POST'])
@app.route('/course/<int:course_id>/studygroup/create', methods=['GET', 'POST'], endpoint='create_study_group_for_course') # For creating from course page
@login_required
def create_study_group(college_id=None, course_id=None):
    target_college = None
    target_course = None

    if course_id: # If creating from a specific course page
        target_course = Course.query.get_or_404(course_id)
        target_college = target_course.college
        college_id = target_college.id # Ensure college_id is set
    elif college_id:
        target_college = College.query.get_or_404(college_id)
    else: # Should not happen if routes are set up correctly
        abort(400, "College ID or Course ID must be provided.")

    if current_user.college_id != target_college.id:
        flash('You must be affiliated with this college to create a study group for it.', 'danger')
        return redirect(url_for('index')) # Or a more relevant page

    form = StudyGroupForm()
    # Dynamically set the query_factory for the course field
    form.course.query_factory = lambda: get_college_courses(target_college.id)
    if target_course: # Pre-select the course if coming from a course page
        form.course.data = target_course

    if form.validate_on_submit():
        study_group = StudyGroup(
            name=form.name.data,
            description=form.description.data,
            user_id=current_user.id,
            college_id=target_college.id,
            course_id=form.course.data.id if form.course.data else None
        )
        db.session.add(study_group)
        db.session.commit()
        flash(f'Study group "{study_group.name}" has been created!', 'success')
        return redirect(url_for('view_study_group', group_id=study_group.id))
    
    return render_template('create_studygroup.html', title='Create New Study Group', 
                           form=form, college=target_college, course=target_course)


@app.route('/studygroup/<int:group_id>', methods=['GET'])
def view_study_group(group_id):
    study_group = StudyGroup.query.get_or_404(group_id)
    return render_template('view_studygroup.html', title=study_group.name, group=study_group)


# -------------------------- Event Routes --------------------------

@app.route('/college/<int:college_id>/events', methods=['GET'])
def list_college_events(college_id):
    college = College.query.get_or_404(college_id)
    page = request.args.get('page', 1, type=int)
    events_pagination = Event.query.filter_by(college_id=college.id)\
        .order_by(Event.date_time.asc())\
        .paginate(page=page, per_page=10)
    return render_template('college_events.html', title=f"Events at {college.name}",
                           college=college, events=events_pagination)

@app.route('/college/<int:college_id>/event/create', methods=['GET', 'POST'])
@login_required
def create_event(college_id):
    college = College.query.get_or_404(college_id)
    if current_user.college_id != college.id:
        flash('You must be affiliated with this college to create an event for it.', 'danger')
        return redirect(url_for('list_college_events', college_id=college.id))

    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            name=form.name.data,
            description=form.description.data,
            date_time=form.date_time.data,
            location=form.location.data,
            user_id=current_user.id,
            college_id=college.id
        )
        db.session.add(event)
        db.session.commit()
        flash(f'Event "{event.name}" has been created!', 'success')
        return redirect(url_for('view_event', event_id=event.id))
    return render_template('create_event.html', title='Create New Event', form=form, college=college)

@app.route('/event/<int:event_id>', methods=['GET'])
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('view_event.html', title=event.name, event=event)


# -------------------------- Admin College Management Routes --------------------------

@app.route('/admin/colleges', methods=['GET'])
@login_required
def admin_list_colleges():
    if not current_user.role == User.ROLE_ADMIN:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))
    
    colleges = College.query.order_by(College.name).all()
    return render_template('admin/list_colleges.html', title="Manage Colleges", colleges=colleges)

@app.route('/admin/college/create', methods=['GET', 'POST'])
@login_required
def admin_create_college():
    if not current_user.role == User.ROLE_ADMIN:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))
    
    form = CollegeForm()
    if form.validate_on_submit():
        existing_college = College.query.filter_by(name=form.name.data).first()
        if existing_college:
            flash('A college with this name already exists.', 'warning')
        else:
            college = College(name=form.name.data, location=form.location.data)
            db.session.add(college)
            db.session.commit()
            flash(f'College "{college.name}" has been created successfully!', 'success')
            return redirect(url_for('admin_list_colleges'))
    return render_template('admin/create_edit_college.html', title="Create New College", form=form)

@app.route('/admin/college/<int:college_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_college(college_id):
    if not current_user.role == User.ROLE_ADMIN:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))
    
    college = College.query.get_or_404(college_id)
    form = CollegeForm(obj=college) # Pre-populate form with existing data

    if form.validate_on_submit():
        # Check if new name conflicts with another existing college
        if form.name.data != college.name:
            existing_college_with_new_name = College.query.filter(College.name == form.name.data, College.id != college.id).first()
            if existing_college_with_new_name:
                flash('Another college with this name already exists.', 'warning')
                return render_template('admin/create_edit_college.html', title=f"Edit College: {college.name}", form=form, college=college)
        
        college.name = form.name.data
        college.location = form.location.data
        db.session.commit()
        flash(f'College "{college.name}" has been updated successfully!', 'success')
        return redirect(url_for('admin_list_colleges'))
    
    return render_template('admin/create_edit_college.html', title=f"Edit College: {college.name}", form=form, college=college)

# Optional: Delete route (requires careful consideration of cascading effects or setting FKs to null)
# @app.route('/admin/college/<int:college_id>/delete', methods=['POST'])
# @login_required
# def admin_delete_college(college_id):
#     if not current_user.role == User.ROLE_ADMIN:
#         flash('You do not have permission to access this page.', 'danger')
#         return redirect(url_for('index'))
#     college_to_delete = College.query.get_or_404(college_id)
#     # Check for dependencies (users, posts, etc.) before deleting or handle them (e.g., reassign, nullify, cascade)
#     if college_to_delete.users.first() or college_to_delete.posts.first(): # Basic check
#         flash(f'College "{college_to_delete.name}" cannot be deleted as it has associated users or posts. Please reassign or remove them first.', 'danger')
#         return redirect(url_for('admin_list_colleges'))
#     db.session.delete(college_to_delete)
#     db.session.commit()
#     flash(f'College "{college_to_delete.name}" has been deleted.', 'success')
#     return redirect(url_for('admin_list_colleges'))


# -------------------------- Reporting Routes --------------------------

@app.route('/report/post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def report_post(post_id):
    post = Post.query.get_or_404(post_id)
    # Prevent users from reporting their own content or reporting multiple times (optional enhancement)
    existing_report = Report.query.filter_by(reporter_id=current_user.id, post_id=post.id).first()
    if existing_report:
        flash('You have already reported this post.', 'info')
        return redirect(url_for('view_post', post_id=post.id))
    if post.author.id == current_user.id:
        flash('You cannot report your own post.', 'warning')
        return redirect(url_for('view_post', post_id=post.id))

    form = ReportForm()
    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            post_id=post.id,
            reason=form.reason.data,
            status=ReportStatus.PENDING
        )
        db.session.add(report)
        db.session.commit()
        flash('Thank you for your report. Our moderators will review it shortly.', 'success')
        return redirect(url_for('view_post', post_id=post.id))
    
    return render_template('report_content.html', title='Report Post', form=form,
                           target_post=post, cancel_url=url_for('view_post', post_id=post.id))

@app.route('/report/comment/<int:comment_id>', methods=['GET', 'POST'])
@login_required
def report_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    existing_report = Report.query.filter_by(reporter_id=current_user.id, comment_id=comment.id).first()
    if existing_report:
        flash('You have already reported this comment.', 'info')
        return redirect(url_for('view_post', post_id=comment.post_id, _anchor=f'comment-{comment.id}'))
    if comment.author.id == current_user.id:
        flash('You cannot report your own comment.', 'warning')
        return redirect(url_for('view_post', post_id=comment.post_id, _anchor=f'comment-{comment.id}'))

    form = ReportForm()
    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            comment_id=comment.id,
            reason=form.reason.data,
            status=ReportStatus.PENDING
        )
        db.session.add(report)
        db.session.commit()
        flash('Thank you for your report. Our moderators will review it shortly.', 'success')
        return redirect(url_for('view_post', post_id=comment.post_id, _anchor=f'comment-{comment.id}'))

    return render_template('report_content.html', title='Report Comment', form=form,
                           target_comment=comment, cancel_url=url_for('view_post', post_id=comment.post_id, _anchor=f'comment-{comment.id}'))


# -------------------------- Admin Report Management Routes --------------------------

@app.route('/admin/reports', methods=['GET'])
@login_required
def admin_list_reports():
    if not current_user.role == User.ROLE_ADMIN:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    # Default to pending reports, but could add filter for all/other statuses
    reports_pagination = Report.query.filter(Report.status == ReportStatus.PENDING)\
                                     .order_by(Report.timestamp.asc())\
                                     .paginate(page=page, per_page=10)
    return render_template('admin/list_reports.html', title="Pending Reports", reports=reports_pagination)

@app.route('/admin/report/<int:report_id>/view', methods=['GET'])
@login_required
def admin_view_report(report_id):
    if not current_user.role == User.ROLE_ADMIN:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))
    
    report = Report.query.get_or_404(report_id)
    status_form = ReportStatusUpdateForm(obj=report) # Pre-populate with current status/notes

    return render_template('admin/view_report.html', title=f"View Report {report.id}", 
                           report=report, status_form=status_form)

@app.route('/admin/report/<int:report_id>/update_status', methods=['POST'])
@login_required
def admin_update_report_status(report_id):
    if not current_user.role == User.ROLE_ADMIN:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))
        
    report = Report.query.get_or_404(report_id)
    status_form = ReportStatusUpdateForm() # Form data will be populated by request

    if status_form.validate_on_submit():
        report.status = status_form.status.data
        report.admin_notes = status_form.admin_notes.data
        db.session.commit()
        flash(f'Report {report.id} status has been updated.', 'success')
        return redirect(url_for('admin_view_report', report_id=report.id))
    else:
        # If form validation fails, re-render the view_report page with errors
        flash('Error updating report status. Please check the form.', 'danger')
        return render_template('admin/view_report.html', title=f"View Report {report.id}", 
                               report=report, status_form=status_form)


# -------------------------- Admin User Management Routes --------------------------

@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if not current_user.role == User.ROLE_ADMIN:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

    user_to_edit = User.query.get_or_404(user_id)
    form = AdminEditUserForm(obj=user_to_edit) # Pre-populate form

    if form.validate_on_submit():
        # Prevent admin from un-admining themselves if they are the only admin (optional safety check)
        if user_to_edit.id == current_user.id and user_to_edit.role == User.ROLE_ADMIN and form.role.data != User.ROLE_ADMIN:
            if User.query.filter_by(role=User.ROLE_ADMIN).count() == 1:
                flash("You cannot remove your own admin status as you are the only administrator.", "danger")
                return redirect(url_for('admin_edit_user', user_id=user_id))

        user_to_edit.role = form.role.data
        user_to_edit.is_college_verified = form.is_college_verified.data
        # user_to_edit.college_id = form.college.data.id if form.college.data else None # If college editing is added
        db.session.commit()
        flash(f"User {user_to_edit.username}'s details have been updated.", "success")
        return redirect(url_for('admin_dashboard')) # Or a more specific user list page

    return render_template('admin/edit_user.html', title=f"Edit User: {user_to_edit.username}",
                           form=form, user_to_edit=user_to_edit)


# -------------------------- Search Route --------------------------

@app.route('/search')
def search():
    query = request.args.get('query', '').strip() # Get query from URL parameter
    # The search_form from context_processor is for rendering in base.html.
    # For processing, we directly use request.args.
    
    posts_results = []
    courses_results = []
    colleges_results = []

    if not query:
        flash('Please enter a search term.', 'info')
        # Optionally, redirect to index or a more dedicated search page if query is empty
        # return redirect(url_for('index')) 
    else:
        search_term = f"%{query}%" # Prepare for ILIKE/LIKE
        
        # Search Posts
        posts_results = Post.query.filter(
            or_(
                Post.title.ilike(search_term),
                Post.content.ilike(search_term)
            )
        ).order_by(Post.timestamp.desc()).all()

        # Search Courses
        courses_results = Course.query.filter(
            or_(
                Course.name.ilike(search_term),
                Course.course_code.ilike(search_term),
                Course.description.ilike(search_term),
                Course.instructor.ilike(search_term) # Assuming instructor is a string field
            )
        ).order_by(Course.name).all()

        # Search Colleges
        colleges_results = College.query.filter(
            or_(
                College.name.ilike(search_term),
                College.location.ilike(search_term)
            )
        ).order_by(College.name).all()

    return render_template('search_results.html', title=f"Search Results for '{query}'",
                           query=query,
                           posts=posts_results,
                           courses=courses_results,
                           colleges=colleges_results)


# -------------------------- User Profile Route --------------------------

@app.route('/user/<username>')
@login_required # Or remove if profiles should be public
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    # Add pagination for posts and comments later if desired
    user_posts = user.posts.order_by(Post.timestamp.desc()).limit(5).all() # Show recent 5 posts
    user_comments = user.comments.order_by(Comment.timestamp.desc()).limit(5).all() # Show recent 5 comments
    
    # Fetch enrolled courses
    enrolled_courses = Course.query.join(CourseEnrollment).filter(
        CourseEnrollment.user_id == user.id, 
        CourseEnrollment.status == 'enrolled'
    ).order_by(Course.name.asc()).all()
    
    return render_template('user_profile.html', title=f"Profile: {user.username}", 
                           user=user, user_posts=user_posts, user_comments=user_comments,
                           enrolled_courses=enrolled_courses)


# -------------------------- Notification Routes --------------------------

@app.route('/notifications')
@login_required
def list_notifications():
    page = request.args.get('page', 1, type=int)
    notifications_pagination = Notification.query.filter_by(user_id=current_user.id)\
                                          .order_by(Notification.timestamp.desc())\
                                          .paginate(page=page, per_page=10)
    
    # Optionally, mark all *displayed* notifications as read upon viewing the page
    # for notif in notifications_pagination.items:
    #     if not notif.is_read:
    #         notif.is_read = True
    # db.session.commit()
    # This approach might be too aggressive. Better to use explicit "mark as read" buttons.

    return render_template('notifications.html', title="Your Notifications", 
                           notifications=notifications_pagination)

@app.route('/notifications/mark_as_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_as_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        abort(403) # Forbidden
    
    notification.is_read = True
    db.session.commit()
    flash('Notification marked as read.', 'success')
    # Try to redirect back to the source of the click or the notifications page
    return redirect(request.referrer or url_for('list_notifications'))


@app.route('/notifications/mark_all_as_read', methods=['POST'])
@login_required
def mark_all_notifications_as_read():
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for notification in unread_notifications:
        notification.is_read = True
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('list_notifications'))

# -------------------------- Edit Profile Route --------------------------
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(original_username=current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.profile_picture_url = form.profile_picture_url.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('user_profile', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.profile_picture_url.data = current_user.profile_picture_url
        form.bio.data = current_user.bio
    return render_template('edit_profile.html', title='Edit Profile', form=form)

# -------------------------- Follow/Unfollow Routes --------------------------
@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        flash('You cannot follow yourself.', 'warning')
        return redirect(url_for('user_profile', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(f'You are now following {username}.', 'success')
    # TODO: Send notification to 'user' that current_user is now following them
    # send_notification(user.id, 'new_follower', {'follower_id': current_user.id, 'follower_username': current_user.username})
    return redirect(url_for('user_profile', username=username))

@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user: # Should not happen if UI prevents this
        flash('You cannot unfollow yourself.', 'warning')
        return redirect(url_for('user_profile', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You have unfollowed {username}.', 'info')
    return redirect(url_for('user_profile', username=username))

# -------------------------- Before Request Handler (last_seen) -----------------
@app.before_request
def before_request_handler():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

# -------------------------- Reel Routes ------------------------------------

@app.route('/reels_feed', methods=['GET'])
@login_required # Optional: make public if desired by removing decorator
def reels_feed():
    page = request.args.get('page', 1, type=int)
    # Fetch reels, ordered by timestamp descending.
    # Could also filter by college or other criteria.
    reels_pagination = Reel.query.order_by(Reel.timestamp.desc()).paginate(
        page=page, per_page=5 # Show 5 reels per page for example
    )
    return render_template('reels_feed.html', title="Reels Feed", 
                           reels=reels_pagination.items, pagination=reels_pagination)

@app.route('/create_reel', methods=['GET', 'POST'])
@login_required
def create_reel():
    form = ReelForm()
    if form.validate_on_submit():
        reel_college_id = current_user.college_id if hasattr(current_user, 'college_id') else None
        
        reel = Reel(
            user_id=current_user.id,
            college_id=reel_college_id,
            video_url=form.video_url.data,
            caption=form.caption.data
        )
        db.session.add(reel)
        db.session.commit()
        flash('Your reel has been posted!', 'success')
        return redirect(url_for('reels_feed')) # Or view_reel for the new reel: url_for('view_reel', reel_id=reel.id)
    return render_template('create_reel.html', title='Create Reel', form=form)

@app.route('/reel/<int:reel_id>', methods=['GET', 'POST'])
def view_reel(reel_id): # login_required not strictly needed for viewing, but is for commenting/liking
    reel = Reel.query.get_or_404(reel_id)
    comment_form = ReelCommentForm()
    
    # Handle comment submission
    if comment_form.validate_on_submit() and current_user.is_authenticated:
        new_comment = ReelComment(
            content=comment_form.content.data,
            user_id=current_user.id,
            reel_id=reel.id
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('Your comment has been posted.', 'success')
        return redirect(url_for('view_reel', reel_id=reel.id))
    elif comment_form.is_submitted() and not current_user.is_authenticated:
        flash('You must be logged in to comment.', 'warning')
        return redirect(url_for('login', next=url_for('view_reel', reel_id=reel.id)))

    # Data for GET request or for re-rendering after failed comment POST
    comments = reel.comments.order_by(ReelComment.timestamp.asc()).all() # Paginate if many comments
    like_count = reel.likes.count()
    user_liked_reel = False
    if current_user.is_authenticated:
        user_liked_reel = ReelLike.query.filter_by(user_id=current_user.id, reel_id=reel.id).first() is not None
        
    # Increment view count - simple version, could be made more robust
    # to avoid double counting from same user in short time, etc.
    # Only increment if not the author viewing their own reel (optional rule)
    if not current_user.is_authenticated or current_user.id != reel.user_id:
        reel.views_count = (reel.views_count or 0) + 1
        db.session.commit()

    return render_template('view_reel.html', title=f"Reel by {reel.author.username}", 
                           reel=reel, comments=comments, comment_form=comment_form,
                           like_count=like_count, user_liked_reel=user_liked_reel)

@app.route('/reel/<int:reel_id>/like', methods=['POST'])
@login_required
def like_reel(reel_id):
    reel = Reel.query.get_or_404(reel_id)
    existing_like = ReelLike.query.filter_by(user_id=current_user.id, reel_id=reel.id).first()

    if existing_like:
        db.session.delete(existing_like)
        flash('You unliked the reel.', 'info')
    else:
        new_like = ReelLike(user_id=current_user.id, reel_id=reel.id)
        db.session.add(new_like)
        flash('You liked the reel!', 'success')
    
    db.session.commit()
    return redirect(url_for('view_reel', reel_id=reel.id))

# -------------------------- Attendance Routes ------------------------------

@app.route('/course/<int:course_id>/take_attendance', methods=['GET', 'POST'])
@login_required
def take_attendance(course_id):
    course = Course.query.get_or_404(course_id)
    # Role Check: Allow Admin or Faculty
    if current_user.role not in [User.ROLE_ADMIN, User.ROLE_FACULTY]:
        flash('You do not have permission to take attendance for this course.', 'danger')
        return redirect(url_for('view_course', course_id=course.id))

    form = TakeAttendanceForm(request.form) # Pass request.form for POST data
    form.course_id.query = Course.query.filter_by(id=course_id) # Set query for the specific course

    if request.method == 'GET':
        form.course_id.data = course # Pre-select current course
        form.date.data = date.today() # Default to today
        
        # Fetch enrolled students for the course
        students_for_attendance = User.query.join(CourseEnrollment).filter(
            CourseEnrollment.course_id == course.id,
            CourseEnrollment.status == 'enrolled'
        ).order_by(User.username.asc()).all()
        
        # Clear existing student entries in form before populating
        while len(form.students.entries) > 0:
            form.students.pop_entry()

        # Fetch existing records for these enrolled students for this course and selected date
        selected_date = form.date.data
        if students_for_attendance: # Only query if there are students to check for
            existing_records_list = AttendanceRecord.query.filter(
                AttendanceRecord.course_id == course.id,
                AttendanceRecord.date == selected_date,
                AttendanceRecord.user_id.in_([s.id for s in students_for_attendance])
            ).all()
            existing_records_map = {rec.user_id: rec.status for rec in existing_records_list}
        else:
            existing_records_map = {}


        for student in students_for_attendance:
            entry_form_data = { # Create a dictionary for FormField data
                'student_id': student.id,
                'username': student.username,
                'status': existing_records_map.get(student.id, 'present') # Default to 'present'
            }
            form.students.append_entry(data=entry_form_data)
            
    elif form.validate_on_submit(): # POST request
        attendance_date = form.date.data
        for student_form_field in form.students:
            student_id = int(student_form_field.student_id.data) # Ensure student_id is int
            status = student_form_field.status.data
            
            record = AttendanceRecord.query.filter_by(
                user_id=student_id, 
                course_id=course.id, 
                date=attendance_date
            ).first()
            
            if record:
                record.status = status
                record.marked_by_id = current_user.id
                record.timestamp = datetime.utcnow()
            else:
                record = AttendanceRecord(
                    user_id=student_id, 
                    course_id=course.id, 
                    date=attendance_date, 
                    status=status, 
                    marked_by_id=current_user.id
                )
                db.session.add(record)
        
        db.session.commit()
        flash('Attendance records have been saved/updated.', 'success')
        # Redirect to the same page, which will then repopulate with the saved data for that date
        return redirect(url_for('take_attendance', course_id=course.id, date=attendance_date.isoformat()))

    # If GET or POST validation failed, render the template
    # For GET, students are populated above. For POST error, WTForms handles field values.
    # If POST fails and we re-render, we might need to re-populate the dynamic student list if it's not preserved by FieldList.
    # The above GET logic for populating students will run again if validation fails on POST,
    # which is acceptable as it will reflect the submitted (but not validated) date.
    return render_template('take_attendance.html', title=f'Take Attendance for {course.name}', form=form, course=course)


@app.route('/course/<int:course_id>/view_attendance', methods=['GET', 'POST'])
@login_required
def view_course_attendance(course_id):
    course = Course.query.get_or_404(course_id)
    # Permission: Allow Admin or Faculty to view course attendance
    # (and potentially student to view their own, handled by view_user_attendance)
    # A more specific check for "instructor of this course" could be added later.
    if current_user.role not in [User.ROLE_ADMIN, User.ROLE_FACULTY]:
        # If student, they should use their own attendance view.
        # If other role, they don't have permission.
        is_student_in_course = False # Placeholder for logic to check if user is student in this course
        if current_user.role == User.ROLE_STUDENT:
            # Here you might check if current_user is enrolled in this course.
            # For now, we'll assume students can't use this specific view directly.
            pass # Keep this check simple for now.
        
        # If not Admin or Faculty, and not a student viewing their own (which this route isn't designed for)
        if current_user.role not in [User.ROLE_ADMIN, User.ROLE_FACULTY]: # Re-check after potential student logic
             flash('You do not have permission to view attendance for this course.', 'danger')
             return redirect(url_for('view_course', course_id=course.id))

    form = ViewAttendanceForm(request.form)
    # Populate choices for the form's QuerySelectFields if they depend on context (e.g., students in this course)
    # form.user_id.query = User.query.filter(User.attendance_records.any(course_id=course.id)).order_by(User.username) # More complex
    # For now, the default query_factory in the form definition (all users) is used.

    query = AttendanceRecord.query.filter_by(course_id=course.id)

    if form.validate_on_submit(): # This handles POST for form submission
        if form.user_id.data:
            query = query.filter(AttendanceRecord.user_id == form.user_id.data.id)
        if form.start_date.data:
            query = query.filter(AttendanceRecord.date >= form.start_date.data)
        if form.end_date.data:
            query = query.filter(AttendanceRecord.date <= form.end_date.data)
    elif request.method == 'GET': # Handle GET request with query parameters for filtering
        if request.args.get('user_id'):
             query = query.filter(AttendanceRecord.user_id == request.args.get('user_id'))
        if request.args.get('start_date'):
            try:
                start_dt = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
                query = query.filter(AttendanceRecord.date >= start_dt)
                form.start_date.data = start_dt # Pre-fill form
            except ValueError:
                flash('Invalid start date format. Please use YYYY-MM-DD.', 'warning')
        if request.args.get('end_date'):
            try:
                end_dt = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
                query = query.filter(AttendanceRecord.date <= end_dt)
                form.end_date.data = end_dt # Pre-fill form
            except ValueError:
                flash('Invalid end date format. Please use YYYY-MM-DD.', 'warning')
        # Pre-fill other form fields from GET args if needed
        if request.args.get('user_id'):
            user_filter_id = request.args.get('user_id', type=int)
            user_for_filter = User.query.get(user_filter_id)
            if user_for_filter:
                form.user_id.data = user_for_filter


    attendance_records = query.order_by(AttendanceRecord.date.desc(), AttendanceRecord.student.has(User.username)).all()
    
    return render_template('view_attendance_course.html', title=f'Attendance for {course.name}', 
                           form=form, course=course, records=attendance_records)


@app.route('/user/<username>/attendance', methods=['GET', 'POST'])
@login_required
def view_user_attendance(username):
    user_profile = User.query.filter_by(username=username).first_or_404()

    if current_user != user_profile and current_user.role != User.ROLE_ADMIN:
        flash('You do not have permission to view this attendance report.', 'danger')
        return redirect(url_for('index'))

    form = ViewAttendanceForm(request.form)
    # Populate form.course_id.query dynamically if it should only show courses the user is in
    # form.course_id.query = Course.query.join(AttendanceRecord).filter(AttendanceRecord.user_id == user_profile.id).distinct().order_by(Course.name)
    # For now, the default query_factory (all courses) is used.

    query = AttendanceRecord.query.filter_by(user_id=user_profile.id)

    if form.validate_on_submit(): # This handles POST for form submission
        if form.course_id.data:
            query = query.filter(AttendanceRecord.course_id == form.course_id.data.id)
        if form.start_date.data:
            query = query.filter(AttendanceRecord.date >= form.start_date.data)
        if form.end_date.data:
            query = query.filter(AttendanceRecord.date <= form.end_date.data)
    elif request.method == 'GET': # Handle GET request with query parameters
        if request.args.get('course_id'):
            query = query.filter(AttendanceRecord.course_id == request.args.get('course_id'))
        if request.args.get('start_date'):
            try:
                start_dt_user = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
                query = query.filter(AttendanceRecord.date >= start_dt_user)
                form.start_date.data = start_dt_user
            except ValueError:
                flash('Invalid start date format. Please use YYYY-MM-DD.', 'warning')
        if request.args.get('end_date'):
            try:
                end_dt_user = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
                query = query.filter(AttendanceRecord.date <= end_dt_user)
                form.end_date.data = end_dt_user
            except ValueError:
                flash('Invalid end date format. Please use YYYY-MM-DD.', 'warning')
        if request.args.get('course_id'):
            course_filter_id = request.args.get('course_id', type=int)
            course_for_filter = Course.query.get(course_filter_id)
            if course_for_filter:
                form.course_id.data = course_for_filter


    attendance_records = query.order_by(AttendanceRecord.course.has(Course.name), AttendanceRecord.date.desc()).all()
    
    return render_template('view_attendance_user.html', title=f'Attendance for {user_profile.username}',
                           form=form, user_profile=user_profile, records=attendance_records)

# -------------------------- Course Enrollment Routes -----------------------

@app.route('/course/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll_in_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check if user is already enrolled
    existing_enrollment = CourseEnrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    
    if existing_enrollment:
        if existing_enrollment.status == 'enrolled':
            flash('You are already enrolled in this course.', 'info')
        elif existing_enrollment.status == 'dropped':
            # Check capacity before re-enrolling a dropped student
            enrolled_count = CourseEnrollment.query.filter_by(course_id=course.id, status='enrolled').count()
            if course.capacity is not None and enrolled_count >= course.capacity:
                flash(f'This course is currently full (capacity: {course.capacity}). You cannot re-enroll at this time.', 'warning')
            else:
                existing_enrollment.status = 'enrolled'
                existing_enrollment.enrollment_date = datetime.utcnow()
                db.session.commit()
                flash('You have been re-enrolled in this course.', 'success')
        else: # e.g., 'waitlisted', 'completed' - handle as per desired logic
            flash(f'Your current enrollment status is "{existing_enrollment.status}". Re-enrollment from this status is not currently supported via this action.', 'warning')
    else:
        # New enrollment: Check capacity
        enrolled_count = CourseEnrollment.query.filter_by(course_id=course.id, status='enrolled').count()
        if course.capacity is not None and enrolled_count >= course.capacity:
            # Basic full check - could implement waitlist logic here if desired
            flash(f'This course is currently full (capacity: {course.capacity}). Enrollment is not possible at this time.', 'warning')
        else:
            new_enrollment = CourseEnrollment(user_id=current_user.id, course_id=course.id, status='enrolled')
            db.session.add(new_enrollment)
            db.session.commit()
            flash('You have successfully enrolled in the course!', 'success')
            
    return redirect(url_for('view_course', course_id=course.id))

# -------------------------- Enrollment Management Route --------------------

@app.route('/course/<int:course_id>/manage_enrollments', methods=['GET', 'POST'])
@login_required
def manage_course_enrollments(course_id):
    course = Course.query.get_or_404(course_id)

    if current_user.role not in [User.ROLE_ADMIN, User.ROLE_MANAGEMENT]:
        # Future: Add check for User.ROLE_FACULTY and if they are instructor for this course
        flash('You do not have permission to manage enrollments for this course.', 'danger')
        return redirect(url_for('view_course', course_id=course.id))

    add_student_form = AddStudentEnrollmentForm()
    # change_status_form is not directly submitted as a whole, but its fields might be used
    # if we render one per student. For now, we'll handle actions based on request.form.
    change_status_form = ChangeEnrollmentStatusForm() # Instantiate for CSRF token if needed per student row

    if request.method == 'POST':
        action = request.form.get('action')

        if add_student_form.submit_add_student.data and add_student_form.validate_on_submit():
            username_or_email = add_student_form.student_username.data
            status = add_student_form.status.data
            
            student_to_enroll = User.query.filter(
                (User.username == username_or_email) | (User.email == username_or_email)
            ).first()

            if student_to_enroll:
                enrollment = CourseEnrollment.query.filter_by(
                    user_id=student_to_enroll.id, course_id=course.id
                ).first()

                if status == 'enrolled':
                    enrolled_count = CourseEnrollment.query.filter_by(course_id=course.id, status='enrolled').count()
                    # If updating an existing non-'enrolled' record to 'enrolled', or adding new as 'enrolled'
                    is_newly_enrolling = (enrollment is None) or (enrollment and enrollment.status != 'enrolled')
                    
                    if course.capacity is not None and enrolled_count >= course.capacity and is_newly_enrolling:
                        flash(f'Cannot enroll {student_to_enroll.username}. Course is full (capacity: {course.capacity}).', 'warning')
                        return redirect(url_for('manage_course_enrollments', course_id=course.id))

                if enrollment:
                    enrollment.status = status
                    enrollment.enrollment_date = datetime.utcnow() # Update date on any status change
                    flash(f'{student_to_enroll.username}\'s enrollment status updated to {status}.', 'success')
                else:
                    new_enrollment = CourseEnrollment(
                        user_id=student_to_enroll.id, 
                        course_id=course.id, 
                        status=status
                    )
                    db.session.add(new_enrollment)
                    flash(f'{student_to_enroll.username} has been {status} in the course.', 'success')
                db.session.commit()
            else:
                # This case should ideally be caught by form.validate_student_username
                flash(f'Student with username/email "{username_or_email}" not found.', 'danger')
            return redirect(url_for('manage_course_enrollments', course_id=course.id))

        elif action == 'change_status':
            student_id_to_change = request.form.get('student_id')
            new_status = request.form.get('new_status') # This should come from the specific student's status select field

            if not student_id_to_change or not new_status:
                flash('Missing student ID or new status for change.', 'danger')
                return redirect(url_for('manage_course_enrollments', course_id=course.id))

            enrollment_to_update = CourseEnrollment.query.filter_by(
                user_id=int(student_id_to_change), course_id=course.id
            ).first_or_404()
            
            if new_status == 'enrolled' and enrollment_to_update.status != 'enrolled':
                enrolled_count = CourseEnrollment.query.filter_by(course_id=course.id, status='enrolled').count()
                if course.capacity is not None and enrolled_count >= course.capacity:
                    flash(f'Cannot change status to "enrolled" for {enrollment_to_update.student.username}. Course is full.', 'warning')
                    return redirect(url_for('manage_course_enrollments', course_id=course.id))
            
            enrollment_to_update.status = new_status
            enrollment_to_update.enrollment_date = datetime.utcnow() # Update timestamp
            db.session.commit()
            flash(f'{enrollment_to_update.student.username}\'s status changed to {new_status}.', 'success')
            return redirect(url_for('manage_course_enrollments', course_id=course.id))

        elif action == 'remove_enrollment':
            student_id_to_remove = request.form.get('student_id')
            if not student_id_to_remove:
                flash('Missing student ID for removal.', 'danger')
                return redirect(url_for('manage_course_enrollments', course_id=course.id))

            enrollment_to_remove = CourseEnrollment.query.filter_by(
                user_id=int(student_id_to_remove), course_id=course.id
            ).first_or_404()
            
            student_username = enrollment_to_remove.student.username # Get username before deleting
            db.session.delete(enrollment_to_remove)
            db.session.commit()
            flash(f'{student_username}\'s enrollment record has been removed from the course.', 'success')
            return redirect(url_for('manage_course_enrollments', course_id=course.id))
        
        else: # POST but not a recognized action, or add_student_form validation failed
            if add_student_form.errors:
                 # Errors will be displayed by the template next to the fields
                flash('Error in adding student. Please check the form.', 'danger')
            else:
                flash('Invalid action or form submission.', 'danger')


    # GET request or after a POST that didn't redirect (e.g. add_student_form validation error)
    enrollments = db.session.query(CourseEnrollment, User.username, User.email).\
        join(User, CourseEnrollment.user_id == User.id).\
        filter(CourseEnrollment.course_id == course.id).\
        order_by(User.username.asc()).all()
    
    # Map to a list of dicts or custom objects if needed by template, or pass query result directly
    # For the template, we need to pass enrollment objects along with student info.
    # The query above already joins User, so student info is accessible via enrollment.student
    
    # Re-fetch just enrollments if needed, or process the joined query result
    enrollment_objects = [enrollment_obj for enrollment_obj, username, email in enrollments]


    return render_template('manage_enrollments.html', 
                           title=f'Manage Enrollments for {course.name}',
                           course=course, 
                           enrollments=enrollment_objects, # Pass the list of CourseEnrollment objects
                           add_student_form=add_student_form,
                           change_status_form=change_status_form) # Pass for CSRF if used per row

@app.route('/course/<int:course_id>/unenroll', methods=['POST'])
@login_required
def unenroll_from_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    enrollment = CourseEnrollment.query.filter_by(user_id=current_user.id, course_id=course.id, status='enrolled').first()
    
    if enrollment:
        enrollment.status = 'dropped' # Soft delete
        # enrollment.enrollment_date = datetime.utcnow() # Optionally update timestamp on status change
        db.session.commit()
        flash('You have successfully unenrolled from the course.', 'success')
    else:
        flash('You are not currently enrolled in this course, or your enrollment is not active.', 'info')
        
    return redirect(url_for('view_course', course_id=course.id))
