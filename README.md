[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://bridgebuild-ai-pm-tool-hxpamzy2hsnyxfksaqqk7c.streamlit.app/)

BridgeBuild AI: The AI-Powered Agile Operating System

A multi-department, role-based SaaS application that uses Google Gemini to instantly translate messy client notes and audio transcripts into structured, actionable workflows tailored to whoever is logged in (Sales, Product Management, or Design).

## The Problem
In B2B software agencies, a major source of friction is the "Translation Gap" between departments:
1. Sales teams promise features without realizing technical complexity or asking the right business questions.
2. Design teams get vague vibes instead of structured user journeys and component lists.
3. Engineering teams receive unstructured requirements, leading to scope creep and missed deadlines.
4. Cost Estimation is often a guess, leading to underpriced contracts.

## The Solution: Role-Based Workspaces
BridgeBuild AI acts as an intelligent, multi-tenant feasibility layer. A single AI engine shape-shifts its personality and UI based on the user's secure department role (managed via Supabase RBAC). It takes raw client emails, meeting notes, or raw audio recordings and generates role-specific outputs:
1. **Super Admin Workspace:** Complete control over the organization's Active Directory. Instantly upgrade or change user roles via an interactive UI that pushes directly to the Supabase PostgreSQL database.
2. **Sales Intake Portal:** Generates rapid Red/Yellow/Green feasibility scores, the critical "Ask List" for clients, deal-breaker warnings, and dynamic MVP budgeting with a real-time USD/INR toggle.
3. **Product Management (PM) Dashboard:** Breaks unstructured requirements down into Agile Epics, MVP User Stories, Technical Risk Analysis, and native Mermaid.js architecture flowcharts.
4. **UX/UI Design Studio:** Strips away backend tech jargon to generate core user flows, key screen layouts, UI component lists, and automatically extracts and renders hex color swatches for the project's "vibe".

## Tech Stack
* **Core Logic:** Python 3.11
* **AI Engine:** Google Gemini 1.5 Flash & Pro (Multimodal File API)
* **Frontend:** Streamlit 
* **Backend & Auth:** Supabase (PostgreSQL, Row Level Security, Secure Email Auth)

## Project Architecture
The application uses a lightweight, modular routing system to prevent technical debt and allow infinite horizontal scaling for new roles:
BridgeBuild-AI-PM-Tool/
├── app.py                   # Router(Login, Auth, Routing)
├── admin_dashboard.py       # RBAC & User Management UI
├── pm_dashboard.py          # PM Agile & Architecture Logic
├── sales_dashboard.py       # Sales Feasibility & Quoting Logic
├── design_dashboard.py      # UX/UI Generation Logic
├── prompts.py               # Centralized AI Personalities
├── utils.py                 # Helper functions (JSON cleaning, currency, PDF)
└── requirements.txt


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
- [x] Fast vs. Scalable Toggle: Dynamic tech stack recommendations based on project constraints.
- [x] Architecture Flowchart Generation: AI-generated native Mermaid.js diagrams.
- [x] Multimodal Audio Ingestion: Process `.mp3`, `.wav`, and `.pdf` transcripts natively.
- [x] Progressive Disclosure UI: Streamlined interface to reduce cognitive load.
- [x] Granular Database History: Save, manage, and specifically delete session history.
- [x] User Authentication: Secure login for team collaboration.
- [x] Epic & Sub-Task Splitter: Automatically break down high-complexity scores into manageable child tickets.
- [x] Multi-tenant Modular Refactoring: Broke monolithic code into scalable, role-based dashboards.
- [x] Super Admin & RBAC Integration: Dynamic assignment of Sales, PM, and Design roles.
- [x] Sales & Design Portals: Shipped dedicated minimum viable products (MVPs) for non-technical departments.

**Upcoming Features** 
- [ ] Company Context Engine: RAG integration to align AI output with internal engineering guidelines.
- [ ] Analytics Dashboard: Visualize cost trends and project complexity over time.
- [ ] Engineering Portal: Pure technical execution, API schemas, JSON payloads, and CI/CD pipelines.
- [ ] Freelancer Mode: An end-to-end pipeline combining Sales, PM, and Engineering views for solo developers.

________
Architectured and Engineered by Manan
