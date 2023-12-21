from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
import re

app = Flask(__name__)
app.debug = True
app.secret_key = os.urandom(24)

# Database Connection
connect = sqlite3.connect("database.db")
connect.execute(
    "CREATE TABLE IF NOT EXISTS USERS (sr_no INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT,password TEXT, email TEXT)"
)

@app.route("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Renders the login page and authenticates user login.
    """
    msg = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        with sqlite3.connect("database.db") as users:
            cursor = users.cursor()
            try:
                cursor.execute(
                    "SELECT * FROM USERS WHERE username = ? AND password = ?",
                    (username, password),
                )
                account = cursor.fetchone()
                if account:
                    session["loggedin"] = True
                    session["sr_no"] = account[0]
                    session["username"] = account[1]
                    msg = "Logged in successfully!"
                    return render_template("index.html", msg=msg)
                else:
                    msg = "Incorrect username / password!"
                    return render_template("login.html", msg=msg)
            except sqlite3.Error as e:
                return render_template("error.html", error=str(e))
    return render_template("login.html", msg=msg)


# Logout
@app.route("/logout")
def logout():
    """
    Logs the user out by clearing session data.
    """
    session.pop("loggedin", None)
    session.pop("id", None)
    session.pop("username", None)
    return redirect(url_for("login"))


# Route to Update
@app.route("/update", methods=["GET", "POST"])
def update():
    """
    Allows logged-in users to update their account information.
    """
    if request.method == "POST":
        if "loggedin" in session:
            username = request.form["username"]
            password = request.form["password"]
            with sqlite3.connect("database.db") as users:
                cursor = users.cursor()
                try:
                    cursor.execute(
                        "UPDATE USERS SET username = ?, password = ? WHERE sr_no = ?",
                        (username, password, session["sr_no"]),
                    )
                    users.commit()
                    session["username"] = username
                    return render_template("index.html")
                except sqlite3.Error as e:
                    return render_template("error.html", error=str(e))
        else:
            return redirect(url_for("login"))
    else:
        return render_template("update.html")


@app.route("/delete", methods=["GET", "POST"])
def delete():
    """
    Deletes the user account.
    """
    if request.method == "POST":
        if "loggedin" in session and "sr_no" in session:
            try:
                with sqlite3.connect("database.db") as users:
                    cursor = users.cursor()
                    cursor.execute(
                        "DELETE FROM USERS WHERE sr_no = ?", (session["sr_no"],)
                    )
                    users.commit()
                session.clear()
                msg = "Your account has been deleted successfully!"
                return render_template("login.html", msg=msg)
            except sqlite3.Error as e:
                return render_template("error.html", error=str(e))
        return redirect(url_for("login"))
    return redirect(url_for("login"))


# Route to Register
@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Registers a new user.
    """
    msg = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        with sqlite3.connect("database.db") as users:
            cursor = users.cursor()
            try:
                cursor.execute("SELECT * FROM USERS WHERE username = ?", (username,))
                account = cursor.fetchone()
                if account:
                    msg = "Account already exists!"
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    msg = "Invalid email address!"
                elif not re.match(r"[A-Za-z0-9]+", username):
                    msg = "Username must contain only characters and numbers!"
                elif not username or not password or not email:
                    msg = "Please fill out the form!"
                else:
                    cursor.execute(
                        "INSERT INTO USERS (username,password, email) VALUES (?, ?, ?)",
                        (username, password, email),
                    )
                    users.commit()
                    msg = "You have successfully registered!"
                    return redirect(url_for("login"))
            except sqlite3.Error as e:
                return render_template("error.html", error=str(e))
    return render_template("register.html", msg=msg)


# Route to login into Admin panel
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """
    Admin login route.
    """
    msg = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # Check if the provided admin credentials are correct
        if username == "admin" and password == "admin":
            # Redirect to admin panel or perform admin-specific actions
            return redirect(url_for("admin_panel"))
        else:
            msg = "Incorrect admin credentials!"
            return render_template("admin_login.html", msg=msg)
    return render_template("admin_login.html", msg=msg)


# route to Admin Panel
@app.route("/admin_panel")
def admin_panel():
    """
    Renders the admin panel.
    """
    with sqlite3.connect("database.db") as users:
        cursor = users.cursor()
        cursor.execute("SELECT * FROM USERS")
        entries = cursor.fetchall()
        return render_template("admin_panel.html", entries=entries)


# Route to edit an entry
@app.route("/admin/edit/<string:entry_id>", methods=["GET", "POST"])
def edit_entry(entry_id):
    """
    Allows editing of a user entry by the admin.
    """
    if request.method == "POST":
        new_username = request.form["username"]
        new_password = request.form["password"]
        try:
            with sqlite3.connect("database.db") as users:
                cursor = users.cursor()
                cursor.execute(
                    "UPDATE USERS SET username = ?, password = ? WHERE sr_no = ?",
                    (new_username, new_password, entry_id),
                )
                users.commit()
        except sqlite3.Error as e:
            print("SQLite error:", e)
        return redirect(url_for("admin_panel"))
    else:
        try:
            with sqlite3.connect("database.db") as users:
                cursor = users.cursor()
                cursor.execute("SELECT * FROM USERS WHERE sr_no = ?", (entry_id,))
                entry = cursor.fetchone()
        except sqlite3.Error as e:
            print("SQLite error:", e)
            entry = None
        return render_template("edit_entry.html", entry=entry)


# Route to delete an entry
@app.route("/admin/delete/<int:entry_id>", methods=["GET"])
def delete_entry(entry_id):
    """
    Deletes a user entry by the admin.
    """
    with sqlite3.connect("database.db") as users:
        cursor = users.cursor()
        cursor.execute("DELETE FROM USERS WHERE sr_no = ?", (entry_id,))
        users.commit()
        return redirect(url_for("admin_panel"))


if __name__ == "__main__":
    app.run(debug=True)
