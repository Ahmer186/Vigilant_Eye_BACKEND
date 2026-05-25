from Vigilant_eye.db import db

class Guard(db.Model):
    __tablename__ = 'guard'

    guard_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)

    # Link to Users table (one-to-one)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)

    # Relationship back to Users
    user_rship = db.relationship("Users", back_populates="guard_rship")
