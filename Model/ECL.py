from Vigilant_eye.db import db

class ECL(db.Model):
    __tablename__ = 'ecl'

    ecl_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # allowed / not allowed

    user = db.relationship("Users", backref="ecl_records")
