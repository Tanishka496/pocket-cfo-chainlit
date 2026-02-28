import chainlit as cl
import requests
import json
import re
import os
from datetime import datetime
from supabase import create_client

# -------------------------
# ENVIRONMENT VARIABLES
# -------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")  # Can be remote
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

# Optional: Print warnings if not set
if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ WARNING: SUPABASE_URL or SUPABASE_KEY not set. Database features will fail.")
print(f"ℹ️ Ollama URL: {OLLAMA_URL}")
print(f"ℹ️ Ollama Model: {OLLAMA_MODEL}")

# -------------------------
# SUPABASE CLIENT
# -------------------------
supabase = None

def get_supabase():
    global supabase
    if supabase is None:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase

TABLE_NAME = "transactions_ai"  # Make sure this table exists in Supabase

# -------------------------
# OLLAMA CONFIG
# -------------------------
# Ollama is accessed via HTTP

print("✅ Ollama configured and ready")

# -------------------------
# EXTRACT TRANSACTION
# -------------------------
async def extract_transaction(user_input: str) -> dict:
    prompt = f"JSON only: {{amount, type, category}}. Text: {user_input}"
    try:
        print(f"DEBUG: Calling Ollama at {OLLAMA_URL}", flush=True)
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=30
        )
        resp.raise_for_status()
        ai_text = resp.json().get("response", "")
        print(f"DEBUG: Ollama response: {ai_text}", flush=True)
        match = re.search(r"\{.*\}", ai_text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            # Ensure keys
            data.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
            data.setdefault("amount", None)
            data.setdefault("type", "expense")
            data.setdefault("category", "Other")
            data.setdefault("description", user_input)
            return data
    except requests.exceptions.Timeout:
        print("ERROR: Ollama request timed out", flush=True)
    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: Cannot connect to Ollama at {OLLAMA_URL}: {e}", flush=True)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Ollama request failed: {e}", flush=True)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse Ollama response: {e}", flush=True)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", flush=True)

    # fallback simple extraction
    print("DEBUG: Using fallback extraction", flush=True)
    amount_match = re.search(r"(\d+(\.\d+)?)", user_input)
    amount = float(amount_match.group(1)) if amount_match else None
    type_ = "expense" if "spent" in user_input.lower() else "revenue"
    categories = ["Rent", "Groceries", "Utilities", "Salary", "Other"]
    category = next((c for c in categories if c.lower() in user_input.lower()), "Other")
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "amount": amount,
        "type": type_,
        "category": category,
        "description": user_input
    }

# -------------------------
# SAVE TRANSACTION TO SUPABASE
# -------------------------
def save_transaction(data: dict):
    try:
        record = {
            "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "amount": data.get("amount", 0.0),
            "type": data.get("type", "expense"),
            "category": data.get("category", "Other"),
            "description": data.get("description", "")
        }
        print(f"DEBUG: Saving transaction to Supabase: {record}", flush=True)
        get_supabase().table(TABLE_NAME).insert(record).execute()
        print("DEBUG: Transaction saved successfully", flush=True)
    except Exception as e:
        print(f"ERROR: Failed to save transaction to Supabase: {e}", flush=True)
        raise

# -------------------------
# FETCH LAST N TRANSACTIONS
# -------------------------
def get_last_transactions(limit=5):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    try:
        resp = get_supabase().table(TABLE_NAME).select("*").order("date", desc=True).limit(limit).execute()
        return resp.data or []
    except Exception as e:
        print(f"ERROR: Failed to fetch transactions: {e}", flush=True)
        return []

# -------------------------
# STREAM INSIGHTS VIA OLLAMA
# -------------------------
async def call_ollama_stream(prompt: str, msg_element: cl.Message):
    """
    Stream insights from Ollama.
    """
    full_response = ""
    try:
        print(f"DEBUG: Calling Ollama for insights", flush=True)
        with requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": True},
            stream=True,
            timeout=None
        ) as response:
            response.raise_for_status()
            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                try:
                    chunk = json.loads(raw_line)
                    token = chunk.get("response", "")
                    if token:
                        full_response += token
                        try:
                            await msg_element.stream_token(token)
                        except Exception:
                            pass
                except json.JSONDecodeError:
                    pass
            
            await msg_element.update()
        return full_response
    except Exception as e:
        print(f"ERROR: Ollama stream failed: {e}", flush=True)
        msg_element.content += f"\n[Error: {e}]"
        await msg_element.update()
        return f"Error: {str(e)}"

# -------------------------
# CHAINLIT EVENTS
# -------------------------
@cl.on_chat_start
async def start():
    print("DEBUG: Chat started", flush=True)
    status = ["🦙 Ollama (llama3.2) Ready"]
    
    if SUPABASE_URL and SUPABASE_KEY:
        status.append("✅ Supabase configured")
    else:
        status.append("⚠️ Supabase not configured (transactions won't save)")
    
    msg = " | ".join(status) + "\n\n⚡ Hackathon Mode Active!"
    await cl.Message(content=msg).send()

@cl.on_message
async def main(message: cl.Message):
    print(f"DEBUG: Received message: {message.content}", flush=True)
    # 1️⃣ Extract structured data
    data = await extract_transaction(message.content)

    if data["amount"] is None:
        await cl.Message(content="Couldn't detect the amount. Try: 'Spent 500 on rent'").send()
        return

    # 2️⃣ Save to Supabase
    try:
        if SUPABASE_URL and SUPABASE_KEY:
            save_transaction(data)
        else:
            print("WARN: Supabase not configured - transaction not saved", flush=True)
    except Exception as e:
        await cl.Message(content=f"❌ Error saving transaction: {e}").send()
        return

    # 3️⃣ Stream confirmation + insights
    res_msg = cl.Message(content="")
    await res_msg.send()

    # Confirmation header
    header = f"✅ **Logged:** {data['type']} | {data['amount']} | {data['category']}\n\n---\n💡 **Insights:** "
    res_msg.content = header
    await res_msg.update()

    # Generate dynamic insight
    last_tx = get_last_transactions(5)
    if last_tx:
        amounts = [tx["amount"] for tx in last_tx if tx["type"] == "expense"]
        avg_expense = sum(amounts)/len(amounts) if amounts else 0
        insight_prompt = f"Give a short financial tip based on these last 5 transactions: {last_tx}"
        await call_ollama_stream(insight_prompt, res_msg)
    else:
        res_msg.content += "No previous transactions yet."
        await res_msg.update()