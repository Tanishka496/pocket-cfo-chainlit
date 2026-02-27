import chainlit as cl
import requests
import json
import re
import os
import pandas as pd
from datetime import datetime

# --- OPTIMIZED CONFIG ---
OLLAMA_URL = "http://localhost:11434/api/generate"
# Switching to 3.2 for 3x speed boost. Run: ollama pull llama3.2
MODEL_NAME = "llama3.2" 
DATA_FILE = "transactions.csv"

# --- DATA STORAGE ---
def save_transaction(data):
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=["date", "amount", "type", "category", "description"]).to_csv(DATA_FILE, index=False)
    
    new_row = {
        "date": data.get("date") or datetime.now().strftime("%Y-%m-%d"),
        "amount": float(data["amount"]),
        "type": data["type"].lower(),
        "category": data["category"],
        "description": data.get("description", "No description")
    }
    pd.DataFrame([new_row]).to_csv(DATA_FILE, mode='a', header=False, index=False)

# --- FAST AI CORE (With Streaming) ---
async def call_ollama_stream(prompt: str, msg_element: cl.Message):
    """Streams the response so the user doesn't wait."""
    full_response = ""
    try:
        with requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": prompt, "stream": True},
            stream=True,
            timeout=30
        ) as response:
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode("utf-8"))
                    token = chunk.get("response", "")
                    full_response += token
                    await msg_element.stream_token(token)
        return full_response
    except Exception as e:
        return f"Error: {str(e)}"

async def extract_transaction(user_input: str) -> dict:
    # Minimal prompt for speed
    prompt = f"JSON only: {{amount, type, category}}. Text: {user_input}"
    
    # We don't stream extraction (it needs to be silent/internal)
    resp = requests.post(OLLAMA_URL, json={"model": MODEL_NAME, "prompt": prompt, "stream": False})
    ai_text = resp.json().get("response", "")
    
    match = re.search(r"\{.*\}", ai_text, re.DOTALL)
    if match:
        try: return json.loads(match.group(0))
        except: pass
    return {"amount": None, "type": None, "category": "Other"}

# --- MAIN LOGIC ---
@cl.on_chat_start
async def start():
    await cl.Message(content="⚡ **Fast Mode Active.** Using Llama 3.2.").send()

@cl.on_message
async def main(message: cl.Message):
    # 1. Quick Extraction
    data = await extract_transaction(message.content)

    if data.get("amount") is None:
        await cl.Message(content="Couldn't catch that. Try: 'Spent 500 on rent'").send()
        return

    # 2. Save
    save_transaction(data)

    # 3. Stream Confirmation & Insights
    res_msg = cl.Message(content="")
    await res_msg.send()
    
    # Static header
    header = f"✅ **Logged:** {data['type']} | {data['amount']} | {data['category']}\n\n---\n💡 **Insights:** "
    res_msg.content = header
    await res_msg.update()

    # Dynamic Insight Streaming
    df = pd.read_csv(DATA_FILE).tail(5)
    insight_prompt = f"Short financial tip based on these 5 records: {df.to_json()}"
    
    await call_ollama_stream(insight_prompt, res_msg)
    await res_msg.update()