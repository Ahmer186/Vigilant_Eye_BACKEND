from Vigilant_eye.db import db

class Penalty(db.Model):
    __tablename__ = 'penalties'

    penalty_id = db.Column(db.Integer, primary_key=True)
    detection_id = db.Column(db.Integer, db.ForeignKey('detection.detection_id'))
    regno = db.Column(db.String(150), db.ForeignKey('student.regno'))  # ✅ bas yeh add karo
    penalty_message = db.Column(db.Text)
    Status = db.Column(db.String(50))

    detection = db.relationship("Detection", back_populates="penalties")
    student = db.relationship("Student")  # ✅ yeh bhi