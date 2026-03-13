[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://bridgebuild-ai-pm-tool-hxpamzy2hsnyxfksaqqk7c.streamlit.app/)

## **BridgeBuild AI: The Enterprise Agile Operating System**

A multi-department, role-based SaaS platform that uses Google Gemini to instantly translate messy client notes and audio transcripts into structured, actionable workflows. BridgeBuild AI eliminates organizational data silos by passing a single source of truth from Sales, to Product Management, to Design, to Engineering without a single copy-paste.

## The Problem: The "Translation Gap"
In B2B software agencies, the biggest point of failure is department handoffs:
1. Sales promises features without realizing technical complexity, deal-breakers, or asking the right business questions.
2. Product Managers spend hours manually translating vague sales transcripts into structured Agile epics.
3. Designers get vague "vibes" instead of structured user journeys and component lists.
4. Engineers receive unstructured requirements, leading to scope creep, missed deadlines, and messy database schemas.

## The Solution: The BridgeBuild OS
BridgeBuild AI acts as an intelligent, continuous feasibility pipeline. A single AI engine shape-shifts its personality, logic, and UI based on the user's secure department role (managed via Supabase RBAC).

Instead of isolated tools, BridgeBuild features a Department Handoff Protocol. When one department finishes their scoping, they route the locked ticket to the next department's inbox. The AI instantly reads the previous department's constraints (budgets, deal-breakers, user stories) and injects them into the next phase of development—ensuring zero data loss and mathematical budget alignment from kickoff to deployment.

## Role-Based Workspaces & Pipelines:
1. **Sales Intake Portal:** Generates rapid Red/Yellow/Green feasibility scores, critical client "Ask Lists", deal-breaker warnings, and dynamic MVP budgeting.
2. **Product Management (PM) Hub:** Catches approved Sales tickets. Breaks requirements down into Agile Epics, MVP User Stories, Technical Risk Analysis, and native Mermaid.js architecture flowcharts.
3. **UX/UI Design Studio:** Catches approved Agile tickets. Strips away backend tech jargon to generate core user flows, key screen layouts, UI component lists, and extracts hex color swatches for the project's visual identity.
4. **Engineering Terminal:** Catches approved Design tickets. Translates business requirements into pure technical execution, providing structured database schemas, REST API routes, tech stack recommendations, and CI/CD pipelines.
5. **Admin Control Center:** A global oversight dashboard that calculates total organizational pipeline value, tracks real-time department bottlenecks, and manages Active Directory access.

## Tech Stack
* **Core Logic:** Python 3.11
* **AI Engine:** Google Gemini 1.5 Flash & Pro (Multimodal File API)
* **Frontend:** Streamlit 
* **Backend & Auth:** Supabase (PostgreSQL, Row Level Security, Secure Email Auth)
* **Artifact Generation:** ReportLab (PDFs), Native Mermaid.js

## Key Architectural Features:
* **Zero-Friction Session Persistence:** Bypasses aggressive iframe browser security using an ironclad URL-parameter session architecture, keeping users securely logged in across deep-work sessions.
* **Multimodal Audio-to-Architecture:** Don't type. Upload raw .mp3 or .wav client meeting recordings directly into the engine and watch it synthesize 45 minutes of messy dialogue into a structured database schema.
* **Automated Stakeholder Artifacts:** Instantly generates and downloads localized, department-specific PDF reports and pre-fills email clients to share specs with external stakeholders in one click.
* **Real-Time Dynamic Quoting:** Toggles multi-thousand dollar budget estimations between USD ($) and INR (₹), automatically recalculating historical database records on the fly.

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
