# Contributing to BridgeBuild AI

Thank you for considering contributing to BridgeBuild AI! We are building the ultimate Enterprise Agile Operating System, and contributions from the community are highly welcome.

## The Workflow

1. Fork the repository.
2. Create a specific feature branch: `git checkout -b feature/AmazingFeature` or `bugfix/IssueName`.
3. Commit your changes with a descriptive message: `git commit -m 'Add AmazingFeature to Marketing Hub'`.
4. Push to the branch: `git push origin feature/AmazingFeature`.
5. Open a Pull Request detailing what you changed and why.

## Local Development Setup

Because BridgeBuild AI relies on external APIs and cloud databases, you must set up your local environment variables before running the application.

1. Install dependencies:
   ```bash
   pip install -r requirements.txt

2. Create a .streamlit folder in the root directory and add a secrets.toml file inside it.

3. Add your development API keys to .streamlit/secrets.toml:
   ```TOML
   GOOGLE_API_KEY = "your_google_gemini_key_here"
   [supabase]
   SUPABASE_URL = "your_supabase_project_url"
   SUPABASE_KEY = "your_supabase_anon_key"

## Code Style & Architecture Guidelines

* **Python Version:** Use Python 3.11+.
* **Linting:** Follow PEP 8 guidelines. Keep functions modular.
* **Streamlit State:** Never mutate st.session_state variables directly inside rendering loops unless triggered by a specific user action (like a button click) to prevent infinite reload loops.
