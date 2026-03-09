import sqlite3
import os
import time
from langchain_anthropic import ChatAnthropic
from langchain_tavily import TavilySearch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

def run_automated_research():
    conn = sqlite3.connect('research.db')
    cursor = conn.cursor()
    
    # 1. Fetch active topics
    cursor.execute("SELECT topic_name FROM topics WHERE is_active = 1")
    active_topics = cursor.fetchall()

    llm = ChatAnthropic(model="claude-sonnet-4-6")
    search = TavilySearch(max_results=5)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    for (topic_name,) in active_topics:
        # 2. SEARCH LIVE NEWS
        raw_news = search.invoke({"query": f"latest news for {topic_name} March 2026"})
        
        # 3. RAG STEP: Search FAISS for "Long-Term Memory"
        memory_context = ""
        if os.path.exists("faiss_index"):
            vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
            # Find the top 3 most semantically similar past reports
            docs = vectorstore.similarity_search(str(raw_news), k=3)
            memory_context = "\n".join([d.page_content for d in docs])

        # 4. REASONING WITH MEMORY
        prompt = f"""
        Topic: {topic_name}
        New Web Data: {raw_news}
        Historical Memory: {memory_context}
        
        Task: Identify 3 high-impact signals. 
        Compare 'New Web Data' against 'Historical Memory'. 
        If these updates are already mentioned in memory, do NOT repeat them.
        If nothing new is found, return 'NO_NEW_UPDATES'.
        """
        
        report = llm.invoke(prompt).content

        if "NO_NEW_UPDATES" not in report:
            # Save to SQLite for the UI
            cursor.execute("INSERT INTO signals (project, report) VALUES (?, ?)", (topic_name, report))
            conn.commit()
            
            # 5. UPDATE FAISS INDEX (New function from app.py logic)
            if os.path.exists("faiss_index"):
                vectorstore.add_texts([report], metadatas=[{"topic": topic_name}])
                vectorstore.save_local("faiss_index")
            else:
                vectorstore = FAISS.from_texts([report], embeddings, metadatas=[{"topic": topic_name}])
                vectorstore.save_local("faiss_index")
            
            print(f"✨ New unique signal stored for {topic_name}")

    conn.close()

if __name__ == "__main__":
    run_automated_research()
