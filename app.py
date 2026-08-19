import os
import time
import json
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

CLIENT_ID = os.environ.get("ACTION1_API_TOKEN") 
CLIENT_SECRET = os.environ.get("ACTION1_CLIENT_SECRET")
ORG_ID = os.environ.get("ACTION1_ORG_ID")

CACHE_FILE = "/tmp/action1_token_cache.json"

def read_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"token": None, "expires_at": 0, "retry_after": 0}

def write_cache(data):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[CACHE ERROR] Could not write cache: {e}")

def get_action1_token():
    now = time.time()
    cache = read_cache()

    # 1. Reuse valid token if available
    if cache.get("token") and now < cache.get("expires_at", 0):
        return cache["token"]

    # 2. Block outbound requests if currently in a rate-limit cooldown
    if now < cache.get("retry_after", 0):
        return None

    token_url = "https://app.eu.action1.com/api/3.0/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        res = requests.post(token_url, data=payload, headers=headers)
        res.raise_for_status()
        data = res.json()
        
        access_token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)
        
        write_cache({
            "token": access_token,
            "expires_at": now + expires_in - 60,
            "retry_after": 0
        })
        return access_token
        
    except requests.exceptions.HTTPError as e:
        retry_seconds = 300  # Default 5-minute cooldown on error
        try:
            err_data = e.response.json()
            retry_seconds = err_data.get("details", {}).get("retry_after", 300)
        except Exception:
            pass

        print(f"[AUTH ERROR] Rate limit or HTTP error. Backing off for {retry_seconds}s.")
        write_cache({
            "token": None,
            "expires_at": 0,
            "retry_after": now + retry_seconds
        })
        return None
    except Exception as e:
        print(f"[AUTH ERROR] Unexpected error: {e}")
        write_cache({"token": None, "expires_at": 0, "retry_after": now + 300})
        return None

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Action1 Status</title>
    <style>
        html, body { height: 100%; margin: 0; padding: 0; box-sizing: border-box; background-color: #000000; overflow: hidden; }
        body { font-family: -apple-system, sans-serif; color: #f1f5f9; padding: 3px; display: flex; flex-direction: column; align-items: center; }
        .container { width: 100%; max-width: 161px; height: 100%; display: flex; flex-direction: column; }
        .endpoint-list { background: #000000; border-radius: 4px; overflow: hidden; border: 1px solid #334155; padding: 2px; margin: 0; list-style: none; height: 100%; display: flex; flex-direction: column; justify-content: space-between; }
        .endpoint-item { padding: 1px; display: flex; flex-direction: column; flex: 1; min-height: 0; }
        .endpoint-box { display: flex; align-items: center; justify-content: center; height: 100%; padding: 2px 4px; border-radius: 3px; font-weight: 700; font-size: 8pt; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: center; }
        .box-connected { background-color: #22c55e; color: #ffffff; border: 1px solid #000000; }
        .box-disconnected { background-color: #4c0519; color: #fb7185; border: 1px solid #e11d48; }
        .empty-state { text-align: center; color: #64748b; padding: 15px; font-size: 8pt; }
    </style>
</head>
<body>
    <div class="container">
        <ul class="endpoint-list">
            {% for ep in endpoints %}
            <li class="endpoint-item">
                <span class="endpoint-box {% if ep.status.lower() == 'connected' %}box-connected{% else %}box-disconnected{% endif %}" title="{{ ep.name }}">
                    {{ ep.name }}
                </span>
            </li>
            {% else %}
            <li class="empty-state">None.</li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>"""

@app.route("/")
def index():
    endpoints = []
    token = get_action1_token()
    
    if token:
        data_url = f"https://app.eu.action1.com/api/3.0/endpoints/managed/{ORG_ID}"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        try:
            response = requests.get(data_url, headers=headers)
            response.raise_for_status()
            endpoints = response.json().get("items", [])
            endpoints.sort(key=lambda x: str(x.get("name", "")).lower())
        except Exception as e:
            print(f"[DATA ERROR] Failed to fetch endpoints: {e}")

    return render_template_string(HTML_TEMPLATE, endpoints=endpoints)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
