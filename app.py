import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import parse_qs, urlsplit
from pm import add_note, add_task, ask, create_project, database, summary


def make_handler(path):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, code, body):
            payload = json.dumps(body).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload)

        def do_GET(self):
            parsed = urlsplit(self.path)
            parts = parsed.path.strip("/").split("/")
            try:
                with database(path) as con:
                    if parsed.path == "/ask":
                        return self.respond(200, ask(con, parse_qs(parsed.query).get("q", [""])[0]))
                    if len(parts) == 2 and parts[0] == "projects":
                        value = summary(con, int(parts[1]))
                        return self.respond(200 if value else 404, value or {"error":"not found"})
                self.respond(404, {"error":"not found"})
            except (ValueError, TypeError) as exc: self.respond(400, {"error":str(exc)})

        def do_POST(self):
            parts = self.path.strip("/").split("/")
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > 16384: raise ValueError("invalid body length")
                data = json.loads(self.rfile.read(length))
                with database(path) as con:
                    if parts == ["projects"]:
                        return self.respond(201, {"id":create_project(con,data["name"],data["budget"])})
                    if len(parts) == 3 and parts[0] == "projects" and parts[2] == "tasks":
                        return self.respond(201, {"id":add_task(con,int(parts[1]),data["title"],data["cost"],data.get("status","todo"))})
                    if len(parts) == 3 and parts[0] == "projects" and parts[2] == "notes":
                        return self.respond(201, {"id":add_note(con,int(parts[1]),data["body"])})
                self.respond(404, {"error":"not found"})
            except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc: self.respond(400, {"error":str(exc)})
    return Handler


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="projects.db")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(args.db)).serve_forever()

