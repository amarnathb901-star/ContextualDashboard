import os
import sqlite3
import streamlit as st
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_tavily import TavilySearch

# 1. INITIAL SETUP & DATABASE
load_dotenv()
st.set_page_config(page_title="PM Contextual Signal", layout="wide")

def init_db():
    conn = sqlite3.connect('research.db')
    # Table for automated tracking topics
    conn.execute('''CREATE TABLE IF NOT EXISTS topics 
                 (id INTEGER PRIMARY KEY, 
                  topic_name TEXT UNIQUE, 
                  frequency TEXT, 
                  is_active INTEGER DEFAULT 1)''')
    # Table for saved research reports
    conn.execute('''CREATE TABLE IF NOT EXISTS signals 
                 (id INTEGER PRIMARY KEY, project TEXT, report TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_signal(project, report):
    conn = sqlite3.connect('research.db')
    conn.execute('INSERT INTO signals (project, report) VALUES (?, ?)', (project, report))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect('research.db')
    data = conn.execute("SELECT project, report, created_at FROM signals ORDER BY created_at DESC").fetchall()
    conn.close()
    return data

# 2. AI RESEARCH LOGIC
def run_research(project_context):
    search = TavilySearch(max_results=3)
    llm = ChatAnthropic(model="claude-sonnet-4-6")
    
    # 1. Search live web
    raw_news = search.invoke({"query": project_context})
    
    # 2. Strategic Prompt
    prompt = f"""
    Analyze the following project context against current market signals.
    PROJECT CONTEXT: {project_context}
    LATEST NEWS: {raw_news}
    
    Identify 3 key market signals and their specific PM impacts (Risk, Opportunity, or Action).
    """
    
    response = llm.invoke(prompt)
    return response.content

# 3. UI COMPONENTS
def topic_management_section():
    st.divider()
    st.header("🎯 Manage Subscriptions")
    
    conn = sqlite3.connect('research.db')
    topics = conn.execute("SELECT id, topic_name, frequency, is_active FROM topics").fetchall()
    
    if not topics:
        st.info("No automated topics currently being tracked.")
    else:
        for t_id, t_name, t_freq, t_active in topics:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{t_name}** ({t_freq})")
            with col2:
                status_label = "✅ Active" if t_active else "🚫 Paused"
                if st.button(f"{status_label}", key=f"status_{t_id}"):
                    new_status = 0 if t_active else 1
                    conn.execute("UPDATE topics SET is_active = ? WHERE id = ?", (new_status, t_id))
                    conn.commit()
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"del_{t_id}"):
                    conn.execute("DELETE FROM topics WHERE id = ?", (t_id,))
                    conn.commit()
                    st.rerun()
    conn.close()

# 4. MAIN APP INTERFACE
def main():
    init_db()
    st.title("📡 Contextual Intelligence Dashboard")
    st.caption("March 2026 Edition | AI-Powered Strategic Monitoring")

    # SIDEBAR: Research History (RAG Component)
    with st.sidebar:
        st.header("📜 Past Signals")
        history = get_history()
        if history:
            for h_project, h_report, h_date in history:
                with st.expander(f"{h_date[:10]}: {h_project[:20]}..."):
                    st.write(h_report)
        else:
            st.write("No history found.")

    # MAIN CONTENT: Tabs for Manual vs Automated
    tab_manual, tab_auto = st.tabs(["🤖 Option: Automated Alerts", "⚡ Option: Manual Research"])

    with tab_auto:
        st.subheader("Configure Background Monitoring")
        st.info("Set a topic here to be tracked by the background Cron job.")
        with st.form("automation_settings_form", clear_on_submit=True):
            topic_name = st.text_input("What topic should I track?")
            frequency = st.selectbox("Alert Frequency", ["Hourly", "Daily", "Weekly"])
            submit_auto = st.form_submit_button("Start Tracking")
            
            if submit_auto:
                if topic_name:
                    conn = sqlite3.connect('research.db')
                    conn.execute("INSERT OR IGNORE INTO topics (topic_name, frequency) VALUES (?, ?)", 
                                 (topic_name, frequency))
                    conn.commit()
                    conn.close()
                    st.success(f"Now tracking {topic_name} {frequency.lower()}!")
                    st.rerun()
                else:
                    st.warning("Please enter a topic.")

    with tab_manual:
        st.subheader("Run Instant Strategic Analysis")
        with st.form("manual_form"):
            project_context = st.text_area("What project roadmap are you tracking?", 
                                         placeholder="e.g., Expanding our Fintech app to the EU market.")
            submit_manual = st.form_submit_button("Generate Strategic Update", type="primary")
            
            if submit_manual:
                if project_context:
                    with st.spinner("Analyzing signals..."):
                        report = run_research(project_context)
                        save_signal(project_context, report)
                        st.success("New Signal Identified!")
                        st.markdown(report)
                else:
                    st.warning("Please enter context.")

 
    # Persistent Management UI at the bottom
    topic_management_section()

if __name__ == "__main__":
    main()