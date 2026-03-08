import os
import sqlite3
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_tavily import TavilySearch  # The new package

import streamlit as st
from dotenv import load_dotenv

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
You are an expert Product Management Consultant. 
Your task is to analyze raw news data in the context of a specific user project.

<instructions>
1. Identify the 'Signal': What actually happened?
2. Determine the 'Impact': How does this change the user's project roadmap or strategy?
3. Suggest a 'Next Step': Give one concrete action the user should take today.
4. Be concise and professional. Use Markdown for formatting.
</instructions>
"""

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
    conn = sqlite3.connect('project_signals.db')
    # Create a table to store your project details and the AI's impact report
    conn.execute('''CREATE TABLE IF NOT EXISTS reports 
                 (id INTEGER PRIMARY KEY, project TEXT, report TEXT, date DATETIME DEFAULT CURRENT_TIMESTAMP)''')
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
