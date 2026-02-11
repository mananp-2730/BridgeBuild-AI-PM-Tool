[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://bridgebuild-ai-pm-tool-hxpamzy2hsnyxfksaqqk7c.streamlit.app/)
# BridgeBuild AI: Automated Sales-to-Engineering Translator

A Product Management tool that uses LLMs (Google Gemini) to instantly convert vague sales requests into structured technical specifications, risk assessments, and budget estimates.

## The Problem
In B2B software companies, a major source of friction is the "Expectation Gap" between Sales and Engineering:
1.  Sales teams promise features (e.g., "Real-time sync") without realizing the technical complexity.
2.  Engineering teams receive vague requirements, leading to scope creep and missed deadlines.
3.  Cost Estimation is often a guess, leading to underpriced contracts.

## The Solution
BridgeBuild AI acts as an intelligent feasibility layer. It takes raw client emails or meeting notes and generates:
* Structured Engineering Tickets (JSON format)
* Technical Risk Analysis (Flagging scalability, compliance, or legacy integration risks)
* Dynamic Budget Estimation (Calculates Dev Time & Cost in USD/INR)

## Tech Stack
* Core Logic: Python 3.11
* AI Engine: Google Gemini 1.5 Flash (via `google-genai` SDK)
* Frontend: Streamlit (for rapid prototyping)
* Version Control: Git & GitHub

## Key Features
| Feature | Description |
| :--- | :--- |
| Ambiguity Detection | Identifies vague terms like "seamless integration" and translates them into specific tech requirements (APIs, Webhooks). |
| Smart Costing | Estimates development costs based on rate cards (US Agency vs. Freelancer) and complexity. |
| Risk Flagging | Automatically detects compliance issues (GDPR, HIPAA) and infrastructure bottlenecks. |
| Session History | Automatically saves all generated tickets in the sidebar for easy comparison and PDF export. |
| Model Selection | Toggle between Gemini 1.5 Flash (speed) and Pro (complex reasoning). |
| Export to PDF/Jira | Allow users to download specs or push them directly to Jira. |


## How It Works
https://private-user-images.githubusercontent.com/259568222/546293363-e221f21e-ff4c-4953-b6c0-768717a49d58.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NzAzOTM1MTIsIm5iZiI6MTc3MDM5MzIxMiwicGF0aCI6Ii8yNTk1NjgyMjIvNTQ2MjkzMzYzLWUyMjFmMjFlLWZmNGMtNDk1My1iNmMwLTc2ODcxN2E0OWQ1OC5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjYwMjA2JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI2MDIwNlQxNTUzMzJaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1lOTgyNjlmZmM2NjczNjdmMmZkM2NjYWI5NTViMmRlMjViZWNkYTA2OTY1MjQ5YmJiNTBkMGM4ODkwNTdiYjIxJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.IYMIXPwjXyOUI37pOEgoR9scmxk-L6xgvTtuaOS3CkM

## Steps to Run Locally
1. Clone the repo
   ```bash
   git clone [https://github.com/mananp-2730/BridgeBuild-AI-PM-Tool.git](https://github.com/mananp-2730/BridgeBuild-AI-PM-Tool.git)
   cd BridgeBuild-AI-PM-Tool
   
2. Install dependencies
   pip install -r requirements.txt

3. Set up your API Key
   - Create a `.env` file in the root directory.
   - Add your Google API key: `GOOGLE_API_KEY=your_key`

4. Run the application
   streamlit run app.py

## Roadmap

### Upcoming Features
- [x] User Authentication: Secure login for team collaboration.
- [ ] Analytics Dashboard: Visualize cost trends per project type.
- [ ] Dark Mode Toggle: Custom UI themes for better accessibility.
- [ ] Multi-Language Support: Generate tickets in Spanish/French for international clients.
- [ ] Auto API integration: No need of adding end user API if using basic version.
- [ ] Team Integration: Number of developers can be added to estimate product timeline even more accurately.
