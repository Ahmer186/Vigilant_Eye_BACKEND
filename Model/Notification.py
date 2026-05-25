from Vigilant_eye.db import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True)  # ✅ notification_id → id
    detection_id = db.Column(db.Integer, db.ForeignKey('detection.detection_id'))
    notification_message = db.Column(db.Text)
    recipient_regno = db.Column(db.String(150), db.ForeignKey('student.regno'), nullable=True)
    recipient_role = db.Column(db.String(50), nullable=True)
    recipient_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    detection = db.relationship("Detection", back_populates="notifications")