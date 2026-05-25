from Vigilant_eye.db import db

class Parent(db.Model):
    __tablename__ = 'parent'

    par_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    cnic = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    regno = db.Column(db.String(150),db.ForeignKey('student.regno'), unique=True)

    user_rship = db.relationship("Users", back_populates="parent")
    student_rship = db.relationship("Student", back_populates="parent")
    # users = db.relationship("users", back_populates="parent")
    # student = db.relationship("Student", back_populates="parent")