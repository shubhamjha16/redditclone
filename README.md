# College Community Platform & Integrated Management Systems

## 1. Overview

This project is a Flask-based web application designed as a multi-faceted platform for college communities. It began as a Reddit-style community system and has been progressively extended to include an Enterprise Resource Planning (ERP) suite, Hackathon Management, RFID & Security Systems, an Online Library, a College Audit System, a Parent Email System, an Appointment System, and a Direct Messaging feature. The goal is to provide a centralized, comprehensive digital environment for students, faculty, staff, and administration.

## 2. Project Structure

The project follows a standard Flask application layout:

*   **`main.py`**: The main entry point to run the Flask application.
*   **`config.py`**: Contains configuration classes for the application (e.g., database URI, secret key for different environments like production and testing).
*   **`app/`**: The main application package.
    *   **`__init__.py`**: Initializes the Flask app, database (SQLAlchemy), login manager, and other extensions. Also contains context processors.
    *   **`models.py`**: Defines all SQLAlchemy database models for the application. This is the primary source of truth for the application's data structure, covering all integrated systems.
    *   **`routes.py`**: Contains all the URL routing logic and view functions that handle requests and interact with models and templates.
    *   **`forms.py`**: Defines forms used throughout the application using Flask-WTF and WTForms.
    *   **`utils.py`**: Utility functions used across the application.
*   **`models/` (JavaScript/Mongoose)**: Contains JavaScript-based Mongoose models (e.g., `College.js`, `Course.js`, `User.js`). These appear to be for a separate Node.js backend or API, distinct from the main Flask application's SQLAlchemy models.
*   **`routes/` (JavaScript)**: Contains JavaScript-based route handlers (e.g., `college.js`), likely associated with the Mongoose models and a Node.js backend.
*   **`static/`**: Stores static files like CSS, JavaScript (for frontend), and images.
    *   `css/style.css`: Custom stylesheets for the application.
*   **`templates/`**: Contains Jinja2 HTML templates used to render pages.
    *   `admin/`: Templates specific to admin functionalities.
    *   Includes templates for various features like posts, courses, events, user profiles, authentication, etc.
*   **`tests/`**: Contains unit and integration tests for the application.
    *   `test_auth.py`, `test_models.py`, `test_routes.py`, etc.
*   **`requirements.txt`**: Lists Python package dependencies for the Flask application.
*   **`vercel.json`**: Configuration file for deploying the Python Flask backend to Vercel.
*   **`app.js`**: Root JavaScript file, potentially for the Node.js backend if used.

## 3. Core Features & Modules

The platform integrates a wide array of functionalities:

### 3.1. College Community Platform (Core)
*   User registration and authentication (students, faculty, alumni, management, admin) with college affiliation.
*   Role-based access control.
*   Reddit-style content platform: Post creation, viewing, voting, and commenting.
*   College-specific spaces (sub-communities).
*   Enhanced User Profiles with bios, profile pictures, and activity tracking.
*   Follower/Following system.
*   Content reporting and admin moderation.
*   User notification system.
*   Reels Section (Instagram-like short video sharing).

### 3.2. Enterprise Resource Planning (ERP) Features
*   **Gradebook Management**: Record and manage student grades for assignments and courses. (Models: `Gradebook`, `Assignment`, `Submission`)
*   **Fee Tracking Integration**: Define fee structures and track student payments. (Models: `FeeStructure`, `StudentFee`)
*   **Timetable Scheduling**: Define and view course schedules. (Model: `TimeSlot`)
*   **Resource Allocation**: Manage and book college resources (e.g., rooms, equipment). (Models: `ResourceType`, `Resource`, `ResourceBooking`)

### 3.3. Hackathon Management System
*   College-specific Hackathon event listings and management.
*   Team registration and solo participation.
*   Project submission system (GitHub, links, demos).
*   Judging dashboard, scoring, and ranking.
*   Automated result publishing and certificate generation.
(Key Models: `Hackathon`, `HackathonTeam`, `HackathonParticipant`, `HackathonProject`, `HackathonJudge`, `HackathonJudgingCriteria`, `HackathonScore`, `HackathonResult`, `Certificate`)

### 3.4. RFID and Security Management System (Phase 5)
*   **RFID Card Management**: Manages RFID cards for identity and access. (Model: `RFIDCard`)
*   **Access Control**: Defines RFID-enabled access points and logs all access attempts. (Models: `AccessPoint`, `AccessLog`)
*   **Security Patrol Logging**: Digital logbook for security personnel activities. (Model: `SecurityPatrolLog`)
*   **Security Camera Catalog**: Catalogs security cameras. (Model: `SecurityCamera`)
*   **Incident Reporting**: Logs security incidents. (Model: `SecurityIncident`)

### 3.5. Online Library System (Phase 6)
*   **Book Catalog & Categorization**: Manages library book inventory, including e-books. (Models: `Book`, `BookCategory`, `EBook`)
*   **Loan Management**: Tracks book lending, due dates, and returns. (Model: `LibraryLoan`)
*   **Fine Management**: Handles fines for overdue or damaged books. (Model: `Fine`)
*   **Book Reservations**: Allows users to reserve unavailable books. (Model: `BookReservation`)

### 3.6. College Audit System (Financials - Phase 7)
*   **Financial Account Management**: Manages the college's chart of accounts. (Model: `FinancialAccount`)
*   **Transaction Ledger**: Records all financial transactions. (Model: `TransactionLedger`)
*   **Budgeting**: Defines and tracks budgets for accounts/departments. (Model: `Budget`)
*   **Audit Trails**: Logs significant financial system actions. (Model: `AuditLog`)

### 3.7. Email System for Parents (Phase 8)
*   **Parent/Guardian Contact Management**: Manages parent/guardian contact details. (Model: `ParentGuardian`)
*   **Announcement System**: Facilitates creating announcements, with potential AI integration for content. (Model: `Announcement`)
*   **Targeted Communication**: Defines recipient groups for announcements. (Model: `AnnouncementRecipientGroup`)
*   **Email Dispatch Logging**: Tracks sent emails and their status. (Model: `SentEmailLog`)

### 3.8. Appointment System (Teachers & Management - Phase 9)
*   **Availability Management**: Staff can define their available appointment slots. (Model: `AppointmentSlot`)
*   **Online Booking**: Users can book available appointments.
*   **Automated Email Notifications**: System supports automated emails for bookings. (Model: `AppointmentBooking`)

### 3.9. Direct Messaging (DM) System (Phase 10)
*   **Private Conversations**: Users can engage in one-on-one or group direct messages. (Model: `Conversation`)
*   **Message Storage**: Stores individual messages within conversations. (Model: `Message`)
*   **Participants & Read Status**: Manages conversation participants and tracks message read status. (Table: `conversation_participant`)

### 3.10. General Features
*   Search functionality (posts, courses, colleges).
*   Mobile-responsive design.
*   Comprehensive test suite (Pytest).

### 3.11. Phase 11: Gemini Powered Chatbot
*   **Conversational AI**: Integrates Google's Gemini Pro model to provide a general-purpose chatbot.
*   **Contextual Answers**: The chatbot can access and utilize data from the application (Colleges, Courses, Events) to provide more relevant answers to user queries.
*   **User Interface**: Accessible via a "Chatbot" link in the navigation bar for logged-in users (at `/chatbot/chatbot_ui`).
*   **Functionality**: Users can ask questions in natural language and receive responses generated by the Gemini API based on both its general knowledge and the contextual data provided from the platform.

## 4. SQLAlchemy Database Models Overview (`app/models.py`)

This application uses SQLAlchemy for database interactions. Below is a list of the primary models defined. For detailed fields and relationships, please refer to the `app/models.py` file.

*   **Core Community & User Management:**
    *   `User`: Central model for all users (students, faculty, admin, etc.), roles, profiles.
    *   `College`: Information about colleges.
    *   `Post`: User-generated content (like forum posts).
    *   `Comment`: Comments on posts.
    *   `Vote`: Upvotes/downvotes for posts and comments.
    *   `StudyGroup`: User-created study groups.
    *   `Event`: College events.
    *   `Report`: For reporting content.
    *   `Notification`: User notifications.
    *   `Reel`, `ReelComment`, `ReelLike`: Short video feature.
*   **Academic & ERP Modules:**
    *   `Course`: Course details, offerings.
    *   `AttendanceRecord`: Student attendance.
    *   `CourseEnrollment`: Student enrollment in courses.
    *   `Gradebook`: Detailed grade items for enrollments.
    *   `Assignment`: Course assignments.
    *   `Submission`: Student submissions for assignments.
    *   `FeeStructure`: Definition of fees.
    *   `StudentFee`: Fees owed by students.
    *   `TimeSlot`: Course scheduling.
    *   `ResourceType`, `Resource`, `ResourceBooking`: Resource management.
*   **Hackathon Management:**
    *   `Hackathon`: Hackathon event details.
    *   `HackathonTeam`: Teams in hackathons.
    *   `HackathonParticipant`: Linking users to teams/hackathons.
    *   `HackathonProject`: Submitted projects.
    *   `HackathonJudge`, `HackathonJudgingCriteria`, `HackathonScore`: Judging process.
    *   `HackathonResult`: Final results.
    *   `Certificate`: Certificates for hackathons.
*   **RFID and Security Management:**
    *   `RFIDCard`: RFID card details.
    *   `AccessPoint`: RFID reader locations.
    *   `AccessLog`: Logs of RFID access attempts.
    *   `SecurityCamera`: Details of security cameras.
    *   `SecurityIncident`: Logs for security incidents.
    *   `SecurityPatrolLog`: Security guard activity logs.
*   **Online Library System:**
    *   `BookCategory`: Categories for books.
    *   `Book`: Library book details.
    *   `EBook`: E-book specific details.
    *   `LibraryLoan`: Tracking book loans.
    *   `Fine`: Fines for library items.
    *   `BookReservation`: Reservations for unavailable books.
*   **College Audit System (Financials):**
    *   `FinancialAccount`: Chart of accounts.
    *   `TransactionLedger`: Financial transactions.
    *   `Budget`: Budget definitions.
    *   `AuditLog`: Audit trails for financial actions.
*   **Email System for Parents:**
    *   `ParentGuardian`: Parent/guardian contact information.
    *   `Announcement`: Announcements to be sent.
    *   `AnnouncementRecipientGroup`: Groups for targeted announcements.
    *   `SentEmailLog`: Logs of dispatched emails.
*   **Appointment System:**
    *   `AppointmentSlot`: Staff availability for appointments.
    *   `AppointmentBooking`: Booked appointments.
*   **Direct Messaging System:**
    *   `Conversation`: Represents a chat session.
    *   `Message`: Individual messages within conversations.
    *   `conversation_participant` (Association Table): Links users to conversations.

## 5. Setup and Installation (Flask Application)

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure the application:**
    *   Set environment variables or update `config.py` directly (not recommended for production secrets).
    *   **`SECRET_KEY`**: A strong, unique secret key (critical for session security).
    *   **`DATABASE_URL`**: Connection string for your database (e.g., `postgresql://user:pass@host:port/dbname`). Defaults to SQLite for local development.
    *   **`GEMINI_API_KEY`**: API key for Google Gemini services, required for the chatbot functionality. Set this environment variable. (The application has a fallback default key for development, but it's recommended to use your own).
5.  **Initialize the database:**
    *   Ensure your database server (e.g., PostgreSQL) is running if not using SQLite.
    *   Open a Flask shell (`flask shell`) and run:
        ```python
        from app import db
        db.create_all()
        ```
    *   Alternatively, if Flask-Migrate is integrated:
        ```bash
        flask db init  # (if first time)
        flask db migrate -m "Initial migration of all models"
        flask db upgrade
        ```

## 6. Running the Flask Application Locally

```bash
flask run
```
Or, if using `main.py` directly (less common for development with auto-reload):
```bash
python main.py
```
The application will typically be available at `http://127.0.0.1:5000/`.

## 7. Running Tests

Tests are located in the `tests/` directory. To run them (assuming pytest):

```bash
pytest
```
To see test coverage:
```bash
pytest --cov=app
```

## 8. Deployment (Vercel Example)

*   This project is configured for deployment on Vercel via the `vercel.json` file for the Python backend.
*   **Database**: For production on Vercel, **a PostgreSQL database is critical**. The `DATABASE_URL` environment variable must be set in your Vercel project settings. SQLite is not suitable for Vercel's production environment.
*   **Environment Variables on Vercel**: Ensure `DATABASE_URL` and `SECRET_KEY` are set in your Vercel project settings. `FLASK_ENV=production` is also recommended and is set in `vercel.json`.
*   Deployment is typically done by connecting your Git repository to Vercel.

---
*This README provides a comprehensive overview. For specific details, always refer to the source code and individual module documentation.* 
```
