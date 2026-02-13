# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability within this project, please **DO NOT** open a public issue.

Instead, please email the maintainer directly at: [pmanan2707@gmail.com].

## API Key Safety
* This project uses `streamlit.secrets` to manage API keys.
* Never commit `.streamlit/secrets.toml` to the repository.
* If a key is exposed, revoke it immediately via Google AI Studio.
