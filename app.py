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
            padding: 8px; /* Ultra-tight screen padding */
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 260px; /* Highly compressed overall footprint */
        }
        .summary-cards { 
            display: flex; 
            gap: 6px; /* Micro gaps between summary counters */
            margin-bottom: 8px; 
        }
        .card { 
            flex: 1; 
            background: #1e293b; 
            padding: 8px; /* Compact padding */
            border-radius: 6px; 
            border: 1px solid #334155; 
        }
        .card.connected { border-left: 3px solid #10b981; }
        .card.disconnected { border-left: 3px solid #f43f5e; }
        .card-title { 
            font-size: 7.5pt; 
            text-transform: uppercase; 
            color: #94a3b8; 
            font-weight: 600; 
            margin-bottom: 2px;
        }
        .card-value { 
            font-size: 13pt; 
            font-weight: 700; 
            color: #f8fafc;
        }
        
        .endpoint-list {
            background: #1e293b; 
            border-radius: 6px; 
            overflow: hidden;
            border: 1px solid #334155; 
            padding: 0;
            margin: 0;
            list-style: none;
        }
        .endpoint-item {
            display: flex;
            align-items: center;
            justify-content: space-between; /* Pushes name and badge cleanly to outer edges of the 260px container */
            padding: 8px 10px; 
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
            font-weight: 600;
            font-size: 9pt;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis; /* Safely cuts off overly long hostnames without breaking row heights */
            margin-right: 8px;
        }
        .badge { 
            display: inline-block; 
            padding: 1px 6px; 
            font-size: 7pt; 
            font-weight: 600; 
            border-radius: 10px; 
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
            padding: 20px;
            font-size: 9pt;
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
                <span class="endpoint-name" title="{{ ep.name }}">{{ ep.name }}</span>
                <span class="badge {% if ep.status.lower() == 'connected' %}badge-connected{% else %}badge-disconnected{% endif %}">
                    {{ ep.status.upper() }}
                </span>
            </li>
            {% else %}
            <li class="empty-state">
                No endpoints found.
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
