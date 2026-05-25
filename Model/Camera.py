from Vigilant_eye.db import db
from datetime import datetime

class Camera(db.Model):
    __tablename__ = 'camera'

    camera_id = db.Column(db.Integer, primary_key=True)
    camera_name = db.Column(db.String(150))
    ipAddress = db.Column(db.String(50))
    status = db.Column(db.String(50))
    active_time = db.Column(db.DateTime, default=datetime.utcnow())
    direction = db.Column(db.String(50))

    locations = db.relationship("Location", back_populates="camera")
