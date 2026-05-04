# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability within this project, please **DO NOT** open a public issue.

Instead, please email the maintainer directly at: [pmanan2707@gmail.com](mailto:pmanan2707@gmail.com). We take all security vulnerabilities seriously and will work to address the issue promptly.

## Credential & API Key Safety
BridgeBuild AI relies on external cloud services (Google Gemini and Supabase). Please adhere to the following security protocols:

* This project uses `streamlit.secrets` for production and environment variables for local testing.
* **NEVER** commit `.streamlit/secrets.toml`, `.env`, or `key.env` to the repository. These are explicitly ignored in our `.gitignore`.
* **Google Gemini:** If a Gemini API key is accidentally exposed, revoke it immediately via [Google AI Studio](https://aistudio.google.com/).
* **Supabase:** If your Supabase Anon or Service Role keys are exposed, cycle them immediately via your Supabase Project Dashboard under `Project Settings -> API`.

## Active Directory & Auth
BridgeBuild AI uses Supabase Auth. For production deployments, ensure Row Level Security (RLS) policies are actively enforced on your database tables to prevent unauthorized cross-department data access.
