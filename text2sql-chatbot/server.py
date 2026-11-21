"""
Web interface for the Text-to-SQL chatbot.

Uses only Python's standard library, so no additional packages are required.
Run with: python server.py, then open http://localhost:8000
"""

from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from engine import ask

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Text-to-SQL Chatbot</title>
<style>
  body { font-family: Arial, sans-serif; max-width: 760px; margin: 40px auto; padding: 0 16px; color: #222; }
  h1 { margin-bottom: 4px; }
  p.sub { color: #666; margin-top: 0; }
  input[type=text] { width: 75%; padding: 10px; font-size: 16px; }
  button { padding: 10px 18px; font-size: 16px; cursor: pointer; }
  pre { background: #f3f3f3; padding: 12px; border-radius: 6px; overflow-x: auto; }
  h3 { margin-bottom: 6px; }
</style>
</head>
<body>
<h1>Text-to-SQL Chatbot</h1>
<p class="sub">Ask a question in plain English. Only SELECT queries are permitted.</p>
<form method="post">
  <input type="text" name="q" value="__QUESTION__" placeholder="Which customer spent the most?">
  <button type="submit">Ask</button>
</form>
__OUTPUT__
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def _send_page(self, question="", output=""):
        html = PAGE.replace("__QUESTION__", escape(question, quote=True)).replace("__OUTPUT__", output)
        data = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send_page()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        question = parse_qs(body).get("q", [""])[0].strip()

        output = ""
        if question:
            sql, result, answer = ask(question)
            output = (
                "<h3>Answer</h3><p>" + escape(str(answer)) + "</p>"
                "<h3>Generated SQL</h3><pre>" + escape(sql) + "</pre>"
                "<h3>Query Result</h3><pre>" + escape(str(result)) + "</pre>"
            )
        self._send_page(question, output)


if __name__ == "__main__":
    print("Server running. Open http://localhost:8000 in your browser (Ctrl+C to stop).")
    HTTPServer(("localhost", 8000), Handler).serve_forever()