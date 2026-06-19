import os
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

# Pull variables securely from Render dashboard
CLIENT_ID = os.environ.get("ACTION1_API_TOKEN") # This is your Client ID
CLIENT_SECRET = os.environ.get("ACTION1_CLIENT_SECRET") # Add this secret on Render!
ORG_ID = os.environ.get("ACTION1_ORG_ID")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Action1 Endpoint Status Report</title>
    <style>
        body { font-family: -apple-system, sans-serif; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 20px; }
        .header-container { background-color: #0f172a; color: white; padding: 20px; border-bottom: 4px solid #0284c7; border-radius: 6px 6px 0 0; }
        .summary-cards { display: flex; gap: 15px; margin: 20px 0; }
        .card { flex: 1; background: white; padding: 15px; border-radius: 6px; border: 1px solid #e2e8f0; }
        .card.connected { border-left: 4px solid #10b981; }
        .card.disconnected { border-left: 4px solid #ef4444; }
        .card-title { font-size: 9pt; text-transform: uppercase; color: #64748b; font-weight: 600; }
        .card-value { font-size: 18pt; font-weight: 700; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 6px; border: 1px solid #e2e8f0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
        th { background-color: #f1f5f9; color: #334155; font-weight: 600; }
        .badge { display: inline-block; padding: 2px 8px; font-size: 8.5pt; font-weight: 600; border-radius: 12px; }
        .badge-connected { background-color: #d1fae5; color: #065f46; }
        .badge-disconnected { background-color: #fee2e2; color: #991b1b; }
    </style>
</head>
<body>
    <div class="header-container">
        <h1>Action1 Endpoint Status Overview</h1>
        <p>Live Connected Inventory Dashboard</p>
    </div>
    <div class="summary-cards">
        <div class="card"><div class="card-title">Total Endpoints</div><div class="card-value">{{ total }}</div></div>
        <div class="card connected"><div class="card-title">Connected</div><div class="card-value" style="color:#10b981;">{{ connected }}</div></div>
        <div class="card disconnected"><div class="card-title">Disconnected</div><div class="card-value" style="color:#ef4444;">{{ disconnected }}</div></div>
        <div class="card"><div class="card-title">Online Rate</div><div class="card-value">{{ online_rate }}%</div></div>
    </div>
    <table>
        <thead>
            <tr><th>Endpoint Name</th><th>IP Address</th><th>OS Version</th><th>Last Seen</th><th>Status</th></tr>
        </thead>
        <tbody>
            {% for ep in endpoints %}
            <tr>
                <td><strong>{{ ep.name }}</strong></td>
                <td>{{ ep.ip_address }}</td>
                <td>{{ ep.os_version }}</td>
                <td>{{ ep.last_seen }}</td>
                <td>
                    <span class="badge {% if ep.status.lower() == 'connected' %}badge-connected{% else %}badge-disconnected{% endif %}">
                        {{ ep.status.upper() }}
                    </span>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="5" style="text-align: center; color: #64748b; padding: 30px;">
                    No endpoints found. Check server configuration logs.
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>"""

def get_action1_token():
    """Exchanges Client ID and Secret for an active Session Token"""
    token_url = "https://app.action1.com/api/3.0/oauth2/token"
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
        # Pull managed endpoints using the fresh token
        data_url = f"https://app.action1.com/api/3.0/endpoints/managed/{ORG_ID}"
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
    online_rate = round((connected / total) * 100, 1) if total > 0 else 0

    return render_template_string(
        HTML_TEMPLATE, 
        endpoints=endpoints, total=total, 
        connected=connected, disconnected=disconnected, online_rate=online_rate
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
