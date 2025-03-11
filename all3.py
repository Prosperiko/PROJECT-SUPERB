from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
from mysql.connector import Error
from flask_bcrypt import Bcrypt
import re
from flask_mail import Mail, Message
import random
from itsdangerous import URLSafeTimedSerializer
app = Flask(__name__, template_folder='.')
bcrypt = Bcrypt(app)
app.secret_key = "your_secret_key"


# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'muhammedtesleemolatundun.com'  # Your email address
app.config['MAIL_PASSWORD'] = 'csqv yavo jcwj bghz'  # Your email password
app.config['MAIL_DEFAULT_SENDER'] = 'projectfinodido@gmail.com'  # Default sender

mail = Mail(app)
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="Teslim",
            password="Tesleem@123",
            database="mydatabase"
        )
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        nationality = request.form['nationality']
        customer_type = request.form['customer_type']

        # Check if all required fields are filled
        if not username or not email or not password or not customer_type:
            flash("All fields are required!", "error")
            return redirect('/signup')

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect('/signup')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                # Check if the username or email already exists
                cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
                existing_user = cursor.fetchone()
                if existing_user:
                    flash("Username or email already exists!", "error")
                    return redirect('/signup')

                # Generate a verification PIN
                pin = random.randint(100000, 999999)

                # Send the verification email
                msg = Message("Email Verification", recipients=[email])
                msg.body = f"Your verification PIN is: {pin}"
                mail.send(msg)

                # Store user data temporarily (you may want to store it in a session or database)
                session['pending_user'] = {
                    'username': username,
                    'fullname': fullname,
                    'email': email,
                    'password': hashed_password,
                    'nationality': nationality,
                    'customer_type': customer_type,
                    'pin': pin
                }

                flash("A verification PIN has been sent to your email. Please check your inbox.", "success")
                return redirect('/verify_pin')
            except Error as e:
                print(f"An error occurred: {e}")
                flash("An error occurred while signing up. Please try again.", "error")
            finally:
                cursor.close()
                conn.close()
        else:
            flash("Database connection failed!", "error")

    return render_template('signup.html')

@app.route('/verify_pin', methods=['GET', 'POST'])
def verify_pin():
    if request.method == 'POST':
        entered_pin = request.form['pin']
        pending_user = session.get('pending_user')

        if pending_user and str(pending_user['pin']) == entered_pin:
            # Insert new user into the database
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO users (username, fullname, email, password, nationality, customer_type)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (pending_user['username'], pending_user['fullname'], pending_user['email'],
                          pending_user['password'], pending_user['nationality'], pending_user['customer_type']))
                    conn.commit()
                    flash("Signup successful! You can now log in.", "success")
                    session.pop('pending_user', None)  # Clear the pending user data
                    return redirect('/login')
                except Error as e:
                    print(f"An error occurred: {e}")
                    flash("An error occurred while signing up. Please try again.", "error")
                finally:
                    cursor.close()
                    conn.close()
            else:
                flash("Database connection failed!", "error")
        else:
            flash("Invalid PIN. Please try again.", "error")

    return render_template('verify_pin.html')

from itsdangerous import URLSafeTimedSerializer

# Flask-Mail Configuration (Already in your code)
app.config['MAIL_DEFAULT_SENDER'] = 'projectfinodido@gmail.com'

# Serializer for token generation
serializer = URLSafeTimedSerializer(app.secret_key)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                # Generate a secure token
                token = serializer.dumps(email, salt='password-reset')

                # Create reset link
                reset_url = f"http://127.0.0.1:5000/reset_password/{token}"

                # Send reset link via email
                msg = Message("Password Reset Request", recipients=[email])
                msg.body = f"Click the link below to reset your password:\n\n{reset_url}\n\nThis link expires in 10 minutes."
                mail.send(msg)

                flash("A password reset link has been sent to your email.", "success")
            else:
                flash("No account found with that email!", "error")

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset', max_age=600)  # Valid for 10 minutes
    except:
        flash("The password reset link is invalid or has expired!", "error")
        return redirect('/forgot_password')

    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(f'/reset_password/{token}')

        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
            conn.commit()
            cursor.close()
            conn.close()

            flash("Password reset successful! You can now log in.", "success")
            return redirect('/login')

    return render_template('reset_password.html', token=token)




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()

                if user:
                    stored_password = user['password']
                    if bcrypt.check_password_hash(stored_password, password):
                        session['user_id'] = user['id']
                        session['username'] = user['username']
                        session['customer_type'] = user['customer_type']

                        flash("Login successful!", "success")

                        
                        if user['customer_type'].lower() == 'individual':
                            return redirect('/home1')
                        else:  
                            return redirect('/home')
                    else:
                        flash("Invalid password!", "error")
                else:
                    flash("User  not found!", "error")
            except Error as e:
                flash(f"An error occurred: {e}", "error")
            finally:
                cursor.close()
                conn.close()
        else:
            flash("Database connection failed!", "error")

        return redirect('/login')

    return render_template('login.html')
@app.route('/some_action')
def some_action():
    return "You chose Action 1!"

@app.route('/another_action')
def another_action():
    return "You chose Action 2!"

@app.route('/yet_another_action')
def yet_another_action():
    return "You chose Action 3!"
@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        customer_type = session['customer_type']

        # Customize the welcome message based on the customer_type
        if customer_type == 'individual':
            welcome_message = f"Welcome, {username}! We're glad to have you here."
        elif customer_type == 'family':
            welcome_message = f"Welcome, {username}! Your family is important to us."
        elif customer_type == 'company':
            welcome_message = f"Welcome, {username}! Thank you for choosing us for your business needs."
        else:
            welcome_message = "Welcome!"

        return render_template('home.html', message=welcome_message)
    else:
        flash("You need to log in first!", "error")
        return redirect('/login')

@app.route('/home1')
def home1():
    if 'username' in session:
        username = session['username']
        customer_type = session['customer_type']

        # Customize the welcome message based on the customer_type
        if customer_type == 'individual':
            welcome_message = f"Welcome, {username}! We're glad to have you here."
        elif customer_type == 'family':
            welcome_message = f"Welcome, {username}! Your family is important to us."
        elif customer_type == 'company':
            welcome_message = f"Welcome, {username}! Thank you for choosing us for your business needs."
        else:
            welcome_message = "Welcome!"

        return render_template('home.html', message=welcome_message)
    else:
        flash("You need to log in first!", "error")
        return redirect('/login')
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)