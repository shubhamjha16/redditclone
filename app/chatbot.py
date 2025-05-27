import google.generativeai as genai
from flask import Blueprint, request, jsonify, current_app, render_template
from app.models import College, Course, Event # Import models

chatbot_bp = Blueprint('chatbot', __name__)

def get_gemini_response(user_query: str, context_data: str = None) -> str:
    try:
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            current_app.logger.error("GEMINI_API_KEY not found in config.")
            return "Error: Chatbot API key not configured."

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')

        if context_data and context_data.strip(): # Ensure context_data is not empty
            prompt = f"""Here is some information that might be relevant to the user's query:
{context_data}

User query: {user_query}
Please answer the user's query based on the information provided above if relevant, or use your general knowledge.
"""
        else:
            prompt = f"User query: {user_query}"
        
        current_app.logger.debug(f"Gemini Prompt: {prompt}") # Log the prompt
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        current_app.logger.error(f"Error in Gemini API call: {e}")
        return "Error: Could not get response from chatbot."

@chatbot_bp.route('/chat', methods=['POST'])
def chat_api():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "No message provided"}), 400

    user_message = data['message'].lower() # Convert to lowercase for easier keyword matching
    context_data_parts = []

    # Rudimentary keyword detection and data fetching
    # College detection
    if "college" in user_message or "colleges" in user_message:
        # Try to extract a name (very basic)
        # This is a placeholder for more advanced NER or entity extraction.
        # For now, we'll just fetch a few colleges as an example if no specific name is easily found.
        colleges = College.query.limit(3).all() # Fetch first 3 colleges as an example
        if colleges:
            college_names = [c.name for c in colleges]
            context_data_parts.append(f"Found colleges: {', '.join(college_names)}.")
        else:
            context_data_parts.append("No college information found in the database.")

    # Course detection
    if "course" in user_message or "courses" in user_message:
        # This is highly simplified. Ideally, we'd link courses to colleges mentioned.
        # For now, just fetch a few courses as an example.
        courses = Course.query.limit(3).all() # Fetch first 3 courses
        if courses:
            course_info = [f"{c.name} (College ID: {c.college_id})" for c in courses] # Assuming courses have college_id
            context_data_parts.append(f"Found courses: {'; '.join(course_info)}.")
        else:
            context_data_parts.append("No course information found in the database.")

    # Event detection
    if "event" in user_message or "events" in user_message:
        # Similar simplification for events.
        events = Event.query.limit(3).all() # Fetch first 3 events
        if events:
            event_info = [f"{e.name} on {e.date.strftime('%Y-%m-%d')} (College ID: {e.college_id})" for e in events] # Assuming events have college_id and date
            context_data_parts.append(f"Upcoming events: {'; '.join(event_info)}.")
        else:
            context_data_parts.append("No event information found in the database.")
    
    context_data_str = "\n".join(context_data_parts) if context_data_parts else ""
    
    bot_response = get_gemini_response(data['message'], context_data_str) # Pass original user message
    
    return jsonify({"response": bot_response})

@chatbot_bp.route('/chatbot_ui')
def chatbot_ui():
    return render_template('chatbot.html')
