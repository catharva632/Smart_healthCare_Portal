from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from chatbot.gpt_api import ask_doctor_bot  # your bot module
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secure_secret_123"  # ✅ use a strong secret key

# ---- Railway MySQL DB Configuration ----
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# ---- Routes ----

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        print(f"Login attempt: {email}, {password}")  # Debug

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user:
                print("User found:", user)  # Debug
                if check_password_hash(user["password"], password):
                    session["user_id"] = user["id"]
                    session["username"] = user["name"]
                    print("✅ Login successful. Redirecting to dashboard.")
                    return redirect(url_for("dashboard"))
                else:
                    flash("❌ Incorrect password", "danger")
            else:
                flash("❌ Email not found", "danger")

        except Error as e:
            print("❌ DB Error:", e)
            flash("❌ Database error", "danger")

        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
                
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        age = request.form.get("age")
        gender = request.form.get("gender")
        password = generate_password_hash(request.form.get("password"))
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, email, password, age, gender) VALUES (%s, %s, %s, %s, %s)",
                           (name, email, password, age, gender))
            conn.commit()
            flash("✅ Registered successfully. Please log in.", "success")
            return redirect(url_for("login"))
        except mysql.connector.IntegrityError:
            flash("❌ Email already exists", "danger")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    return render_template("register.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("user_id"):
        flash("⚠️ Please login to access the dashboard.", "warning")
        return redirect(url_for("login"))
    
    bot_response = ""
    if request.method == "POST":
        user_input = request.form.get("symptoms", "")
        if user_input:
            bot_response = ask_doctor_bot(user_input)
    
    return render_template("dashboard.html", username=session.get("username"), response=bot_response)

@app.route("/logout")
def logout():
    session.clear()
    flash("✅ Logged out successfully.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
