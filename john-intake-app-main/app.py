from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def init_db():
    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            phone TEXT,
            email TEXT,
            service TEXT,
            service_option TEXT,
            stylist TEXT,
            stylist TEXT,
            appointment_date TEXT,
            appointment_time TEXT,
            hair_type TEXT,
            hair_length TEXT,
            notes TEXT,
            deposit_status TEXT,
            booking_status TEXT,
            photo_filename TEXT
        )
    """)
    try:
        cursor.execute("ALTER TABLE appointments ADD COLUMN photo_filename TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE appointments ADD COLUMN service_option TEXT")
    except sqlite3.OperationalError:
        pass
        conn.commit()
        conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        client_name = request.form.get("client_name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        service = request.form.get("service")
        service_option = request.form.get("service_option")
        stylist = request.form.get("stylist")
        appointment_date = request.form.get("appointment_date")
        appointment_time = request.form.get("appointment_time")
        hair_type = request.form.get("hair_type")
        hair_length = request.form.get("hair_length")
        notes = request.form.get("notes")

        photo_filename = None
        photo = request.files.get("photo")

        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            allowed_extensions = {"png", "jpg", "jpeg", "webp"}

            if "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions:
                photo_filename = filename
                save_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
                photo.save(save_path)

        conn = sqlite3.connect("appointments.db")
        cursor = conn.cursor()

        # Prevent double-booking the same stylist, date, and time
        cursor.execute("""
            SELECT id
            FROM appointments
            WHERE stylist = ?
            AND appointment_date = ?
            AND appointment_time = ?
            AND booking_status != 'Cancelled'
        """, (stylist, appointment_date, appointment_time))

        existing_appointment = cursor.fetchone()

        if existing_appointment:
            conn.close()
            return render_template(
                "intake.html",
                error="That stylist is already booked for the selected date and time. Please choose another time."
            )

        cursor.execute("""
            INSERT INTO appointments (
                client_name,
                phone,
                email,
                service,
                service_option,
                stylist,
                appointment_date,
                appointment_time,
                hair_type,
                hair_length,
                notes,
                deposit_status,
                booking_status,
                photo_filename
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            client_name,
            phone,
            email,
            service,
            service_option,
            stylist,
            appointment_date,
            appointment_time,
            hair_type,
            hair_length,
            notes,
            "Not Paid",
            "Pending",
            photo_filename
        ))

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

    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()

    filter_status = request.args.get("status", "active")

    base_query = """
        SELECT
            id,
            client_name,
            phone,
            email,
            service,
            service_option,
            stylist,
            appointment_date,
            appointment_time,
            hair_type,
            hair_length,
            notes,
            deposit_status,
            booking_status,
            photo_filename
        FROM appointments
    """

        

    if filter_status == "pending":
        base_query += " WHERE booking_status = 'Pending'"
    elif filter_status == "confirmed":
        base_query += " WHERE booking_status = 'Confirmed'"
    elif filter_status == "cancelled":
        base_query += " WHERE booking_status = 'Cancelled'"
    elif filter_status == "active":
            base_query += " WHERE booking_status != 'Cancelled'"

    base_query += " ORDER BY appointment_date ASC, appointment_time ASC"

    cursor.execute(base_query)
    appointments = cursor.fetchall()
    conn.close()

    return render_template("admin.html", appointments=appointments)    

@app.route("/confirm/<int:appointment_id>")
def confirm_appointment(appointment_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE appointments
        SET booking_status = ?
        WHERE id = ?
    """, ("Confirmed", appointment_id))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


@app.route("/cancel/<int:appointment_id>")
def cancel_appointment(appointment_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE appointments
        SET booking_status = ?
        WHERE id = ?
    """, ("Cancelled", appointment_id))

    conn.commit()
    conn.close()
    return redirect(url_for("admin"))
@app.route("/restore/<int:appointment_id>")
def restore_appointment(appointment_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE appointments
        SET booking_status = ?
        WHERE id = ?
    """, ("Pending", appointment_id))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))
   
@app.route("/deposit-paid/<int:appointment_id>")
def deposit_paid(appointment_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE appointments
        SET deposit_status = ?
        WHERE id = ?
    """, ("Paid", appointment_id))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


@app.route("/deposit-unpaid/<int:appointment_id>")
def deposit_unpaid(appointment_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE appointments
        SET deposit_status = ?
        WHERE id = ?
    """, ("Not Paid", appointment_id))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))
@app.route("/upload-photo/<int:appointment_id>", methods=["POST"])
def upload_photo(appointment_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if "photo" not in request.files:
        return redirect(url_for("edit_appointment", appointment_id=appointment_id))

    photo = request.files["photo"]

    if photo.filename == "":
        return redirect(url_for("edit_appointment", appointment_id=appointment_id))

    filename = secure_filename(photo.filename)

    allowed_extensions = {"png", "jpg", "jpeg", "webp"}

    if "." not in filename or filename.rsplit(".", 1)[1].lower() not in allowed_extensions:
        return redirect(url_for("edit_appointment", appointment_id=appointment_id))

    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    photo.save(save_path)

    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE appointments
        SET photo_filename = ?
        WHERE id = ?
    """, (filename, appointment_id))

    conn.commit()
    conn.close()

    return redirect(url_for("edit_appointment", appointment_id=appointment_id))
@app.route("/edit/<int:appointment_id>", methods=["GET", "POST"])
def edit_appointment(appointment_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()

    if request.method == "POST":
        client_name = request.form.get("client_name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        service = request.form.get("service")
        stylist = request.form.get("stylist")
        appointment_date = request.form.get("appointment_date")
        appointment_time = request.form.get("appointment_time")
        hair_type = request.form.get("hair_type")
        hair_length = request.form.get("hair_length")
        notes = request.form.get("notes")
        deposit_status = request.form.get("deposit_status")
        booking_status = request.form.get("booking_status")

        cursor.execute("""
            UPDATE appointments
            SET client_name = ?,
                phone = ?,
                email = ?,
                service = ?,
                stylist = ?,
                appointment_date = ?,
                appointment_time = ?,
                hair_type = ?,
                hair_length = ?,
                notes = ?,
                deposit_status = ?,
                booking_status = ?
            WHERE id = ?
        """, (
            client_name,
            phone,
            email,
            service,
            stylist,
            appointment_date,
            appointment_time,
            hair_type,
            hair_length,
            notes,
            deposit_status,
            booking_status,
            appointment_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("admin"))

    cursor.execute("""
        SELECT
            id,
            client_name,
            phone,
            email,
            service,
            stylist,
            appointment_date,
            appointment_time,
            hair_type,
            hair_length,
            notes,
            deposit_status,
            booking_status,
            photo_filename
            FROM appointments
        WHERE id = ?
    """, (appointment_id,))

    appointment = cursor.fetchone()
    conn.close()

    print("APPOINTMENT DATA:", appointment)

    return render_template("edit_appointment.html", appointment=appointment)
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)