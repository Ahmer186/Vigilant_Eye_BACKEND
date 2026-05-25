from Vigilant_eye.db import db

class CommitteeMember(db.Model):
    __tablename__ = 'committee_members'

    id = db.Column(db.Integer, primary_key=True)
    committee_type = db.Column(db.String(100), nullable=False)  # "fighting", "smoking", "harassment"
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    position = db.Column(db.String(50), nullable=False, default='member')  # "head" ya "member"

    user = db.relationship("Users", back_populates="committee_memberships")