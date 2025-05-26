# College Community Platform

**Description:** A Reddit-style community platform designed for college communities, enabling students, faculty, and staff to connect, share information, and build communities around academic interests, courses, campus life, and events.

**Features:**
*   User registration and authentication (with college affiliation, student ID, year of college).
*   Role-based access control (User, Admin).
*   Reddit-style content platform:
    *   Post creation, viewing, voting, and commenting.
    *   College-specific spaces (sub-communities).
    *   Content display in a card-based, Reddit-like UI.
*   **Enhanced User Profiles & Follow System:**
    *   Customizable profile pictures and bios.
    *   User activity tracking (`last_seen`).
    *   Follower/Following system enabling users to connect.
*   College-Specific Features:
    *   Course discussions.
    *   Study group organization.
    *   Event creation and management.
    *   **Student Enrollment Management:**
        *   Courses can have defined capacities.
        *   Students can enroll in and unenroll from courses.
        *   Enrollment is subject to course capacity (waitlist functionality can be a future addition).
        *   Admins and Management can manage enrollments (add, drop, change student status in courses).
        *   User profiles display enrolled courses.
        *   Course listings show current enrollment counts vs. capacity.
        *   Attendance system now uses enrollment data for accurate rosters.
        *   Introduction of a 'Management' user role with permissions for enrollment management.
*   Administrative Tools:
    *   College management (create, edit).
    *   User management (verify affiliation, change roles).
    *   Content moderation (reporting system, review reported content).
*   **Attendance Management System:**
    *   Faculty/Admins can take attendance for courses, marking students as present, absent, late, or excused.
    *   Students can view their own attendance records.
    *   Admins/Faculty can view attendance reports for courses, with filtering options.
    *   Introduction of a 'Faculty' user role with specific permissions for taking attendance.
*   Search functionality (posts, courses, colleges).
*   User notification system (e.g., for new comments on posts).
*   **Reels Section (Instagram-like):**
    *   Users can post short video content (via URL) with captions.
    *   Viewable feed of reels with pagination.
    *   Ability to like and comment on reels.
    *   View count for reels.
*   Mobile-responsive design.
*   Comprehensive test suite (Pytest).

  **  Hackathon Management System (Integrated Module)**

This module extends the Reddit-style College Community Platform by enabling colleges to organize, manage, and host hackathons within their dedicated community spaces. It streamlines event creation, team registration, project submission, judging, and result publishing — all from within the same platform.

Features:

College-specific Hackathon Listings: Display upcoming, ongoing, and past hackathons.

User Registration: Solo or team-based signups using verified college profiles.

Project Submission System: Upload GitHub repos, design links, demos, and documentation.

Judging Dashboard: Score, review, and rank submissions with role-based access for judges.

Result & Certificate Generation: Auto-publish winners and generate participation/winner certificates.

Discussion & Collaboration: Built-in comments, Q&A, and team-finding threads.

Notification System: Alerts for deadlines, updates, and feedback.

**Technologies Used:**
*   Backend: Python, Flask, SQLAlchemy, Gunicorn
*   Frontend: HTML, CSS, Bootstrap (for basic structure and components)
*   Database: SQLite (for development), PostgreSQL (recommended for production)
*   Testing: Pytest, Pytest-Flask, Pytest-Cov

**Prerequisites for Local Setup:**
*   Python 3.8+
*   pip (Python package installer)
*   Virtual environment tool (e.g., `venv`)

**Local Development Setup:**
1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows
    # venv\Scripts\activate
    # On macOS/Linux
    # source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Initialize the database:**
    *   The application is configured to create `site.db` (SQLite) automatically if it doesn't exist when run locally for development. For a fresh start, simply delete `site.db` if it exists.
    *   To manually create all tables if needed (e.g., after code changes to models before implementing migrations):
        ```python
        # In a Python shell, from the project root:
        from app import create_app, db
        app = create_app()
        with app.app_context():
            db.create_all()
        ```
5.  **Set up environment variables (optional for local development with defaults):**
    *   `SECRET_KEY`: A default is provided in `config.py` for development. For production, this **must** be a strong, unique key set as an environment variable.
    *   `DATABASE_URL`: Defaults to SQLite (`site.db`). Set this environment variable if you wish to use PostgreSQL or another database locally.

**Running the Application Locally:**
```bash
flask run
# Or
python main.py
```
The application will typically be available at `http://127.0.0.1:5000/`.

**Running Tests:**
```bash
pytest
```
To see test coverage:
```bash
pytest --cov=app
```

**Deployment (Vercel):**
*   This project is configured for deployment on Vercel via the `vercel.json` file.
*   **Critical for Production:** The application **must** be configured to use a **PostgreSQL database** (e.g., Vercel Postgres, Neon, Aiven) for production deployment on Vercel. The `DATABASE_URL` environment variable must be set in your Vercel project settings. SQLite is not suitable for Vercel's production environment.
*   **Environment Variables on Vercel:** Ensure the following are set in your Vercel project settings:
    *   `DATABASE_URL`: Connection string for your production PostgreSQL database.
    *   `SECRET_KEY`: A strong, unique secret key.
    *   `FLASK_ENV`: `production` (this is also set in `vercel.json`).
*   Deployment is typically done by connecting your Git repository (GitHub, GitLab, Bitbucket) to Vercel. Vercel will use the `vercel.json` file to build and deploy the application.

---

*This README provides a general guide. Specific details for your repository URL and any further project-specific configurations should be added as needed. The database initialization instructions may need adjustment based on whether an app factory (`create_app`) pattern is adopted or if the direct `app` instance is used from `main.py` or `app/__init__.py`.*
