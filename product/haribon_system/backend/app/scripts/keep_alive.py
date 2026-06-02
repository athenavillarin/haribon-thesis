import requests
import os
from datetime import datetime

RENDER_APP_URL = os.getenv("RENDER_APP_URL", "https://haribon-app.onrender.com")

def keep_alive():
    try:
        response = requests.get(f"{RENDER_APP_URL}/api/summary/overview", timeout=5)
        # Any HTTP response = app is awake (even 404). Only timeouts/exceptions = app is asleep
        print(f"[KEEP-ALIVE] Service awake at {datetime.now()} (status: {response.status_code})")
    except requests.exceptions.Timeout:
        print(f"[KEEP-ALIVE] Timeout - app may be sleeping")
    except Exception as e:
        print(f"[KEEP-ALIVE] Connection failed - app may be asleep: {e}")

if __name__ == "__main__":
    keep_alive()