from Vigilant_eye.db import db

class DetectionDetails(db.Model):
    __tablename__ = 'detection_details'

    detail_id = db.Column(db.Integer, primary_key=True)
    detection_id = db.Column(db.Integer, db.ForeignKey('detection.detection_id'))
    person_involved = db.Column(db.String(150))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    accuracy = db.Column(db.Float)
    detect_img = db.Column(db.String(255))
    detect_video = db.Column(db.String(255))

    detection = db.relationship("Detection", back_populates="details")
