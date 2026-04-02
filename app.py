from flask import Flask, render_template, request, redirect, session,url_for
from db import connection
from flask import redirect, url_for, flash
import subprocess

app = Flask(__name__)
app.secret_key = "lostfoundsecret"

@app.route('/backup_db')
def backup_db():
    os.system("mysqldump -u root -pWoMoXi22@#** lost_found_db > latest_backup.sql")
    flash("Database backup created successfully!")
    return redirect(url_for('dashboard'))

@app.route("/")
def home():
    return redirect("/login")

@app.route('/sync_db')
def sync_db():
    try:
        with open("latest_backup.sql", "w") as backup_file:
            subprocess.run(
                [
                    "mysqldump",
                    "-u", "root",
                    "-pWoMoXi22@#**",
                    "lost_found_db"
                ],
                stdout=backup_file,
                check=True
            )

        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(
            ["git", "commit", "-m", "Auto DB backup sync"],
            check=False
        )
        subprocess.run(["git", "push"], check=True)

        flash("Backup + GitHub sync successful!")

    except subprocess.CalledProcessError as e:
        flash(f"Sync failed: {e}")

    return redirect(url_for("dashboard"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO Users(name, email, password, role)
            VALUES (%s, %s, %s, %s)
            """,
            (name, email, password, "student")
        )
        connection.commit()

        return redirect("/login")

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM Users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cursor.fetchone()

        if user:
            session["user_id"] = user[0]   # user_id
            return redirect("/dashboard")
        else:
            return "Invalid email or password"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return '''<h2>Welcome</h2>
              <a href="/report-lost">Report Lost Item</a><br><br>
              <a href="/report-found">Report Found Item</a><br><br>
              <a href="/logout">Logout</a>
              <a href="/sync_db"><button>Backup & Sync to GitHub</button></a>
              '''

@app.route("/report-lost", methods=["GET", "POST"])
def report_lost():
    if request.method == "POST":
        item_name = request.form["item_name"]
        category = request.form["category"]
        description = request.form["description"]
        location = request.form["location"]
        date_lost = request.form["date_lost"]

        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO Lost_items
            (user_id, item_name, category, description, location, date_lost, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                item_name,
                category,
                description,
                location,
                date_lost,
                "lost"
            )
        )
        connection.commit()

        return "Lost item submitted successfully"

    return render_template("report_lost.html")


@app.route("/report-found", methods=["GET", "POST"])
def report_found():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        item_name = request.form["item_name"]
        category = request.form["category"]
        description = request.form["description"]
        location_found = request.form["location_found"]
        date_found = request.form["date_found"]

        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO Found_items
            (user_id, item_name, category, description, location_found, date_found, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                item_name,
                category,
                description,
                location_found,
                date_found,
                "claimed"  
            )
        )
        connection.commit()

        return "Found item submitted successfully"

    return render_template("report_found.html")

if __name__ == "__main__":
    app.run(debug=True)