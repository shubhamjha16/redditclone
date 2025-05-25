# College Community Platform

**Description:** A Reddit-style community platform designed for college communities, enabling students, faculty, and staff to connect, share information, and build communities around academic interests, courses, campus life, and events.

**Features:**
*   User registration and authentication (with college affiliation, student ID, year of college).
*   Role-based access control (User, Admin).
*   Reddit-style content platform:
    *   Post creation, viewing, voting, and commenting.
    *   College-specific spaces (sub-communities).
    *   Content display in a card-based, Reddit-like UI.
*   College-Specific Features:
    *   Course discussions.
    *   Study group organization.
    *   Event creation and management.
*   Administrative Tools:
    *   College management (create, edit).
    *   User management (verify affiliation, change roles).
    *   Content moderation (reporting system, review reported content).
*   Search functionality (posts, courses, colleges).
*   User notification system (e.g., for new comments on posts).
*   Mobile-responsive design.
*   Comprehensive test suite (Pytest).

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
