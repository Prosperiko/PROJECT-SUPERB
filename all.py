from flask import Flask, render_template, request, redirect, flash, session, jsonify, send_file
app = Flask(__name__, template_folder='.')
app.secret_key = "your_secret_key"

@app.route('/')
def index():
    return render_template("index.html")
@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")


@app.route('/get-started', methods=['GET', 'POST'])
def get_started():
    return render_template("signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html")    

if __name__ == '__main__':
    app.run(debug=True)