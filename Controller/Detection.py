from flask import request, jsonify
from Vigilant_eye.Model.Student import Student
from Vigilant_eye.Model.Detection import Detection
from Vigilant_eye.Model.DetectionDetails import DetectionDetails
from Vigilant_eye.Model.Parent import Parent
from Vigilant_eye.Model.Location import Location

from Vigilant_eye.Model.Camera import Camera
from Vigilant_eye.Model.Penalties import Penalty
from Vigilant_eye.model_processing import process_video_router
from Vigilant_eye.Model.Notification import Notification
from Vigilant_eye.Model.DisciplineCommittee import DisciplineCommittee
from datetime import datetime
import os


from sqlalchemy import and_
from datetime import datetime

from flask import request, jsonify, current_app
import threading

from Vigilant_eye.model_processing import stream_status
from Vigilant_eye.model_processing import process_live_stream

from Vigilant_eye.db import db
class Detection_Controller:

    @staticmethod
    def detections_without_penalty_cases(user_id):
        try:

            # ==========================================
            # GET COMMITTEE OF LOGGED-IN USER
            # ==========================================
            committee = DisciplineCommittee.query.filter_by(
                user_id=user_id
            ).first()

            if not committee:
                return jsonify({"error": "Committee not found"}), 404

            committee_cases = [
                c.strip() for c in committee.case_solving.split(",")
            ]
            # ==========================================
            # FILTER DETECTIONS BY ACTIVITY
            # ==========================================
            records = (
                db.session.query(
                    Detection.detection_id,
                    Detection.activity.label("detected_activity"),
                    Location.loc_name.label("location_name"),
                    DetectionDetails.person_involved,
                    DetectionDetails.date,
                    DetectionDetails.time,
                    DetectionDetails.accuracy,
                    DetectionDetails.detect_video,
                )
                .join(
                    DetectionDetails,
                    DetectionDetails.detection_id == Detection.detection_id
                )
                .join(
                    Location,
                    Detection.location_id == Location.loc_id
                )

                # ✅ MAIN FILTER
                .filter(Detection.activity.in_(committee_cases))

                .order_by(Detection.detection_id.desc())
                .all()
            )

            if not records:
                return jsonify({
                    "message": f"No {', '.join(committee_cases)} detections found"
                }), 404

            results = []

            for r in records:

                regnos = (
                    [p.strip() for p in r.person_involved.split(",")]
                    if r.person_involved else []
                )

                students_without_penalty = []

                for regno in regnos:

                    existing_penalty = Penalty.query.filter_by(
                        detection_id=r.detection_id,
                        regno=regno
                    ).first()

                    if not existing_penalty:

                        student = Student.query.filter_by(
                            regno=regno
                        ).first()

                        if student:

                            students_without_penalty.append({
                                "student_name": student.name,
                                "registration_number": student.regno,
                                "section": student.section,
                                "semester": student.semester,
                            })

                        else:

                            students_without_penalty.append({
                                "student_name": "Unknown",
                                "registration_number": regno,
                                "section": "Unknown",
                                "semester": "Unknown",
                            })

                if students_without_penalty:
                    results.append({
                        "detection_id": r.detection_id,
                        "detected_activity": r.detected_activity,
                        "location": r.location_name,
                        "date": str(r.date),
                        "time": str(r.time),
                        "accuracy": round(r.accuracy * 100, 2)
                        if r.accuracy else 0,
                        "video_path": r.detect_video,
                        "students": students_without_penalty
                    })

            if not results:
                return jsonify({
                    "message": f"No {', '.join(committee_cases)} detections found"
                }), 404

            return jsonify(results), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    @staticmethod
    def detect_video():
            try:
                camera_name = request.form.get("camera_name")
                video = request.files.get("video")

                if not camera_name or not video:
                    return jsonify({"error": "camera_name and video required"}), 400

                # -------- CAMERA --------
                camera = Camera.query.filter_by(camera_name=camera_name).first()
                if not camera:
                    return jsonify({"error": "Camera not found"}), 404

                # -------- LOCATION --------
                location = Location.query.filter_by(camera_id=camera.camera_id).first()
                location_name = location.loc_name if location else "Unknown"

                # -------- SAVE VIDEO --------
                upload_path = "uploads"
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)

                video_path = os.path.join(upload_path, video.filename)
                video.save(video_path)

                # -------- MODEL --------
                results = process_video_router(video_path)

                # -------- RESPONSE --------
                output = []
                for r in results:
                    output.append({
                        "person": r["person"],
                        "activity": r["activity"],
                        "camera_name": camera.camera_name,
                        "location": location_name
                    })

                return jsonify({
                    "message": "Detection completed",
                    "camera": camera.camera_name,
                    "location": location_name,
                    "total_events": len(output),
                    "results": output
                }), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 500

    @staticmethod
    def detect_activity():
        try:
            video = request.files.get("video")
            camera_id = request.form.get("camera_id")

            if not video or not camera_id:
                return jsonify({"error": "camera_id and video required"}), 400

            camera = Camera.query.filter_by(camera_id=camera_id).first()
            if not camera:
                return jsonify({"error": "Camera not found"}), 404

            location = Location.query.filter_by(camera_id=camera.camera_id).first()
            location_id = location.loc_id if location else None
            location_name = location.loc_name if location else "Unknown"

            upload_path = "uploads"
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)

            video_path = os.path.join(upload_path, video.filename)
            video.save(video_path)

            result = process_video_router(video_path)

            # ✅ NORMAL → SAVE NAHI HOGI
            if result["activity"] == "Normal":

                # uploads folder se delete
                if os.path.exists(video_path):
                    os.remove(video_path)

                return jsonify({
                    "activity": "Normal",
                    "confidence": result["confidence"],
                    "people": result["people"],
                    "message": "No abnormal activity detected"
                }), 200
            print("ROUTER RESULT:", result)

            arid_list = result.get("people", [])
            students_data = []
            regnos = []

            for arid in arid_list:
                student = Student.query.filter_by(regno=arid).first()
                if student:
                    students_data.append({
                        "arid": student.regno,
                        "name": student.name,
                        "semester": student.semester,
                        "section": student.section
                    })
                    regnos.append(student.regno)
                else:
                    students_data.append({"arid": arid, "name": "Unknown"})

            if not regnos:
                regnos = ["Unknown"]

            # Save Detection
            detection = Detection(
                user_id=1,
                location_id=location_id,
                activity=result["activity"]
            )
            db.session.add(detection)
            db.session.commit()

            # Save DetectionDetails
            now = datetime.now()
            details = DetectionDetails(
                detection_id=detection.detection_id,
                person_involved=",".join(regnos),
                date=now.date(),
                time=now.time(),
                accuracy=result["confidence"],
                detect_video=video_path
            )
            db.session.add(details)

            # =============================
            # NOTIFICATIONS
            # =============================
            activity = result["activity"]
            total_people = len(arid_list) if arid_list else 0

            # ✅ Har detected student ko notification
            for regno in regnos:
                if regno == "Unknown":
                    continue
                student = Student.query.filter_by(regno=regno).first()
                if student:
                    student_notif = Notification(
                        detection_id=detection.detection_id,
                        notification_message=f"You have been detected in a case of {activity} at {location_name}.",
                        recipient_regno=regno,
                        recipient_role="student",
                        recipient_user_id=student.user_id
                    )
                    db.session.add(student_notif)
                if activity=='Female Harassment':
                    parent_notif = Notification(
                        detection_id=detection.detection_id,
                        notification_message=f"You are invited in meeting.",
                        recipient_regno=None,
                        recipient_role="Parent",
                        recipient_user_id=Parent.user_id
                    )
                    db.session.add(parent_notif)

            # ✅ Relevant DC ko notification — case_solving match karo
            committees = DisciplineCommittee.query.all()
            for committee in committees:
                if not committee.case_solving:
                    continue
                solving_list = [
                    s.strip().lower()
                    for s in committee.case_solving.split(",")
                ]
                if activity.lower() in solving_list:
                    committee_notif = Notification(
                        detection_id=detection.detection_id,
                        notification_message=f"{total_people} person(s) detected in a case of {activity} at {location_name}.",
                        recipient_regno=None,
                        recipient_role="discipline_committee",
                        recipient_user_id=committee.user_id  # ✅ specific DC
                    )
                    db.session.add(committee_notif)

            db.session.commit()

            return jsonify({
                "camera": camera.camera_name,
                "location": location_name,
                "activity": result["activity"],
                "confidence": round(result["confidence"] * 100, 2),
                "students": students_data
            }), 200

        except Exception as e:
            print("ERROR:", e)
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def remove_wrong_person():

        try:

            data = request.get_json()

            if not data:
                return jsonify({"error": "JSON body required"}), 400

            detection_id = data.get("detection_id")
            regno = data.get("regno")

            if not detection_id or not regno:
                return jsonify({
                    "error": "detection_id and regno required"
                }), 400

            details = DetectionDetails.query.filter_by(
                detection_id=detection_id
            ).first()

            if not details:
                return jsonify({
                    "error": "Detection details not found"
                }), 404

            people = [
                p.strip()
                for p in details.person_involved.split(",")
                if p.strip().lower() != regno.lower() and p.strip().lower() != "Unknown"
            ]

            # ✅ IF NO PERSON LEFT -> DELETE FULL CASE
            if not people:
                db.session.delete(details)

                # OPTIONAL:
                # delete main detection row too
                # detection = Detection.query.get(detection_id)
                # if detection:
                #     db.session.delete(detection)

                db.session.commit()

                return jsonify({
                    "message": f"Full detection {detection_id} deleted"
                }), 200

            # ✅ OTHERWISE UPDATE REMAINING PEOPLE
            details.person_involved = ",".join(people)

            db.session.commit()

            return jsonify({
                "message": f"{regno} removed successfully",
                "remaining_people": people
            }), 200

        except Exception as e:

            db.session.rollback()

            return jsonify({
                "error": str(e)
            }), 500
    @staticmethod
    def add_student_to_detection():
        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "JSON body required"}), 400

            detection_id = data.get("detection_id")

            # Student Data
            name = data.get("name")
            regno = data.get("regno")
            semester = data.get("semester")
            section = data.get("section")

            if not detection_id:
                return jsonify({"error": "detection_id required"}), 400

            if not all([name, regno, semester, section]):
                return jsonify({
                    "error": "name, regno, semester, section required"
                }), 400

            # =============================
            # FIND DETECTION DETAILS
            # =============================
            details = DetectionDetails.query.filter_by(
                detection_id=detection_id
            ).first()

            if not details:
                return jsonify({
                    "error": "Detection details not found"
                }), 404

            # =============================
            # CHECK STUDENT EXISTS
            # =============================
            student = Student.query.filter_by(regno=regno).first()

            # Agar student exist nahi karta to create karo
            if not student:
                student = Student(
                    name=name,
                    regno=regno,
                    semester=semester,
                    section=section
                )

                db.session.add(student)
                db.session.commit()

            # =============================
            # PERSON INVOLVED UPDATE
            # =============================
            current_people = []

            if details.person_involved:
                current_people = [
                    p.strip()
                    for p in details.person_involved.split(",")
                    if p.strip() and p.strip() != "Unknown"
                ]

            # Duplicate avoid
            if regno not in current_people:
                current_people.append(regno)

            details.person_involved = ",".join(current_people)

            db.session.commit()

            return jsonify({
                "message": "Student added successfully",
                "student": {
                    "name": student.name,
                    "regno": student.regno,
                    "semester": student.semester,
                    "section": student.section
                },
                "updated_people": current_people
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500



    @staticmethod
    def start_stream():
        data = request.get_json()

        camera_id = data.get("camera_id")
        rtsp_url = data.get("rtsp_url")

        if not camera_id or not rtsp_url:
            return jsonify({"error": "missing data"}), 400

        if stream_status.get(camera_id, {}).get("running"):
            return jsonify({"message": "Already running"}), 200

        # ✅ Camera & Location fetch karo
        camera = Camera.query.filter_by(camera_id=camera_id).first()
        location = Location.query.filter_by(camera_id=camera_id).first()

        location_id = location.loc_id if location else None
        location_name = location.loc_name if location else "Unknown"

        print("DEBUG LOCATION:", location_id, location_name)

        app = current_app._get_current_object()

        stream_status[camera_id] = {"running": True}

        thread = threading.Thread(
            target=process_live_stream,
            args=(rtsp_url, camera_id, location_id, location_name, app),  # ✅ FIXED
            daemon=True
        )
        thread.start()

        return jsonify({
            "message": f"Camera {camera_id} started",
            "location_id": location_id
        })
    @staticmethod
    def stop_stream():
        data = request.get_json()
        camera_id = data.get("camera_id")

        if not camera_id:
            return jsonify({"error": "camera_id required"}), 400

        if not stream_status.get(camera_id):
            return jsonify({"message": "Camera not running"}), 200

        stream_status[camera_id]["running"] = False

        return jsonify({"message": f"Camera {camera_id} stopped"})

    @staticmethod
    def detections_without_penalty():
        try:
            records = (
                db.session.query(
                    Detection.detection_id,
                    Detection.activity.label("detected_activity"),
                    Location.loc_name.label("location_name"),
                    DetectionDetails.person_involved,
                    DetectionDetails.date,
                    DetectionDetails.time,
                    DetectionDetails.accuracy,
                    DetectionDetails.detect_video,
                )
                .join(DetectionDetails, DetectionDetails.detection_id == Detection.detection_id)
                .join(Location, Detection.location_id == Location.loc_id)
                .order_by(Detection.detection_id.desc())
                .all()
            )

            if not records:
                return jsonify({"message": "No detections found without penalties"}), 404

            results = []
            for r in records:
                regnos = [p.strip() for p in r.person_involved.split(",")] if r.person_involved else []

                students_without_penalty = []
                for regno in regnos:
                    # ✅ Per student per detection penalty check
                    existing_penalty = Penalty.query.filter_by(
                        detection_id=r.detection_id,
                        regno=regno
                    ).first()

                    if not existing_penalty:
                        student = Student.query.filter_by(regno=regno).first()
                        if student:
                            students_without_penalty.append({
                                "student_name": student.name,
                                "registration_number": student.regno,
                                "section": student.section,
                                "semester": student.semester,
                            })
                        else:
                            students_without_penalty.append({
                                "student_name": "Unknown",
                                "registration_number": regno,
                                "section": "Unknown",
                                "semester": "Unknown",
                            })

                # ✅ Sirf tab dikhao jab koi student bina penalty ke ho
                if students_without_penalty:
                    results.append({
                        "detection_id": r.detection_id,
                        "detected_activity": r.detected_activity,
                        "location": r.location_name,
                        "date": str(r.date),
                        "time": str(r.time),
                        "accuracy": round(r.accuracy * 100, 2) if r.accuracy else 0,
                        "video_path": r.detect_video,
                        "students": students_without_penalty
                    })

            if not results:
                return jsonify({"message": "No detections found without penalties"}), 404

            return jsonify(results), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    @staticmethod
    def get_student_activity(aridno):

        try:

            # =====================================================
            # DATE FILTER
            # =====================================================
            start_date = request.args.get("start_date")
            end_date = request.args.get("end_date")

            # =====================================================
            # FIND STUDENT
            # =====================================================
            student = Student.query.filter_by(
                regno=aridno
            ).first()

            if not student:
                return jsonify({
                    "error": "Student not found"
                }), 404

            # =====================================================
            # QUERY
            # =====================================================
            query = db.session.query(

                Detection.detection_id,
                Detection.activity,
                Detection.created_at,

                DetectionDetails.date,
                DetectionDetails.time,
                DetectionDetails.accuracy,
                DetectionDetails.detect_img,
                DetectionDetails.detect_video,

                Location.loc_name,

                Penalty.penalty_id,
                Penalty.Status,
                Penalty.regno

            ).join(

                Penalty,
                Detection.detection_id == Penalty.detection_id

            ).join(

                DetectionDetails,
                Detection.detection_id == DetectionDetails.detection_id

            ).outerjoin(

                Location,
                Detection.location_id == Location.loc_id

            ).filter(

                Penalty.regno == aridno

            )

            # =====================================================
            # DATE FILTER
            # =====================================================
            if start_date and end_date:
                start = datetime.strptime(
                    start_date,
                    "%Y-%m-%d"
                ).date()

                end = datetime.strptime(
                    end_date,
                    "%Y-%m-%d"
                ).date()

                query = query.filter(
                    DetectionDetails.date.between(start, end)
                )

            # =====================================================
            # GET RECORDS
            # =====================================================
            records = query.order_by(
                Detection.created_at.desc()
            ).all()

            # =====================================================
            # COUNTS
            # =====================================================
            total_activities = 0
            pending_activities = 0
            resolved_activities = 0

            activities = []

            # =====================================================
            # LOOP
            # =====================================================
            for row in records:

                total_activities += 1

                # =================================================
                # STATUS
                # =================================================
                if row.Status:

                    if row.Status.lower() == "resolved":

                        status = "Resolved"
                        resolved_activities += 1

                    else:

                        status = "Pending"
                        pending_activities += 1

                else:

                    status = "Pending"
                    pending_activities += 1

                # =================================================
                # APPEND
                # =================================================
                activities.append({

                    "detection_id": row.detection_id,

                    "activity": row.activity,

                    "status": status,

                    "date": str(row.date),

                    "time": str(row.time),

                    "accuracy": row.accuracy,

                    "location": row.loc_name
                    if row.loc_name else "Unknown",

                    "detect_image": row.detect_img,

                    "detect_video": row.detect_video

                })

            # =====================================================
            # RESPONSE
            # =====================================================
            return jsonify({

                "student": {

                    "aridno": student.regno,
                    "name": student.name,
                    "semester": student.semester,
                    "section": student.section,
                    "phone": student.phone

                },

                "filter": {

                    "start_date": start_date,
                    "end_date": end_date

                },

                "counts": {

                    "total": total_activities,
                    "pending": pending_activities,
                    "resolved": resolved_activities

                },

                "activities": activities

            }), 200

        except Exception as e:

            print("ERROR:", e)

            return jsonify({
                "error": str(e)
            }), 500