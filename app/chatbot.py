import google.generativeai as genai
from flask import Blueprint, request, jsonify, current_app, render_template
from app.models import College, Course, Event # Import models

chatbot_bp = Blueprint('chatbot', __name__)

def get_gemini_response(user_query: str, context_data: str = None) -> str:
    try:
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            current_app.logger.error('GEMINI_API_KEY not found.')
            return "Chatbot is not configured. Missing API key."

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')

        full_prompt = user_query
        if context_data and context_data.strip(): # ensure context_data is not just whitespace
            # The prompt structure can be important.
            # Using the structure from a previous successful implementation.
            full_prompt = f"""Here is some information that might be relevant to the user's query:
{context_data}

User query: {user_query}
Please answer the user's query based on the information provided above if relevant, or use your general knowledge.
"""
        
        current_app.logger.debug(f"Gemini Prompt: {full_prompt}")
        response = model.generate_content(full_prompt)
        return response.text
        
    except Exception as e:
        current_app.logger.error(f"Gemini API call failed: {e}")
        return "Sorry, I encountered an error trying to respond. Please try again later."

@chatbot_bp.route('/chat', methods=['POST'])
def chat_api():
    # Using request.get_json() is generally preferred as it handles content type checking.
    data = request.get_json() 
    if not data or 'message' not in data: # Check if data is None or 'message' key is missing
        return jsonify({"error": "No message provided"}), 400

    user_message = data['message'] # If data is not None and 'message' is present
    
    # Step 2.b: Convert user_message to lowercase for keyword matching
    lower_query = user_message.lower()
    
    # Step 2.c: Initialize context_data_parts
    context_data_parts = []

    # Step 2.d: College Data
    if "college" in lower_query:
        colleges = College.query.limit(3).all()
        if colleges:
            college_info = ", ".join([c.name for c in colleges])
            context_data_parts.append(f"Some colleges in the system: {college_info}.")

    # Step 2.e: Course Data
    if "course" in lower_query:
        courses = Course.query.limit(3).all()
        if courses:
            # Assuming c.college.name is accessible if courses have a loaded 'college' relationship.
            # For simplicity, sticking to c.name as per direct instruction.
            # A more robust version might try:
            # course_info_parts = []
            # for c in courses:
            #   info = c.name
            #   try: # Attempt to get college name if relationship exists and is loaded
            #       if c.college: info += f" (at {c.college.name})"
            #   except Exception: pass # Ignore if college info isn't easily accessible
            #   course_info_parts.append(info)
            # course_info = ", ".join(course_info_parts)
            course_info = ", ".join([c.name for c in courses])
            context_data_parts.append(f"Some available courses: {course_info}.")

    # Step 2.f: Event Data
    if "event" in lower_query:
        # Assuming Event model has 'date_time' attribute for ordering
        # If it's just 'date', then Event.date.desc()
        # Let's assume 'date_time' exists as per instruction.
        # If Event.date_time is not available, this would cause an error.
        # A safer default would be to not order or order by ID if date_time is uncertain.
        # For now, following instruction.
        try:
            events = Event.query.order_by(Event.date_time.desc()).limit(3).all()
            if events:
                event_info = ", ".join([e.name for e in events])
                context_data_parts.append(f"Some recent or upcoming events: {event_info}.")
        except AttributeError: # Fallback if Event.date_time doesn't exist
            current_app.logger.warning("Event.date_time attribute not found for ordering, fetching without specific order.")
            events = Event.query.limit(3).all()
            if events:
                event_info = ", ".join([e.name for e in events])
                context_data_parts.append(f"Some events: {event_info}.")


    # Step 2.g: Join context parts
    context_data_str = " ".join(context_data_parts) if context_data_parts else None
    
    # Step 2.h: Call get_gemini_response with user message and context
    response_text = get_gemini_response(user_message, context_data=context_data_str) 
    
    return jsonify({'response': response_text})

@chatbot_bp.route('/chatbot_ui', methods=['GET'])
def chatbot_ui():
    return render_template('chatbot.html')
