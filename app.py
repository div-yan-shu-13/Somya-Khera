from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import mysql.connector
from mysql.connector import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
import os
import atexit

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', "this will work!!")  # Replace this in production

# Debugging: Print the database name being used
DATABASE_NAME = "careerpathdb"
print(f"Connecting to database: {DATABASE_NAME}")

# Create database if it doesn't exist
try:
    db_create = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234"
    )
    cursor_create = db_create.cursor()
    cursor_create.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}")
    db_create.commit()
except mysql.connector.Error as err:
    print(f"Database creation error: {err}")
    exit(1)
finally:
    if db_create:
        db_create.close()
    if cursor_create:
        cursor_create.close()

# Connect to the created database
db = None  # Initialize db to None
cursor = None  # Initialize cursor to None
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database=DATABASE_NAME  # Ensure the correct database name is used here
    )
    cursor = db.cursor()
except mysql.connector.Error as err:
    print(f"Database connection error: {err}")
    exit(1)

# Close the database connection when the application exits
def close_db():
    if cursor:
        cursor.close()
    if db:
        db.close()

atexit.register(close_db)

# Create tables
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS career_fields (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            course_required VARCHAR(100),
            skills_required TEXT,
            related_jobs TEXT,
            description TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            query VARCHAR(255) NOT NULL,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    db.commit()
except mysql.connector.Error as err:
    print(f"Error creating tables: {err}")

# Home Route
@app.route("/")
def home():
    return redirect(url_for("login"))

# Signup Route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = escape(request.form["username"])
        email = escape(request.form["email"])
        password = generate_password_hash(request.form["password"], method="pbkdf2:sha256")

        try:
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                           (username, email, password))
            db.commit()
            session["user_id"] = cursor.lastrowid
            return redirect(url_for("career_search"))
        except IntegrityError:
            flash("Email already exists.")
            return redirect(url_for("signup"))
        except mysql.connector.Error as err:
            print(f"Database error during signup: {err}")
            flash("Database error occurred.")
            return redirect(url_for("signup"))

    return render_template("signup.html")

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = escape(request.form["email"])
        password = request.form["password"]

        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user[3], password):
                session["user_id"] = user[0]
                return redirect(url_for("career_search"))

            flash("Invalid credentials.")
            return redirect(url_for("login"))
        except mysql.connector.Error as err:
            print(f"Database error during login: {err}")
            flash("Database error occurred.")
            return redirect(url_for("login"))

    return render_template("login.html")

# Logout Route
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

# Career Search Page Route
@app.route("/career_search")
def career_search():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("career_search.html")

# Search Route
@app.route("/search", methods=["GET"])
def search():
    if "user_id" not in session:
        return {"error": "Not logged in"}, 401

    query = request.args.get("q", "").strip()
    if not query:
        return {"error": "No query provided"}, 400

    try:
        # Store search history
        cursor.execute("INSERT INTO search_history (user_id, query) VALUES (%s, %s)", (session["user_id"], query))
        db.commit()

        # Search in career_fields table
        sql_query = """
            SELECT name, course_required, skills_required, related_jobs, description
            FROM career_fields
            WHERE name LIKE %s
               OR course_required LIKE %s
               OR skills_required LIKE %s
               OR related_jobs LIKE %s
               OR description LIKE %s
        """
        values = (f"%{query}%",) * 5
        cursor.execute(sql_query, values)
        results = cursor.fetchall()

        if results:
            careers = [{
                "name": row[0],
                "course_required": row[1],
                "skills_required": row[2],
                "related_jobs": row[3],
                "description": row[4]
            } for row in results]
            return {"results": careers}

        return {"message": "No matching careers found"}, 404

    except mysql.connector.Error as err:
        print(f"Database error during search: {err}")
        return {"error": "Database error"}, 500

# Run App
if __name__ == "__main__":
    app.run(debug=True)
