"""
Web interface for the Text-to-SQL chatbot (standard library only).
Run locally: python server.py, then open http://localhost:8000
"""

import ast
import os
import time
from collections import defaultdict, deque
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from engine import ask

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Text-to-SQL Chatbot</title>
<style>
  :root {
    --bg: #f6f7fb; --card: #ffffff; --text: #1c1f2a; --muted: #6b7280;
    --border: #e5e7eb; --accent: #4f46e5; --accent-hover: #4338ca;
    --code-bg: #0f172a; --code-text: #e2e8f0; --err-bg: #fef2f2; --err-text: #b91c1c;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0b1020; --card: #151b2e; --text: #e5e7eb; --muted: #9ca3af;
      --border: #263049; --accent: #818cf8; --accent-hover: #a5b4fc;
      --code-bg: #060a16; --code-text: #e2e8f0; --err-bg: #3b1519; --err-text: #fca5a5;
    }
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--text);
         font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif; line-height: 1.5; }
  .wrap { max-width: 820px; margin: 0 auto; padding: 40px 16px 60px; }
  header { text-align: center; margin-bottom: 28px; }
  h1 { margin: 0 0 6px; font-size: 2rem; }
  .sub { color: var(--muted); margin: 0; }
  .badges { margin-top: 12px; display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }
  .badge { font-size: 12px; padding: 4px 10px; border-radius: 999px;
           border: 1px solid var(--border); color: var(--muted); background: var(--card); }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 14px;
          padding: 20px; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(0,0,0,.05); }
  form { display: flex; gap: 10px; }
  input[type=text] { flex: 1; padding: 13px 14px; font-size: 16px; border-radius: 10px;
                     border: 1px solid var(--border); background: var(--bg); color: var(--text); outline: none; }
  input[type=text]:focus { border-color: var(--accent); }
  button.ask { padding: 13px 22px; font-size: 16px; border: 0; border-radius: 10px;
               background: var(--accent); color: #fff; cursor: pointer; font-weight: 600; }
  button.ask:hover { background: var(--accent-hover); }
  button.ask:disabled { opacity: .7; cursor: wait; }
  .chips { margin-top: 14px; display: flex; flex-wrap: wrap; gap: 8px; }
  .chip { font-size: 13px; padding: 6px 12px; border-radius: 999px; cursor: pointer;
          border: 1px solid var(--border); background: var(--bg); color: var(--text); }
  .chip:hover { border-color: var(--accent); color: var(--accent); }
  .label { font-size: 12px; text-transform: uppercase; letter-spacing: .06em;
           color: var(--muted); margin: 0 0 8px; font-weight: 600; }
  .answer { font-size: 18px; margin: 0; }
  pre { margin: 0; background: var(--code-bg); color: var(--code-text); padding: 14px;
        border-radius: 10px; overflow-x: auto; font-size: 14px; }
  .table-wrap { overflow-x: auto; }
  table { border-collapse: collapse; width: 100%; font-size: 14px; }
  td { border: 1px solid var(--border); padding: 8px 12px; }
  tr:nth-child(even) td { background: var(--bg); }
  .error { background: var(--err-bg); color: var(--err-text); border-radius: 10px; padding: 14px; }
  .spinner { display: none; width: 18px; height: 18px; margin: 14px auto 0;
             border: 3px solid var(--border); border-top-color: var(--accent);
             border-radius: 50%; animation: spin .8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  footer { text-align: center; color: var(--muted); font-size: 13px; margin-top: 30px; }
  @media (max-width: 520px) { form { flex-direction: column; } }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Text-to-SQL Chatbot</h1>
    <p class="sub">Ask a question in plain English and get the SQL query and the answer.</p>
    <div class="badges">
      <span class="badge">Python</span><span class="badge">SQLite</span>
      <span class="badge">Groq LLM</span><span class="badge">Read-only (SELECT only)</span>
    </div>
  </header>

  <div class="card">
    <form method="post" id="f">
      <input type="text" name="q" id="q" value="__QUESTION__"
             placeholder="Which customer spent the most?" autocomplete="off" required>
      <button class="ask" type="submit" id="btn">Ask</button>
    </form>
    <div class="chips">
      <button class="chip" type="button">Which customer spent the most?</button>
      <button class="chip" type="button">How many customers are there?</button>
      <button class="chip" type="button">Total sales by city</button>
      <button class="chip" type="button">Orders above 10000</button>
      <button class="chip" type="button">Delete all orders</button>
    </div>
    <div class="spinner" id="sp"></div>
  </div>

  __OUTPUT__

  <footer>Built by Shailja Pandey &middot; Sample shop database &middot; Only SELECT queries run</footer>
</div>
<script>
  var f = document.getElementById("f"), q = document.getElementById("q"),
      btn = document.getElementById("btn"), sp = document.getElementById("sp");
  document.querySelectorAll(".chip").forEach(function (c) {
    c.addEventListener("click", function () { q.value = c.textContent; f.requestSubmit(); });
  });
  f.addEventListener("submit", function () {
    btn.disabled = true; btn.textContent = "Thinking..."; sp.style.display = "block";
  });
</script>
</body>
</html>"""

HITS = defaultdict(deque)


def rate_limited(ip, limit=10, window=60):
    now = time.time()
    hits = HITS[ip]
    while hits and now - hits[0] > window:
        hits.popleft()
    if len(hits) >= limit:
        return True
    hits.append(now)
    return False


def render_result(result):
    if result is None or str(result).strip() in ("", "None"):
        return ""
    try:
        rows = ast.literal_eval(result) if isinstance(result, str) else result
    except Exception:
        rows = None
    if isinstance(rows, list) and rows and all(isinstance(r, (tuple, list)) for r in rows):
        body = "".join(
            "<tr>" + "".join("<td>" + escape(str(c)) + "</td>" for c in r) + "</tr>" for r in rows
        )
        inner = '<div class="table-wrap"><table>' + body + "</table></div>"
    else:
        inner = "<pre>" + escape(str(result)) + "</pre>"
    return '<div class="card"><p class="label">Query result</p>' + inner + "</div>"


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
        question = parse_qs(body).get("q", [""])[0].strip()[:300]

        ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
        output = ""
        if question:
            if rate_limited(ip):
                output = '<div class="card error">Too many questions. Please wait a minute and try again.</div>'
            else:
                try:
                    sql, result, answer = ask(question)
                    output = (
                        '<div class="card"><p class="label">Answer</p><p class="answer">'
                        + escape(str(answer)) + "</p></div>"
                        '<div class="card"><p class="label">Generated SQL</p><pre>'
                        + escape(str(sql)) + "</pre></div>"
                        + render_result(result)
                    )
                except Exception as e:
                    output = '<div class="card error">Something went wrong: ' + escape(str(e)[:200]) + "</div>"
        self._send_page(question, output)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0" if os.environ.get("PORT") else "localhost"
    print(f"Server running on http://{host}:{port} (Ctrl+C to stop).")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
