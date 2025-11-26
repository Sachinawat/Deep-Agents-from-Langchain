import os
import requests
import msal
from fastapi import FastAPI, Request
from openai import OpenAI
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ====== LOAD FROM .env ======
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# ============================

client = OpenAI(api_key=OPENAI_API_KEY)

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

app = FastAPI()

def get_token():
    app_ctx = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
    )
    token = app_ctx.acquire_token_for_client(scopes=SCOPE)
    return token.get("access_token")

def send_email(subject, body, to_email, reply_to_id=None):
    access_token = get_token()
    url = f"https://graph.microsoft.com/v1.0/users/{SENDER_EMAIL}/sendMail"

    message = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body},
            "toRecipients": [{"emailAddress": {"address": to_email}}],
        },
        "saveToSentItems": True,
    }

    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=message)
    print(response.status_code, response.text)  # Add this line for debugging

def generate_reply(user_message):
    prompt = f"Write a helpful and polite reply to this email:\n\n{user_message}\n\nResponse:"
    result = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return result.choices[0].message.content

@app.post("/incoming-email")
async def incoming_email(request: Request):
    data = await request.json()
    message_id = data["id"]
    sender_email = data["sender"]
    text = data["text"]

    ai_reply = generate_reply(text)
    send_email("Re: Thanks for your reply!", ai_reply, sender_email, reply_to_id=message_id)

    return {"status": "replied successfully"}

@app.post("/send-initial-email")
async def send_initial_email():
    subject = "Hello from Sachin Awati"
    body = "Hi, this is an initial email sent automatically."
    to_email = "abc021@gmail.com"
    send_email(subject, body, to_email)
    return {"status": "initial email sent"}
