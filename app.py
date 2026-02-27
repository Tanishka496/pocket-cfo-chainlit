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

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Please set SUPABASE_URL and SUPABASE_KEY as environment variables.\n"
        "PowerShell example:\n"
        "  setx SUPABASE_URL \"https://your-project.supabase.co\"\n"
        "  setx SUPABASE_KEY \"your_anon_or_service_key\""
    )

# -------------------------
# SUPABASE CLIENT
# -------------------------
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TABLE_NAME = "transactions_ai"  # Make sure this table exists in Supabase

# -------------------------
# OLLAMA CONFIG
# -------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"  # faster than default

# -------------------------
# EXTRACT TRANSACTION
# -------------------------
async def extract_transaction(user_input: str) -> dict:
    prompt = f"JSON only: {{amount, type, category}}. Text: {user_input}"
    try:
        print(f"DEBUG: Calling Ollama at {OLLAMA_URL} with prompt: {prompt}", flush=True)
        resp = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
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
        print("ERROR: Ollama request timed out after 30s", flush=True)
    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: Cannot connect to Ollama at {OLLAMA_URL}: {e}", flush=True)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Ollama request failed: {e}", flush=True)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse Ollama response: {e}", flush=True)
    except Exception as e:
        print(f"ERROR: Unexpected error in extract_transaction: {e}", flush=True)

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
        supabase.table(TABLE_NAME).insert(record).execute()
        print("DEBUG: Transaction saved successfully", flush=True)
    except Exception as e:
        print(f"ERROR: Failed to save transaction to Supabase: {e}", flush=True)
        raise

# -------------------------
# FETCH LAST N TRANSACTIONS
# -------------------------
def get_last_transactions(limit=5):
    resp = supabase.table(TABLE_NAME).select("*").order("date", desc=True).limit(limit).execute()
    return resp.data or []

# -------------------------
# STREAM INSIGHTS VIA OLLAMA
# -------------------------
async def call_ollama_stream(prompt: str, msg_element: cl.Message):
    """
    Stream tokens from the Ollama streaming endpoint and forward them to
    the Chainlit message element. This function tolerates non-JSON or
    partial lines and will continue streaming rather than aborting on a
    single malformed chunk.
    """
    full_response = ""
    try:
        with requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": prompt, "stream": True},
            stream=True,
            timeout=None
        ) as response:
            # ensure we received a successful response
            try:
                response.raise_for_status()
            except Exception as e:
                # surface HTTP errors to the caller/UI
                await msg_element.stream_token(f"[stream http error] {e}\n")
                return f"Error: {e}"
            # iter_lines(decode_unicode=True) returns decoded strings
            for raw_line in response.iter_lines(decode_unicode=True, chunk_size=1):
                if not raw_line:
                    continue
                line = raw_line.strip()
                token = None
                # Try parsing JSON first
                try:
                    chunk = json.loads(line)
                    # different versions may put text under different keys
                    token = chunk.get("response") or chunk.get("token") or chunk.get("text")
                except Exception:
                    # fallback: try to extract a JSON object inside the line
                    m = re.search(r"\{.*\}", line)
                    if m:
                        try:
                            chunk = json.loads(m.group(0))
                            token = chunk.get("response") or chunk.get("token") or chunk.get("text")
                        except Exception:
                            token = line
                    else:
                        token = line

                if token:
                    full_response += token
                    print(f"DEBUG: token: {token}", flush=True)
                    try:
                        await msg_element.stream_token(token)
                    except Exception:
                        # If streaming tokens to Chainlit fails, continue
                        pass

            # ensure final update so UI shows full result
            try:
                await msg_element.update()
            except Exception:
                pass

        return full_response
    except Exception as e:
        try:
            await msg_element.stream_token(f"[stream error] {e}")
        except Exception:
            pass
        return f"Error: {str(e)}"

# -------------------------
# CHAINLIT EVENTS
# -------------------------
@cl.on_chat_start
async def start():
    print("DEBUG: Chat started", flush=True)
    # Test Ollama connectivity
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            await cl.Message(content="✅ Ollama connected. ⚡ Hackathon Mode Active. Transactions go directly to Supabase!").send()
        else:
            await cl.Message(content=f"⚠️ Ollama returned status {resp.status_code}. Fallback to simple extraction.").send()
    except Exception as e:
        await cl.Message(content=f"⚠️ Ollama not responding ({e}). Using fallback extraction.").send()

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
        save_transaction(data)
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