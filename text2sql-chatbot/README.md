# Text-to-SQL Chatbot

Ask questions in plain English and get SQL queries and answers from a database.

## How it works
Question → LLM (Groq) → SQL → SQLite (read-only) → Answer

## Features
- Converts natural language questions into SQLite queries using an LLM
- Safety check: only `SELECT` queries are allowed (DROP, DELETE, UPDATE, INSERT and similar are blocked)
- Database opened in read-only mode as a second safety layer
- Shows the generated SQL, the raw result and a plain-English answer
- Lightweight: the core engine uses only Python's standard library (`sqlite3`, `urllib`)
- Web UI with Streamlit, plus a dependency-free backup UI (`server.py`)

## Tech stack
Python, SQLite, Groq API (gpt-oss-120b), python-dotenv, Streamlit

## Project structure
```
text2sql-chatbot/
├── Create_database.py   # creates the sample shop.db database
├── engine.py            # question -> SQL -> result -> answer
├── ui.py                # Streamlit web UI
├── server.py            # backup web UI (standard library only)
├── requirements.txt
└── README.md
```

## Setup
1. Clone the repo and open the `text2sql-chatbot` folder
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
4. Get a free API key from [console.groq.com](https://console.groq.com) and create a `.env` file:
   ```
   GROQ_API_KEY=your_key_here
   ```
5. Create the sample database (run once):
   ```bash
   python Create_database.py
   ```

## Run
Terminal version:
```bash
python engine.py
```
Web UI (Streamlit):
```bash
python -m streamlit run ui.py
```
Web UI (no extra packages), then open http://localhost:8000:
```bash
python server.py
```
Web interface (no extra packages), then open http://localhost:8000:
```bash


## Example questions
- Which customer spent the most?
- How many customers are there?
- Total sales by city
- Orders above 10000
- Delete all orders → blocked by the safety check

## Sample database
Two tables: `customers` (id, name, city) and `orders` (id, customer_id, product, amount, order_date).

## Future improvements
- Support for MS SQL and other databases
- Self-correction when a generated query fails
- Charts for query results
- Chat history for follow-up questions

## Demo
![Output](output.png)