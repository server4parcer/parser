#!/usr/bin/env python3
"""ABSOLUTE SIMPLEST - Hello World HTTP Server"""
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        if self.path == '/health':
            response = b'{"status": "ok", "hello": "world"}'
        else:
            response = b'<h1>Hello World!</h1><p>TimeWeb deployment test</p>'
        
        self.wfile.write(response)
    
    def log_message(self, format, *args):
        # Print to stdout so we can see in TimeWeb logs
        print(f"REQUEST: {format % args}")

if __name__ == '__main__':
    port = 8000  # Fixed port, no environment variables
    print(f"=== STARTING HELLO WORLD SERVER ON PORT {port} ===")
    print(f"=== ENDPOINTS: / and /health ===")
    
    try:
        server = HTTPServer(('0.0.0.0', port), SimpleHandler)
        print(f"=== SERVER RUNNING SUCCESSFULLY ===")
        server.serve_forever()
    except Exception as e:
        print(f"=== ERROR STARTING SERVER: {e} ===")
        exit(1)
