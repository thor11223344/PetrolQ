import os
import sys
import threading
import time
import requests
import uvicorn
from contextlib import contextmanager

# 1. Monkey-patch socket to block non-localhost outbound traffic
import socket
original_socket = socket.socket
class OfflineSocket(original_socket):
    def connect(self, address):
        # address is usually (host, port)
        if isinstance(address, tuple):
            host = address[0]
            if host not in ("127.0.0.1", "::1", "localhost"):
                raise OSError(f"Network is offline. Blocked connection to {host}")
        return super().connect(address)

socket.socket = OfflineSocket

# We must ensure the backend is imported AFTER patching
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def test_offline_search():
    print("Importing backend.main (this might take a few minutes as HF retries offline)...")
    from backend.main import app
    print("Backend imported successfully. Starting server...")
    
    server_thread = threading.Thread(target=lambda: uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error"), daemon=True)
    server_thread.start()
    
    # Wait for server to boot
    time.sleep(3)
    
    print("Testing offline /api/events/search endpoint...")
    try:
        response = requests.get("http://127.0.0.1:8001/api/events/search", params={"query": "stuck pipe"}, timeout=60)
        print(f"Status Code: {response.status_code}")
        print("Response:", response.json())
    except Exception as e:
        print("Test failed with error:", repr(e))

if __name__ == "__main__":
    test_offline_search()
