from Vigilant_eye.db import db

class DisciplineCommittee(db.Model):
    __tablename__ = 'discipline_committee'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    case_solving = db.Column(db.String(255), nullable=True)  # ✅ naya

    user_rship = db.relationship("Users", back_populates="committee_rship")