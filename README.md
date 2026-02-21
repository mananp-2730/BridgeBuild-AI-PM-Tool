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
* Structured Engineering Tickets (JSON & Jira Markup)
* Technical Risk Analysis (Flagging scalability, compliance, or legacy integration risks)
* Dynamic Budget Estimation (Calculates Dev Time & Cost in USD/INR)
* **[NEW]** AI Co-Pilot Iteration (Refine tickets instantly via chat)

## Tech Stack
* **Core Logic:** Python 3.11
* **AI Engine:** Google Gemini 1.5 Flash & Pro (via `google-genai` SDK)
* **Frontend:** Streamlit 
* **Backend & Auth:** Supabase (PostgreSQL, Row Level Security, Secure Email Auth)

## Key Features
| Feature | Description |
| :--- | :--- |
| **Ambiguity Detection** | Identifies vague terms like "seamless integration" and translates them into specific tech requirements (APIs, Webhooks). |
| **Smart Costing** | Estimates development costs based on rate cards (US Agency vs. Freelancer) and complexity. |
| **Risk Flagging** | Automatically detects compliance issues (GDPR, HIPAA) and infrastructure bottlenecks. |
| **Enterprise Auth & DB** | Secure user accounts with persistent cloud storage. Row Level Security (RLS) ensures users only see their own data. |
| **AI Co-Pilot** | Don't like the first draft? Use the built-in chat to instruct the AI to refine the tech stack, risks, or timeline on the fly. |
| **1-Click Workflows** | Export professional PDFs, copy Jira markdown, or instantly draft a pre-formatted email to your engineering team. |

## Steps to Run Locally
1. **Clone the repo**
   ```bash
   git clone [https://github.com/mananp-2730/BridgeBuild-AI-PM-Tool.git](https://github.com/mananp-2730/BridgeBuild-AI-PM-Tool.git)
   cd BridgeBuild-AI-PM-Tool
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
3. **Set up your API Keys**
   Create a folder named .streamlit in the root directory and create a secrets.toml file inside it:
   ```toml
   GOOGLE_API_KEY = "your_google_gemini_key_here"
   [supabase]
   SUPABASE_URL = "your_supabase_project_url"
   SUPABASE_KEY = "your_supabase_anon_key"
4. **Run the application**
   ```bash
   streamlit run app.py


Roadmap:

Completed Milestones 
[x] User Authentication: Secure login for team collaboration.
[x] Persistent Database: Save session history to the cloud.
[x] Auto API Integration: Hidden backend keys for a seamless user experience.
[x] Advanced Workflows: 1-click email drafts and Jira markup generation.

Upcoming Features 
[ ] Analytics Dashboard: Visualize cost trends and project complexity over time.
[ ] Dark/Light Mode Toggle: Custom UI theme overrides for accessibility.
[ ] Multi-Language Support: Generate tickets in Spanish/French for international clients.
