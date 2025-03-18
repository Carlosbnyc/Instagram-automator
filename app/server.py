from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")  # For session security

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Change if using a different email provider
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    insta_username = db.Column(db.String(150))
    insta_password = db.Column(db.String(150))
    target_accounts = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Log in instead.', 'danger')
            return redirect(url_for('login'))

        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        # Send verification email
        send_verification_email(email)

        flash('Account created! Check your email to verify.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/verify/<email>')
def verify_email(email):
    user = User.query.filter_by(email=email).first()
    if user:
        user.verified = True
        db.session.commit()
        flash('Email verified! You can now log in.', 'success')
        return redirect(url_for('login'))
    else:
        flash('Invalid verification link.', 'danger')
        return redirect(url_for('home'))

def send_verification_email(email):
    msg = Message('Verify Your Account', sender=os.getenv("EMAIL_USER"), recipients=[email])
    msg.body = f"Click the link to verify your account: {url_for('verify_email', email=email, _external=True)}"
    mail.send(msg)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email, password=password).first()
        if user and user.verified:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials or unverified email.', 'danger')

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        current_user.insta_username = request.form['insta_username']
        current_user.insta_password = request.form['insta_password']
        current_user.target_accounts = request.form['target_accounts']
        db.session.commit()
        flash('Settings saved!', 'success')

    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)