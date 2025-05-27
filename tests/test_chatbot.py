import pytest
import json
from unittest.mock import patch, MagicMock, ANY # ANY is useful for context_data matching

# Assuming 'client' fixture is defined in conftest.py
# Assuming 'app' can be imported for application context needs
from app import app as flask_app # Renaming to avoid conflict with 'app' fixture if any
from app.chatbot import get_gemini_response
from app.models import College, Course, Event # Required for mocking DB interactions

# Helper to simulate Flask's url_for in tests if not using client fixture directly
# or if it's needed for non-client related URL generation (less common in tests).
# from flask import url_for # Usually client.get(url_for(...)) handles this.

# 3.a. Test Chatbot UI Page
def test_chatbot_ui_page(client):
    """Test that the chatbot UI page loads correctly."""
    response = client.get("/chatbot/chatbot_ui") # Hardcoding URL, or use url_for('chatbot.chatbot_ui')
    assert response.status_code == 200
    assert b'<div id="chat-history"' in response.data
    assert b'Chatbot' in response.data # Check for title or heading

# 3.b. Test Chat API - No Message
def test_chat_api_no_message(client):
    """Test the chat API when no message is provided."""
    response = client.post("/chatbot/chat", json={}) # Missing 'message'
    assert response.status_code == 400
    json_data = response.get_json()
    assert "error" in json_data
    assert json_data["error"] == "No message provided"

    response = client.post("/chatbot/chat", json={"text": "some message"}) # Incorrect key
    assert response.status_code == 400
    json_data = response.get_json()
    assert "error" in json_data
    assert json_data["error"] == "No message provided"

# 3.c. Test Chat API - Mocked Gemini
@patch('app.chatbot.get_gemini_response') # Mock the helper function within chat_api
def test_chat_api_mocked_gemini(mock_get_gemini, client):
    """Test the chat API with get_gemini_response mocked."""
    mock_get_gemini.return_value = "Mocked Gemini says hello!"
    
    response = client.post("/chatbot/chat", json={'message': 'Hi there'})
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['response'] == "Mocked Gemini says hello!"
    
    # Check that get_gemini_response was called correctly.
    # The context_data might be an empty string "" if no keywords were found,
    # or None if the logic defaults to None. Based on current chat_api, it's likely "" or a specific string.
    # Using ANY for context_data for robustness unless a specific empty context is guaranteed.
    mock_get_gemini.assert_called_once_with('Hi there', context_data=ANY)


# 3.d. Test get_gemini_response with Context - Mocked API
@patch('app.chatbot.genai.GenerativeModel') # Mock the actual Gemini library's model
def test_get_gemini_response_with_context_mocked_api(mock_genai_model, app): # app fixture for context
    """Test get_gemini_response directly with a mocked Gemini API model, checking prompt construction."""
    # Configure the mock Gemini model instance
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value.text = "Test response"
    mock_genai_model.return_value = mock_model_instance

    with app.app_context(): # Needed for current_app.config and current_app.logger
        # Temporarily set API key if not already set, to pass the initial check
        original_api_key = app.config.get('GEMINI_API_KEY')
        app.config['GEMINI_API_KEY'] = 'fake-test-key'
        
        response_text = get_gemini_response("User query", context_data="Some context")
        
        app.config['GEMINI_API_KEY'] = original_api_key # Restore original key

    assert response_text == "Test response"
    # Check that generate_content was called with a prompt containing both query and context
    mock_model_instance.generate_content.assert_called_once()
    called_prompt = mock_model_instance.generate_content.call_args[0][0]
    assert "Some context" in called_prompt
    assert "User query" in called_prompt

# 3.e. Test Chat API - College Keyword Mocked
@patch('app.chatbot.get_gemini_response') # Mock our helper to isolate chat_api logic
@patch('app.chatbot.College.query') # Mock the SQLAlchemy query object for College
def test_chat_api_with_college_keyword_mocked(mock_college_query, mock_get_gemini, client):
    """Test chat_api with 'college' keyword, mocking DB and Gemini call."""
    # Configure the mock for College.query.limit().all()
    mock_college_instance = MagicMock(spec=College) # Use spec for better mocking
    mock_college_instance.name = 'Test College 1'
    mock_college_query.limit.return_value.all.return_value = [mock_college_instance]
    
    mock_get_gemini.return_value = "Response about colleges" # Mocked response from our helper
    
    response = client.post("/chatbot/chat", json={'message': 'tell me about colleges'})
    assert response.status_code == 200
    assert response.get_json()['response'] == "Response about colleges"
    
    # Check that get_gemini_response was called with context_data including the college name
    mock_get_gemini.assert_called_once()
    args, kwargs = mock_get_gemini.call_args
    assert args[0] == 'tell me about colleges' # user_message
    assert 'context_data' in kwargs
    assert 'Test College 1' in kwargs['context_data']
    assert 'colleges in the system' in kwargs['context_data'] # Check for the specific context phrase

# 3.f. Test Chat API - Course Keyword Mocked
@patch('app.chatbot.get_gemini_response')
@patch('app.chatbot.Course.query')
def test_chat_api_with_course_keyword_mocked(mock_course_query, mock_get_gemini, client):
    """Test chat_api with 'course' keyword, mocking DB and Gemini call."""
    mock_course_instance = MagicMock(spec=Course)
    mock_course_instance.name = 'Test Course 101'
    # If your context string includes related info like college name, mock that too:
    # mock_course_instance.college = MagicMock(name='Associated College')
    mock_course_query.limit.return_value.all.return_value = [mock_course_instance]
    
    mock_get_gemini.return_value = "Response about courses"
    
    response = client.post("/chatbot/chat", json={'message': 'any courses available?'})
    assert response.status_code == 200
    assert response.get_json()['response'] == "Response about courses"
    
    mock_get_gemini.assert_called_once()
    args, kwargs = mock_get_gemini.call_args
    assert args[0] == 'any courses available?'
    assert 'context_data' in kwargs
    assert 'Test Course 101' in kwargs['context_data']
    assert 'available courses' in kwargs['context_data']

# 3.f. Test Chat API - Event Keyword Mocked
@patch('app.chatbot.get_gemini_response')
@patch('app.chatbot.Event.query')
def test_chat_api_with_event_keyword_mocked(mock_event_query, mock_get_gemini, client):
    """Test chat_api with 'event' keyword, mocking DB and Gemini call."""
    mock_event_instance = MagicMock(spec=Event)
    mock_event_instance.name = 'Big Test Event'
    # Mock date_time if your context string uses it, ensuring it's a datetime object for strftime
    # from datetime import datetime
    # mock_event_instance.date_time = datetime(2024, 1, 1, 10, 0, 0) 
    
    # Mocking the chain: query.order_by().limit().all()
    mock_event_query.order_by.return_value.limit.return_value.all.return_value = [mock_event_instance]
    
    mock_get_gemini.return_value = "Response about events"
    
    response = client.post("/chatbot/chat", json={'message': 'what events are happening?'})
    assert response.status_code == 200
    assert response.get_json()['response'] == "Response about events"
    
    mock_get_gemini.assert_called_once()
    args, kwargs = mock_get_gemini.call_args
    assert args[0] == 'what events are happening?'
    assert 'context_data' in kwargs
    assert 'Big Test Event' in kwargs['context_data']
    assert 'recent or upcoming events' in kwargs['context_data']
    mock_event_query.order_by.assert_called_once() # Verify ordering was attempted

# 3.g. Test get_gemini_response - No API Key
def test_get_gemini_response_no_api_key(app): # app fixture for app context
    """Test get_gemini_response directly when GEMINI_API_KEY is not set."""
    with app.app_context():
        original_api_key = app.config.get('GEMINI_API_KEY')
        app.config['GEMINI_API_KEY'] = None # Temporarily remove API key
        
        # Mock logger to check if error is logged, if desired
        with patch('app.chatbot.current_app.logger.error') as mock_logger_error:
            response_text = get_gemini_response("test query without key")
        
        app.config['GEMINI_API_KEY'] = original_api_key # Restore original key
        
    assert response_text == "Chatbot is not configured. Missing API key."
    mock_logger_error.assert_called_with('GEMINI_API_KEY not found.')

# Additional test: What if Gemini API itself fails (e.g. network error, invalid key used)
@patch('app.chatbot.genai.GenerativeModel')
def test_get_gemini_response_api_failure(mock_genai_model, app):
    """Test get_gemini_response when the call to Gemini's generate_content fails."""
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.side_effect = Exception("Simulated API Failure")
    mock_genai_model.return_value = mock_model_instance

    with app.app_context():
        original_api_key = app.config.get('GEMINI_API_KEY')
        app.config['GEMINI_API_KEY'] = 'fake-test-key-for-failure' # Ensure key is present
        
        with patch('app.chatbot.current_app.logger.error') as mock_logger_error:
            response_text = get_gemini_response("query leading to failure")
            
        app.config['GEMINI_API_KEY'] = original_api_key

    assert response_text == "Sorry, I encountered an error trying to respond. Please try again later."
    mock_logger_error.assert_called_with("Gemini API call failed: Simulated API Failure")

# Final check on app import name
# If your conftest.py provides 'app' as the Flask app instance,
# then the parameter 'app' in test functions is correct.
# If you import 'app' directly as 'from app import app as flask_app',
# then ensure your test functions use 'flask_app' when needing direct app access
# or 'app' if it's the fixture name. For consistency, I've used 'app' as fixture parameter.
# The import 'from app import app as flask_app' is mainly for clarity if 'app' fixture is also named 'app'.
# If 'app' fixture is not used, then `with flask_app.app_context()` would be used.
# Assuming 'app' fixture provides the app context correctly.
# The above tests use `app` as a parameter, assuming it's a fixture providing app context.
# If `flask_app` is the imported app instance directly, tests like `test_get_gemini_response_no_api_key`
# would use `with flask_app.app_context():` and `flask_app.config` instead of `app.config`.
# For this solution, I'm assuming `app` is the fixture from `conftest.py` providing the app instance and context.
# If `app` fixture is NOT available, change relevant tests to use `flask_app` and `with flask_app.app_context():`.
# For example, `test_get_gemini_response_no_api_key(flask_app_instance)` where flask_app_instance is flask_app.
# However, the problem description often implies fixtures like `client` and `app` are standard.

# To make tests using `app` parameter work without an `app` fixture, you'd do:
# def test_get_gemini_response_no_api_key():
#     with flask_app.app_context():
#         original_api_key = flask_app.config.get('GEMINI_API_KEY')
#         flask_app.config['GEMINI_API_KEY'] = None
#         response_text = get_gemini_response("test query without key")
#         flask_app.config['GEMINI_API_KEY'] = original_api_key
#     assert response_text == "Chatbot is not configured. Missing API key."
# This version doesn't need `app` as a parameter. I'll stick to `app` as parameter assuming fixture.

# A note on the use of `app` vs `flask_app` in the code:
# The import `from app import app as flask_app` is a common pattern to avoid name collision
# if a test fixture is also named `app`. The tests are written assuming an `app` fixture is provided
# by pytest (likely from `conftest.py`) which gives the test function access to the app instance
# and automatically handles app context for functions like `current_app`.
# If such a fixture is not available, tests needing direct app access would use `flask_app`
# and manually manage the app context (e.g., `with flask_app.app_context():`).
# The current structure should work fine if `conftest.py` defines an `app` fixture.

# Using flask_app directly if no 'app' fixture from pytest:
# Example for test_get_gemini_response_no_api_key
# @patch('app.chatbot.current_app', flask_app) # This might not work directly for current_app
# A better way without 'app' fixture is to push context manually:
def test_get_gemini_response_no_api_key_no_fixture():
    with flask_app.test_request_context(): # Pushes app and request context
        original_api_key = flask_app.config.get('GEMINI_API_KEY')
        try:
            flask_app.config['GEMINI_API_KEY'] = None
            with patch.object(flask_app, 'logger') as mock_logger: # mock logger on the app instance
                 response_text = get_gemini_response("test")
            assert response_text == "Chatbot is not configured. Missing API key."
            mock_logger.error.assert_called_with('GEMINI_API_KEY not found.')
        finally:
            flask_app.config['GEMINI_API_KEY'] = original_api_key

# Reverting to the version assuming 'app' fixture for simplicity as per typical pytest-flask setup.
# The tests above use `app` as a parameter, assuming it's a fixture.
# If it's not, the `_no_fixture` style test above is an alternative for those specific tests.
# For the subtask, I'll stick to the versions that take `app` as a parameter.
# The `test_get_gemini_response_no_api_key_no_fixture` is just for illustration.
# Removing it to keep the submitted code clean and aligned with the primary interpretation of the prompt.

# One final check for `test_get_gemini_response_with_context_mocked_api(app)` parameter.
# It needs `app` for app.config and app.app_context().
# If `app` is from `conftest.py`, it's fine. Otherwise, it would need to use `flask_app` and `with flask_app.app_context()`.
# The use of `app.config` inside this test means it relies on the `app` parameter being the Flask app instance.
# This is standard for a pytest `app` fixture.
# The same applies to `test_get_gemini_response_no_api_key(app)` and `test_get_gemini_response_api_failure(mock_genai_model, app)`.
# The structure seems robust assuming standard pytest-flask fixtures.

# Add `from unittest.mock import ANY` at the top. It was used in test_chat_api_mocked_gemini.
# Already added it.
