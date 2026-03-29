[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://bridgebuild-ai-pm-tool-hxpamzy2hsnyxfksaqqk7c.streamlit.app/)

## **BridgeBuild AI: The Enterprise Agile Operating System**

A multi-department, role-based SaaS platform that uses Google Gemini to instantly translate messy client notes and audio transcripts into structured, actionable workflows. BridgeBuild AI eliminates organizational data silos by passing a single source of truth from Sales, to Product Management, to Design, Engineering, and Marketing—without a single manual copy-paste.

## The Problem: The "Translation Gap"
In B2B software agencies, the biggest point of failure is department handoffs:
1. **Sales** promises features without realizing technical complexity, deal-breakers, or asking the right business questions.
2. **Product Managers** spend hours manually translating vague sales transcripts into structured Agile epics.
3. **Designers** get vague "vibes" instead of structured user journeys and component lists.
4. **Engineers** receive unstructured requirements, leading to scope creep, missed deadlines, and messy database schemas.
5. **Marketing** struggles to extract actual customer benefits from highly technical engineering documentation.

## The Solution: The BridgeBuild OS
BridgeBuild AI acts as an intelligent, continuous feasibility pipeline. A single AI engine shape-shifts its personality, logic, and UI based on the user's secure department role (managed via Supabase RBAC).

Instead of isolated tools, BridgeBuild features a **Department Handoff Protocol**. When one department finishes their scoping, they route the locked ticket to the next department's inbox. The AI instantly reads the previous department's constraints (budgets, deal-breakers, user stories) and injects them into the next phase of development—ensuring zero data loss and mathematical budget alignment from kickoff to deployment.

## Role-Based Workspaces & Pipelines:
1. **Sales Intake Portal:** Generates rapid Red/Yellow/Green feasibility scores, critical client "Ask Lists", deal-breaker warnings, and dynamic MVP budgeting.
2. **Product Management (PM) Hub:** Catches approved Sales tickets. Breaks requirements down into Agile Epics, MVP User Stories, Technical Risk Analysis, and native Mermaid.js architecture flowcharts.
3. **UX/UI Design Studio:** Catches approved Agile tickets. Strips away backend tech jargon to generate core user flows, key screen layouts, UI component lists, and extracts hex color swatches for the project's visual identity.
4. **Engineering Terminal:** Catches approved Design tickets. Translates business requirements into pure technical execution, providing structured database schemas, REST API routes, tech stack recommendations, and CI/CD pipelines.
5. **Marketing Studio (GTM Hub):** Analyzes technical architecture and instantly translates it into high-converting Go-To-Market strategies, including landing page copy, SEO metadata, and Product Hunt launch campaigns.
6. **Admin Control Center:** A global oversight dashboard that calculates total organizational pipeline value, tracks real-time department bottlenecks, and manages Active Directory access.

## **PM Thinking & Strategic Trade-Offs**
Building an Enterprise Agile OS required balancing complex AI pipelines with a frictionless, scalable user experience. Here are the key product decisions made during the development of BridgeBuild AI:

* **Decision 1: Streamlit vs. Custom React/Node.js Frontend**
  * **The Trade-off:** We sacrificed pixel-perfect frontend customization and complex client-side state management in favor of Streamlit's Python-based rapid UI rendering.
  * **The PM Rationale:** For an MVP, the core hypothesis to validate was the *cross-department AI handoff logic* (Sales → PM → Eng), not the UI components. Streamlit provided extreme development velocity, allowing us to build a 6-department platform with complex Supabase routing in weeks rather than months, accelerating our time-to-market.

* **Decision 2: SQLite vs. Cloud PostgreSQL**
  * **The Trade-off:** We launched with a local SQLite database instead of a scalable, enterprise-grade cloud SQL server.
  * **The PM Rationale:** The core hypothesis to prove was "Can an LLM reliably translate voice to SQL and render UI components?" SQLite allowed for zero-configuration local testing and immediate validation of this "Text-to-SQL" agent without incurring cloud database costs or setting up complex VPCs for an MVP.

* **Decision 3: Muting the Mic During TTS Playback**
  * **The Trade-off:** The user cannot interrupt the AI while it is speaking, creating a walkie-talkie-style interaction rather than true full-duplex conversation.
  * **The PM Rationale:** If the Web Speech API mic remained active while the AI's Text-to-Speech (TTS) engine spoke, the system would transcribe its own voice, creating an infinite hallucination loop. Ensuring data accuracy and system stability took priority over concurrent speaking capabilities.

* **Decision 4: Skipping API Integrations (Salesforce/HubSpot)**
  * **The Trade-off:** We require the user to upload a CSV or use our dummy SQL database rather than connecting directly to their real SaaS tools.
  * **The PM Rationale:** Building OAuth pipelines for external APIs would delay the MVP launch by weeks. We prioritized building the core Generative Dashboard Engine first. If users find value in generating Chart.js files from raw CSVs, the logical next iteration is to build the API connectors.

## Tech Stack
* **Core Logic:** Python 3.11, Pandas
* **AI Engine:** Google Gemini 1.5 Flash & Pro (Multimodal File API)
* **Frontend:** Streamlit with Custom Dynamic CSS Injection (Stealth UI)
* **Backend & Auth:** Supabase (PostgreSQL, Row Level Security, Secure Email Auth)
* **Artifact Generation:** ReportLab (PDFs), Python-PPTX (PowerPoint), Native Mermaid.js, CSV Bulk Exporters

## Key Architectural Features:
* **Zero-Friction Session Persistence:** Bypasses aggressive iframe browser security using an ironclad URL-parameter session architecture, keeping users securely logged in across deep-work sessions.
* **Multimodal Audio-to-Architecture:** Don't type. Upload raw .mp3 or .wav client meeting recordings directly into the engine and watch it synthesize 45 minutes of messy dialogue into a structured database schema.
* **Automated Stakeholder Artifacts:** Instantly generates and downloads localized, department-specific PDF reports and pre-fills email clients to share specs with external stakeholders in one click.
* **Real-Time Dynamic Quoting:** Toggles multi-thousand dollar budget estimations between USD ($) and INR (₹), automatically recalculating historical database records on the fly.
* **1-Click Client Pitch Decks:** Instantly format internal sales and feasibility data into a client-ready, scrubbed, and professional `.pptx` presentation.

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
- [x] Multi-tenant Modular Refactoring: Scalable, role-based dashboards.
- [x] Super Admin God View: Global pipeline analytics and Active Directory RBAC.
- [x] Department Handoff Protocol: Cross-user database injections and Inbox queues.
- [x] Zero-Friction Auth: Bulletproof URL session routing.
- [x] Multimodal Audio Ingestion: Process .mp3, .wav, and .pdf transcripts natively.
- [x] Automated Artifact Generation: Dynamic PDF and Stakeholder Email creation.
- [x] Architecture Flowchart Generation: AI-generated native Mermaid.js diagrams.
- [x] Jira / Linear Integration: One-click bulk CSV export of Agile epics and Developer schemas.
- [x] Dynamic Stealth UI: Custom CSS engine for flawless dark mode transitions.
- [x] Engine Auto-Healing: Resilient JSON parsing to prevent AI hallucination crashes.
- [x] Pitch Deck Generator: Auto-generation of client-ready PowerPoint files.
- [x] Profitability Calibration Engine: Financial tracking and estimation vs. actual variance analytics.
- [x] Company Context Engine: RAG integration to align AI output with internal engineering guidelines.
- [x] Marketing Studio: Go-To-Market asset generation from technical schemas.

**Upcoming Features** 
- [ ] Company Context Engine: RAG integration to align AI output with internal engineering guidelines.
- [ ] Analytics Dashboard: Visualize cost trends and project complexity over time.
- [ ] Freelancer Mode: An end-to-end pipeline combining Sales, PM, and Engineering views for solo developers.
- [ ] Automated QA Generation: Auto-generate Selenium or Cypress testing scripts based on the PM Hub's Acceptance Criteria.
- [ ] Database Lockdown: Strict Supabase Row Level Security (RLS) enforcement for production-grade data 


~Manan
