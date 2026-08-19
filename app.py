import os
import time
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

# Pull variables securely from Render environment
CLIENT_ID = os.environ.get("ACTION1_API_TOKEN") # Your Client ID
CLIENT_SECRET = os.environ.get("ACTION1_CLIENT_SECRET") # Your Client Secret
ORG_ID = os.environ.get("ACTION1_ORG_ID")

# In-memory cache to prevent Action1 429 Rate Limit errors
TOKEN_CACHE = {"token": None, "expires_at": 0}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Action1 Status</title>
    <style>
        html, body {
            height: 100%;
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            background-color: #000000;
            overflow: hidden;
        }
        body { 
            font-family: -apple-system, sans-serif; 
            color: #f1f5f9; 
            padding: 3px; 
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 161px;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .endpoint-list {
            background: #000000;
            border-radius: 4px; 
            overflow: hidden;
            border: 1px solid #334155; 
            padding: 2px; 
            margin: 0;
            list-style: none;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .endpoint-item {
            padding: 1px;
            display: flex;
            flex-direction: column;
            flex: 1; 
            min-height: 0; 
        }
        
        .endpoint-box {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            padding: 2px 4px; 
            border-radius: 3px;
            font-weight: 700;
            font-size: 8pt;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            text-align: center;
        }
        
        .box-connected {
            background-color: #22c55e;
            color: #ffffff; 
            border: 1px solid #000000;
        }
        
        .box-disconnected {
            background-color: #4c0519; 
            color: #fb7185; 
            border: 1px solid #e11d48;
        }
        
        .empty-state {
            text-align: center; 
            color: #64748b; 
            padding: 15px;
            font-size: 8pt;
        }
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
            <li class="empty-state">
                None.
            </li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>"""

def get_action1_token():
    """Fetches an Action1 token, reusing the cached token if still valid."""
    # Reuse valid token if available
    if TOKEN_CACHE["token"] and time.time() < TOKEN_CACHE["expires_at"]:
        return TOKEN_CACHE["token"]

    token_url = "https://app.eu.action1.com/api/3.0/oauth2/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    try:
        res = requests.post(token_url, data=payload, headers=headers)
        res.raise_for_status()
        data = res.json()
        
        # Cache token for its lifespan (default 3600 seconds) minus a 60s buffer
        expires_in = data.get("expires_in", 3600)
        TOKEN_CACHE["token"] = data.get("access_token")
        TOKEN_CACHE["expires_at"] = time.time() + expires_in - 60
        
        return TOKEN_CACHE["token"]
    except Exception as e:
        print(f"[AUTH ERROR] Failed to generate OAuth token: {e}")
        return None

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
            
            # Sort endpoints alphabetically (case-insensitive)
            endpoints.sort(key=lambda x: str(x.get("name", "")).lower())
            
        except Exception as e:
            print(f"[DATA ERROR] Failed to fetch endpoints from Action1: {e}")

    return render_template_string(HTML_TEMPLATE, endpoints=endpoints)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
