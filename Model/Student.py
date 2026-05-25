from Vigilant_eye.db import db

class Student(db.Model):
    __tablename__ = 'student'

    regno = db.Column(db.String(150), primary_key=True)
    name = db.Column(db.String(150))
    semester = db.Column(db.Integer)
    section = db.Column(db.String(50))
    phone = db.Column(db.String(20))


    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    parent = db.relationship("Parent",back_populates="student_rship")
    user_rship = db.relationship("Users", back_populates="student_rship")
    images = db.relationship(
        'StudentImage',
        back_populates="student_rship",
        cascade="all, delete-orphan"
    )


