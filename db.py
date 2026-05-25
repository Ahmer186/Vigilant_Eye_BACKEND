# Vigilant_eye/db.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import URL

app = Flask(__name__)

connection_url = URL.create(
    "mssql+pyodbc",
    username="sa",
    password="123",
    host="DESKTOP-H8E8QK5\\VRSERVER",
    database="VIGILANT_EYE",
    query={
        "driver": "ODBC Driver 17 for SQL Server",
        "Encrypt": "no",
        "TrustServerCertificate": "yes"
    }
)

app.config["SQLALCHEMY_DATABASE_URI"] = connection_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
