"""Local preview server for the ScriptLens waitlist landing page.

Serves static files and handles waitlist POSTs the same way submit.php does
on Hostinger. Production still uses submit.php on the host.

Usage:
    venv\\Scripts\\python.exe landing/serve.py
Then open http://127.0.0.1:8765/
"""

from __future__ import annotations

import csv
import re
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

LANDING_DIR = Path(__file__).resolve().parent
WAITLIST_FILE = LANDING_DIR / "waitlist.csv"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HOST = "127.0.0.1"
PORT = 8765


def append_email(email: str, ip: str, user_agent: str) -> None:
    """Append a waitlist row to waitlist.csv, skipping duplicates."""
    email_norm = email.strip().lower()
    if WAITLIST_FILE.exists():
        with WAITLIST_FILE.open(newline="", encoding="utf-8") as fh:
            for row in csv.reader(fh):
                if row and row[0].strip().lower() == email_norm:
                    return
    else:
        with WAITLIST_FILE.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["email", "subscribed_at", "ip", "user_agent"])

    with WAITLIST_FILE.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                email_norm,
                datetime.now(timezone.utc).isoformat(),
                ip[:64],
                user_agent[:200],
            ]
        )


class LandingHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves the landing folder and accepts waitlist posts."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(LANDING_DIR), **kwargs)

    def do_POST(self) -> None:
        """Handle waitlist form posts to submit.php."""
        if self.path.split("?", 1)[0] not in ("/submit.php", "/submit"):
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        form = parse_qs(raw, keep_blank_values=True)

        honeypot = (form.get("website") or [""])[0].strip()
        if honeypot:
            self._redirect("/thank-you.html")
            return

        email = (form.get("email") or [""])[0].strip()
        if not email or not EMAIL_RE.match(email):
            self._redirect("/index.html?error=1")
            return

        ip = self.client_address[0] if self.client_address else ""
        ua = self.headers.get("User-Agent", "")
        try:
            append_email(email, ip, ua)
        except OSError:
            self._redirect("/index.html?error=1")
            return

        self._redirect("/thank-you.html")

    def _redirect(self, location: str) -> None:
        """Send a 303 redirect to location."""
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        """Print concise request logs."""
        print(f"[{self.log_date_time_string()}] {format % args}")


def main() -> None:
    """Start the local waitlist preview server."""
    server = ThreadingHTTPServer((HOST, PORT), LandingHandler)
    print(f"ScriptLens waitlist preview: http://{HOST}:{PORT}/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
