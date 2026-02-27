import chainlit as cl
import requests
import json
import re
import os
from datetime import datetime
from supabase import create_client
from huggingface_hub import InferenceClient

# -------------------------
# ENVIRONMENT VARIABLES
# -------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
HF_TOKEN = os.environ.get("HF_TOKEN")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Please set SUPABASE_URL and SUPABASE_KEY as environment variables.\n"
        "PowerShell example:\n"
        "  setx SUPABASE_URL \"https://your-project.supabase.co\"\n"
        "  setx SUPABASE_KEY \"your_anon_or_service_key\""
    )

if not HF_TOKEN:
    raise RuntimeError(
        "Please set HF_TOKEN as an environment variable.\n"
        "Get your token from: https://huggingface.co/settings/tokens\n"
        "PowerShell example:\n"
        "  setx HF_TOKEN \"hf_your_token_here\""
    )

# -------------------------
# SUPABASE CLIENT
# -------------------------
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TABLE_NAME = "transactions_ai"  # Make sure this table exists in Supabase

# -------------------------
# HUGGING FACE CONFIG
# -------------------------
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"
hf_client = InferenceClient(api_key=HF_TOKEN)

# -------------------------
# EXTRACT TRANSACTION
# -------------------------
# -------------------------
# EXTRACT TRANSACTION
# -------------------------
async def extract_transaction(user_input: str) -> dict:
    prompt = f"Extract JSON with fields: amount (number), type (expense/revenue), category (string). Text: {user_input}\nRespond with valid JSON only."
    try:
        print(f"DEBUG: Calling Hugging Face with model {HF_MODEL}", flush=True)
        response = hf_client.text_generation(
            prompt,
            model=HF_MODEL,
            max_new_tokens=200,
            temperature=0.3
        )
        print(f"DEBUG: HF response: {response}", flush=True)
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            # Ensure keys
            data.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
            data.setdefault("amount", None)
            data.setdefault("type", "expense")
            data.setdefault("category", "Other")
            data.setdefault("description", user_input)
            return data
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse response JSON: {e}", flush=True)
    except Exception as e:
        print(f"ERROR: HF API error: {e}", flush=True)

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
# STREAM INSIGHTS VIA HUGGING FACE
# -------------------------
async def call_hf_stream(prompt: str, msg_element: cl.Message):
    """
    Get insights from Hugging Face and update Chainlit message.
    """
    try:
        print(f"DEBUG: Calling HF for insights", flush=True)
        response = hf_client.text_generation(
            prompt,
            model=HF_MODEL,
            max_new_tokens=500,
            temperature=0.7
        )
        msg_element.content += response
        await msg_element.update()
        return response
    except Exception as e:
        print(f"ERROR: HF stream failed: {e}", flush=True)
        msg_element.content += f"\n[Error generating insight: {e}]"
        await msg_element.update()
        return f"Error: {str(e)}"

# -------------------------
# CHAINLIT EVENTS
# -------------------------
@cl.on_chat_start
async def start():
    print("DEBUG: Chat started", flush=True)
    # Test HF connectivity
    try:
        await cl.Message(content="✅ Hugging Face connected. ⚡ Hackathon Mode Active. Transactions go directly to Supabase!").send()
    except Exception as e:
        await cl.Message(content=f"⚠️ Error: {e}").send()

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
        await call_hf_stream(insight_prompt, res_msg)
    else:
        res_msg.content += "No previous transactions yet."
        await res_msg.update()