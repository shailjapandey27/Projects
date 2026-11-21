"""
Text-to-SQL Engine

Converts a natural language question into a SQL query using an LLM (Groq API),
executes it safely against a SQLite database, and returns a plain-English answer.
"""

import os
import re
import json
import sqlite3
import urllib.request
import urllib.error

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "openai/gpt-oss-120b"
DB_FILE = "shop.db"
API_URL = "https://api.groq.com/openai/v1/chat/completions"


def llm(prompt):
    """Send a prompt to the Groq API and return the model's text response."""
    request = urllib.request.Request(
        API_URL,
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
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as error:
        raise Exception(f"API request failed ({error.code}): {error.read().decode()}")


def get_schema():
    """Return the CREATE TABLE statements of the database as a single string."""
    connection = sqlite3.connect(DB_FILE)
    rows = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table'"
    ).fetchall()
    connection.close()
    return "\n".join(row[0] for row in rows if row[0])


def generate_sql(question):
    """Generate a SQLite SELECT query for the given natural language question."""
    prompt = f"""You are an expert SQLite data analyst.

Database schema:
{get_schema()}

Write exactly ONE SQLite SELECT query that answers the question below.
Return only the SQL query, with no explanation and no markdown formatting.

Question: {question}"""
    sql = llm(prompt)
    return sql.replace("```sql", "").replace("```", "").strip()


def is_safe(sql):
    """Allow only read-only SELECT statements; block any data-modifying keywords."""
    blocked_keywords = r"\b(drop|delete|update|insert|alter|create|truncate|replace)\b"
    return sql.lower().startswith("select") and not re.search(blocked_keywords, sql.lower())


def run_sql(sql):
    """Execute a query on a read-only database connection as an additional safeguard."""
    connection = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
    rows = connection.execute(sql).fetchall()
    connection.close()
    return rows


def ask(question):
    """
    Process a user question end to end.

    Returns a tuple of (generated_sql, raw_result, answer).
    """
    try:
        sql = generate_sql(question)

        if not is_safe(sql):
            return sql, None, "Only SELECT queries are permitted."

        result = run_sql(sql)
        answer = llm(
            f"Question: {question}\n"
            f"SQL query: {sql}\n"
            f"Query result: {result}\n\n"
            "Based on the query result, answer the question in one or two clear, "
            "professional English sentences."
        )
        return sql, result, answer

    except Exception as error:
        return "", None, f"An error occurred: {error}"


if __name__ == "__main__":
    while True:
        user_question = input("\nEnter your question (type 'exit' to quit): ")
        if user_question.strip().lower() == "exit":
            break

        generated_sql, query_result, final_answer = ask(user_question)
        print("\nGenerated SQL:", generated_sql)
        print("Query Result:", query_result)
        print("Answer:", final_answer)