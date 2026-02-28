[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://bridgebuild-ai-pm-tool-hxpamzy2hsnyxfksaqqk7c.streamlit.app/)

# BridgeBuild AI: Automated Sales-to-Engineering Translator

A Product Management tool that uses LLMs (Google Gemini) to instantly convert vague sales requests into structured technical specifications, risk assessments, and budget estimates.

## The Problem
In B2B software companies, a major source of friction is the "Expectation Gap" between Sales and Engineering:
1.  Sales teams promise features (e.g., "Real-time sync") without realizing the technical complexity.
2.  Engineering teams receive vague requirements, leading to scope creep and missed deadlines.
3.  Cost Estimation is often a guess, leading to underpriced contracts.

## The Solution
BridgeBuild AI acts as an intelligent feasibility layer. It takes raw client emails, meeting notes, or **raw audio recordings** and generates:
* Structured Engineering Tickets (JSON & Jira Markup)
* Technical Risk Analysis (Flagging scalability, compliance, or legacy integration risks)
* Dynamic Budget Estimation (Calculates Dev Time & Cost in USD/INR)
* **[NEW]** Multimodal Audio Ingestion (Directly upload `.mp3`/`.wav` meeting recordings)
* **[NEW]** AI Co-Pilot Iteration (Refine tickets instantly via chat)
* **[NEW]** Progressive Disclosure UI (Clean, collapsible data views)

## Tech Stack
* **Core Logic:** Python 3.11
* **AI Engine:** Google Gemini 1.5 Flash & Pro (Multimodal File API)
* **Frontend:** Streamlit 
* **Backend & Auth:** Supabase (PostgreSQL, Row Level Security, Secure Email Auth)

## Key Features
| Feature | Description |
| :--- | :--- |
| **Multimodal Audio Ingestion** | Skip typing entirely. Upload Zoom meeting audio or transcripts and let the AI listen to the client's raw request. |
| **Progressive Disclosure UI** | Organizes massive amounts of technical data into clean, collapsible sections so users are never overwhelmed. |
| **Granular History Management** | Securely stores past generated tickets with individual deletion controls and 1-click PDF/Email retrieval. |
| **Ambiguity Detection** | Identifies vague terms like "seamless integration" and translates them into specific tech requirements. |
| **Smart Costing** | Estimates development costs based on rate cards (US Agency vs. Freelancer) and complexity. |
| **Enterprise Auth & DB** | Secure user accounts with persistent cloud storage. Row Level Security (RLS) ensures data privacy. |
| **AI Co-Pilot** | Use the built-in chat to instruct the AI to refine the tech stack, risks, or timeline on the fly. |
| **Epic Splitter** | Dynamically detects high-complexity requests and automatically breaks monolithic projects into manageable Agile sub-tasks. |

## Steps to Run Locally
1. **Clone the repo**
   ```bash
   git clone [https://github.com/mananp-2730/BridgeBuild-AI-PM-Tool.git](https://github.com/mananp-2730/BridgeBuild-AI-PM-Tool.git)
   cd BridgeBuild-AI-PM-Tool
   
2. **Install Dependencies**
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

## Roadmap

**Completed Milestones** 
- [x] Architecture Flowchart Generation: AI-generated native Mermaid.js diagrams.
- [x] Multimodal Audio Ingestion: Process `.mp3`, `.wav`, and `.pdf` transcripts natively.
- [x] Progressive Disclosure UI: Streamlined interface to reduce cognitive load.
- [x] Granular Database History: Save, manage, and specifically delete session history.
- [x] User Authentication: Secure login for team collaboration.
- [x] Epic & Sub-Task Splitter: Automatically break down high-complexity scores into manageable child tickets.

**Upcoming Features** 
- [ ] Fast vs. Scalable Toggle: Dynamic tech stack recommendations based on project constraints.
- [ ] Company Context Engine: RAG integration to align AI output with internal engineering guidelines.
- [ ] Analytics Dashboard: Visualize cost trends and project complexity over time.

________
Architectured and Engineered by Manan
