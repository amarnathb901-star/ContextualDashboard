import os
import sqlite3
import time
from dotenv import load_dotenv

# AI & Search Imports
from langchain_anthropic import ChatAnthropic
from langchain_tavily import TavilySearch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Slack Import
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# 1. SETUP
load_dotenv()
client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def send_slack_notification(topic, report_text):
    """Sends a formatted Slack message with a button to the dashboard."""
    channel_id = "bot-updates" # Ensure your bot is invited to this channel
    app_url = "https://your-app-url.streamlit.app" 

    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*🚨 New Strategic Signal: {topic}*"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": report_text[:3000]}},
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
        client.chat_postMessage(channel=channel_id, blocks=blocks, text=f"Update: {topic}")
    except SlackApiError as e:
        print(f"Slack Error: {e.response['error']}")

def run_worker():
    print("🤖 Worker started: Checking for updates...")
    conn = sqlite3.connect('research.db')
    cursor = conn.cursor()

    # Get active topics from your UI settings
    cursor.execute("SELECT topic_name FROM topics WHERE is_active = 1")
    active_topics = cursor.fetchall()

    if not active_topics:
        print("💤 No active topics to track.")
        return

    llm = ChatAnthropic(model="claude-sonnet-4-6")
    search = TavilySearch(max_results=5)

    for (topic_name,) in active_topics:
        print(f"🔍 Researching: {topic_name}")
        
        # 1. Live Web Search
        raw_news = search.invoke({"query": f"latest features and news for {topic_name} March 2026"})

        # 2. Semantic Memory Retrieval (FAISS)
        memory_context = ""
        if os.path.exists("faiss_index"):
            vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
            docs = vectorstore.similarity_search(str(raw_news), k=2)
            memory_context = "\n".join([d.page_content for d in docs])

        # 3. AI Reasoning (Filtering for Uniqueness)
        prompt = f"""
        Topic: {topic_name}
        New Data: {raw_news}
        Past Reports: {memory_context}
        
        Instruction: Summarize the new updates. 
        If the information in 'New Data' is already present in 'Past Reports', return 'NO_NEW_UPDATES'.
        Otherwise, provide a PM Strategic Impact report.
        """
        
        report = llm.invoke(prompt).content

        if "NO_NEW_UPDATES" not in report:
            # 4. Save to DB
            cursor.execute("INSERT INTO signals (project, report) VALUES (?, ?)", (topic_name, report))
            conn.commit()
            
            # 5. Send Slack Alert
            send_slack_notification(topic_name, report)

            # 6. Update FAISS Memory
            if os.path.exists("faiss_index"):
                vectorstore.add_texts([report], metadatas=[{"topic": topic_name}])
                vectorstore.save_local("faiss_index")
            else:
                vectorstore = FAISS.from_texts([report], embeddings, metadatas=[{"topic": topic_name}])
                vectorstore.save_local("faiss_index")
            
            print(f"✅ Alert sent for {topic_name}")
        else:
            print(f"⏭️ No new unique info for {topic_name}")

    conn.close()

if __name__ == "__main__":
    run_worker()