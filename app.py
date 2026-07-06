import os
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

# Pull variables securely from Render dashboard
CLIENT_ID = os.environ.get("ACTION1_API_TOKEN") # Your Client ID
CLIENT_SECRET = os.environ.get("ACTION1_CLIENT_SECRET") # Your Client Secret
ORG_ID = os.environ.get("ACTION1_ORG_ID")

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
            background-color: #000000; /* Changed outside background to pure black */
            overflow: hidden; /* Total lock on scrolling */
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
            background: #000000; /* Also made the list container background black for consistency */
            border-radius: 4px; 
            overflow: hidden;
            border: 1px solid #334155; 
            padding: 2px; 
            margin: 0;
            list-style: none;
            
            /* Fill container completely and act as a flex column parent */
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .endpoint-item {
            padding: 1px;
            display: flex;
            flex-direction: column;
            
            /* Forces rows to automatically shrink or grow evenly to fill the 572px frame */
            flex: 1; 
            min-height: 0; 
        }
        
        .endpoint-box {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%; /* Spans the entire dynamically calculated row height */
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
            background-color: #22c55e; /* Bright green matching screenshot */
            color: #ffffff;            /* Solid white text */
            border: 1px solid #000000; /* Dark separator borders */
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
    """Exchanges Client ID and Secret for an active Session Token on the EU cluster"""
    token_url = "https://app.eu.action1.com/api/3.0/oauth2/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    try:
        res = requests.post(token_url, data=payload, headers=headers)
        res.raise_for_status()
        return res.json().get("access_token")
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
            
            # Sort endpoints alphabetically (case-insensitive) by the "name" key
            endpoints.sort(key=lambda x: str(x.get("name", "")).lower())
            
        except Exception as e:
            print(f"[DATA ERROR] Failed to fetch endpoints from Action1: {e}")

    return render_template_string(HTML_TEMPLATE, endpoints=endpoints)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
