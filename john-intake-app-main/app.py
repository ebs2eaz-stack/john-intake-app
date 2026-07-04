from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "change-this-secret-key"


def init_db():
    conn = sqlite3.connect("intake.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            dob TEXT
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/intake", methods=["GET", "POST"])
def intake():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        dob = request.form.get("dob")

        conn = sqlite3.connect("intake.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO submissions (name, email, phone, dob)
            VALUES (?, ?, ?, ?)
        """, (name, email, phone, dob))
        conn.commit()
        conn.close()

        return render_template("thank_you.html")

    return render_template("intake.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "password123":
            session["logged_in"] = True
            return redirect(url_for("admin"))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


@app.route("/admin")
def admin():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("intake.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, dob FROM submissions ORDER BY id DESC")
    submissions = cursor.fetchall()
    conn.close()

    return render_template("admin.html", submissions=submissions)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)