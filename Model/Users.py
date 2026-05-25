from Vigilant_eye.db import db

class Users(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(db.String(50))
    status = db.Column(db.String(50))
    wasi= db.Column(db.Interger)

    # Relationships
    student_rship = db.relationship("Student", back_populates="user_rship", uselist=False)
    guard_rship = db.relationship("Guard", back_populates="user_rship", uselist=False)
    admin_rship = db.relationship("Admin", back_populates="user_rship", uselist=False)
    committee_rship = db.relationship("DisciplineCommittee", back_populates="user_rship", uselist=False)
    detections = db.relationship("Detection", back_populates="user")
    committee_memberships = db.relationship("CommitteeMember", back_populates="user")
    parent = db.relationship("Parent",back_populates="user_rship")
