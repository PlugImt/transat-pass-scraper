#!/bin/bash

# Start cron service
service cron start

# Optional: Start a simple health check server
python3 -c "
import http.server
import socketserver
import threading
import time

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{\"status\": \"healthy\", \"service\": \"scraper\"}')
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server():
    with socketserver.TCPServer(('', 8080), HealthHandler) as httpd:
        httpd.serve_forever()

# Start health server in background
health_thread = threading.Thread(target=start_health_server, daemon=True)
health_thread.start()

print('Scraper container started. Cron scheduled for 6:00 AM daily.')
print('Health check available at http://localhost:8080/health')

# Keep container running
while True:
    time.sleep(60)
" &

# Keep the container running
tail -f /dev/null
