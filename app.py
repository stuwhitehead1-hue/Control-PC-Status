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
    <title>Action1 Endpoint Status Report</title>
    <style>
        body { 
            font-family: -apple-system, sans-serif; 
            color: #f1f5f9; 
            background-color: #0f172a; 
            margin: 0; 
            padding: 15px; 
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 400px; /* Reduced container size to keep elements compact */
        }
        .summary-cards { 
            display: flex; 
            gap: 10px; 
            margin-bottom: 15px; 
        }
        .card { 
            flex: 1; 
            background: #1e293b; 
            padding: 12px; 
            border-radius: 8px; 
            border: 1px solid #334155; 
        }
        .card.connected { border-left: 4px solid #10b981; }
        .card.disconnected { border-left: 4px solid #f43f5e; }
        .card-title { 
            font-size: 8.5pt; 
            text-transform: uppercase; 
            color: #94a3b8; 
            font-weight: 600; 
            margin-bottom: 3px;
        }
        .card-value { 
            font-size: 16pt; 
            font-weight: 700; 
            color: #f8fafc;
        }
        
        /* Replaced traditional table with a highly dense list layout */
        .endpoint-list {
            background: #1e293b; 
            border-radius: 8px; 
            overflow: hidden;
            border: 1px solid #334155; 
            padding: 0;
            margin: 0;
            list-style: none;
        }
        .endpoint-item {
            display: flex;
            align-items: center;
            justify-content: flex-start; /* Forces items to bundle to the left */
            gap: 12px; /* Small, fixed gap between the name and status badge */
            padding: 10px 14px; 
            border-bottom: 1px solid #334155;
        }
        .endpoint-item:last-child {
            border-bottom: none;
        }
        .endpoint-item:nth-child(even) {
            background-color: #182235;
        }
        .endpoint-name {
            color: #f8fafc;
            font-weight: bold;
            font-size: 10pt;
            white-space: nowrap;
        }
        .badge { 
            display: inline-block; 
            padding: 2px 8px; 
            font-size: 7.5pt; 
            font-weight: 600; 
            border-radius: 12px; 
            text-align: center;
            white-space: nowrap;
        }
        .badge-connected { 
            background-color: #064e3b; 
            color: #34d399; 
            border: 1px solid #059669;
        }
        .badge-disconnected { 
            background-color: #4c0519; 
            color: #fb7185; 
            border: 1px solid #e11d48;
        }
        .empty-state {
            text-align: center; 
            color: #64748b; 
            padding: 30px;
            font-size: 10pt;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="summary-cards">
            <div class="card connected"><div class="card-title">Connected</div><div class="card-value" style="color:#34d399;">{{ connected }}</div></div>
            <div class="card disconnected"><div class="card-title">Disconnected</div><div class="card-value" style="color:#fb7185;">{{ disconnected }}</div></div>
        </div>
        
        <ul class="endpoint-list">
            {% for ep in endpoints %}
            <li class="endpoint-item">
                <span class="endpoint-name">{{ ep.name }}</span>
                <span class="badge {% if ep.status.lower() == 'connected' %}badge-connected{% else %}badge-disconnected{% endif %}">
                    {{ ep.status.upper() }}
                </span>
            </li>
            {% else %}
            <li class="empty-state">
                No endpoints found. Check server configuration logs.
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

    total = len(endpoints)
    connected = len([e for e in endpoints if str(e.get("status")).lower() == "connected"])
    disconnected = total - connected

    return render_template_string(
        HTML_TEMPLATE, 
        endpoints=endpoints, 
        connected=connected, disconnected=disconnected
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
