#!/usr/bin/env python3
"""Launch script for KidsColorAI desktop application"""
import os
import sys
import webbrowser
import time

import uvicorn

from app.main import app, APP_VERSION, APP_DATETIME


def main():
    port = int(os.getenv("FASTAPI_PORT", 8046))

    print(f"Starting KidsColorAI v{APP_VERSION}...")

    def open_browser():
        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{port}")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()