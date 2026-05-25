from Vigilant_eye.db import db

class StudentImage(db.Model):
    __tablename__ = 'student_images'

    id = db.Column(db.Integer, primary_key=True)
    regno = db.Column(db.String(150), db.ForeignKey('student.regno'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)

    # relationship back to Student
    student_rship = db.relationship("Student", back_populates="images")