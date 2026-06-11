"""
MR. HYRE - Production / Development WSGI Server Entry Point
Author: Human Written & Optimized
"""

import os
from app import create_app

config_name = os.environ.get("FLASK_CONFIG", "development")
app = create_app(config_name)

if __name__ == "__main__":
    print(f"[+] Starting Mr. Hyre Backend Server in [{config_name.upper()}] mode...")
    app.run(host="127.0.0.1", port=5000, debug=(config_name == "development"))