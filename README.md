📡 Contextual Intelligence Dashboard
March 2026 Edition | AI-Powered Strategic Monitoring for Product Managers

The Contextual Intelligence Dashboard is a high-performance Agentic RAG (Retrieval-Augmented Generation) tool. It bridges the gap between internal project roadmaps and external market shifts by combining live web research with persistent local memory.

🚀 Key Features
Dual-Mode Intelligence:

Manual Research: Run instant, deep-dive analysis on any specific project roadmap.

Automated Alerts: Configure background tracking for specific topics (Anthropic, Nvidia, etc.) with customizable frequencies.

Agentic RAG Pipeline: Uses Tavily Search to pull real-time data and Claude 4.6 to perform strategic reasoning.

Persistence Layer: Built-in SQLite integration to store and manage research history and automated subscriptions.

Strategic Impact Reporting: Automatically categorizes findings into "Signal," "PM Impact," and "Recommended Action."

🛠️ Tech Stack
UI Framework: Streamlit

LLM: Anthropic Claude 4.6 (Sonnet)

Search Engine: Tavily API

Database: SQLite3

Automation: Linux/macOS Cron

📦 Installation & Setup
1. Clone the Repository
Bash
git clone https://github.com/amarnathb901-star/ContextualDashboard.git
cd ContextualDashboard
2. Set Up the Environment
Bash
python -m venv faiss_env
source faiss_env/bin/activate  # On Windows use `faiss_env\Scripts\activate`
pip install -r requirements.txt
3. Configure API Keys
Create a .env file in the root directory:

Plaintext
ANTHROPIC_API_KEY="your_anthropic_key"
TAVILY_API_KEY="your_tavily_key"
⚙️ Running the Application
Start the Dashboard (UI)
Bash
streamlit run app.py
Set Up Automated Alerts (Background)
To enable the "Option: Automated" features, schedule the worker.py script using Cron:

Open crontab: crontab -e

Add this line (runs every hour):
0 * * * * /path/to/faiss_env/bin/python /path/to/worker.py

📂 Project Structure
app.py: The main Streamlit interface and manual research logic.

worker.py: The background automation script that processes scheduled alerts.

research.db: SQLite database storing your topics and signal history.

requirements.txt: List of Python dependencies.