from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    profile_picture = db.Column(db.String(150), nullable=True)
    first_name = db.Column(db.String(150), nullable=True)
    last_name = db.Column(db.String(150), nullable=True)
    patronymic = db.Column(db.String(150), nullable=True)
    address = db.Column(db.String(250), nullable=True)
    phone_number = db.Column(db.String(50), nullable=True)
    about_me = db.Column(db.Text, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
