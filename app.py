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
            padding: 20px; 
        }
        .summary-cards { 
            display: flex; 
            gap: 15px; 
            margin-bottom: 20px; 
        }
        .card { 
            flex: 1; 
            background: #1e293b; 
            padding: 15px; 
            border-radius: 8px; 
            border: 1px solid #334155; 
        }
        .card.connected { border-left: 4px solid #10b981; }
        .card.disconnected { border-left: 4px solid #f43f5e; }
        .card-title { 
            font-size: 9pt; 
            text-transform: uppercase; 
            color: #94a3b8; 
            font-weight: 600; 
            margin-bottom: 5px;
        }
        .card-value { 
            font-size: 18pt; 
            font-weight: 700; 
            color: #f8fafc;
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            background: #1e293b; 
            border-radius: 8px; 
            overflow: hidden;
            border: 1px solid #334155; 
        }
        th, td { 
            padding: 14px; 
            text-align: left; 
            border-bottom: 1px solid #334155; 
        }
        th { 
            background-color: #0f172a; 
            color: #94a3b8; 
            font-weight: 600; 
            font-size: 9.5pt;
        }
        td {
            color: #cbd5e1;
        }
        tr:hover td {
            background-color: #1e293b;
        }
        tr:nth-child(even) td {
            background-color: #182235;
        }
        .badge { 
            display: inline-block; 
            padding: 4px 10px; 
            font-size: 8.5pt; 
            font-weight: 600; 
            border-radius: 12px; 
            text-align: center;
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
    </style>
</head>
<body>
    <div class="summary-cards">
        <div class="card connected"><div class="card-title">Connected</div><div class="card-value" style="color:#34d399;">{{ connected }}</div></div>
        <div class="card disconnected"><div class="card-title">Disconnected</div><div class="card-value" style="color:#fb7185;">{{ disconnected }}</div></div>
    </div>
    <table>
        <thead>
            <tr>
                <th>Endpoint Name</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for ep in endpoints %}
            <tr>
                <td><strong style="color: #f8fafc;">{{ ep.name }}</strong></td>
                <td>
                    <span class="badge {% if ep.status.lower() == 'connected' %}badge-connected{% else %}badge-disconnected{% endif %}">
                        {{ ep.status.upper() }}
                    </span>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="2" style="text-align: center; color: #64748b; padding: 30px;">
                    No endpoints found. Check server configuration logs.
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
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
