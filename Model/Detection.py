from Vigilant_eye.db import db
from datetime import datetime

class Detection(db.Model):
    __tablename__ = 'detection'

    detection_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('location.loc_id'))
    activity = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("Users", back_populates="detections")
    location = db.relationship("Location", back_populates="detections")
    details = db.relationship("DetectionDetails", back_populates="detection", uselist=False)
    notifications = db.relationship("Notification", back_populates="detection")
    penalties = db.relationship("Penalty", back_populates="detection")
