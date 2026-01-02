import sqlite3

con = sqlite3.connect("database.db")
cur = con.cursor()

# USERS
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

# BOOKS (WITH category)
cur.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    author TEXT,
    category TEXT,
    quantity INTEGER
)
""")

# ISSUED BOOKS
cur.execute("""
CREATE TABLE IF NOT EXISTS issued_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    user_id INTEGER,
    issue_date TEXT,
    due_date TEXT,
    return_date TEXT
)
""")

# Default admin
cur.execute("SELECT * FROM users WHERE role='admin'")
if cur.fetchone() is None:
    cur.execute(
        "INSERT INTO users(name,email,password,role) VALUES (?,?,?,?)",
        ("Admin", "admin@gmail.com", "admin123", "admin")
    )

con.commit()
con.close()

print("Database created with category column successfully!")
