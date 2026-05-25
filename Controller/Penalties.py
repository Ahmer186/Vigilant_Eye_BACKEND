from flask import request, jsonify
from Vigilant_eye.Model import Penalty, Detection, DetectionDetails, Student,Users, Location
from Vigilant_eye.Model.ECL import ECL
from Vigilant_eye.db import db
from Vigilant_eye.Model.Notification import Notification
from Vigilant_eye.Model.DisciplineCommittee import DisciplineCommittee
from Vigilant_eye.Model.Parent import Parent

class penalty_Controller:
    @staticmethod
    def penalties_by_user():
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400

        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"error": "Provide 'user_id' in JSON body"}), 400

        try:
            # ✅ user_id se student ka regno nikalo
            student = Student.query.filter_by(user_id=user_id).first()
            if not student:
                return jsonify({"message": "No student found for this user"}), 404

            # ✅ regno se penalties dhundo
            rows = (
                db.session.query(
                    Penalty.penalty_id.label("PenaltyID"),
                    Penalty.penalty_message,
                    Penalty.Status.label("status"),
                    Detection.activity,
                    DetectionDetails.date.label("detection_date"),
                    Location.loc_name.label("location")
                )
                .join(Detection, Penalty.detection_id == Detection.detection_id)
                .join(DetectionDetails, DetectionDetails.detection_id == Detection.detection_id)
                .join(Location, Detection.location_id == Location.loc_id)
                .filter(Penalty.regno == student.regno)  # ✅ regno se filter
                .order_by(DetectionDetails.date.desc())
                .all()
            )

            if not rows:
                return jsonify({"message": "No penalties found for this user"}), 404

            results = []
            for row in rows:
                results.append({
                    "PenaltyID": row.PenaltyID,
                    "penalty_message": row.penalty_message,
                    "status": row.status,
                    "activity": row.activity,
                    "detection_date": row.detection_date.strftime("%Y-%m-%d") if row.detection_date else None,
                    "location": row.location
                })

            return jsonify(results), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def show_all_pending_penalties(user_id):

        try:

            # ====================================
            # GET COMMITTEE
            # ====================================
            committee = DisciplineCommittee.query.filter_by(
                user_id=user_id
            ).first()

            if not committee:
                return jsonify({
                    "error": "Committee not found"
                }), 404

            committee_cases = [
                c.strip() for c in committee.case_solving.split(",")
            ]

            # ====================================
            # GET FILTERED PENALTIES
            # ====================================
            records = (
                db.session.query(
                    Penalty.penalty_id,
                    Penalty.regno,
                    Student.name.label("student_name"),
                    Detection.activity,
                    Location.loc_name.label("location"),
                    Penalty.penalty_message,
                    Penalty.Status.label("status")
                )
                .join(
                    Detection,
                    Penalty.detection_id == Detection.detection_id
                )
                .join(
                    Student,
                    Penalty.regno == Student.regno
                )
                .join(
                    Location,
                    Detection.location_id == Location.loc_id
                )

                # ✅ FILTER BY COMMITTEE CASE

                .filter(Detection.activity.in_(committee_cases))

                .filter(
                    Penalty.Status == "Pending"
                )

                .order_by(Student.name.asc())
                .all()
            )

            if not records:
                return jsonify({
                    "message": f"No {', '.join(committee_cases)} detections found"
                }), 404

            results = []

            for r in records:
                results.append({
                    "penalty_id": r.penalty_id,
                    "student_name": r.student_name,
                    "registration_number": r.regno,
                    "activity": r.activity,
                    "location": r.location,
                    "penalty_message": r.penalty_message,
                    "status": r.status
                })

            return jsonify({
                "total_pending_penalties": len(results),
                "pending_penalties": results
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    @staticmethod
    def resolve_penalty():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON body required"}), 400

            penalty_id = data.get("penalty_id")
            if not penalty_id:
                return jsonify({"error": "Provide 'penalty_id'"}), 400

            penalty = Penalty.query.filter_by(penalty_id=penalty_id).first()
            if not penalty:
                return jsonify({"error": "Penalty not found"}), 404

            if penalty.Status != "Pending":
                return jsonify({"error": "Only pending penalties can be resolved"}), 400

            penalty.Status = "Resolved"

            # ✅ Student ko resolve notification
            student = Student.query.filter_by(regno=penalty.regno).first()

            if student:
                location = Location.query.filter_by(
                    loc_id=penalty.detection.location_id
                ).first()
                location_name = location.loc_name if location else "Unknown"

                resolve_notif = Notification(
                    detection_id=penalty.detection_id,
                    notification_message=f"Your penalty for {penalty.detection.activity} at {location_name} has been resolved. You are now allowed.",
                    recipient_regno=penalty.regno,
                    recipient_role="student",
                    recipient_user_id=student.user_id
                )
                db.session.add(resolve_notif)
                                # ✅ ECL status bhi update karo — resolved ho gaya
                ecl_record = ECL.query.filter_by(
                    user_id=student.user_id,
                    activity=penalty.detection.activity
                ).first()
                if ecl_record:
                    ecl_record.status = "allowed"

            db.session.commit()

            return jsonify({
                "message": "Penalty resolved successfully",
                "penalty_id": penalty.penalty_id,
                "new_status": penalty.Status
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    @staticmethod
    def add_penalty_to_detection():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON body required"}), 400

            detection_id = data.get("detection_id")
            penalty_message = data.get("penalty_message")
            regno = data.get("regno")

            if not detection_id or not penalty_message or not regno:
                return jsonify({"error": "Provide detection_id, penalty_message and regno"}), 400

            detection = Detection.query.filter_by(detection_id=detection_id).first()
            if not detection:
                return jsonify({"error": "Detection not found"}), 404

            student = Student.query.filter_by(regno=regno).first()
            parent = Parent.query.filter_by(regno=regno).first()
            if not student:
                return jsonify({"error": f"Student {regno} not found"}), 404

            existing = Penalty.query.filter_by(
                detection_id=detection_id,
                regno=regno,

            ).first()
            if existing:
                return jsonify({"error": f"Penalty already exists for {regno}"}), 400

            # Save Penalty
            new_penalty = Penalty(
                detection_id=detection_id,
                regno=regno,
                penalty_message=penalty_message,
                Status="Pending"
            )
            db.session.add(new_penalty)

            # ECL update
            ecl_record = ECL.query.filter_by(
                user_id=student.user_id,
                activity=detection.activity
            ).first()

            if ecl_record:
                ecl_record.status = "not allowed"
            else:
                new_ecl = ECL(
                    user_id=student.user_id,
                    activity=detection.activity,
                    status="not allowed"
                )
                db.session.add(new_ecl)

            # Location fetch karo
            location = Location.query.filter_by(loc_id=detection.location_id).first()
            location_name = location.loc_name if location else "Unknown"

            # ✅ Student ko penalty notification
            penalty_notif = Notification(
                detection_id=detection_id,
                notification_message=f"A penalty has been issued to you for {detection.activity} at {location_name}. Details: {penalty_message}",
                recipient_regno=regno,
                recipient_role="student",
                recipient_user_id=student.user_id
            )

            parent_notif = Notification(
                detection_id=detection_id,
                notification_message=f"Your are called for a meeting.",
                recipient_regno=None,
                recipient_role="parent",
                recipient_user_id=parent.user_id
            )
            db.session.add(penalty_notif)
            db.session.add(parent_notif)
            db.session.commit()

            return jsonify({
                "message": f"Penalty added for {student.name}",
                "detection_id": detection_id,
                "regno": regno,
                "penalty_status": "Pending",
                "ecl_status": "not allowed"
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

