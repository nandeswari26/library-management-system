from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "library_secret"

# ---------------- DATABASE ----------------
def db():
    return sqlite3.connect("database.db")


# ---------------- HOME / LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email,password))
        user = cur.fetchone()

        if user:
            session["uid"] = user[0]
            session["name"] = user[1]
            session["role"] = user[4]

            if user[4] == "admin":
                return redirect("/admin/dashboard")
            else:
                return redirect("/member/dashboard")

    return render_template("auth/login.html")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        con = db()
        cur = con.cursor()
        cur.execute("INSERT INTO users(name,email,password,role) VALUES (?,?,?,?)",
                    (name,email,password,"member"))
        con.commit()
        return redirect("/")

    return render_template("auth/register.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# =====================================================
# ===================== ADMIN =========================
# =====================================================

@app.route("/admin/dashboard")
def admin_dashboard():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM books")
    books = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE role='member'")
    members = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM issued_books WHERE return_date IS NULL")
    issued = cur.fetchone()[0]
    return render_template("admin/dashboard.html", books=books, members=members, issued=issued)


# ---------------- ADD BOOK ----------------
@app.route("/admin/add_book", methods=["GET","POST"])
def add_book():
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        category = request.form["category"]
        quantity = request.form["quantity"]

        con = db()
        cur = con.cursor()
        cur.execute("INSERT INTO books(title,author,category,quantity) VALUES (?,?,?,?)",
                    (title,author,category,quantity))
        con.commit()
        return redirect("/admin/manage_books")

    return render_template("admin/add_book.html")


# ---------------- MANAGE BOOKS ----------------
@app.route("/admin/manage_books")
def manage_books():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM books")
    books = cur.fetchall()
    return render_template("admin/manage_books.html", books=books)


@app.route("/admin/delete_book/<id>")
def delete_book(id):
    con = db()
    cur = con.cursor()
    cur.execute("DELETE FROM books WHERE id=?", (id,))
    con.commit()
    return redirect("/admin/manage_books")


# ---------------- ISSUE BOOK ----------------
@app.route("/admin/issue", methods=["GET","POST"])
def issue_book():
    con = db()
    cur = con.cursor()

    if request.method == "POST":
        user_id = request.form["user_id"]
        book_id = request.form["book_id"]

        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=7)

        cur.execute("INSERT INTO issued_books(book_id,user_id,issue_date,due_date) VALUES (?,?,?,?)",
                    (book_id,user_id,issue_date,due_date))
        cur.execute("UPDATE books SET quantity = quantity - 1 WHERE id=?", (book_id,))
        con.commit()
        return redirect("/admin/dashboard")

    cur.execute("SELECT id,name FROM users WHERE role='member'")
    members = cur.fetchall()
    cur.execute("SELECT id,title FROM books WHERE quantity>0")
    books = cur.fetchall()

    return render_template("admin/issue_book.html", members=members, books=books)


# ---------------- RETURN BOOK ----------------
@app.route("/admin/return", methods=["GET","POST"])
def return_book():
    con = db()
    cur = con.cursor()

    if request.method == "POST":
        iid = request.form["iid"]
        today = datetime.now()

        cur.execute("SELECT book_id FROM issued_books WHERE id=?", (iid,))
        book_id = cur.fetchone()[0]

        cur.execute("UPDATE issued_books SET return_date=? WHERE id=?", (today,iid))
        cur.execute("UPDATE books SET quantity=quantity+1 WHERE id=?", (book_id,))
        con.commit()

        return redirect("/admin/dashboard")

    cur.execute("""
        SELECT issued_books.id, users.name, books.title, issued_books.issue_date
        FROM issued_books
        JOIN users ON users.id = issued_books.user_id
        JOIN books ON books.id = issued_books.book_id
        WHERE return_date IS NULL
    """)
    data = cur.fetchall()

    return render_template("admin/return_book.html", data=data)


# ---------------- MANAGE MEMBERS ----------------
@app.route("/admin/members")
def manage_members():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE role='member'")
    members = cur.fetchall()
    return render_template("admin/manage_members.html", members=members)


# ---------------- REPORTS ----------------
@app.route("/admin/reports")
def reports():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM issued_books")
    data = cur.fetchall()
    return render_template("admin/reports.html", data=data)


# =====================================================
# ===================== MEMBER ========================
# =====================================================

@app.route("/member/dashboard")
def member_dashboard():
    return render_template("member/dashboard.html", name=session["name"])

@app.route("/member/my_books")
def my_books():
    uid = session["uid"]
    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT books.title, issued_books.issue_date, issued_books.due_date, issued_books.return_date
        FROM issued_books
        JOIN books ON books.id = issued_books.book_id
        WHERE issued_books.user_id=?
    """,(uid,))
    
    rows = cur.fetchall()

    data = []
    for r in rows:
        title = r[0]
        issue_date = datetime.fromisoformat(r[1])
        due_date = datetime.fromisoformat(r[2])
        return_date = r[3]

        data.append((title, issue_date, due_date, return_date))

    today = datetime.now()
    return render_template("member/my_books.html", data=data, today=today)


@app.route("/member/search")
def search_books():
    con = db()
    cur = con.cursor()

    cur.execute("SELECT id, title, author, category, quantity FROM books")
    books = cur.fetchall()

    return render_template("member/search_books.html", books=books)



@app.route("/member/profile")
def profile():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (session["uid"],))
    user = cur.fetchone()
    return render_template("member/profile.html", user=user)


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
