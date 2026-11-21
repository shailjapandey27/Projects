import os, re, json, sqlite3, urllib.request
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "openai/gpt-oss-120b"
DB_FILE = "shop.db"

def llm(prompt):
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps({
            "model": MODEL,
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
        }).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "text2sql-app/1.0",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

def get_schema():
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
    conn.close()
    return "\n".join(r[0] for r in rows if r[0])

def generate_sql(question):
    prompt = f"""You are an expert SQLite analyst.
Database schema:
{get_schema()}

Write ONE SQLite SELECT query that answers the question.
Return ONLY the SQL, no explanation, no markdown.

Question: {question}"""
    sql = llm(prompt)
    return sql.replace("```sql", "").replace("```", "").strip()

def is_safe(sql):
    banned = r"\b(drop|delete|update|insert|alter|create|truncate|replace)\b"
    return sql.lower().startswith("select") and not re.search(banned, sql.lower())

def run_sql(sql):
    # read-only connection: extra safety
    conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
    rows = conn.execute(sql).fetchall()
    conn.close()
    return rows

def ask(question):
    try:
        sql = generate_sql(question)
        if not is_safe(sql):
            return sql, None, "Sirf SELECT queries allowed hain."
        result = run_sql(sql)
        answer = llm(
            f"Question: {question}\nSQL: {sql}\nResult: {result}\n"
            "Is result ke basis pe simple English mein answer do."
        )
        return sql, result, answer
    except Exception as e:
        return "", None, f"Error: {e}"

if __name__ == "__main__":
    while True:
        q = input("\nSawaal (exit likho band karne ke liye): ")
        if q.strip().lower() == "exit":
            break
        sql, result, answer = ask(q)
        print("\nSQL:", sql)
        print("Result:", result)
        print("Answer:", answer)