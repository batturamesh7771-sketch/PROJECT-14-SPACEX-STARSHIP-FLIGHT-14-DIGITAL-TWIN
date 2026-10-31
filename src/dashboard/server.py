"""
Local Web Server for Phase 10: Digital Engineering Spatial Dashboard.
Starship Flight 14 Digital Engineering Lab.

Serves static dashboard web application files (HTML/CSS/JS/Vendor)
and auto-refreshes data bundle prior to serving.
"""

import os
import sys
import argparse
import http.server
import socketserver
import traceback
from typing import Optional

from src.dashboard.adapter import export_dashboard_data


class DashboardRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving from the dashboard static directory."""

    def __init__(self, *args, **kwargs):
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        super().__init__(*args, directory=static_dir, **kwargs)

    def do_GET(self):
        if self.path in ("/favicon.ico", "favicon.ico"):
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()

    def end_headers(self):
        # Enable CORS and disable caching for real-time local digital engineering iteration
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()



def run_server(port: int = 8080, host: str = "127.0.0.1", export_data: bool = True) -> None:
    """
    Exports latest scenario data and starts local HTTP server.
    """
    if export_data:
        print("[Dashboard] Generating and bundling latest scenario data from Phases 1-9...")
        s_path, m_path = export_dashboard_data()
        print(f"[Dashboard] Scenario dataset bundled at {s_path}")
        print(f"[Dashboard] Manifest dataset bundled at {m_path}")

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)

    handler = DashboardRequestHandler
    # Allow port reuse to avoid 'Address already in use' during development restarts
    socketserver.TCPServer.allow_reuse_address = True

    class RobustHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

        def handle_error(self, request, client_address):
            exc_type, _, _ = sys.exc_info()
            if exc_type in (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                return
            super().handle_error(request, client_address)

    try:
        with RobustHTTPServer((host, port), handler) as httpd:
            print(f"[Dashboard] ========================================================")
            print(f"[Dashboard] STARSHIP FLIGHT 14 DIGITAL ENGINEERING SPATIAL DASHBOARD")
            print(f"[Dashboard] Serving WebGL application at: http://{host}:{port}/")
            print(f"[Dashboard] Static webroot: {static_dir}")
            print(f"[Dashboard] Press Ctrl+C to terminate server.")
            print(f"[Dashboard] ========================================================")
            while True:
                try:
                    httpd.serve_forever()
                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                    continue
    except KeyboardInterrupt:
        print("\n[Dashboard] Server stopped gracefully by user.")
    except Exception as e:
        print(f"[Dashboard] Error starting server: {e}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Starship Flight 14 Spatial Dashboard Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to serve on (default: 8080)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--no-export", action="store_true", help="Skip re-exporting scenario dataset")
    args = parser.parse_args()

    run_server(port=args.port, host=args.host, export_data=not args.no_export)
