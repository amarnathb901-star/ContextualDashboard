import os
import sqlite3
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_tavily import TavilySearch  # The new package

import streamlit as st
from dotenv import load_dotenv

import streamlit as st

import streamlit as st

def main_interface():
    st.title("🛡️ Contextual Intelligence Dashboard")
    st.markdown("---")

    # Creating two distinct options for the user
    option_manual, option_automated = st.tabs(["⚡ Option: Manual Research", "🤖 Option: Automated Alerts"])

    # --- MANUAL OPTION ---
    with option_manual:
        st.subheader("Run Instant Strategic Analysis")
        st.info("Use this for one-time deep dives into a specific project roadmap.")
        
        with st.container(border=True):
            project_context = st.text_area(
                "What project roadmap are you tracking?", 
                placeholder="e.g., Expanding our Fintech app to the EU market...",
                key="manual_input"
            )
            if st.button("Generate Strategic Update", type="primary"):
                # Your existing research logic here
                st.write("Running manual research...")

    # --- AUTOMATED OPTION ---
    with option_automated:
        st.subheader("Configure Background Automation")
        st.info("Set up recurring alerts for specific topics. Results are saved to your history.")
        
        with st.container(border=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                topic_to_track = st.text_input(
                    "What topic should I track?", 
                    placeholder="e.g., Anthropic latest news",
                    key="auto_input"
                )
            with col2:
                alert_freq = st.selectbox("Frequency", ["Hourly", "Daily", "Weekly"])
            
            if st.form_submit_button("Start Tracking") if 'form' in globals() else st.button("Activate Automation"):
                # Your existing SQLite saving logic here
                st.success(f"Automation active: Tracking '{topic_to_track}' {alert_freq.lower()}.")

    # --- TOPIC MANAGEMENT (HISTORY) ---
    st.markdown("---")
    topic_management_interface() # The function we wrote earlier for deleting/pausing

def topic_management_interface():
    st.divider() # Adds a visual line to separate sections
    st.header("🎯 Topic Management")
    
    # Form to add new topics
    with st.form("new_topic_form", clear_on_submit=True):
        topic_name = st.text_input("What topic should I track?")
        frequency = st.selectbox("Alert Frequency", ["Hourly", "Daily", "Weekly"])
        if st.form_submit_button("Start Tracking"):
            conn = sqlite3.connect('research.db')
            conn.execute("INSERT OR IGNORE INTO topics (topic_name, frequency) VALUES (?, ?)", 
                         (topic_name, frequency))
            conn.commit()
            conn.close()
            st.success(f"Now tracking {topic_name}!")
            st.rerun() # Refreshes UI to show new topic


    # 2. List and Modify Topics
    st.subheader("Current Subscriptions")
    conn = sqlite3.connect('research.db')
    topics = conn.execute("SELECT id, topic_name, frequency, is_active FROM topics").fetchall()
    
    for t_id, t_name, t_freq, t_active in topics:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{t_name}** ({t_freq})")
        with col2:
            # Toggle Active Status
            status_label = "✅ Active" if t_active else "🚫 Paused"
            if st.button(f"{status_label} (Toggle)", key=f"status_{t_id}"):
                new_status = 0 if t_active else 1
                conn.execute("UPDATE topics SET is_active = ? WHERE id = ?", (new_status, t_id))
                conn.commit()
                st.rerun()
        with col3:
            # Delete Topic
            if st.button("🗑️", key=f"del_{t_id}"):
                conn.execute("DELETE FROM topics WHERE id = ?", (t_id,))
                conn.commit()
                st.rerun()
    conn.close()

# 1. Load your keys FIRST
load_dotenv()

# 2. Initialize the search tool
search = TavilySearch(max_results=3)

# 3. Initialize the Brain
# Updated for March 2026 stability
llm = ChatAnthropic(model="claude-sonnet-4-6", anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))


# Verification: This should print your key (check your terminal)
print(f"DEBUG: Tavily Key found: {os.getenv('TAVILY_API_KEY') is not None}")

import sys
print(sys.path)


# 2. Initialize the Search Tool
# New official way
from langchain_tavily import TavilySearch

# Updated instantiation
search = TavilySearch(max_results=3)

SYSTEM_PROMPT = """
Research the latest news for {topic_name}. The previous reports contained: {last_3_signals}. Identify only new and unique updates worth noting. If no significant new information is found, return 'No new updates.' Formulate the response as a PM Impact Report."""

def run_research(project_context):
    # Execute the live web search
    search_results = search.invoke({"query": project_context})
    
    # Combine everything into a single message for Claude
    combined_prompt = f"{SYSTEM_PROMPT}\n\nUSER PROJECT CONTEXT: {project_context}\n\nLATEST NEWS SIGNALS: {search_results}"
    
    # Get the strategic response
    response = llm.invoke(combined_prompt)
    return response.content

print(run_research("CTV ads"))


def init_db():
    conn = sqlite3.connect('research.db')
    # Table for research topics and their alert frequency
    conn.execute('''CREATE TABLE IF NOT EXISTS topics 
                 (id INTEGER PRIMARY KEY, 
                  topic_name TEXT UNIQUE, 
                  frequency TEXT, 
                  is_active INTEGER DEFAULT 1)''')
    # Existing table for signals
    conn.execute('''CREATE TABLE IF NOT EXISTS signals 
                 (id INTEGER PRIMARY KEY, project TEXT, report TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close() 

def save_report(project_name, ai_report):
    conn = sqlite3.connect('project_signals.db')
    conn.execute('INSERT INTO reports (project, report) VALUES (?, ?)', (project_name, ai_report))
    conn.commit()
    conn.close()

def save_signal(project, report):
    conn = sqlite3.connect('research.db')
    # Use 'signals' as the table name to match your get_history function
    conn.execute('INSERT INTO signals (project, report) VALUES (?, ?)', (project, report))
    conn.commit()
    conn.close()

def manage_topics():
    st.header("🎯 Topic Management")
    
    # Input for new topic
    with st.form("add_topic_form"):
        new_topic = st.text_input("New Research Topic")
        freq = st.selectbox("Alert Frequency", ["Hourly", "Daily", "Weekly"])
        if st.form_submit_button("Add Topic"):
            conn = sqlite3.connect('research.db')
            conn.execute("INSERT OR IGNORE INTO topics (topic_name, frequency) VALUES (?, ?)", (new_topic, freq))
            conn.commit()
            st.success(f"Added: {new_topic}")

    # Display and Manage existing topics
    conn = sqlite3.connect('research.db')
    topics = conn.execute("SELECT id, topic_name, frequency, is_active FROM topics").fetchall()
    
    for t_id, t_name, t_freq, t_active in topics:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{t_name}** ({t_freq})")
        with col2:
            # Toggle Active Status
            if st.button("Discontinue" if t_active else "Resume", key=f"tog_{t_id}"):
                conn.execute("UPDATE topics SET is_active = ? WHERE id = ?", (0 if t_active else 1, t_id))
                conn.commit()
                st.rerun()
        with col3:
            # Delete Topic
            if st.button("🗑️", key=f"del_{t_id}"):
                conn.execute("DELETE FROM topics WHERE id = ?", (t_id,))
                conn.commit()
                st.rerun()
    conn.close()

# Initialize the DB at the start of your script
import sqlite3
init_db()

load_dotenv()

# --- UTILS & DB ---
def get_history():
    conn = sqlite3.connect('research.db')
    # Defensive step: Ensure the table exists before querying
    conn.execute('''CREATE TABLE IF NOT EXISTS signals 
                 (id INTEGER PRIMARY KEY, project TEXT, report TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Now perform the selection
    data = conn.execute("SELECT project, report, created_at FROM signals ORDER BY created_at DESC").fetchall()
    conn.close()
    return data

# --- UI SETUP ---
st.set_page_config(page_title="PM Contextual Signal", layout="wide")

st.title("📡 Contextual Signal Dashboard")
st.caption("March 2026 Edition | Powered by Claude 4.6 & Tavily")

# Sidebar for History
with st.sidebar:
    st.header("📜 Past Signals")
    history = get_history()
    for h_project, h_report, h_date in history:
        with st.expander(f"{h_date[:10]}: {h_project[:20]}..."):
            st.write(h_report)

# Main Input
project_context = st.text_area("What project roadmap are you tracking?", 
                              placeholder="e.g., Expanding our Fintech app's crypto-wallet to the EU market.")

# --- EXECUTION BUTTON ---
if st.button("Generate Strategic Update"):
    if not project_context:
        st.warning("Please enter your project context first.")
    else:
        with st.spinner("Analyzing market signals..."):
            # 1. Search
            search = TavilySearch(max_results=3)
            raw_news = search.invoke({"query": project_context})
            
            # 2. Reasoning (Using the 2026 Stable Model)
            llm = ChatAnthropic(model="claude-sonnet-4-6")
            prompt = f"Context: {project_context}\nNews: {raw_news}\nIdentify 3 market signals and their PM impact."
            report = llm.invoke(prompt).content
            
            # 3. Save & Display
            save_signal(project_context, report) # From your Hour 3 code
            st.success("New Signal Identified!")
            st.markdown(report)

# Inside your streamlit app script
with st.form("new_topic_form"):
    topic_name = st.text_input("What topic should I track?")
    # THIS IS THE MISSING OPTION:
    frequency = st.selectbox("How often should I alert you?", ["Hourly", "Daily", "Weekly"])
    
    if st.form_submit_button("Start Tracking"):
        # Code to save to SQLite...
        st.success(f"Tracking {topic_name} every {frequency}!")

# At the bottom of your script
if __name__ == "__main__":
    init_db() # Ensure tables exist
    
    # Your existing main app code here...
    
    # ADD THIS LINE:
    topic_management_interface()
