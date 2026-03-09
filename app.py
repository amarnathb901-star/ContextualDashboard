import os
import sqlite3
import streamlit as st
import time
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_tavily import TavilySearch
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from fpdf import FPDF
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# 1. INITIAL SETUP & DATABASE
load_dotenv()
st.set_page_config(page_title="PM Contextual Signal", layout="wide")

# CLEANED PDF GENERATION: Handles Unicode/Special Characters
def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Strategic Intelligence Report", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    for project, report, date in data:
        pdf.set_font("Arial", "B", 12)
        pdf.multi_cell(0, 10, f"Topic: {project} ({date[:10]})")
        pdf.set_font("Arial", size=10)
        # Clean special characters that latin-1 can't handle
        clean_report = report.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, clean_report)
        pdf.ln(5)
    
    # CRITICAL FIX: Return as encoded bytes
    pdf_string = pdf.output(dest='S')
    return pdf_string.encode('latin-1')

# UNIFIED SLACK NOTIFICATION
def send_slack_notification(topic, report_text):
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    channel_id = "D0AK9R53FP0" # Ensure your bot is invited to this ID
    app_url = "https://contextualdashboard.streamlit.app"

    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*🚨 New Strategic Signal: {topic}*"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": report_text[:2900]} # Truncated for safety
        },
        {
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {"type": "plain_text", "text": "🌐 Open Dashboard"},
                "url": app_url
            }]
        }
    ]

    try:
        client.chat_postMessage(channel=channel_id, blocks=blocks, text=f"New Signal: {topic}")
    except SlackApiError as e:
        st.error(f"Slack Error: {e.response['error']}")

def init_db():
    conn = sqlite3.connect('research.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS topics 
                 (id INTEGER PRIMARY KEY, topic_name TEXT UNIQUE, frequency TEXT, is_active INTEGER DEFAULT 1)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS signals 
                 (id INTEGER PRIMARY KEY, project TEXT, report TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_signal(project, report):
    conn = sqlite3.connect('research.db')
    conn.execute('INSERT INTO signals (project, report) VALUES (?, ?)', (project, report))
    conn.commit()
    conn.close()
    update_faiss_index(project, report)
    # This ensures both Manual and Auto send to Slack
    send_slack_notification(project, report)

def update_faiss_index(topic, report):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    if os.path.exists("faiss_index"):
        vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        vectorstore.add_texts([report], metadatas=[{"topic": topic}])
    else:
        vectorstore = FAISS.from_texts([report], embeddings, metadatas=[{"topic": topic}])
    vectorstore.save_local("faiss_index")

def get_history():
    conn = sqlite3.connect('research.db')
    data = conn.execute("SELECT project, report, created_at FROM signals ORDER BY created_at DESC").fetchall()
    conn.close()
    return data

def run_research(project_context):
    search = TavilySearch(max_results=3)
    llm = ChatAnthropic(model="claude-sonnet-4-6")
    raw_news = search.invoke({"query": project_context})
    prompt = f"Analyze project context: {project_context} against news: {raw_news}. Identify 3 signals and PM impacts."
    return llm.invoke(prompt).content

# UI SECTIONS
def topic_management_section():
    st.divider()
    st.header("🎯 Manage Subscriptions")
    conn = sqlite3.connect('research.db')
    topics = conn.execute("SELECT id, topic_name, frequency, is_active FROM topics").fetchall()
    if not topics:
        st.info("No automated topics.")
    else:
        for t_id, t_name, t_freq, t_active in topics:
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1: st.write(f"**{t_name}**")
            with c2:
                if st.button("✅ Active" if t_active else "🚫 Paused", key=f"s_{t_id}"):
                    conn.execute("UPDATE topics SET is_active = ? WHERE id = ?", (int(not t_active), t_id))
                    conn.commit()
                    st.rerun()
            with c3:
                if st.button("🗑️", key=f"d_{t_id}"):
                    conn.execute("DELETE FROM topics WHERE id = ?", (t_id,))
                    conn.commit()
                    st.rerun()
    conn.close()

def worker_status_sidebar():
    st.sidebar.divider()
    st.sidebar.subheader("🤖 Worker Status")
    
    log_path = "/Users/appit2015140/Documents/Courses/GenAI/ContextualDashboard/worker_log.txt"
    
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            # Read the last 5 lines to find the latest heartbeat
            lines = f.readlines()[-10:]
            latest_log = "".join(lines)
            
            if "💓 [HEARTBEAT]" in latest_log:
                st.sidebar.success("✅ Background Worker: Active")
                # Extract the timestamp from the heartbeat line
                for line in reversed(lines):
                    if "💓 [HEARTBEAT]" in line:
                        st.sidebar.caption(f"Last Run: {line.split('at')[-1].strip()}")
                        break
            else:
                st.sidebar.warning("⚠️ Worker status unknown")
                
        if st.sidebar.button("🔍 View Detailed Logs"):
            st.code(latest_log)
    else:
        st.sidebar.error("❌ No log file found. Check Cron job.")


def main():
    init_db()
    st.title("📡 Contextual Intelligence Dashboard")

    # SIDEBAR: Research History
    with st.sidebar:
        st.header("📜 Past Signals")
        history = get_history()
        if history:
            # Full History Download
            full_pdf = generate_pdf(history)
            st.download_button("📥 Download All as PDF", full_pdf, "full_history.pdf", "application/pdf")
            for h_p, h_r, h_d in history:
                with st.expander(f"{h_d[:10]}: {h_p[:20]}"): st.write(h_r)
        else:
            st.write("No history.")

    tab_auto, tab_manual = st.tabs(["🤖 Automated Alerts", "⚡ Manual Research"])

    with tab_auto:
        with st.form("auto_form", clear_on_submit=True):
            t_name = st.text_input("Track Topic:")
            freq = st.selectbox("Frequency:", ["Hourly", "Daily"])
            if st.form_submit_button("Start Tracking") and t_name:
                conn = sqlite3.connect('research.db')
                conn.execute("INSERT OR IGNORE INTO topics (topic_name, frequency) VALUES (?,?)", (t_name, freq))
                conn.commit(); conn.close()
                st.success("Tracking started!"); st.rerun()

    with tab_manual:
        # Removed Form to allow button to trigger conditional UI elements
        project_context = st.text_area("Roadmap Context:")
        if st.button("Generate Strategic Update", type="primary"):
            if project_context:
                with st.spinner("Analyzing..."):
                    report = run_research(project_context)
                    save_signal(project_context, report) # Triggers Slack
                    st.markdown(report)
                    
                    # INDIVIDUAL PDF DOWNLOAD
                    single_pdf = generate_pdf([(project_context, report, "Just Now")])
                    st.download_button(
                        label="📥 Download this Update as PDF",
                        data=single_pdf,
                        file_name=f"Update_{int(time.time())}.pdf",
                        mime="application/pdf"
                    )
            else:
                st.warning("Enter context.")

    topic_management_section()
    worker_status_sidebar()

if __name__ == "__main__":
    main()