from flask import request, jsonify
from Vigilant_eye.Model.Notification import Notification
from Vigilant_eye.Model.Detection import Detection
from Vigilant_eye.Model.Users import Users
from Vigilant_eye.Model.Student import Student
from Vigilant_eye.Model.DisciplineCommittee import DisciplineCommittee
from Vigilant_eye.db import db
class Notification_Controller:
    @staticmethod
    def notifications_by_user():
        data = request.get_json()
        if not data:
            return jsonify({"notifications": []}), 400

        username = data.get('username')
        if not username:
            return jsonify({"notifications": []}), 400

        try:
            user = Users.query.filter_by(username=username).first()
            if not user:
                return jsonify({"notifications": []}), 404

            if user.role == "Committee":
                # ✅ DC — sirf apni activities ka
                notifications = (
                    db.session.query(
                        Notification.notification_message,
                        Detection.activity,
                        Notification.created_at
                    )
                    .join(Detection, Notification.detection_id == Detection.detection_id)
                    .filter(Notification.recipient_user_id == user.id)
                    .order_by(Notification.created_at.desc())
                    .all()
                )
            else:
                # ✅ Student — apni notifications
                student = Student.query.filter_by(user_id=user.id).first()
                if not student:
                    return jsonify({"notifications": []}), 404

                notifications = (
                    db.session.query(
                        Notification.notification_message,
                        Detection.activity,
                        Notification.created_at
                    )
                    .join(Detection, Notification.detection_id == Detection.detection_id)
                    .filter(Notification.recipient_regno == student.regno)
                    .order_by(Notification.created_at.desc())
                    .all()
                )

            results = []
            for n in notifications:
                results.append({
                    "notification_message": n.notification_message or "",
                    "activity": n.activity or "",
                    "created_at": n.created_at.strftime('%Y-%m-%d %H:%M:%S') if n.created_at else ""
                })

            return jsonify({"notifications": results}), 200

        except Exception as e:
            return jsonify({"notifications": [], "error": str(e)}), 500