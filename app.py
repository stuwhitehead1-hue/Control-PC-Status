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
        body { 
            font-family: -apple-system, sans-serif; 
            color: #f1f5f9; 
            background-color: #0f172a; 
            margin: 0; 
            padding: 2px; /* Tightened padding to maximize space */
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 153px; /* Slightly adjusted to fit a 157px view nicely */
        }
        .endpoint-list {
            background: #1e293b; 
            border-radius: 4px; 
            overflow: hidden;
            border: 1px solid #334155; 
            padding: 0;
            margin: 0;
            list-style: none;
            max-height: 655px; /* Optimized precisely for your 665px display height */
            overflow-y: auto; 
        }
        .endpoint-item {
            display: flex;
            align-items: center;
            padding: 5px 6px; /* Reduced vertical padding to fit more items on screen */
            border-bottom: 1px solid #334155;
        }
        .endpoint-item:last-child {
            border-bottom: none;
        }
        .endpoint-item:nth-child(even) {
            background-color: #182235;
        }
        
        .status-dot {
            width: 6px; /* Slightly smaller dot */
            height: 6px;
            border-radius: 50%;
            margin-right: 6px;
            flex-shrink: 0;
        }
        .dot-connected {
            background-color: #34d399;
            box-shadow: 0 0 4px #10b981;
        }
        .dot-disconnected {
            background-color: #fb7185;
            box-shadow: 0 0 4px #f43f5e;
        }

        .endpoint-name {
            color: #f8fafc;
            font-weight: 600;
            font-size: 8pt; /* Slightly smaller text font to maximize horizontal room */
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            flex-grow: 1;
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
                <span class="status-dot {% if ep.status.lower() == 'connected' %}dot-connected{% else %}dot-disconnected{% endif %}"></span>
                <span class="endpoint-name" title="{{ ep.name }}">{{ ep.name }}</span>
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
