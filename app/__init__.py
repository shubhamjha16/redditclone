from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # The route to redirect to for login_required
login_manager.login_message_category = 'info'

# Import and register Blueprints
from app.chatbot import chatbot_bp
app.register_blueprint(chatbot_bp, url_prefix='/chatbot')


from app import routes, models # routes needs to be imported before context processor usually

# Context processors make functions available in all templates
@app.context_processor
def inject_utilities():
    from app.utils import (get_target_score, get_colleges_for_navbar, 
                           get_pending_reports_count, get_unread_notifications_count) # Added
    from app.models import Post, Comment, Course, StudyGroup, Event, ReportStatus
    from app.forms import SearchForm 
    return dict(
        get_target_score=get_target_score,
        get_colleges_for_navbar=get_colleges_for_navbar,
        get_pending_reports_count=get_pending_reports_count,
        get_unread_notifications_count=get_unread_notifications_count, # Added
        search_form=SearchForm(), 
        Post=Post,
        Comment=Comment,
        Course=Course,
        StudyGroup=StudyGroup,
        Event=Event,
        ReportStatus=ReportStatus
    )

# Import models after db initialization and potential context processors
# from app import models # already imported above
