from Vigilant_eye.db import db

class CameraLinks(db.Model):
    __tablename__ = 'camera_links'

    cam_id_details = db.Column(db.Integer, primary_key=True)  # matches your table
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.camera_id'))
    linked_camera_id = db.Column(db.Integer, db.ForeignKey('camera.camera_id'))

    camera = db.relationship("Camera", foreign_keys=[camera_id])
    linked_camera = db.relationship("Camera", foreign_keys=[linked_camera_id])