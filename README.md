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
5. Engineering Terminal: Translates business requirements into pure technical execution, providing structured database schemas, color-coded REST API endpoints, tech stack recommendations, and CI/CD pipeline strategies.

## Tech Stack
* **Core Logic:** Python 3.11
* **AI Engine:** Google Gemini 1.5 Flash & Pro (Multimodal File API)
* **Frontend:** Streamlit 
* **Backend & Auth:** Supabase (PostgreSQL, Row Level Security, Secure Email Auth)

## Key value adding features:
* **Multimodal Audio-to-Architecture:** Don't type. Upload raw .mp3 or .wav client meeting recordings directly into the engine and watch it synthesize 45 minutes of messy dialogue into a structured database schema and budget.
* **Shape-Shifting AI Brains:** The application acts as four different SaaS products in one. The UI, logic, and core LLM system prompts dynamically rewrite themselves the exact moment a user logs into their specific department role.
* **Generative Visuals & Flowcharts:** Moves beyond standard text generation by rendering native Mermaid.js architecture diagrams for Engineers and extracting/rendering live CSS Hex color swatches for Designers.
* **Real-Time Dynamic Quoting:** Instantly toggles multi-thousand dollar budget estimations between USD ($) and INR (₹), automatically recalculating historical CRM records on the fly without database refreshes.

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
- [x] Engineering Portal: Pure technical execution, API schemas, JSON payloads, and CI/CD pipelines.

**Upcoming Features** 
- [ ] Company Context Engine: RAG integration to align AI output with internal engineering guidelines.
- [ ] Analytics Dashboard: Visualize cost trends and project complexity over time.
- [ ] Freelancer Mode: An end-to-end pipeline combining Sales, PM, and Engineering views for solo developers.

________
Architectured and Engineered by Manan
