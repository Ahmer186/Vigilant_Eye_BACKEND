from flask import jsonify
from Vigilant_eye.db import db
from Vigilant_eye.Model.ECL import ECL
from Vigilant_eye.Model.Student import Student
from Vigilant_eye.Model.Detection import Detection
from Vigilant_eye.Model.Users import Users
from Vigilant_eye.Model.Penalties import Penalty
from Vigilant_eye.Model.DetectionDetails import DetectionDetails
class Guard_Controller:
    @staticmethod
    def detections_pending_not_allowed():
        try:
            records = (
                db.session.query(
                    Student.name.label("student_name"),
                    Student.regno.label("registration_number"),
                    Student.section,
                    Student.semester,
                    Detection.activity.label("detected_activity"),
                    Penalty.Status.label("penalty_status"),
                    DetectionDetails.date.label("detection_date"),  # ✅ naya
                    DetectionDetails.time.label("detection_time"),  # ✅ naya
                )
                .join(Penalty, Penalty.detection_id == Detection.detection_id)
                .join(Student, Student.regno == Penalty.regno)
                .join(DetectionDetails, DetectionDetails.detection_id == Detection.detection_id)  # ✅ naya
                .join(ECL,
                      (ECL.user_id == Student.user_id) &
                      (db.func.lower(ECL.activity) == db.func.lower(Detection.activity))
                      )
                .filter(
                    Penalty.Status == 'Pending',
                    Penalty.regno != None,
                    ECL.status == 'not allowed'
                )
                .order_by(Student.name.asc(), DetectionDetails.date.desc())
                .all()
            )

            if not records:
                return jsonify({
                    "message": "No students found with pending penalties and not allowed activities"
                }), 404

            results = []
            for r in records:
                results.append({
                    "student_name": r.student_name,
                    "registration_number": r.registration_number,
                    "section": r.section,
                    "semester": r.semester,
                    "detected_activity": r.detected_activity,
                    "penalty_status": r.penalty_status,
                    "detection_date": str(r.detection_date) if r.detection_date else None,  # ✅ naya
                    "detection_time": str(r.detection_time) if r.detection_time else None,  # ✅ naya
                })

            return jsonify(results), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500