import sqlite3
import os
import time
from langchain_anthropic import ChatAnthropic
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv()

def run_automated_research():
    conn = sqlite3.connect('research.db')
    cursor = conn.cursor()
    
    # Fetch active topics
    cursor.execute("SELECT id, topic_name FROM topics WHERE is_active = 1")
    active_topics = cursor.fetchall()

    llm = ChatAnthropic(model="claude-sonnet-4-6")
    search = TavilySearch(max_results=5)

    for t_id, topic_name in active_topics:
        # Get last 3 signals to prevent repeats
        cursor.execute("SELECT report FROM signals WHERE project = ? ORDER BY created_at DESC LIMIT 3", (topic_name,))
        past_reports = [row[0] for row in cursor.fetchall()]
        context_history = "\n---\n".join(past_reports)

        # 1. Search for live news
        raw_news = search.invoke({"query": f"latest news and updates for {topic_name} March 2026"})
        
        # 2. Reasoning with "Anti-Repeat" prompt
        prompt = f"""
        Topic: {topic_name}
        New Search Results: {raw_news}
        Past Reports History: {context_history}
        
        Task: Identify 3 high-impact market signals. 
        CRITICAL: Only include updates that are DIFFERENT from the Past Reports History. 
        If no new significant updates are found, respond exactly with "NO_NEW_UPDATES".
        Format: Signal, PM Impact, and Recommended Action.
        """
        
        report = llm.invoke(prompt).content

        if "NO_NEW_UPDATES" not in report:
            # 3. Save new unique signal
            cursor.execute("INSERT INTO signals (project, report) VALUES (?, ?)", (topic_name, report))
            conn.commit()
            print(f"New alert generated for: {topic_name}")
        else:
            print(f"No unique updates for: {topic_name}")

    conn.close()

if __name__ == "__main__":
    run_automated_research()
