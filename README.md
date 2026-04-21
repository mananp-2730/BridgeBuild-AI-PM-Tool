[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://bridgebuild-ai-pm-tool-hxpamzy2hsnyxfksaqqk7c.streamlit.app/)

## **BridgeBuild AI: The Enterprise Agile Operating System**

A multi-department, role-based SaaS platform that uses Google Gemini to instantly translate messy client notes and audio transcripts into structured, actionable workflows. BridgeBuild AI eliminates organizational data silos by passing a single source of truth from Sales, to Product Management, to Design, Engineering, and Marketing—without a single manual copy-paste.

## Product Management Artifacts
As a product-led platform, BridgeBuild AI was architected with a strict focus on user personas, cross-functional workflows, and business KPIs.
* **Read the full Product Requirements Document (PRD) [here](./PRD.md)** to explore the product strategy, persona breakdowns, and success metrics.

## The Problem: The "Translation Gap"
In B2B software agencies, the biggest point of failure is department handoffs:
1. **Sales** promises features without realizing technical complexity, deal-breakers, or asking the right business questions.
2. **Product Managers** spend hours manually translating vague sales transcripts into structured Agile epics, and struggle to price mid-sprint scope creep.
3. **Designers** get vague "vibes" instead of structured user journeys and component lists.
4. **Engineers** receive unstructured requirements, leading to missed deadlines and messy database schemas.
5. **Marketing** struggles to extract actual customer benefits from highly technical engineering documentation.

## The Solution: The BridgeBuild OS
BridgeBuild AI acts as an intelligent, continuous feasibility pipeline. A single AI engine shape-shifts its personality, logic, and UI based on the user's secure department role (managed via Supabase RBAC).

Instead of isolated tools, BridgeBuild features a **Department Handoff Protocol**. When one department finishes their scoping, they route the locked ticket to the next department's inbox. The AI instantly reads the previous department's constraints (budgets, deal-breakers, user stories) and injects them into the next phase of development—ensuring zero data loss and mathematical budget alignment from kickoff to deployment.

## Role-Based Workspaces & Pipelines:
1. **Sales Intake Portal:** Generates rapid Red/Yellow/Green feasibility scores, critical client "Ask Lists", deal-breaker warnings, and dynamic MVP budgeting.
2. **Product Management (PM) Hub:** Catches approved Sales tickets. Breaks requirements down into Agile Epics, MVP User Stories, and Technical Risk Analysis. **Features a Scope Creep Calculator to mathematically price mid-sprint feature requests.**
3. **UX/UI Design Studio:** Catches approved Agile tickets. Generates core user flows, hex color swatches, writes React/Tailwind boilerplate, and **compiles a Live-Render Prototype Sandbox displaying a fully functional Single Page Application (SPA).**
4. **Engineering Terminal:** Catches approved Design tickets. Translates business requirements into pure technical execution, providing structured database schemas, REST API routes, tech stack recommendations, and CI/CD pipelines.
5. **Marketing Studio (GTM Hub):** Analyzes technical architecture and instantly translates it into high-converting Go-To-Market strategies, including landing page copy, SEO metadata, and Product Hunt launch campaigns.
6. **Admin Control Center:** A "God View" global oversight dashboard featuring real-time visual analytics. It calculates total organizational pipeline value, tracks department bottlenecks via dynamic bar charts, visualizes AI estimate vs. actual margin variance, and manages Active Directory access.

## Key Architectural Features:
* **Live-Render Prototype Sandbox:** Bypasses static code generation by instantly compiling AI-written React and Tailwind CSS into a live, clickable Single Page Application (SPA) directly inside the platform's iframe.
* **Scope Creep (CR) Calculator:** A margin-protection engine that cross-references new client feature requests against the existing scoped database to automatically calculate technical impact, additional costs, and timeline delays.
* **Zero-Friction Session Persistence:** Bypasses aggressive iframe browser security using an ironclad URL-parameter session architecture, keeping users securely logged in across deep-work sessions.
* **Multimodal Audio-to-Architecture:** Upload raw .mp3 or .wav client meeting recordings directly into the engine and watch it synthesize 45 minutes of messy dialogue into structured database schemas.
* **Design-to-Code Component Factory:** Automatically writes syntax-highlighted React + Tailwind CSS boilerplate code based on the AI's generated UI specifications.
* **Global Expansion Engine:** Instantly localizes Go-To-Market strategies into multiple languages and cultural business etiquettes, turning a local product launch into an international campaign.
* **Real-Time Dynamic Quoting:** Toggles multi-thousand dollar budget estimations between USD ($) and INR (₹), automatically recalculating historical database records on the fly.

## **PM Thinking & Strategic Trade-Offs**
Building an Enterprise Agile OS required balancing complex AI pipelines with a frictionless, scalable user experience. Here are the key product decisions made during the development of BridgeBuild AI:

* **Decision 1: Streamlit vs. Custom React/Node.js Frontend**
  * **The Trade-off:** We sacrificed pixel-perfect frontend customization and complex client-side state management in favor of Streamlit's Python-based rapid UI rendering.
  * **The PM Rationale:** For an MVP, the core hypothesis to validate was the *cross-department AI handoff logic* (Sales → PM → Eng), not the UI components. Streamlit provided extreme development velocity, allowing us to build a 6-department platform with complex Supabase routing in weeks rather than months, accelerating our time-to-market.

* **Decision 2: Asynchronous Handoffs vs. Real-Time Collaboration**
  * **The Trade-off:** We built a gated, asynchronous "Inbox" system where departments must explicitly "Approve" and send tickets, rather than a real-time collaborative canvas (like Google Docs or Miro).
  * **The PM Rationale:** In B2B agencies, uncontrolled real-time edits lead to massive scope creep and misaligned budgets. A strict "Department Handoff Protocol" (passing locked JSON states) enforces accountability. It ensures that what Engineering builds is mathematically aligned with the budget Sales originally quoted.

* **Decision 3: Custom RegEx JSON Auto-Healing vs. Strict Schema Validation**
  * **The Trade-off:** We invested engineering hours into building a custom RegEx auto-healing engine to fix broken AI outputs, rather than simply throwing an error if the LLM hallucinated a trailing comma.
  * **The PM Rationale:** LLMs are inherently probabilistic. Failing an entire 45-second Engineering Architecture generation because of one missing markdown bracket destroys the user experience. The auto-healing engine ensures a resilient, crash-free pipeline, prioritizing workflow completion and user trust over rigid schema enforcement.

* **Decision 4: URL-Parameter Session State vs. Standard Cookie Auth**
  * **The Trade-off:** We routed the authenticated user's session ID through the URL parameters rather than relying strictly on hidden browser cookies.
  * **The PM Rationale:** Hosted Python applications (like Streamlit) often face aggressive cross-site iframe security blocks that unexpectedly drop user sessions. By tying the authentication state directly to the URL, we guaranteed zero-friction session persistence. A PM can stay logged in during deep-work sessions without the app timing out and losing their generated Agile epics.

* **Decision 5: Generative Code vs. Drag-and-Drop Builders**
  * **The Trade-off:** We opted to auto-generate raw React/Tailwind boilerplate in the Design Studio rather than building a complex drag-and-drop visual canvas (like Webflow).
  * **The PM Rationale:** Developers heavily dislike exported "spaghetti code" from visual builders. By giving them clean, semantic React boilerplate that they can immediately copy-paste, we drastically reduced time-to-first-paint while keeping the engineering team in absolute control of the final architecture.

* **Decision 6: Single Page Application (SPA) Prototypes vs. Multi-Page HTML**
  * **The Trade-off:** We force the AI to generate complex Javascript to toggle hidden `<div>` elements rather than allowing standard `<a href>` tag navigation.
  * * **The PM Rationale:** Standard HTML links inside a Streamlit iframe cause the parent application to reload and crash the session state. By enforcing SPA architecture, the prototype renders and navigates flawlessly within the Live Sandbox.
      
## Tech Stack
* **Core Logic:** Python 3.11, Pandas
* **AI Engine:** Google Gemini 1.5 Flash & Pro (Multimodal File API)
* **Frontend:** Streamlit with Custom Dynamic CSS Injection (Stealth UI)
* **Backend & Auth:** Supabase (PostgreSQL, Row Level Security, Secure Email Auth)
* **Artifact Generation:** ReportLab (PDFs), Python-PPTX (PowerPoint), Native Mermaid.js, CSV Bulk Exporters

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
- [x] Global Expansion Engine: 1-click international GTM localization.
- [x] Design-to-Code Factory: Automated React + Tailwind CSS boilerplate generation.
- [x] Analytics Dashboard Visualizer: Dynamic charts mapping cost trends, margin variance, and department bottlenecks.
- [x] Scope Creep Calculator: AI-driven financial impact analysis for mid-sprint client requests.
- [x] Live-Render Prototype Sandbox: In-app iframe execution of AI-generated Single Page Applications (SPAs).

**Upcoming Features** 
- [ ] Freelancer Mode: An end-to-end pipeline combining Sales, PM, and Engineering views for solo developers.
- [ ] Automated QA Generation: Auto-generate Selenium or Cypress testing scripts based on the PM Hub's Acceptance Criteria.
- [ ] Database Lockdown: Strict Supabase Row Level Security (RLS) enforcement for production-grade data 


~Manan
