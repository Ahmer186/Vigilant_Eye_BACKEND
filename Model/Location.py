from Vigilant_eye.db import db

class Location(db.Model):
    __tablename__ = 'location'

    loc_id = db.Column(db.Integer, primary_key=True)
    loc_name = db.Column(db.String(150))

    camera_id = db.Column(db.Integer, db.ForeignKey('camera.camera_id'))

    camera = db.relationship("Camera", back_populates="locations")
    detections = db.relationship("Detection", back_populates="location")
