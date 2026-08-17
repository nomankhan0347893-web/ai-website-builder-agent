# ⚡ Autonomous AI Website Builder Agent

An autonomous multi-agent software engineering system built with **LangGraph**, **FastAPI**, **React 18**, and **Tailwind CSS**. It takes high-level business ideas, architects full-stack web applications, generates production-ready React code, runs automated QA reviews, checkpoints progress in Git, and deploys directly to cloud hosting.

---

## 🌟 Key Features

- **🤖 Autonomous Multi-Agent Team:**
  - **Orchestrator Agent:** Devises multi-section blueprints and enforces quality standards.
  - **Asset Agent:** Curates dynamic high-res photos and semantic Lucide icons.
  - **Design Agent:** Synthesizes responsive React 18 code with Tailwind CSS styling.
  - **Backend Agent:** Scaffolds Express.js REST API endpoints with CORS support.
  - **QA Reviewer:** Validates syntax, layout contrast, and prevents cliché design tropes.
  - **Execution Agent:** Safely executes commands with human permission gates and Git checkpointing.
- **🖥️ Interactive Embedded Live Preview:** Instant in-browser Babel compilation with Desktop 💻 / Mobile 📱 view toggling.
- **💬 Natural Language Refinement Loop:** Describe changes in plain English to dynamically update design and styles.
- **🛡️ Human-in-the-Loop Safe Execution:** Transparent plain-English explanations before writing files or running commands.
- **🌿 Automated Git Checkpoints:** Automatically commits each accepted stage with full version history.
- **🚀 1-Click Cloud Deployment:** Directly deploys to Netlify via REST API or Netlify Drop with permanent HTTPS links.
- **⚙️ In-App Environment Settings:** Update API keys (`GOOGLE_API_KEY`, `NETLIFY_AUTH_TOKEN`, etc.) directly from the dashboard.

---

## 🛠️ Tech Stack & Model Choices

| Component | Technology / Model | Purpose |
| :--- | :--- | :--- |
| **Agent Orchestration** | LangGraph / StateGraph | Multi-agent state routing & human-in-the-loop checkpoints |
| **Agent LLMs** | Google Gemini 2.5 Flash / Flash-Lite | Planning, coding, and fast visual extraction |
| **Backend Server** | FastAPI, Uvicorn, Python 3.11+ | Graph API endpoints & Netlify cloud deployment engine |
| **Frontend UI** | React 18, Vite, Tailwind CSS | Dashboard UI with live iframe preview & refinement chat |
| **Live Compiler** | `@babel/standalone` | In-browser JSX transpilation without port collisions |
| **Deployment** | Netlify REST API / Netlify Drop | Direct cloud publishing with custom headers |

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd "AI Website Builder Agent"
```

### 2. Configure Backend Environment
Navigate to `backend/` and copy `.env.example`:
```bash
cd backend
cp .env.example .env
```
Add your API keys:
```env
GOOGLE_API_KEY="your_gemini_api_key_here"
NETLIFY_AUTH_TOKEN="your_netlify_token_here" # Optional for 1-click deploy
```

### 3. Setup Python Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\activate   # On Windows
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies
```bash
cd ../frontend
npm install
```

### 5. Run the Application
In separate terminal windows:

**Backend Server (Port 8000):**
```bash
cd backend
.\venv\Scripts\python server.py
```

**Frontend Dashboard (Port 5173):**
```bash
cd frontend
npm run dev
```

Open **`http://localhost:5173`** in your browser!

---

## 📄 License
MIT License. Created with ❤️ by the AI Website Builder Agent team.
