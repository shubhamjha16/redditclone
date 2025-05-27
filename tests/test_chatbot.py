import pytest
import json
from unittest import mock # Corrected import for mock

# Assuming 'client' fixture is defined in conftest.py and 'app' is available
# from app import app # If you need direct app access for url_for outside of client context

def test_chatbot_ui_page(client):
    """Test the chatbot UI page loads correctly."""
    response = client.get("/chatbot/chatbot_ui") # Hardcoding for now, url_for might be better
    assert response.status_code == 200
    assert b"Chat with Our Bot" in response.data
    assert b"chat-history" in response.data # Check for an element ID

def test_chat_api_basic(client):
    """Test basic POST request to the chat API."""
    response = client.post("/chatbot/chat", json={"message": "Hello"})
    assert response.status_code == 200
    assert response.content_type == "application/json"
    json_data = response.get_json()
    assert "response" in json_data

@mock.patch('app.chatbot.get_gemini_response') # Path to the function to mock
def test_chat_api_mocked_gemini(mock_get_gemini_response, client):
    """Test the chat API with a mocked Gemini response."""
    mock_get_gemini_response.return_value = "Mocked Gemini Response"
    
    response = client.post("/chatbot/chat", json={"message": "Test message"})
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["response"] == "Mocked Gemini Response"
    mock_get_gemini_response.assert_called_once_with("Test message", mock.ANY) # ANY for context_data for now

@mock.patch('app.chatbot.get_gemini_response')
@mock.patch('app.chatbot.College') # Mock the College model
def test_chat_api_with_college_keyword_and_mocked_db(mock_College, mock_get_gemini_response, client, app):
    """
    Test chat API with a college-related keyword, ensuring context is attempted to be fetched
    and passed to the mocked Gemini response function.
    """
    # Configure the mock for College.query.limit().all()
    # This setup assumes College instances have a 'name' attribute.
    mock_college_instance = mock.Mock()
    mock_college_instance.name = "Test University"
    mock_College.query.limit.return_value.all.return_value = [mock_college_instance]
    
    # Set the return value for the mocked gemini response
    mock_get_gemini_response.return_value = "Mocked response about colleges"
    
    response = client.post("/chatbot/chat", json={"message": "tell me about colleges"})
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["response"] == "Mocked response about colleges"
    
    # Check that get_gemini_response was called with context_data containing college info
    # The first argument to get_gemini_response is the user_message ("tell me about colleges")
    # The second argument is the context_data string.
    # We expect "Found colleges: Test University." to be part of this context_data string.
    mock_get_gemini_response.assert_called_once()
    args, _ = mock_get_gemini_response.call_args
    assert args[0] == "tell me about colleges" # Original message
    assert "Found colleges: Test University." in args[1] # Context data
    
    # Verify that the database was queried (or at least the mock for it was)
    mock_College.query.limit.assert_called_once_with(3)
    mock_College.query.limit.return_value.all.assert_called_once()

# TODO: Add tests for Course and Event keywords similar to the college keyword test if time permits.
# TODO: Add test for case where GEMINI_API_KEY is not set (if possible to manipulate config in test)
# TODO: Add test for error from Gemini API (e.g. model.generate_content throws exception)
# TODO: Test for no message provided in chat API
def test_chat_api_no_message(client):
    """Test chat API when no message is provided in the payload."""
    response = client.post("/chatbot/chat", json={}) # Empty JSON
    assert response.status_code == 400
    assert response.content_type == "application/json"
    json_data = response.get_json()
    assert "error" in json_data
    assert json_data["error"] == "No message provided"

    response = client.post("/chatbot/chat", json={"msg": "Hello"}) # Incorrect key
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["error"] == "No message provided"

# Test for get_gemini_response internal error handling (e.g. API key missing)
@mock.patch('app.chatbot.genai.GenerativeModel') # Mock the model instantiation
@mock.patch('app.chatbot.current_app') # Mock current_app to control config
def test_get_gemini_response_no_api_key(mock_current_app, mock_GenerativeModel, app):
    """
    Test get_gemini_response when GEMINI_API_KEY is not configured.
    This test calls get_gemini_response directly, not through the client.
    """
    from app.chatbot import get_gemini_response # import locally for direct test
    
    # Configure mock_current_app to simulate missing API key
    mock_current_app.config = {} # No GEMINI_API_KEY
    mock_current_app.logger = app.logger # Use real logger or mock it too

    # Call the function directly
    with app.app_context(): # Need app context for current_app.logger
        response_text = get_gemini_response("test query")
    
    assert response_text == "Error: Chatbot API key not configured."
    mock_GenerativeModel.assert_not_called() # Model should not be initialized

@mock.patch('app.chatbot.genai.GenerativeModel')
@mock.patch('app.chatbot.current_app')
def test_get_gemini_response_api_error(mock_current_app, mock_GenerativeModel, app):
    """Test get_gemini_response when the Gemini API call itself fails."""
    from app.chatbot import get_gemini_response

    # Configure mock_current_app with API key
    mock_current_app.config = {'GEMINI_API_KEY': 'fake-key'}
    mock_current_app.logger = app.logger

    # Configure the mock model to raise an exception
    mock_model_instance = mock.Mock()
    mock_model_instance.generate_content.side_effect = Exception("Simulated API error")
    mock_GenerativeModel.return_value = mock_model_instance

    with app.app_context():
        response_text = get_gemini_response("test query")

    assert response_text == "Error: Could not get response from chatbot."
    mock_model_instance.generate_content.assert_called_once()
    # Check that an error was logged (optional, depends on logger mock setup)
    # mock_current_app.logger.error.assert_called()
