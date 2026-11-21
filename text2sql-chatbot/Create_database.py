import sqlite3

conn = sqlite3.connect("shop.db")
c = conn.cursor()
c.executescript("""
CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY, name TEXT, city TEXT);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, customer_id INTEGER,
                    product TEXT, amount REAL, order_date TEXT);
INSERT INTO customers VALUES (1,'Aman','Indore'),(2,'Riya','Bhopal'),(3,'Neha','Jabalpur');
INSERT INTO orders VALUES
(1,1,'Laptop',55000,'2026-10-01'),
(2,2,'Phone',20000,'2026-10-05'),
(3,1,'Mouse',500,'2026-10-07'),
(4,3,'Keyboard',1500,'2026-10-10');
""")
conn.commit()
conn.close()
print("Database ready")