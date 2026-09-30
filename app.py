from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime
import sqlite3


app = Flask(__name__)

# ---------------- SECRET KEY ----------------

app.secret_key = "change-this-secret-key"


# ---------------- FOLDERS AND DATABASE ----------------

UPLOAD_FOLDER = Path("uploads")
DATABASE = "circulars.db"

UPLOAD_FOLDER.mkdir(exist_ok=True)


# ---------------- MANAGER LOGIN ----------------

MANAGER_USERNAME = "SVPCET"
MANAGER_PASSWORD = "SVPCET31"


# ---------------- DATABASE ----------------

def init_database():

    connection = sqlite3.connect(DATABASE)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS circulars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            upload_date TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# ---------------- PUBLIC CIRCULARS PAGE ----------------

@app.route("/")
def home():

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    circulars = connection.execute("""
        SELECT *
        FROM circulars
        ORDER BY upload_date DESC, id DESC
    """).fetchall()

    connection.close()

    return render_template(
        "index.html",
        circulars=circulars
    )


# ---------------- OPEN CIRCULAR PDF ----------------

@app.route("/circular/<filename>")
def open_circular(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


# ---------------- MANAGER LOGIN ----------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if (
            username == MANAGER_USERNAME
            and password == MANAGER_PASSWORD
        ):

            session["manager_logged_in"] = True

            return redirect(
                url_for("admin_upload")
            )

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


# ---------------- MANAGER UPLOAD ----------------

@app.route("/admin/upload", methods=["GET", "POST"])
def admin_upload():

    if not session.get("manager_logged_in"):

        return redirect(
            url_for("admin_login")
        )

    if request.method == "POST":

        file = request.files.get("circular")

        # Check file selected
        if not file or file.filename == "":

            return render_template(
                "upload.html",
                error="Please select a PDF file."
            )

        # Check PDF
        if not file.filename.lower().endswith(".pdf"):

            return render_template(
                "upload.html",
                error="Only PDF files are allowed."
            )

        # Secure filename
        filename = secure_filename(
            file.filename
        )

        # Save PDF
        file.save(
            UPLOAD_FOLDER / filename
        )

        # Create title from filename
        title = (
            Path(filename)
            .stem
            .replace("_", " ")
            .replace("-", " ")
        )

        # Current date
        upload_date = datetime.now().strftime(
            "%Y-%m-%d"
        )

        # Save details into database
        connection = sqlite3.connect(DATABASE)

        connection.execute("""
            INSERT INTO circulars
            (title, filename, upload_date)
            VALUES (?, ?, ?)
        """, (
            title,
            filename,
            upload_date
        ))

        connection.commit()
        connection.close()

        return redirect(
            url_for("home")
        )

    return render_template("upload.html")


# ---------------- LOGOUT ----------------

@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "manager_logged_in",
        None
    )

    return redirect(
        url_for("home")
    )


# ---------------- INITIALIZE DATABASE ----------------

init_database()


# ---------------- START APPLICATION ----------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )