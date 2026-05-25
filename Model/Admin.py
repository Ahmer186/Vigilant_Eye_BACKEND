from Vigilant_eye.db import db

class Admin(db.Model):
    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)

    user_rship = db.relationship("Users", back_populates="admin_rship")
